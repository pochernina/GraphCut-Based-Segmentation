import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk
import GraphCut

'''
GraphCut1 - начальная версия
GraphCut2 - 4-связность, greyscale, доп вес (на границе)
GraphCut3 - 6-связность, greyscale, доп вес
GraphCut4 - 8-связность, greyscale, доп вес, работает плохо почему-то :(
GraphCut5 - 6-связность, greyscale, красивая маска!

продолжаю с третьей версией
'''

button_color = 'plum'

cnvs_img = None
img = None
lbl_mask = None

bg_pixels = []
fg_pixels = []


def pixel(x, y):
    w, h = img.size
    return (max(min(w - 3, x), 2), max(min(h - 3, y), 2))

def draw_red_line(event):
    global cnvs_img, fg_pixels
    cnvs_img.create_rectangle(event.x - 2, event.y + 2, event.x + 2, event.y - 2, 
                              outline='red', fill='red',  tags='lines')
    for i in range (-2, 3):
        for j in range (-2, 3):
            fg_pixels.append(pixel(event.x + i, event.y + j))

def draw_blue_line(event):
    global cnvs_img, bg_pixels
    cnvs_img.create_rectangle(event.x - 2, event.y + 2, event.x + 2, event.y - 2, 
                              outline='blue', fill='blue',  tags='lines')
    for i in range (-2, 3):
        for j in range (-2, 3):
            bg_pixels.append(pixel(event.x + i, event.y + j))

def upload_image():
    global cnvs_img, img, frm_mask, ph_img
    image_types = [('Image Files', '*.jpg'), ('Image Files','*.png')]
    filename = askopenfilename(filetypes=image_types)

    img = Image.open(filename)
    max_size = (window_width // 2 - 25, window_height - frm_buttons.winfo_height() - 50)
    img.thumbnail(max_size)

    frm_cnvs = tk.Frame(window)
    if cnvs_img:
        clear_canvas()
        cnvs_img.destroy()
    frm_img = tk.Frame(frm_cnvs)
    frm_img.grid(row=0, column=0, padx=10, pady=10)
    frm_mask = tk.Frame(frm_cnvs, width=img.size[0], height=img.size[1])
    frm_mask.grid(row=0, column=1, padx=10, pady=10)

    cnvs_img = tk.Canvas(frm_img, width=img.size[0], height=img.size[1])
    ph_img = ImageTk.PhotoImage(img)
    cnvs_img.create_image(0, 0, image=ph_img, anchor='nw')
    frm_cnvs.rowconfigure(0, minsize=200, weight=2)
    frm_cnvs.grid(row=1, column=0)
    cnvs_img.pack()

    cnvs_img.bind("<B1-Motion>", draw_red_line)
    cnvs_img.bind("<ButtonRelease-1>", predict)
    cnvs_img.bind("<B3-Motion>", draw_blue_line)
    cnvs_img.bind("<ButtonRelease-3>", predict)

    btn_clear.grid(row=0, column=1, padx=20, pady=15)

def clear_canvas():
    global cnvs_img, bg_pixels, fg_pixels, lbl_mask
    cnvs_img.delete('lines')
    if lbl_mask:
        lbl_mask.destroy()
    bg_pixels = []
    fg_pixels = []

def predict(event):
    global img, frm_mask, lbl_mask
    if (len(bg_pixels) * len(fg_pixels)):
        mask = GraphCut.predict(img, fg_pixels, bg_pixels)
        mask.thumbnail(img.size)
        ph_mask = ImageTk.PhotoImage(mask)
        if lbl_mask:
            lbl_mask.destroy()
        lbl_mask = tk.Label(frm_mask, image=ph_mask)
        lbl_mask.image = ph_mask
        lbl_mask.pack()


window = tk.Tk()
window.title('GUI for GraphCut')
window_width, window_height = window.wm_maxsize()
window.columnconfigure(0, minsize=250, weight=1)

frm_buttons = tk.Frame(window)
frm_buttons.rowconfigure(0, minsize=125, weight=1)
frm_buttons.grid(row=0, column=0, sticky="ns")
btn_upload = tk.Button(frm_buttons, text='Upload Image', relief=tk.RIDGE,
                       width=20, height=2, bg=button_color,
                       command = upload_image)
btn_upload.grid(row=0, column=0, padx = 20, pady=15)

btn_clear = tk.Button(frm_buttons, text='Clear Mask', relief=tk.RIDGE,
                       width=20, height=2, bg=button_color,
                       command = clear_canvas)

btn_predict = tk.Button(frm_buttons, text='Predict', relief=tk.RIDGE,
                       width=20, height=2, bg=button_color, 
                       command = predict)

window.mainloop()