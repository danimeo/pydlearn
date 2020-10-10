import datetime, time
import random
from threading import Thread, Lock
from tkinter import Tk, Entry, Button, Label, StringVar, messagebox, Canvas, ALL, Checkbutton, IntVar
import math
import pyttsx3

from dcam_framework import Timestamp, Task, Event

width = 800
height = 800
canvas_x = 0
canvas_y = 210
graph_radius = 150
graph_ring_width = 20
refreshing_interval = 0.2
painting_interval = 60
schedule_filename = 'dcam_data/schedules/dcam_schedule_20201007.txt'
timer_records_filename = 'dcam_data/records/dcam_timer_records.txt'
fore_notifying_minutes = 1

refreshing = False
now = initial_time = datetime.datetime.now()
zero_duration = initial_time - initial_time

events = []
current_event_index = 0
running_event = None
notifying = False
lock = Lock()

engine = pyttsx3.init()
rate = engine.getProperty('rate')
engine.setProperty('rate', rate - 10)


tk = Tk()
tk.title('DCAM-Cephret时间分配器（v2020.10.8）')
tk.minsize(width, height)
canvas = Canvas(tk, width=width, height=height-canvas_y, bg='white')
canvas.place(x=canvas_x, y=canvas_y, anchor='nw')
tk.update()
label_text = StringVar(tk, '', '')
lbl1 = Label(tk, textvariable=label_text)
var1 = StringVar()
var2 = StringVar()
var3 = StringVar()
ent1 = Entry(tk, textvariable=var1)
ent2 = Entry(tk, textvariable=var2)
ent3 = Entry(tk, textvariable=var3)
check_var1 = IntVar()
cb1 = Checkbutton(text='永久', variable=check_var1)


def change_current_event_color_by_random():
    events[current_event_index].change_color_by_random()
    draw_graph()


btn_random_color = Button(tk, text='随机更改颜色', command=change_current_event_color_by_random)


def fill_with_default_event():
    var1.set('新事件')
    if initial_time.minute >= 59:
        init_time = initial_time.replace(hour=initial_time.hour + 1, minute=0, second=0)
    else:
        init_time = initial_time.replace(minute=initial_time.minute + 1, second=0)

    var2.set(str(init_time).split('.')[0])
    var3.set(str(init_time + datetime.timedelta(minutes=20)).split('.')[0])


fill_with_default_event()


def conflicts(_event, _events):
    for e in _events:
        if _event.end_time > e.start_time and e.end_time > _event.start_time:
            return True
    return False


labels = []
label_vars = []
commands = []


class Command:
    def __init__(self, index, name):
        self.index = index
        self.name = name

    def run(self, param):
        global current_event_index, label_text
        print('CHOSEN:', self.index)
        current_event_index = self.index
        var1.set(events[self.index].name)
        var2.set(str(events[self.index].start_time).split('.')[0])
        var3.set(str(events[self.index].end_time).split('.')[0])
        if events[self.index].frequency == 'only_once':
            check_var1.set(0)
        else:
            check_var1.set(1)
        labels[current_event_index].lift()


def get_name(e: Event, separation='\n'):
    if str(e.start_time.date()) == str(e.end_time.date()) == str(datetime.datetime.now().date()):
        start_time_str = str(e.start_time.time()).split('.')[0]
        end_time_str = str(e.end_time.time()).split('.')[0]
    else:
        start_time_str = str(e.start_time).split('.')[0]
        end_time_str = str(e.end_time).split('.')[0]
    if start_time_str.endswith(':00') and end_time_str.endswith(':00'):
        start_time_str = start_time_str[:-3]
        end_time_str = end_time_str[:-3]
    return e.name + separation + '(' + start_time_str + ' ~ ' + end_time_str + ')'


center_x = canvas.winfo_width() / 2
center_y = canvas.winfo_height() / 2
inner_radius = graph_radius - graph_ring_width
shapes_to_delete = []


