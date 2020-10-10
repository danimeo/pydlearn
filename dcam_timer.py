import codecs
import datetime, time
from threading import Thread
from tkinter import Tk, Button, Label, StringVar, Text, END, LabelFrame, Frame
import random
import jieba.posseg as pseg
import pyttsx3

from dcam_framework import Task, Note, timedelta_to_str, numerical_grad_1d

refreshing_interval = 0.1
notes_span_seconds = 10
attention_probing_interval = (300, 900)
attention_probing_timeout = 3
task_log_filename = 'dcam_data/records/dcam_timer_log.txt'
task_records_filename = 'dcam_data/records/dcam_timer_records.txt'
notes_filename = 'notes/notes_multi-subject.txt'
auto_start_time = '2020-10-10 13:00:00'
auto_jump_to_task_0 = True
auto_jump_to_undone_task = True
timer_event_name = '再接再厉90分钟'
timer_event_type = '课内学习 & 自学'
# timer_event_type = '课内学习 & 听课'
# task_names_n_full_duration_minutes = [('(自由时间)', '', 30), ('自学', '英语', 45), ('听讲', '英语', 15)]
task_names_n_full_duration_minutes = [('(自由时间)', '', 30)
    , ('自由学习', 'C/C++程序设计', 15)
    , ('逆矩阵及其应用', '线性代数', 15)
    , ('查补：第1章 随机事件及其概率', '概率论与数理统计', 15)
    , ('第2章 轴向拉伸与压缩', '材料力学', 15)]
ufd_delta_param = 0.5

task_names = [task_tuple[0] for task_tuple in task_names_n_full_duration_minutes]
fixed_total_full_duration = datetime.timedelta(seconds=datetime.timedelta(minutes=sum([task_tuple[2] for task_tuple in task_names_n_full_duration_minutes])).total_seconds())

initial_time = datetime.datetime.now()
printing = False
datetime_p = datetime.datetime.strptime(auto_start_time, '%Y-%m-%d %H:%M:%S')

start_time = initial_time
tasks_all_done = False

tasks = []
for i, task_name in enumerate(task_names):
    tasks.append(Task(task_name, datetime.timedelta(minutes=task_names_n_full_duration_minutes[i][2]), subject=task_names_n_full_duration_minutes[i][1]))

engine = pyttsx3.init()
rate = engine.getProperty('rate')
engine.setProperty('rate', rate - 10)


def total_duration():
    td = datetime.timedelta()
    for task in tasks:
        td += task.get_duration()
    return td


def total_full_duration():
    tfd = datetime.timedelta()
    for task in tasks:
        tfd += task.full_duration
    return tfd


current_task_index = 0

notes = []
attention_probes = []
attention_response = False


def update_full_durations(delta_seconds: float):
    is_any_task_running = False
    for task in tasks:
        if task.running:
            is_any_task_running = True
            break
    if not is_any_task_running:
        return

    delta = datetime.timedelta(seconds=delta_seconds)

    all_tasks_indexes = set(n for n in range(0, len(tasks)))
    available_tasks_indexes = set()
    for i, tsk in enumerate(tasks):
        if i != current_task_index and tsk.get_duration() < tsk.full_duration:
            available_tasks_indexes.add(i)

    for task_index in available_tasks_indexes:
        tasks[task_index].full_duration -= delta / len(available_tasks_indexes)

    overflowing = datetime.timedelta()
    for task_index in all_tasks_indexes:
        if tasks[task_index].full_duration < tasks[task_index].get_duration():
            overflowing += tasks[task_index].get_duration() - tasks[task_index].full_duration
            tasks[task_index].full_duration = tasks[task_index].get_duration()
    if overflowing != datetime.timedelta():
        for task_index in available_tasks_indexes:
            if overflowing < datetime.timedelta():
                tasks[task_index].full_duration += overflowing / len(available_tasks_indexes)
            else:
                tasks[task_index].full_duration -= overflowing / len(available_tasks_indexes)

    if available_tasks_indexes:
        tasks[current_task_index].full_duration += delta

    if total_full_duration() > fixed_total_full_duration:
        tasks[current_task_index].full_duration -= total_full_duration() - fixed_total_full_duration
    elif total_full_duration() < fixed_total_full_duration:
        tasks[current_task_index].full_duration += fixed_total_full_duration - total_full_duration()

    for i, task in enumerate(tasks):
        task_names_n_full_duration_minutes[i] = tasks[i].name, tasks[i].subject, tasks[
            i].full_duration.total_seconds() / 60


