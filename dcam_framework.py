import random
import datetime


class Timestamp:
    stamp = None
    stamp_type = 'start'

    def __init__(self, stamp, stamp_type):
        self.stamp = stamp
        self.stamp_type = stamp_type

    def __sub__(self, other):
        if other.stamp_type == 'start' and self.stamp_type == 'end':
            return self.stamp - other.stamp
        else:
            return other.stamp - self.stamp

    def __str__(self):
        return str(self.stamp) + '|' + self.stamp_type


class Task:

    def __init__(self, name: str, full_duration: datetime.timedelta, subject=''):
        self.name = name
        self.subject = subject
        self.timestamps = []
        self.running = False
        self.full_duration = full_duration

    def start(self):
        '''for ts in self.timestamps:
            print(ts)'''
        if not self.running:
            self.timestamps.append(Timestamp(datetime.datetime.now(), 'start'))
            self.running = True
            # print(len(self.timestamps), self.running)

    def get_duration(self, start=datetime.datetime.now(), end=datetime.datetime.now()):
        d = datetime.timedelta()
        for timestamp in self.timestamps:
            if timestamp.stamp_type == 'start':
                start = timestamp.stamp
            elif timestamp.stamp_type == 'end':
                d += timestamp.stamp - start
        if self.timestamps:
            last = self.timestamps[-1]
            if last.stamp_type == 'start':
                d += end - last.stamp
        return d

    def end(self):
        self.timestamps.clear()
        self.running = False

    def pause(self):
        if len(self.timestamps) > 0 and self.running:
            self.timestamps.append(Timestamp(datetime.datetime.now(), 'end'))
            self.running = False


def timedelta_to_str(td: datetime.timedelta, mode=''):
    if mode == 'by_minutes':
        return str(td.total_seconds() / 60) + ' min'
    elif mode == 'by_hours':
        return str(td.total_seconds() / 3600) + ' h'
    elif mode == 'by_seconds':
        return str(td.total_seconds()) + ' s'
    else:
        if td.days:
            days = str(td.days) + 'd '
        else:
            days = ''

        hours_num = int(td.total_seconds() // 3600 % 24)
        if hours_num:
            hours = str(hours_num) + 'h '
        else:
            hours = ''

        minutes_num = int(td.total_seconds() // 60 % 60)
        if minutes_num:
            minutes = str(minutes_num) + 'min '
        else:
            minutes = ''

        seconds_num = int(td.total_seconds() % 60)
        if seconds_num:
            seconds = str(seconds_num) + 's '
        else:
            if td.days or hours_num or minutes_num:
                seconds = ''
            else:
                seconds = '0s'
        time_str = days + hours + minutes + seconds
        if time_str.endswith(' '):
            time_str = time_str[:-1]
        return time_str


class Note:

    def __init__(self, content: str, time: datetime.datetime):
        self.content = content
        self.time = time


class Event:
    def __init__(self, name, fixed_total_full_duration: datetime.timedelta
                 , type='未命名事件'
                 , frequency='permanent'
                 , color="#%02x%02x%02x" % (180, 180, 180)
                 , start_time=datetime.datetime.now()
                 , end_time=datetime.datetime.now() + datetime.timedelta(minutes=20)):
        self.name = name
        self.type = type
        self.color = color
        self.start_time = start_time
        self.end_time = end_time
        self.frequency = frequency
        self.tasks = []
        self.fixed_total_full_duration = fixed_total_full_duration

    def change_color_by_random(self):
        self.color = "#%02x%02x%02x" % (random.randint(40, 220), random.randint(40, 220), random.randint(40, 220))

    def get_duration(self):
        duration = datetime.timedelta()
        for task in self.tasks:
            duration += task.get_duration(end=self.end_time)
        return duration

    def get_total_subject_duration(self, plan_filename: str):
        subject_names = []
        with open(plan_filename, 'rt', encoding='utf-8') as file_input:
            subject_names = [line.strip().split('\t')[0] for line in file_input.readlines()]

        duration = datetime.timedelta()
        for task in self.tasks:
            if task.subject in subject_names:
                duration += task.get_duration(end=self.end_time)

        return duration


def numerical_grad_1d(f, x, delta=1e-6):
    f_l, f_r = f(x + delta), f(x - delta)
    grad = (f_l - f_r) / (2 * delta)
    return grad