def draw_graph():
    global now, shapes_to_delete

    for shape in shapes_to_delete:
        canvas.delete(shape)
    shapes_to_delete.clear()

    for a, event in enumerate(events):
        zero_oclock = event.start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        start_time_duration_seconds = (event.start_time - zero_oclock).total_seconds()
        end_time_duration_seconds = (event.end_time - zero_oclock).total_seconds()
        start_time_angle = start_time_duration_seconds / 86400 * 2 * math.pi - math.pi / 2
        end_time_angle = end_time_duration_seconds / 86400 * 2 * math.pi - math.pi / 2

        start_time_point_inner = center_x + inner_radius * math.cos(start_time_angle)\
            , center_y + inner_radius * math.sin(start_time_angle)
        end_time_point_inner = center_x + inner_radius * math.cos(end_time_angle)\
            , center_y + inner_radius * math.sin(end_time_angle)

        arc = [start_time_point_inner[0], start_time_point_inner[1]]
        n = (end_time_angle - start_time_angle) / (2 * math.pi) * 360
        for i in range(0, int(n) + 1):
            arc.append(center_x + graph_radius * math.cos(start_time_angle + (end_time_angle - start_time_angle) / n * i))
            arc.append(center_y + graph_radius * math.sin(start_time_angle + (end_time_angle - start_time_angle) / n * i))
        arc.append(end_time_point_inner[0])
        arc.append(end_time_point_inner[1])
        for i in range(0, int(n) + 1):
            arc.append(center_x + inner_radius * math.cos(end_time_angle - (end_time_angle - start_time_angle) / n * i))
            arc.append(center_y + inner_radius * math.sin(end_time_angle - (end_time_angle - start_time_angle) / n * i))

        if n < 2:
            event_arc = canvas.create_line(start_time_point_inner[0], start_time_point_inner[1]
                               , center_x + graph_radius * math.cos(start_time_angle)
                               , center_y + graph_radius * math.sin(start_time_angle), width=2, fill=event.color)
        else:
            event_arc = canvas.create_polygon(tuple(arc), fill=event.color, outline='')
        shapes_to_delete.append(event_arc)

        label_x = center_x + (graph_radius + labels[a].winfo_width()) * math.cos(start_time_angle + (end_time_angle - start_time_angle) / 2)
        label_y = center_y + (graph_radius + labels[a].winfo_height()) * math.sin(start_time_angle + (end_time_angle - start_time_angle) / 2)
        middle_point_of_arc_x = center_x + graph_radius * math.cos(start_time_angle + (end_time_angle - start_time_angle) / 2)
        middle_point_of_arc_y = center_y + graph_radius * math.sin(start_time_angle + (end_time_angle - start_time_angle) / 2)
        label_line = canvas.create_line(middle_point_of_arc_x, middle_point_of_arc_y, label_x, label_y)
        shapes_to_delete.append(label_line)
        labels[a].place(x=canvas_x + label_x - labels[a].winfo_width() / 2, y=canvas_y + label_y - labels[a].winfo_height() / 2, anchor='nw')
        label_vars[a].set(get_name(event))


with open(schedule_filename, 'rt', encoding='utf-8') as file_input:
    while True:
        line = file_input.readline()
        if not line:
            break
        properties = line[:-1].split(' || ')
        e = Event(properties[0])
        e.color = properties[1]
        e.start_time = datetime.datetime.strptime(properties[2], '%Y-%m-%d %H:%M:%S')
        e.end_time = datetime.datetime.strptime(properties[3], '%Y-%m-%d %H:%M:%S')
        e.frequency = properties[4]
        events.append(e)

        name = get_name(e)
        var = StringVar()
        label = Label(tk, textvariable=var)
        var.set(name)
        cmd = Command(len(events) - 1, name)
        label.bind('<Button-1>', cmd.run)
        label.pack()
        labels.append(label)
        label_vars.append(var)
        commands.append(cmd)
        cmd.run(None)

records_list = []
with open(timer_records_filename, 'rt', encoding='utf-8') as file_input:
    records_list = [line.strip() for line in file_input.readlines()]