stopKey = [w.strip() for w in codecs.open('data/stopWord.txt', 'r', encoding='utf-8').readlines()]


def data_preprocess(text, stopkey):
    l = []
    pos = ['n', 'nz', 'v', 'vd', 'vn', 'l', 'a', 'd']
    seg = pseg.cut(text)
    for i in seg:
        if i.word not in stopkey and i.flag in pos:
            l.append(i.word)
    return l


def qoi_of_note(note: Note):
    return len(data_preprocess(note.content, stopKey))


def count_notes(start_time: datetime.datetime, end_time: datetime.datetime):
    count = 0
    things = notes
    for thing in things:
        t = thing.time
        if start_time < end_time:
            time_a, time_b = start_time, end_time
        elif end_time < start_time:
            time_a, time_b = end_time, start_time
        else:
            time_a = time_b = start_time
        if time_a <= t <= time_b:
            count += 1
    return count


def count_attention_probes(start_time: datetime.datetime, end_time: datetime.datetime):
    count = 0
    things = attention_probes
    for thing in things:
        t = thing[0]
        if start_time < end_time:
            time_a, time_b = start_time, end_time
        elif end_time < start_time:
            time_a, time_b = end_time, start_time
        else:
            time_a = time_b = start_time
        if time_a <= t <= time_b:
            if thing[1]:
                count += 1
            else:
                count -= 1
    return count


def count(seconds: float):
    seconds_ago = datetime.datetime.now() - datetime.timedelta(seconds=seconds)
    now = datetime.datetime.now()
    cap = count_attention_probes(initial_time, now)
    if cap > 0:
        cap = 0
    return count_notes(seconds_ago, now) + cap


ds_velocity = 0


def calc_ds_velocity():
    global ds_velocity

    total_qoi = 0
    for note in notes:
        qoi = qoi_of_note(note)
        if datetime.datetime.now() - datetime.timedelta(seconds=notes_span_seconds) <= note.time <= datetime.datetime.now():
            total_qoi += qoi
        else:
            if total_qoi - qoi >= 0:
                total_qoi -= qoi

    ds_velocity = (count(notes_span_seconds) - 1 + total_qoi) * ufd_delta_param
    return ds_velocity


tk = Tk()
tk.minsize(720, 580)
tk.title('DCAM-Cephret多任务切换计时器（v2020.10.10）')
label_text = StringVar(tk, '', '')
lbl1 = Label(tk, textvariable=label_text)
text1 = Text(tk)


