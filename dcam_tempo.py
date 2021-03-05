import time
import datetime
from threading import Thread
from tkinter import Tk, StringVar, Label, Entry, Button
import dcam_distribution as distr
from dcam_framework import timedelta_to_str, Task

default_time = datetime.datetime.now()
used_time = Task('', distr.available_time_range[1] - distr.available_time_range[0])

current_index = 0
current_item_code = '000'
duration = datetime.timedelta()

tk = Tk()
tk.minsize(450, 250)
tk.title('DCAM-Cephret临时计时器（v2021.3.5）')
label_text = StringVar(tk, '', '')
lbl1 = Label(tk, textvariable=label_text)
lbl1.pack()

labels = []
label_texts = []
commands = []


class Command:
    def __init__(self, index, item_code):
        self.index = index
        self.item_code = item_code

    def run(self, param):
        global current_index, current_item_code
        current_index = self.index
        current_item_code = self.item_code
        if datetime.datetime.now() in distr.available_time:
            print('开始计时并消耗时间')
            used_time.start()
        else:
            print('你现在没有时间做这件事情')


prices = {'000': ('(无)', 0)}
prices.update(distr.read_prices())

for code in prices:
    label_txt = StringVar(tk)
    label = Label(tk, textvariable=label_txt)
    label.pack()
    labels.append(label)
    command = Command(len(labels) - 1, code)
    label.bind('<Button-1>', command.run)
    label_txt.set(code + '  ' + prices[code][0] + '  [价格：' + str(prices[code][1]) + ']')
    label_texts.append(label_txt)


def pause():
    global current_index, current_item_code
    current_index = 0
    current_item_code = '000'
    used_time.pause()
    print('已暂停任务计时，但你仍在消耗可用时间')


def purchase_current_item():
    global used_time, current_index, current_item_code
    distr.transact(current_item_code, used_time.get_duration())
    current_index = 0
    current_item_code = '000'
    used_time.end()
    print('交易成功！任务计时已清零，但你仍在消耗可用时间')


btn1 = Button(tk, text='暂停计时', command=pause)
btn1.pack()
btn2 = Button(tk, text='结算当前交易项', command=purchase_current_item)
btn2.pack()
var1 = StringVar(tk, '', '')
ent1 = Entry(tk, textvariable=var1)
var1.set(str(default_time.replace(minute=default_time.minute + 1, second=0)).split('.')[0])
ent1.pack()
var2 = StringVar(tk, '', '')
ent2 = Entry(tk, textvariable=var2)
var2.set(str(default_time.replace(minute=default_time.minute + 1, second=0) + datetime.timedelta(minutes=10)).split('.')[0])
ent2.pack()


def buy_time():
    start_time = datetime.datetime.strptime(var1.get(), '%Y-%m-%d %H:%M:%S')
    end_time = datetime.datetime.strptime(var2.get(), '%Y-%m-%d %H:%M:%S')
    distr.available_time.new_fragment(start_time, end_time, purchased=True)


def buy_all_idle_time():
    distr.available_time.purchase_all_idle_time()


btn3 = Button(tk, text='购买时间', command=buy_time)
btn3.pack()
btn4 = Button(tk, text='购买今日所有空闲时间', command=buy_all_idle_time)
btn4.pack()


def loop():
    while True:
        # print(distr.available_time.get_purchased_duration(), distr.available_time.get_used_duration())
        a_t_str = timedelta_to_str(distr.available_time.get_purchased_duration() - distr.available_time.get_used_duration())
        u_t_str = timedelta_to_str(used_time.get_duration())
        label_text.set('余额：' + format(distr.balance, '.1f')
                       + ' | 可用时长：' + a_t_str
                       + ' | [当前交易项：' + current_item_code
                       + ' ' + prices[current_item_code][0] + ' (已进行时间：' + u_t_str + ')]')

        time.sleep(0.1)

        '''print('Fragments: ', end='')
        for fragment in distr.available_time.fragments:
            print(str(fragment), end=', ')
        print('\b\b')'''


def sync_from_server_loop():
    while True:
        distr.available_time.sync_from_server(distr.distribution_filename, distr.balance_filename)


thread = Thread(target=loop, args=())
sync_from_server_thread = Thread(target=sync_from_server_loop, args=())
thread.start()
sync_from_server_thread.start()
tk.mainloop()