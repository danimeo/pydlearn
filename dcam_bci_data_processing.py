import socket
import time
import datetime
import re
from threading import Thread
from tkinter import StringVar, Tk, Label
import serial


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
            print([hex(c) for c in data])

    thread = Thread(target=loop, args=(str_var, ))
    return thread


def com_data_thread(str_var: StringVar, output_filename: str, type='raw', interval=0.1):
    ser = serial.Serial('COM3', 57600, timeout=None)
    with open(output_filename, 'wt', encoding='utf-8') as file_output:
        file_output.write('time\tvalue\n')

    data_list = [0xaa, 0xaa, 0x4, 0x80, 0x2, 0x0, 0x0, 0xff]

    def loop(str_var: StringVar):
        nonlocal data_list
        while True:
            if type == 'raw':
                data_list = []
                # print([hex(c) for c in data_list])
                if data_list[0] == 0xaa and data_list[1] == 0xaa and data_list[2] == 0x20 and data_list[3] == 0x2:
                    ser.read(28)
                raw_high, raw_low = data_list[5], data_list[6]
                sum = ((0x80 + 0x02 + raw_high + raw_low) ^ 0xFFFFFFFF) & 0xFF
                if sum != data_list[7]:
                    continue
                while not (data_list[0] == 0xaa and data_list[1] == 0xaa):
                    ser.read()

                data_list = list(ser.read(8))
                value = (raw_high << 8) | raw_low
                if value > 32768:
                    value -= 65536

                str_var.set(str(value))
                print([hex(c) for c in data_list])
                with open(output_filename, 'at', encoding='utf-8') as file_output:
                    file_output.write(str(datetime.datetime.now().timestamp()) + '\t' + str(value) + '\n')

                time.sleep(interval)
            elif type == 'attention':
                pass
            else:
                pass

    thread = Thread(target=loop, args=(str_var, ))
    return thread


def read_data_from_file(filename: str):
    with open(filename, 'rt', encoding='utf-8') as file_input:
        lines = file_input.readlines()[1:]
    for line in lines:
        timestamp_n_value = line.split('\t')
        timestamp = datetime.datetime.fromtimestamp(float(timestamp_n_value[0]))
        value = int(timestamp_n_value[1])



if __name__ == '__main__':
    from threading import Thread
    tk = Tk()
    tk.minsize(720, 580)
    tk.title('DCAM-BCI TGAM脑电数据采集 v2021.3.2')
    label_text = StringVar(tk, '', '')
    lbl1 = Label(tk, textvariable=label_text)
    lbl1.pack()
    label_text2 = StringVar(tk, '', '')
    lbl2 = Label(tk, textvariable=label_text2)
    lbl2.pack()
    '''var1 = StringVar()
    ent1 = Entry(tk, textvariable=var1)'''

    thr = com_data_thread(label_text
                          , 'bci_data/wordnet/raw_' + label_text2.get()
                          + '-' + re.sub(r'[^0-9]', '', str(datetime.datetime.now()))
                          + '.txt'
                          , interval=0)
    thr.start()
    tk.mainloop()

    # authorization = {'appName': 'DajunBCI-1', 'appKey': hashlib.sha1('DajunBCI-1'.encode('utf-8')).hexdigest()}
    # print(json.dumps(authorization).encode('utf-8'))

