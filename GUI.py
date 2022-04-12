import tkinter as tk
from tkinter.filedialog import askopenfilename
from turtle import st
from PIL import Image, ImageTk
import GraphCut

# image max size: 1351 * 738   =>  1320 * 730 

button_color = 'plum'

cnvs = None
img = None

bg_pixels = []
fg_pixels = []


def pixel(x, y):
    w, h = img.size
    return (max(min(w - 3, x), 2), max(min(h - 3, y), 2))

def draw_red_line(event):
    global cnvs, fg_pixels
    cnvs.create_rectangle(event.x - 2, event.y + 2, event.x + 2, event.y - 2, 
                              outline='', fill='red',  tags='lines')
    for i in range (-2, 3):
        for j in range (-2, 3):
            fg_pixels.append(pixel(event.x + i, event.y + j))

def draw_blue_line(event):
    global cnvs, bg_pixels
    cnvs.create_rectangle(event.x - 2, event.y + 2, event.x + 2, event.y - 2, 
                              outline='', fill='blue',  tags='lines')
    for i in range (-2, 3):
        for j in range (-2, 3):
            bg_pixels.append(pixel(event.x + i, event.y + j))

def upload_image():
    global cnvs, img, ph_img, image_contain
    image_types = [('Image Files', '*.jpg'), ('Image Files','*.png')]
    filename = askopenfilename(filetypes=image_types)

    img = Image.open(filename)
    w, h = img.size

    if cnvs:
        clear_canvas()
        cnvs.destroy()

    cnvs = tk.Canvas(window, width=w, height=h)
    ph_img = ImageTk.PhotoImage(img)
    image_contain = cnvs.create_image(0, 0, image=ph_img, anchor='nw')
    cnvs.grid(row=0, column=1)

    cnvs.bind("<B1-Motion>", draw_red_line)
    cnvs.bind("<ButtonRelease-1>", predict)
    cnvs.bind("<B3-Motion>", draw_blue_line)
    cnvs.bind("<ButtonRelease-3>", predict)

    btn_clear.grid(row=1, column=0, padx=10, pady=15)

def clear_canvas():
    global cnvs, bg_pixels, fg_pixels
    cnvs.delete('lines')
    cnvs.itemconfig(image_contain, image=ph_img)
    bg_pixels = []
    fg_pixels = []

def predict(event):
    global img, ph_mask, image_contain
    if (len(bg_pixels) * len(fg_pixels)):
        mask = GraphCut.predict(img, fg_pixels, bg_pixels)
        ph_mask = ImageTk.PhotoImage(mask)
        cnvs.itemconfig(image_contain, image=ph_mask)


window = tk.Tk()
window.title('GUI for GraphCut')
window.rowconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
frm_buttons = tk.Frame(window)
frm_buttons.grid(row=0, column=0, rowspan=2)
btn_upload = tk.Button(frm_buttons, text='Upload Image', relief=tk.RIDGE,
                       width=20, height=2, bg=button_color,
                       command = upload_image)
btn_upload.grid(row=0, column=0, padx = 10, pady=15)

btn_clear = tk.Button(frm_buttons, text='Clear Mask', relief=tk.RIDGE,
                       width=20, height=2, bg=button_color,
                       command = clear_canvas)

window.mainloop()