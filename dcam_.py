import datetime, time
from threading import Thread
from tkinter import Tk

rated_attention_span = datetime.timedelta(minutes=35)
rated_time_unit = datetime.timedelta(minutes=5)

init_time = datetime.datetime.now()


def update():
    while True:
        print(str(datetime.datetime.now() - init_time).split('.')[0])
        time.sleep(1)


def update_ras(qoi: float):
    pass


updating_thread = Thread(target=update, args=())
updating_thread.start()

window = Tk()
window.mainloop()