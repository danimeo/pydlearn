from tkinter import Tk, StringVar, Label

tk = Tk()
tk.minsize(450, 250)
tk.title('DCAM-Cephret临时计时器（v2021.1.9）')
label_text = StringVar(tk, '', '')
lbl1 = Label(tk, textvariable=label_text)
lbl1.pack()



tk.mainloop()