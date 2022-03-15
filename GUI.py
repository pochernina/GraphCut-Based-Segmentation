import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk
import numpy as np

button_color = 'plum'
cnvs_img = None
mask = None

def begin_draw(event):
    btn_predict.grid(row=2, column=0, sticky="ew", pady=10)

def draw_red_line(event):
    global cnvs_img, mask
    cnvs_img.create_rectangle(event.x - 2, event.y + 2, event.x + 2, event.y - 2, 
                        outline='red', fill='red',  tags='lines')
    for i in range (-2, 3):
        for j in range (-2, 3):
            mask[event.y + i][event.x + j] = 1

def draw_blue_line(event):
    global cnvs_img, mask
    cnvs_img.create_rectangle(event.x - 2, event.y + 2, event.x + 2, event.y - 2, 
                        outline='blue', fill='blue',  tags='lines')
    for i in range (-2, 3):
        for j in range (-2, 3):
            mask[event.y + i][event.x + j] = -1

def upload_image():
    global cnvs_img, img, ph_img, mask
    image_types = [('Image Files', '*.jpg'), ('Image Files','*.png')]
    filename = askopenfilename(filetypes=image_types)

    img = Image.open(filename)
    max_size = (window_width - frm_buttons.winfo_width(), window_height)
    img.thumbnail(max_size)

    frm_cnvs = tk.Frame(window)
    if cnvs_img:
        cnvs_img.destroy()
    cnvs_img = tk.Canvas(frm_cnvs, width=img.size[0], height=img.size[1])
    ph_img = ImageTk.PhotoImage(img)
    cnvs_img.create_image(0, 0, image=ph_img, anchor='nw')
    frm_cnvs.grid(row=0, column=1)
    cnvs_img.pack()

    cnvs_img.bind("<Button-1>", begin_draw)
    cnvs_img.bind("<B1-Motion>", draw_red_line)
    cnvs_img.bind("<Button-3>", begin_draw)
    cnvs_img.bind("<B3-Motion>", draw_blue_line)

    btn_clear.grid(row=1, column=0, sticky="ew", pady=10)

    mask = np.zeros(img.size)

def clear_canvas():
    global cnvs_img, img, mask
    cnvs_img.delete('lines')
    mask = np.zeros(img.size)

def get_mask():
    print(mask[:20, :20])

window = tk.Tk()
window.title('GUI for GraphCut')
window_width, window_height = window.wm_maxsize()
window.rowconfigure(0, minsize=200, weight=1)
window.columnconfigure(0, minsize=200, weight=1)

frm_buttons = tk.Frame(window)
frm_buttons.grid(row=0, column=0, sticky="ns")
btn_upload = tk.Button(frm_buttons, text='Upload Image', relief=tk.RIDGE,
                       width=20, height=2, bg=button_color,
                       command = upload_image)
btn_upload.grid(row=0, column=0, sticky="ew", pady=10)

btn_clear = tk.Button(frm_buttons, text='Clear Mask', relief=tk.RIDGE,
                       width=20, height=2, bg=button_color,
                       command = clear_canvas)

btn_predict = tk.Button(frm_buttons, text='Predict', relief=tk.RIDGE,
                       width=20, height=2, bg=button_color,
                       command = get_mask)

window.mainloop()