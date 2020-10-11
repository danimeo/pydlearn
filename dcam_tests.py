import datetime
import time
from threading import Thread
from tkinter import Canvas, ALL
import pyttsx3
import random

engine = pyttsx3.init()
engine.setProperty('rate', engine.getProperty('rate') - 10)


def basic_attention_test(label_frame, result_list: list, rounds_num = 1, mode = 'vision', seconds_per_round = 60
                         , choices = ('1', '2', '3'), interval = 0.2, showing_timeleft_switch = False):
    waiting = True
    current_input = ''
    round_ending = False
    a = ''
    n = 0
    text = ''
    showing_timeleft = True

    result_list.append((datetime.timedelta(), 0, 0))

    def paint(canvas: Canvas, n: int, text: str, text_timeleft='', text_size=32, text_color=(0, 0, 0),
              text_floating=False):
        canvas.delete(ALL)
        canvas.create_text(50, 15, text='进度：' + str(n) + '/' + str(rounds_num), font='微软雅黑 11')
        if text_floating:
            x_offset = random.randint(-10, 10)
            y_offset = random.randint(-10, 10)
        else:
            x_offset = y_offset = 0
        canvas.create_text(canvas.winfo_width() / 2 + x_offset, canvas.winfo_height() / 2 + y_offset
                           , text=text, font='微软雅黑 ' + str(text_size), fill="#%02x%02x%02x" % text_color)
        canvas.create_text(80, 36, text=text_timeleft, font='微软雅黑 11')

    def show_timeleft(canvas: Canvas, start_time):
        if not showing_timeleft_switch:
            return
        while showing_timeleft:
            paint(canvas, n, text,
                  text_timeleft='剩余时间：' + str(start_time + datetime.timedelta(seconds=seconds_per_round)
                                              - datetime.datetime.now()).split('.')[0])
            time.sleep(0.9)

    label_frame.config(text='DPsycho-4注意测试')
    canvas = Canvas(label_frame, bg='white')
    canvas.pack(fill='both', expand='yes')
    canvas.update()
    canvas.focus_set()
    canvas.bind('<Button-1>', func=lambda event: canvas.focus_set())

    def process_keyboard_event(k):
        nonlocal waiting, current_input

        if k.keysym == 'Return':
            waiting = False

        if current_input:
            return
        if k.keysym == '1':
            current_input = '1'
        elif k.keysym == '2':
            current_input = '2'
        elif k.keysym == '3':
            current_input = '3'
        else:
            return

        if current_input == a and not round_ending:
            paint(canvas, n, current_input, text_color=(0, 255, 0), text_floating=False)
        else:
            paint(canvas, n, current_input, text_color=(255, 0, 0), text_floating=False)

    canvas.bind(sequence="<Key>", func=process_keyboard_event)
    canvas.focus_set()

    if mode == 'listening':
        mode_str = '听觉'
    else:
        mode_str = '视觉'

    print('下面开始DPsycho-4' + mode_str + '注意力测试。')
    paint(canvas, 0, '下面开始DPsycho-4' + mode_str + '注意力测试。按下Enter键开始测试。', text_size=12)
    '''engine.say('下面开始DPsycho4' + mode_str + '注意力测试。按下Enter键开始测试。')
    engine.runAndWait()'''
    while waiting:
        time.sleep(0.1)

    record = ''
    duration_in_all = datetime.datetime.now() - datetime.datetime.now()
    correct_count_in_all = 0
    count_in_all = 0

    for n in range(1, rounds_num + 1):
        round_ending = False

        paint(canvas, n, '3')
        time.sleep(1)
        paint(canvas, n, '2')
        time.sleep(1)
        paint(canvas, n, '1')
        time.sleep(1)
        print('进度：' + str(n) + '/' + str(rounds_num))
        print('请听……')

        testee_answers = []
        keys = []

        start_time = datetime.datetime.now()
        showing_timeleft_thread = Thread(target=show_timeleft, args=(canvas, start_time))
        showing_timeleft = True
        showing_timeleft_thread.start()

        count = 0
        while (datetime.datetime.now() - start_time).total_seconds() < seconds_per_round:
            a = random.choice(choices)
            rgb = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
            if mode == 'listening':
                text = '请听'
                paint(canvas, n, text)
                engine.say(a)
                engine.runAndWait()
            else:
                text = a
                paint(canvas, n, a, text_color=rgb, text_floating=True)
                time.sleep(random.uniform(1, 1.5))
            time.sleep(interval)
            testee_answers.append(current_input)
            keys.append(a)
            current_input = ''
            count += 1

        end_time = datetime.datetime.now()
        showing_timeleft = False
        round_ending = True

        correct_count = 0
        for index, answer in enumerate(testee_answers):
            if keys[index] == answer:
                correct_count += 1

        duration = end_time - start_time
        rec = '时长：' + str(duration) + ' 正确数：' + str(correct_count) + '/' + str(count)\
              + ' 正确率：' + '{:.1%}'.format(correct_count / count)
        print(rec)
        record += str(n) + '. ' + rec + '\n'''
        duration_in_all += duration
        correct_count_in_all += correct_count
        count_in_all += count
        result_list[0] = duration_in_all, correct_count_in_all, count_in_all
        paint(canvas, n, rec + '\n\n按下Enter键继续。', text_size=18)
        '''engine.say('按下Enter键继续。')
        engine.runAndWait()'''
        waiting = True
        while waiting:
            time.sleep(0.1)

    rec_in_all = '总计：\n时长：' + str(duration_in_all)\
                 + ' 错误次数：' + str(count_in_all - correct_count_in_all) + '/' + str(count_in_all)\
                 + ' 错误率：' + '{:.1%}'.format((count_in_all - correct_count_in_all) / count_in_all)\
                 + '\n错误发生频率：'\
                 + str((count_in_all - correct_count_in_all) / (duration_in_all.total_seconds() / 60)) + '次/min\n'
    paint(canvas, rounds_num, rec_in_all, text_size=12)

    time.sleep(5)

    canvas.destroy()
    label_frame.pack_forget()