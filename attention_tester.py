import pyttsx3
import datetime
import time
from threading import Thread

test_duration_minutes = 30

engine = pyttsx3.init()
rate = engine.getProperty('rate')
engine.setProperty('rate', rate - 10)

start_time = datetime.datetime.now()
_30_minutes = datetime.timedelta(minutes=30)
words_to_say = ['这里是DLearn注意力实测辅助程序。按下Enter键开始测试。']

is_started = False
is_saying = False


def engine_say(text: str):
    global is_started, is_saying
    if is_started and not is_saying:
        print('Hello', 1)
        engine.endLoop()
    print('Hello', 2)
    engine.say(text)
    print('Hello', 3)
    if not is_saying:
        print('Hello', 4)
        is_saying = True
        if not is_started:
            print('Hello', 5)
            is_started = True
        print('Hello', 6)
        # engine.runAndWait()
        engine.startLoop()
        print('Hello', 7)
        is_saying = False


def engine_run(words_to_say: list):
    while True:
        if words_to_say and words_to_say[0]:
            print('not empty1')
            print('not empty2')
            engine_say(words_to_say[0])
            print('not empty3')
            time.sleep(0.2)
            print('not empty4')
        else:
            time.sleep(1)
            print('empty')


thread1 = Thread(target=engine_run, args=(words_to_say, ))
thread1.start()


def starting_input():
    inp = input('这里是DLearn注意力实测辅助程序。按下Enter键开始测试。')


thread2 = Thread(target=starting_input, args=())
thread2.start()
thread2.join()


while (datetime.datetime.now() - start_time) < _30_minutes:
    engine_run(['请选择'])
    inp = input('如果你')