class PrintingThread(Thread):
    def run(self):
        global printing, label_text, datetime_p, current_task_index, tasks_all_done

        def refresh_labels():
            if tasks[current_task_index].subject:
                subj = '(' + tasks[current_task_index].subject + ') '
            else:
                subj = ''
            label_text.set('总进行时间：[' + str(total_duration()).split('.')[0] + ' / ' + timedelta_to_str(
                total_full_duration()) + '] | ' + '当前任务：' + subj + tasks[current_task_index].name)

            for i, task in enumerate(tasks):
                if tasks[i].subject:
                    subj = tasks[i].subject + ': '
                else:
                    subj = ''
                label_texts[i].set(
                    str(i) + '. ' + subj + tasks[i].name + ' [' + str(tasks[i].get_duration()).split('.')[
                        0] + ' / ' + str(tasks[i].full_duration).split('.')[0] + ']')

        while True:
            while printing:
                now = datetime.datetime.now()

                update_full_durations(calc_ds_velocity() * refreshing_interval)

                if not tasks[current_task_index].running and (
                        now - datetime_p).total_seconds() <= 1 and now >= datetime_p:
                    if total_duration() == datetime.timedelta() and True not in [t.running for t in tasks]:
                        start_time = datetime.datetime.now()
                    tasks[current_task_index].start()

                if auto_jump_to_task_0 and not tasks[0].running and not current_task_index == 0 and tasks[
                    current_task_index].get_duration() >= tasks[current_task_index].full_duration:
                    for task in tasks:
                        task.pause()
                    if tasks[0].get_duration() < tasks[0].full_duration:
                        tasks[0].start()
                    current_task_index = 0

                if auto_jump_to_undone_task and tasks[current_task_index].get_duration() >= tasks[
                    current_task_index].full_duration:
                    for n_, task in enumerate(tasks):
                        if n_ and task.get_duration() < task.full_duration:
                            task.start()
                            current_task_index = n_
                            break
                        elif not n_:
                            task.pause()

                refresh_labels()

                time.sleep(refreshing_interval)

                if total_duration() >= total_full_duration():
                    for task in tasks:
                        task.pause()
                    printing = False
                    refresh_labels()
                    break

            if not tasks_all_done and total_duration() >= total_full_duration():
                now = datetime.datetime.now()
                with open(task_log_filename, 'at', encoding='utf-8') as file_output:
                    file_output.write('================================\n')
                    file_output.write(timer_event_name + ' | [' + timer_event_type + ']\n')
                    file_output.write('--------------------------------\n')
                    file_output.write('任务列表：\n')
                    for n, task in enumerate(tasks):
                        if task.subject:
                            subject = task.subject + ': '
                        else:
                            subject = ''
                        file_output.write(str(n) + '. ' + subject + task.name + ' [' + str(task.get_duration()).split('.')[
                            0] + ' / ' + str(task.full_duration).split('.')[0] + ']\n')
                    file_output.write('--------------------------------\n')
                    file_output.write('[开始时间：' + str(start_time) + ']\n')
                    file_output.write('[完成时间：' + str(now) + ']\n')
                    file_output.write('[总计耗时：[' + str(total_duration()) + ' / ' + str(total_full_duration()) + ']\n')
                    file_output.write('================================\n\n')
                with open(task_records_filename, 'at', encoding='utf-8') as file_output:
                    t_str = str(start_time) + '\t' + str(
                        now) + '\t' + timer_event_name + '\t' + timer_event_type + '\t' + str(
                        fixed_total_full_duration) + '\t'
                    for i, tsk in enumerate(tasks):
                        ts_str = ''
                        for ts in tsk.timestamps:
                            ts_str += str(ts) + '~'
                        t_str += str(i) + ',' + tsk.name + ',' + tsk.subject + ',' + str(
                            tsk.full_duration) + ',' + ts_str[:-1] + '; '
                    file_output.write(t_str[:-2] + '\n')

                tasks_all_done = True

            while not printing:
                time.sleep(0.1)


thread = PrintingThread()
thread_running = False


def start_printing():
    global printing, thread_running
    printing = True
    if not thread_running:
        thread.start()
    thread_running = True


def stop_printing():
    global printing
    printing = False


def start_current_task():
    global start_time, tasks_all_done
    if total_duration() == datetime.timedelta() and True not in [t.running for t in tasks]:
        start_time = datetime.datetime.now()
        tasks_all_done = False
    tasks[current_task_index].start()


def pause_current_task():
    tasks[current_task_index].pause()


def end_current_task():
    tasks[current_task_index].end()


def end_all_tasks():
    for tsk in tasks:
        tsk.end()


def end_and_reset_all_tasks():
    tasks.clear()
    for i, task_name in enumerate(task_names):
        tasks.append(Task(task_name, datetime.timedelta(minutes=task_names_n_full_duration_minutes[i][2]),
                          subject=task_names_n_full_duration_minutes[i][1]))


labels = []
label_texts = []
commands = []


class Command:
    index = 0

    def __init__(self, index):
        self.index = index

    def run(self, param):
        global current_task_index, start_time
        for n, tsk in enumerate(tasks):
            if n == self.index:
                if total_duration() == datetime.timedelta() and True not in [t.running for t in tasks]:
                    start_time = datetime.datetime.now()
                tasks[n].start()
                current_task_index = n
            else:
                tasks[n].pause()



