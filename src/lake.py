#LAKE 

import tkinter as tk
import os
from create_settings import Settings

import datetime

from logger import getLogger
from test_simulation import TestSimulation
from tools import import_test_config

model_name = [
    "1TL",
    "2TL",
    "7TL",
    "Roxas", 
]


def func_centerWindow(w=800, h=800):
    ws = window.winfo_screenwidth()
    hs = window.winfo_screenheight()
    x = (ws/2) - (w/2)    
    y = (hs/2) - (h/2)
    window.geometry('%dx%d+%d+%d' % (w, h, x, y))

    
def func_btn_simulate():
    label_backgroundImage.config(image=bg_simulate)
    lbl_load_model.place(x = 320, y = 420)
    lm_colon1.place(x=580, y = 440)
    lm_colon2.place(x=580, y = 460)
    drp_load_model.place(x = 610, y = 430)

    btn_start_simulation.place(x = 790, y = 700)  
    btn_start.place_forget()

    btn_goBack.place(x = 180, y = 150)
    
def func_go_back():
    label_backgroundImage.config(image=bg_info)
    lbl_load_model.place_forget()
    lm_colon1.place_forget()
    lm_colon2.place_forget()
    drp_load_model.place_forget()

    btn_start_simulation.place_forget()

    btn_goBack.place_forget()
    btn_start.place(x = 815, y = 700)

def func_create_test_settings():
    test_load_model = tl_load_model.get()
    settings = Settings('test_settings.ini')
    settings.generate_test_settings(3600, f'{test_load_model}','v1.0', f'{test_load_model}/{test_load_model}')
    # os.system('loading.py')

def func_test_file():
    getLogger().info('===== START TEST PROGRAM =====')
    config = import_test_config('test_settings.ini')

    simulation = TestSimulation(config)
    timestamp_start = datetime.datetime.now()
    simulation.run()

    getLogger().info(f'SUMMARY -> Start time: {timestamp_start} End time: {datetime.datetime.now()}')
    getLogger().info('====== END TEST PROGRAM ======')

def func_start_btn_simulate():
    window.destroy()
    func_create_test_settings()
    func_test_file()

if __name__ == "__main__":

    window = tk.Tk()

    func_centerWindow(1200,850)
    bg_info = tk.PhotoImage(file = "lake_gui/lake-bg-info.png")
    bg_simulate = tk.PhotoImage(file = "lake_gui/lake-simulate-bg.png")

    label_backgroundImage = tk.Label(master=window,
                                    image=bg_info)
    label_backgroundImage.place(x = -2, y = 0)
        
    tl_load_model= tk.StringVar()
    tl_load_model.set("1TL")

    ### BUTTONS ###
    btn_start = tk.Button(master=window,
                        bg="#c5e8ff",
                        fg="#391326",
                        relief=tk.FLAT,
                        text="SIMULATE",
                        command=func_btn_simulate,
                        font=("Century Gothic", 22, "bold"),
                        width=15,
                        height=1)
    btn_start.place(x = 815, y = 700)

    btn_simulate = tk.Button(master=window,
                        bg="#391326",
                        fg="#ffecd3",
                        relief=tk.FLAT,
                        text="SIMULATE",
                        command=func_btn_simulate,
                        font=("Century Gothic", 22, "bold"),
                        width=20,
                        height=1)

    btn_goBack = tk.Button(master=window,
                        bg="#6accf8",
                        fg="#391326",
                        relief=tk.FLAT,
                        text="GO BACK",
                        command=func_go_back,
                        font=("Century Gothic", 10, "bold"),
                        width=10,
                        height=2)

    ### SIMULATE WINDOW ###

    # load model gui
    # load model text
    lbl_load_model = tk.Label(master=window,
                            bg="#c5e8ff",
                            fg="#0d4398",
                            relief=tk.FLAT,
                            text="LOAD MODEL",
                            font=("Century Gothic", 22, "bold"),
                            width=18,
                            height=2)
    # load model colon
    lm_colon1 = tk.Frame(master=window,
                            bg="#0277bd",
                            width=15,
                            height=15)
    # load model colon
    lm_colon2 = tk.Frame(master=window,
                            bg="#6acbf7",
                            width=15,
                            height=15)
    # load model dropdown 
    drp_load_model = tk.OptionMenu(window, tl_load_model, *model_name)
    drp_load_model.config(height=1,
                width=10,
                bg="#80d8fe",
                relief=tk.FLAT,
                font=("Century Gothic", 22, "bold"))

    # start simulation button
    btn_start_simulation = tk.Button(master=window,
                        bg="#c5e8ff",
                        fg="#391326",
                        text="START SIMULATION",
                        relief=tk.FLAT,
                        command=func_start_btn_simulate,
                        font=("Century Gothic", 18, "bold"),
                        width=20,
                        height=1)

    # load model colon

    # gui window settings
    window.title("LAKE: Traffic flows through me.")
    window.wm_attributes('-transparentcolor', '#ab23ff')
    window.resizable(False, False)
    window.mainloop()
