import os
import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageTk, ImageDraw


class LabelingTool(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Rail Labeling Tool")
        self.image_path = None

        self.canvas = tk.Canvas(self, bg="white", width=800, height=600)
        self.canvas.pack()

        self.pen_color = "blue"
        self.pen_radius = 5

        self.canvas.bind("<B1-Motion>", self.paint)

        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        self.file_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Image", command=self.open_image)

        self.pen_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="Pen", menu=self.pen_menu)
        self.pen_menu.add_command(
            label="Non Rail (Blue)", command=self.set_pen_blue)
        self.pen_menu.add_command(label="Rail (Red)", command=self.set_pen_red)
        self.pen_menu.add_command(
            label="Set Pen Radius", command=self.set_pen_radius)

        self.init_labelled_images()

    def init_labelled_images(self):
        training_data_dir = "training_data"
        for root, dirs, files in os.walk(training_data_dir):
            for file in files:
                if file.endswith(".png"):
                    img_path = os.path.join(root, file)
                    labelled_img_path = os.path.join(root, f"labelled_{file}")
                    if not os.path.exists(labelled_img_path):
                        img = Image.open(img_path)
                        labelled_img = Image.new("RGB", img.size, "blue")
                        labelled_img.save(labelled_img_path)

    def open_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image_path = file_path
            self.original_image = Image.open(self.image_path)
            self.current_image = self.original_image.copy()
            self.photo = ImageTk.PhotoImage(self.current_image)
            self.canvas.config(width=self.current_image.width,
                               height=self.current_image.height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

            self.draw = ImageDraw.Draw(self.current_image)

    def paint(self, event):
        x1, y1 = event.x - self.pen_radius, event.y - self.pen_radius
        x2, y2 = event.x + self.pen_radius, event.y + self.pen_radius

        self.canvas.create_oval(
            x1, y1, x2, y2, fill=self.pen_color, outline="")
        self.draw.ellipse([x1, y1, x2, y2], fill=self.pen_color)

    def set_pen_blue(self):
        self.pen_color = "blue"

    def set_pen_red(self):
        self.pen_color = "red"

    def set_pen_radius(self):
        radius = tk.simpledialog.askinteger(
            "Pen Radius", "Enter pen radius:", initialvalue=self.pen_radius)
        if radius:
            self.pen_radius = radius


if __name__ == "__main__":
    app = LabelingTool()
    app.mainloop()