def submit_note(event):
    content = text1.get(1.0, END).strip()
    if not content:
        return
    note = Note(content, datetime.datetime.now())
    notes.append(note)
    text1.delete(1.0, END)

    notes_in_file_num = 0
    with open(notes_filename, 'rt', encoding='utf-8') as file_input:
        lines = file_input.readlines()
        for line in lines:
            if line.replace('\n', ''):
                notes_in_file_num += 1

    with open(notes_filename ,'at', encoding='utf-8') as file_output:
        file_output.write(str(notes_in_file_num + 1) + '. ' + note.content + '\n')
        print(str(notes_in_file_num + notes.index(note) + 1) + '. ' + note.content + '\n')


def process_keyboard_event(k):
    global attention_response
    attention_response = True


def is_any_task_running():
    any_task_running = False
    for task in tasks:
        if task.running:
            any_task_running = True
            break
    return any_task_running


def update_full_durations_by_attention():
    while True:
        text1.unbind_all('<Key>')
        text1.bind('<Return>', submit_note)
        if not is_any_task_running():
            continue

        time.sleep(random.uniform(attention_probing_interval[0], attention_probing_interval[1]))

        if not is_any_task_running():
            continue

        global attention_response
        text1.unbind_all('<Return>')
        text1.bind(sequence='<Key>', func=process_keyboard_event)
        text1.bind(sequence='<Return>', func=process_keyboard_event)
        stop_printing()
        label_text.set('！！！请按下任意键表示保持注意！！！')

        def run():
            engine.say('请按下任意键')
            engine.runAndWait()

        thr = Thread(target=run, args=())
        thr.start()
        text1.focus_set()
        time_when_start_to_wait = datetime.datetime.now()
        responding_in_time = True
        while not attention_response and responding_in_time:
            time.sleep(0.1)
            responding_in_time = datetime.datetime.now() - time_when_start_to_wait < datetime.timedelta(seconds=attention_probing_timeout)
        print(attention_response)
        attention_probes.append((datetime.datetime.now(), attention_response))
        attention_response = False
        start_printing()
        text1.unbind_all('<Key>')
        text1.unbind_all('<Return>')
        text1.bind('<Return>', submit_note)


attention_probing_thread = Thread(target=update_full_durations_by_attention, args=())


frame1 = Frame(tk)
btn1 = Button(frame1, text='开始/继续当前任务', command=start_current_task)
btn2 = Button(frame1, text='暂停当前任务', command=pause_current_task)
btn3 = Button(frame1, text='停止并重置当前任务计时', command=end_current_task)
btn4 = Button(frame1, text='停止并重置所有任务计时', command=end_all_tasks)
btn5 = Button(frame1, text='停止并重置所有任务计时和预定时间', command=end_and_reset_all_tasks)
lf1 = LabelFrame(tk, text='任务列表')

lbl1.pack(pady=3)
# frame1.pack(side='top', fill='both', expand=False, padx=40)
frame1.pack(pady=5)
packing_list = [btn1, btn2, btn3, btn4, btn5]
for packing_index, to_be_packed in enumerate(packing_list):
    to_be_packed.grid(row=0, column=packing_index)
# lf1.pack(side='top', fill='both', expand=False, padx=40)
lf1.pack(fill='both', padx=10, pady=5)
# text1.pack(side=BOTTOM, padx=10)
#text1.place(x=125, y=450, anchor='nw')
text1.pack(fill='both', padx=10, pady=5)

for i, task in enumerate(tasks):
    label_text_i = StringVar(tk, '', '')
    label_text_i.set(task_names[i])
    label_texts.append(label_text_i)
    label = Label(lf1, textvariable=label_text_i)
    cmd = Command(i)
    label.bind('<Button-1>', cmd.run)
    label.pack()
    labels.append(label)


# inp = input('按回车开始：')


def start():
    start_printing()
    attention_probing_thread.start()

    tk.mainloop()


if __name__ == '__main__':
    start()
