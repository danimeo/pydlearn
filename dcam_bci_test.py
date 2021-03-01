import json
import socket
import hashlib
from threading import Thread
from tkinter import StringVar, Tk, Label


def data_loop(str_var: StringVar, type='raw'):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 13854))

    s.setblocking(True)

    def loop(str_var: StringVar):
        while True:
            data = list(s.recv(1024))
            if len(data) <= 8:
                continue
            if type == 'raw' and data[2] == 0x2:
                value = data[3]
            elif type == 'attention' and data[-4] == 0x4:
                value = data[-3]
                print(str(data[-3]))
            else:
                value = 0
            str_var.set(str(value))
            # print([hex(c) for c in data])

    thread = Thread(target=loop, args=(str_var, ))
    return thread


'''if __name__ == '__main__':
    from threading import Thread
    tk = Tk()
    tk.minsize(720, 580)
    tk.title('DCAM BCI使用测试 2021.2.27')
    label_text = StringVar(tk, '', '')
    lbl1 = Label(tk, textvariable=label_text)
    lbl1.pack()
    thr = Thread(target=new_data_loop, args=(label_text, ))
    thr.start()
    tk.mainloop()

    # authorization = {'appName': 'DajunBCI-1', 'appKey': hashlib.sha1('DajunBCI-1'.encode('utf-8')).hexdigest()}
    # print(json.dumps(authorization).encode('utf-8'))'''

