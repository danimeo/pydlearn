import datetime, time
from threading import Thread
from tkinter import Tk, StringVar, Label

from dcam_framework import Timestamp, Task, Event, timedelta_to_str

plan_filename = 'dcam_data/plans/plan_202010a.txt'
records_filename = 'dcam_data/records/dcam_timer_records.txt'
updating_interval = 2

plans = {}
events = []

with open(plan_filename, 'rt', encoding='utf-8') as file_input:
    name_n_durations = [line.strip().split('\t') for line in file_input.readlines()]
    for name_n_duration in name_n_durations:
        plans[name_n_duration[0]] = float(name_n_duration[1])


tk = Tk()
tk.minsize(450, 250)
tk.title('DCAM-Cephret长时计划时间分配器（v2020.10.10）')
label_text = StringVar(tk, '', '')
lbl1 = Label(tk, textvariable=label_text)
lbl1.pack()

labels = []
label_texts = {}
for subject in plans:
    label_text_i = StringVar(tk, '', '')
    label_texts[subject] = label_text_i
    label = Label(tk, textvariable=label_text_i)
    label.pack(pady=1)
    labels.append(label)


def get_total_duration_by_subject(subject: str):
    total_duration_by_subject = datetime.timedelta()
    for event in events:
        for task in event.tasks:
            if task.subject == subject:
                total_duration_by_subject += task.get_duration()
    return total_duration_by_subject


def update():
    while True:
        events.clear()
        records_list = []
        with open(records_filename, 'rt', encoding='utf-8') as file_input:
            records_list = [line.strip() for line in file_input.readlines()]

        for record in records_list:
            r_list = record.split('\t')
            if r_list[6] == 'undone':
                continue
            event = Event(r_list[2],
                          datetime.datetime.strptime(r_list[4], '%H:%M:%S') - datetime.datetime.strptime('0:00:00',
                                                                                                         '%H:%M:%S'),
                          type=r_list[3])
            event.start_time = datetime.datetime.strptime(r_list[0], '%Y-%m-%d %H:%M:%S.%f')
            event.end_time = datetime.datetime.strptime(r_list[1], '%Y-%m-%d %H:%M:%S.%f')
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
                '''if [ts for ts in item_list[4].split('~')] == ['']:
                    print(t)'''
                ts_list = item_list[4].split('~')
                if len(ts_list) > 1 or (len(ts_list) == 1 and ts_list[0]):
                    task.timestamps = [Timestamp(datetime.datetime.strptime(ts_list[0], '%Y-%m-%d %H:%M:%S.%f'), ts_list[1]) for ts_list in (ts.split('|') for ts in ts_list)]
                event.tasks[int(item_list[0])] = task
            events.append(event)

        total_duration = datetime.timedelta()
        # fixed_total_full_duration = datetime.timedelta()
        for event in events:
            total_duration += event.get_total_subject_duration(plan_filename)
            # fixed_total_full_duration += event.fixed_total_full_duration

        total_planned_duration = datetime.timedelta(minutes=sum([plans[plan] for plan in plans]))

        label_text.set('[总计投入时间：' + timedelta_to_str(total_duration) + ' / ' + timedelta_to_str(total_planned_duration) + ' (' + '{:.2%}'.format(total_duration / total_planned_duration) + ')]')
        for subject in plans:
            label_texts[subject].set(subject + ': ' + timedelta_to_str(get_total_duration_by_subject(subject)) + ' / ' + timedelta_to_str(datetime.timedelta(minutes=plans[subject])) + ' (' + '{:.2%}'.format(get_total_duration_by_subject(subject) / datetime.timedelta(minutes=plans[subject])) + ')')

        time.sleep(updating_interval)


updating_thread = Thread(target=update, args=())


if __name__ == '__main__':
    updating_thread.start()
    tk.mainloop()

