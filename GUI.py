import tkinter as tk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk
import GraphCut
import numpy as np


button_color = 'plum'
marker_size = 2

cnvs = None
img = None
mask = None

bg_pixels = []
fg_pixels = []
last_scribble = []


def resize(event):
    if cnvs:
        cnvs.configure(scrollregion=cnvs.bbox(tk.ALL))

def pixel(x, y):
    w, h = img.size
    return (max(min(w - marker_size - 1, x), marker_size), max(min(h - marker_size - 1, y), marker_size))

def draw_red_line(event):
    global fg_pixels, last_scribble
    canvas = event.widget
    x = int(canvas.canvasx(event.x))
    y = int(canvas.canvasy(event.y))
    canvas.create_rectangle(x - marker_size, y + marker_size, x + marker_size, y - marker_size, outline='', fill='red',  tags='lines')
    for i in range (-marker_size, marker_size + 1):
         for j in range (-marker_size, marker_size + 1):
            fg_pixels.append(pixel(x + i, y + j))
            last_scribble.append(pixel(x + i, y + j))

def draw_blue_line(event):
    global bg_pixels, last_scribble
    canvas = event.widget
    x = int(canvas.canvasx(event.x))
    y = int(canvas.canvasy(event.y))
    canvas.create_rectangle(x - marker_size, y + marker_size, x + marker_size, y - marker_size, outline='', fill='blue',  tags='lines')
    for i in range (-marker_size, marker_size + 1):
        for j in range (-marker_size, marker_size + 1):
            bg_pixels.append(pixel(x + i, y + j))
            last_scribble.append(pixel(x + i, y + j))


def upload_image():
    global cnvs, img, mask, ph_img, image_contain
    image_types = [('Image Files', '*.jpg'), ('Image Files','*.png')]
    filename = askopenfilename(filetypes=image_types)

    img = Image.open(filename)
    mask = np.zeros(img.size[::-1]) - 1
    w = window.winfo_screenwidth() - frm_buttons.winfo_width()
    h = window.winfo_screenheight()

    if cnvs:
        clear_canvas()
        cnvs.destroy()

    cnvs = tk.Canvas(frm_cnvs, width=w, height=h, xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    scroll_x.config(command=cnvs.xview)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    scroll_y.config(command=cnvs.yview)

    ph_img = ImageTk.PhotoImage(img)
    image_contain = cnvs.create_image(0, 0, image=ph_img, anchor='nw')
    cnvs.pack()

    cnvs.bind("<B1-Motion>", draw_red_line)
    cnvs.bind("<ButtonRelease-1>", predict)
    cnvs.bind("<B3-Motion>", draw_blue_line)
    cnvs.bind("<ButtonRelease-3>", predict)

    btn_clear.grid(row=1, column=0, padx=10, pady=15)


def clear_canvas():
    global cnvs, mask, bg_pixels, fg_pixels, last_scribble
    cnvs.delete('lines')
    cnvs.itemconfig(image_contain, image=ph_img)
    bg_pixels, fg_pixels, last_scribble = [], [], []
    mask = np.zeros(img.size[::-1]) - 1


def predict(event):
    global ph_mask, bg_pixels, fg_pixels, mask, last_scribble
    if not last_scribble:
        return

    predicted_mask = GraphCut.predict(img, fg_pixels, bg_pixels, last_scribble)
    if predicted_mask is None:
        return

    # new_mask = mask.copy()
    # new_mask[(mask==-1) & (predicted_mask==0)] = 0
    # new_mask[(mask==-1) & (predicted_mask==1)] = 1
    # new_mask[(mask!=-1) & (predicted_mask!=-1) & (predicted_mask!=mask)] = -1
    # mask = new_mask

    mask[predicted_mask==0] = 0
    mask[predicted_mask==1] = 1

    mask_a = img.copy()
    mask_a = np.asarray(mask_a).astype('uint8')
    mask_a[mask==-1] = (0, 255, 0)
    mask_a[mask==0] = (0, 0, 255)
    mask_a[mask==1] = (255, 0, 0)
    mask_a = Image.fromarray(mask_a.astype('uint8'), 'RGB')
    mask_a.putalpha(77)    

    img_a = img.copy()
    img_a.putalpha(255)

    im = Image.alpha_composite(img_a, mask_a)
    im.save("result.png", "PNG")
    ph_mask = ImageTk.PhotoImage(im)
    cnvs.itemconfig(image_contain, image=ph_mask)
    last_scribble = []



window = tk.Tk()
window.title('GUI for GraphCut')
window.rowconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
window.bind("<Configure>", resize)

frm_buttons = tk.Frame(window)
frm_buttons.grid(row=0, column=0, rowspan=3)
btn_upload = tk.Button(frm_buttons, text='Upload Image', relief=tk.RIDGE,
                       width=20, height=2, bg=button_color,
                       command = upload_image)
btn_upload.grid(row=0, column=0, padx = 10, pady=15)

btn_clear = tk.Button(frm_buttons, text='Clear Mask', relief=tk.RIDGE,
                       width=20, height=2, bg=button_color,
                       command = clear_canvas)

frm_cnvs = tk.Frame(window)
frm_cnvs.grid(row=0, column=1)
scroll_x = tk.Scrollbar(frm_cnvs, orient=tk.HORIZONTAL)
scroll_y = tk.Scrollbar(frm_cnvs, orient=tk.VERTICAL)

window.mainloop()