for record in records_list:
    r_list = record.split('\t')
    event = Event(r_list[2],
                  datetime.datetime.strptime(r_list[4], '%H:%M:%S') - datetime.datetime.strptime('0:00:00',
                                                                                                 '%H:%M:%S'),
                  type=r_list[3])
    event.start_time = datetime.datetime.strptime(r_list[0], '%Y-%m-%d %H:%M:%S.%f')
    event.end_time = datetime.datetime.strptime(r_list[1], '%Y-%m-%d %H:%M:%S.%f')

    if event.end_time >= datetime.datetime.now().replace(day=datetime.datetime.now().day + 1, hour=0, minute=0, second=0, microsecond=0) or event.start_time < datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
        continue

    t_list = r_list[5].split('; ')
    event.tasks = [Task('', datetime.timedelta())] * len(t_list)
    for t in t_list:
        item_list = t.split(',')
        if '.' in item_list[3]:
            s_t = datetime.datetime.strptime(item_list[3], '%H:%M:%S.%f')
        else:
            s_t = datetime.datetime.strptime(item_list[3], '%H:%M:%S')
        task = Task(item_list[1],
                    s_t - datetime.datetime.strptime(
                        '0:00:00',
                        '%H:%M:%S'),
                    subject=item_list[2])
        task.timestamps = [
            Timestamp(datetime.datetime.strptime(ts.split('|')[0], '%Y-%m-%d %H:%M:%S.%f'),
                      ts.split('|')[1])
            for ts in item_list[4].split('~')]
        event.tasks[int(item_list[0])] = task
    events.append(event)

    name = get_name(event)
    var = StringVar()
    label = Label(tk, textvariable=var)
    var.set(name)
    cmd = Command(len(events) - 1, name)
    label.bind('<Button-1>', cmd.run)
    label.pack()
    labels.append(label)
    label_vars.append(var)
    commands.append(cmd)
    cmd.run(None)

draw_graph()


def save():
    with open(schedule_filename, 'wt', encoding='utf-8') as file_output:
        for e in events:
            file_output.write(e.name + ' || ' + e.color
                              + ' || ' + str(e.start_time).split('.')[0] + ' || ' + str(e.end_time).split('.')[0]
                              + ' || ' + e.frequency + '\n')


def add_event():
    global current_event_index
    e = Event(ent1.get())
    e.start_time = datetime.datetime.strptime(ent2.get(), '%Y-%m-%d %H:%M:%S')
    e.end_time = datetime.datetime.strptime(ent3.get(), '%Y-%m-%d %H:%M:%S')
    e.color = "#%02x%02x%02x" % (random.randint(40, 220), random.randint(40, 220), random.randint(40, 220))
    if e.start_time == e.end_time:
        if e.end_time.second < 59:
            e.end_time = e.end_time.replace(second=e.end_time.second + 1)
        else:
            e.end_time = e.end_time.replace(minute=e.end_time.minute + 1, second=0)
        var3.set(str(e.end_time).split('.')[0])
    if check_var1.get():
        e.frequency = 'permanent'
    else:
        e.frequency = 'only_once'
    if conflicts(e, events):
        messagebox.showerror('错误', '时间冲突。')
        return
    events.append(e)

    name = get_name(e)
    var = StringVar()
    label = Label(tk, textvariable=var)
    var.set(name)
    cmd = Command(len(events) - 1, name)
    label.bind('<Button-1>', cmd.run)
    label.pack()
    labels.append(label)
    label_vars.append(var)
    commands.append(cmd)
    cmd.run(None)
    commands[len(commands) - 1].run(None)

    save()
    draw_graph()


def edit_event():
    e_ = Event(ent1.get())
    e_.start_time = datetime.datetime.strptime(ent2.get(), '%Y-%m-%d %H:%M:%S')
    e_.end_time = datetime.datetime.strptime(ent3.get(), '%Y-%m-%d %H:%M:%S')

    events_without_current_event = events.copy()
    events_without_current_event.remove(events[current_event_index])
    if conflicts(e_, events_without_current_event):
        messagebox.showerror('错误', '时间冲突。')
        return
    events[current_event_index].name = e_.name
    events[current_event_index].start_time = e_.start_time
    events[current_event_index].end_time = e_.end_time
    if check_var1.get():
        events[current_event_index].frequency = 'permanent'
    else:
        events[current_event_index].frequency = 'only_once'

    name = get_name(events[current_event_index])
    label_vars[current_event_index].set(name)
    commands[current_event_index].name = name

    save()
    draw_graph()


def delete_event(index: int):
    global current_event_index, running_event
    if index == current_event_index:
        running_event = None
    events.pop(index)
    labels[index].destroy()
    labels.pop(index)
    label_vars.pop(index)
    commands.pop(index)
    for i_ in range(0, len(commands)):
        commands[i_].name = events[i_].name
        commands[i_].index = i_
    if len(commands) > 0:
        commands[len(commands) - 1].run(None)
    if len(events) == 0:
        fill_with_default_event()

    save()
    draw_graph()


def delete_current_event():
    delete_event(current_event_index)


def notify(text: str):
    global notifying
    while notifying:
        time.sleep(0.1)
    notifying = True

    def run():
        engine.say(text)
        lock.acquire()
        engine.runAndWait()
        lock.release()
    thr = Thread(target=run)
    thr.start()

    notifying = False


