import datetime
import socket
from dcam_framework import timedelta_to_str

server_address_balance, server_address_distribution = ('120.25.26.164', 8202), ('120.25.26.164', 8203)
mode = 'local' # 'local', 'server'
distribution_filename = 'dcam_data/distributions/time_collection.txt'
balance_filename = 'dcam_data/finance/balance.txt'
available_time_range = (datetime.datetime.now().replace(hour=8, minute=25, second=0, microsecond=0)
                        , datetime.datetime.now().replace(hour=23, minute=00, second=0, microsecond=0))
default_datetime = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


class TimeFragment:
    def __init__(self, start_time:datetime.datetime, end_time: datetime.datetime, purpose='', purchased=False):
        self.start = start_time
        self.end = end_time
        self.purpose = purpose
        self.purchased = purchased

    def __contains__(self, item):
        if self.start <= item < self.end:
            return True
        return False

    def __str__(self):
        return '(' + str(self.start).split('.')[0] + ' - ' + str(self.end).split('.')[0] + ' [' + timedelta_to_str(self.end - self.start) + '])'


def change_balance(purc_: bool, purc: bool, duration: datetime.timedelta):
    global balance
    balance_change = -0.2 * duration.total_seconds() / 60
    if balance + balance_change >= 0:
        if not purc_ and purc:
            balance += balance_change
            update_balance()
            return 1
        elif purc_ and not purc:
            balance -= balance_change
            update_balance()
            return -1
    return 0


