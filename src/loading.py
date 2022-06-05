#LAKE 

import tkinter as tk
import time

def func_centerWindow(w=800, h=800):
    ws = window.winfo_screenwidth()
    hs = window.winfo_screenheight()
    x = (ws/2) - (w/2)    
    y = (hs/2) - (h/2)
    window.geometry('%dx%d+%d+%d' % (w, h, x, y))

def func_loading(x1, x2, x3):
    loading_one.place(x = x1, y = 250)
    loading_two.place(x = x2, y = 250)
    loading_three.place(x = x3, y = 250)

window = tk.Tk()

func_centerWindow(620,300)

bg_info = tk.PhotoImage(file = "lake_gui/loading-bg.png")
label_backgroundImage = tk.Label(master=window,
                                 image=bg_info)
label_backgroundImage.place(x = -2, y = 0)

# loading indicators

# box 1
loading_one = tk.Frame(master=window,
                        bg="#0e47a1",
                        width=15,
                        height=15)

# box 2
loading_two = tk.Frame(master=window,
                        bg="#6acbf7",
                        width=15,
                        height=15)

# box 3
loading_three = tk.Frame(master=window,
                        bg="#c5e8ff",
                        width=15,
                        height=15)

loading_one.place(x = 250, y = 250)
loading_two.place(x = 300, y = 250)
loading_three.place(x = 350, y = 250)


window.title("LAKE: Traffic flows through me.")
window.wm_attributes('-transparentcolor', '#ab23ff')
window.resizable(False, False)
window.after(20000,lambda:window.destroy())
window.mainloop()