def check():
    global running_event, notifying, current_event_index
    for n_, event in enumerate(events):
        if event.start_time <= now < event.end_time:
            if (now - event.start_time).total_seconds() <= 2:
                notify(event.name + '开始')
            running_event = event
            return
        elif now >= event.end_time:
            if (now - event.end_time).total_seconds() <= 2:
                notify(event.name + '结束')
            if event.frequency == 'only_once':
                delete_event(n_)
        else:
            if fore_notifying_minutes * 60 - 2 < (event.start_time - now).total_seconds() <= fore_notifying_minutes * 60:
                notify('%.2f' % fore_notifying_minutes + '分钟后将开始' + event.name)
        running_event = None


class RefreshingThread(Thread):
    def run(self):
        global now
        while refreshing:
            now = datetime.datetime.now()
            check()
            if running_event:
                running_event_str = '正在进行：' + get_name(running_event, separation=' ')
            else:
                running_event_str = '空闲时间'
            label_text.set(str(now).split('.')[0] + '\n' + running_event_str)

            now_time_angle = (now - now.replace(hour=0, minute=0, second=0,
                                                microsecond=0)).total_seconds() / 86400 * 2 * math.pi - math.pi / 2
            pointer_line = canvas.create_line(center_x, center_y
                                              , center_x + graph_radius * math.cos(now_time_angle)
                                              , center_y + graph_radius * math.sin(now_time_angle),
                                              fill="#%02x%02x%02x" % (100, 100, 255), width=3)
            shapes_to_delete.append(pointer_line)

            tk.update()
            time.sleep(refreshing_interval)


class PaintingThread(Thread):
    def run(self):
        while True:
            draw_graph()
            time.sleep(painting_interval)


btn1 = Button(tk, text='添加事件', command=add_event)
btn2 = Button(tk, text='编辑事件', command=edit_event)
btn3 = Button(tk, text='删除事件', command=delete_current_event)

lbl1.pack()
ent1.pack()
ent2.pack()
ent3.pack()
cb1.pack()
btn_random_color.pack()
btn1.pack()
btn2.pack()
btn3.pack()

canvas.create_oval(center_x - graph_radius, center_y - graph_radius
                       , center_x + graph_radius, center_y + graph_radius, fill="#%02x%02x%02x" % (240, 240, 240), outline='grey')
canvas.create_oval(center_x - graph_radius + graph_ring_width, center_y - graph_radius + graph_ring_width
                       , center_x + graph_radius - graph_ring_width, center_y + graph_radius - graph_ring_width,
                       fill="#%02x%02x%02x" % (200, 220, 255), outline='grey')
canvas.create_oval(center_x - graph_radius + graph_ring_width + 28, center_y - graph_radius + graph_ring_width + 28
                       , center_x + graph_radius - graph_ring_width - 28, center_y + graph_radius - graph_ring_width - 28,
                       fill="#%02x%02x%02x" % (120, 140, 255), outline='')
canvas.create_oval(center_x - graph_radius + graph_ring_width + 40, center_y - graph_radius + graph_ring_width + 40
                       , center_x + graph_radius - graph_ring_width - 40, center_y + graph_radius - graph_ring_width - 40,
                       fill="#%02x%02x%02x" % (150, 170, 255), outline='')
canvas.create_oval(center_x - graph_radius + graph_ring_width + 55, center_y - graph_radius + graph_ring_width + 55
                       , center_x + graph_radius - graph_ring_width - 55, center_y + graph_radius - graph_ring_width - 55,
                       fill="#%02x%02x%02x" % (180, 210, 255), outline='')

pin_radius = inner_radius - 5
for i in range(0, 24):
    angle = 2 * math.pi / 24 * i - math.pi / 2
    canvas.create_line(center_x + pin_radius * math.cos(angle), center_y + pin_radius * math.sin(angle)
        , center_x + inner_radius * math.cos(angle), center_y + inner_radius * math.sin(angle))
    canvas.create_text(center_x + (pin_radius - 10) * math.cos(angle)
        , center_y + (pin_radius - 10) * math.sin(angle), text=str(i), font='微软雅黑 10')

thread = RefreshingThread()
refreshing = True
painting_thread = PaintingThread()


def start():
    thread.start()
    painting_thread.start()
    tk.mainloop()


if __name__ == '__main__':
    start()