class TimeCollection:
    def __init__(self, start_time=default_datetime, end_time=default_datetime):
        self.fragments = [TimeFragment(start_time, end_time)]

    def __contains__(self, item):
        for fragment in self.fragments:
            if not fragment.purchased:
                continue
            if fragment.start <= item <= fragment.end:
                return True
        return False

    def save_to_file(self, filename: str):
        output = ''
        for fragment in self.fragments:
            output += str(fragment.start) + ',' + str(fragment.end) + ',' + fragment.purpose + ',' + str(fragment.purchased) + '\n'
        with open(filename, 'wt', encoding='utf-8') as file_output:
            file_output.write(output)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(server_address_distribution)
        s.send(('d' + output).encode('utf-8'))
        s.close()

    def sync_from_server(self, distribution_filename_: str, balance_filename_: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(server_address_balance)
        global balance
        balance = float(s.recv(1024).decode('utf-8'))
        with open(balance_filename_, 'wt', encoding='utf-8') as file_output:
            file_output.write(str(balance))
        output = s.recv(16384).decode('utf-8')
        s.close()
        with open(distribution_filename_, 'wt', encoding='utf-8') as file_output:
            file_output.write(output)
        self.read_from_file(distribution_filename_)

    def read_from_file(self, filename: str):
        with open(filename, 'rt', encoding='utf-8') as file_input:
            lines = [line.strip() for line in file_input.readlines()]
        self.fragments.clear()
        for line in lines:
            attrs = line.split(',')
            start = datetime.datetime.strptime(attrs[0], '%Y-%m-%d %H:%M:%S')
            end = datetime.datetime.strptime(attrs[1], '%Y-%m-%d %H:%M:%S')
            if attrs[3] == 'True':
                purchased = True
            else:
                purchased = False
            self.fragments.append(TimeFragment(start, end, purpose=attrs[2], purchased=purchased))

        zero = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        for i, fragment in enumerate(self.fragments):
            if fragment.start < zero or fragment.end < zero:
                self.fragments = [TimeFragment(available_time_range[0], available_time_range[1])]
                self.save_to_file(filename)
                break

    def new_fragment(self, start_time: datetime.datetime, end_time: datetime.datetime, purpose='', purchased=False):
        _start = self.fragments[0].start
        nearest_start = -1
        for i, fragment in enumerate(self.fragments):
            if start_time not in fragment or end_time not in fragment:
                continue
            if fragment.start >= _start:
                _start = fragment.start
                nearest_start = i

        end_, purpose_, purchased_ = self.fragments[nearest_start].end, self.fragments[nearest_start].purpose, self.fragments[nearest_start].purchased

        if available_time_range[1] <= start_time < available_time_range[0].replace(
                day=available_time_range[0].day + 1) or available_time_range[1] <= end_time < available_time_range[0].replace(
            day=available_time_range[0].day + 1):
            print('时间不在可交易范围内')
            return

        if purchased_ ^ purchased:
            if change_balance(purchased_, purchased, end_time - start_time):
                print('时间购买成功！')
            else:
                print('余额不足，无法购买时间')
                return
        elif purchased_:
            print('该时间段已被购买，不可重复购买')
            return

        self.fragments[nearest_start].end = start_time
        self.fragments.append(TimeFragment(start_time, end_time, purpose=purpose, purchased=purchased))
        self.fragments.append(TimeFragment(end_time, end_, purpose=purpose_, purchased=purchased_))

        self.save_to_file(distribution_filename)

    def purchase_all_idle_time(self):
        d = datetime.timedelta()
        for fragment in self.fragments:
            d += fragment.end - fragment.start
        if change_balance(False, True, d):
            for fragment in self.fragments:
                if not fragment.purchased:
                    fragment.purchased = True
            print('时间购买成功！')
        else:
            print('余额不足，无法购买时间')
        self.save_to_file(distribution_filename)

    def get_current_fragment(self):
        for fragment in self.fragments:
            if fragment.start <= datetime.datetime.now() < fragment.end:
                return fragment
        return None

    def get_total_duration(self):
        d = datetime.timedelta()
        for fragment in self.fragments:
            d += fragment.end - fragment.start
        return d

    def get_purchased_duration(self):
        d = datetime.timedelta()
        for fragment in self.fragments:
            if not fragment.purchased:
                continue
            d += fragment.end - fragment.start
        return d

    '''def get_used_duration(self):
        d = datetime.timedelta()
        now = datetime.datetime.now()
        for fragment in self.fragments:
            if not fragment.purchased:
                continue
            if now >= fragment.end:
                d += fragment.end - fragment.start
            else:
                d += now - fragment.start
        return d'''

    def get_used_duration(self):
        d = datetime.timedelta()
        now = datetime.datetime.now()
        for fragment in self.fragments:
            if not fragment.purchased:
                continue
            if now in fragment:
                d += now - fragment.start
            elif fragment.end < now:
                d += fragment.end - fragment.start
        return d


with open(balance_filename, 'rt', encoding='utf-8') as file_input:
    balance = float(file_input.readline())


def read_prices():
    with open('dcam_data/finance/prices.txt', 'rt', encoding='utf-8') as file_input:
        prices_list = [line.strip() for line in file_input.readlines()]
    prices = {}
    for price_line in prices_list:
        code_purpose_price = price_line.split('\t')
        prices[code_purpose_price[0]] = (code_purpose_price[1], float(code_purpose_price[2]))
    return prices


prices = read_prices()
'''available_time = TimeCollection(available_time_range[0], available_time_range[1])
available_time.save_to_file(distribution_filename)'''
available_time = TimeCollection()
available_time.read_from_file(distribution_filename)

curricula = []


def distribute(purpose: str, time_delta: datetime.timedelta):
    time_usage = TimeCollection()
    return time_usage


def update_balance():
    global balance
    with open(balance_filename, 'wt', encoding='utf-8') as file_output:
        file_output.write(str(balance))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(server_address_distribution)
    s.send(('b' + str(balance)).encode('utf-8'))
    s.close()

def transact(code: str, duration: datetime.timedelta):
    if available_time_range[1] <= datetime.datetime.now() < available_time_range[0].replace(day=available_time_range[0].day + 1):
        print('现在不是可交易时间')
        return

    global balance
    if not code or code not in prices or not duration.total_seconds():
        return

    balance_change = prices[code][1] * duration.total_seconds() / 60
    if balance + balance_change >= 0:
        balance += balance_change
        print('交易成功！')
    else:
        print('余额不足，无法完成交易')
    update_balance()


if __name__ == '__main__':
    inp = input('请输入交易代码：')
