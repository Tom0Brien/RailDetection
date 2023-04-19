import os
import tkinter as tk
import glob
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk, ImageDraw


class LabelingTool(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Rail Labeling Tool")
        self.image_path = None

        self.canvas = tk.Canvas(self, bg="white", width=1024, height=1024)
        self.canvas.pack(side=tk.LEFT)

        self.pen_color = "blue"
        self.pen_radius = 5

        self.canvas.bind("<B1-Motion>", self.paint)

        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        self.file_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_menu)

        self.pen_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="Pen", menu=self.pen_menu)
        self.pen_menu.add_command(
            label="Non Rail (Blue)", command=self.set_pen_blue)
        self.pen_menu.add_command(label="Rail (Red)", command=self.set_pen_red)
        self.pen_menu.add_command(
            label="Set Pen Radius", command=self.set_pen_radius)

        self.init_labelled_images()
        self.image_paths, self.labelled_image_paths = self.load_image_list()
        self.image_index = 0
        self.create_side_panel()
        self.update_image_display()

    def load_image_list(self):
        image_paths = sorted(glob.glob('training_data/*/*.png'))
        image_paths = [
            path for path in image_paths if not path.endswith('_segmentation.png')]
        labelled_image_paths = [path.replace(
            '.png', '_segmentation.png') for path in image_paths]

        return image_paths, labelled_image_paths

    def update_image_display(self):
        if self.image_paths:
            image_path = self.image_paths[self.image_index]
            labelled_image_path = self.labelled_image_paths[self.image_index]

            unlabelled_image = Image.open(image_path)
            labelled_image = Image.open(labelled_image_path).convert('RGBA')

            # Apply opacity to the segmentation layer
            opacity = int(0.5 * 255)
            alpha = Image.new('L', labelled_image.size, opacity)
            labelled_image.putalpha(alpha)

            # Combine unlabelled and labelled images
            combined_image = Image.alpha_composite(
                unlabelled_image.convert('RGBA'), labelled_image)

            self.current_image = combined_image
            self.photo = ImageTk.PhotoImage(self.current_image)
            self.canvas.config(width=self.current_image.width,
                               height=self.current_image.height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

            self.draw = ImageDraw.Draw(self.current_image)

    def create_side_panel(self):
        self.side_panel = tk.Frame(self)
        self.side_panel.pack(side=tk.RIGHT)

        self.image_list = tk.Listbox(self.side_panel)
        self.image_list.pack()

        for index, image_path in enumerate(self.image_paths):
            self.image_list.insert(
                tk.END, f"{index}: {os.path.basename(image_path)}")

        self.image_list.bind("<<ListboxSelect>>", self.on_image_select)

        self.segmentation_done_var = tk.BooleanVar()
        self.segmentation_done_checkbox = tk.Checkbutton(
            self.side_panel, text="Segmentation Done", variable=self.segmentation_done_var)
        self.segmentation_done_checkbox.pack(side=tk.TOP)

        self.prev_button = tk.Button(
            self.side_panel, text="Previous", command=self.prev_image)

    def on_image_select(self, event):
        index = int(self.image_list.curselection()[0])
        self.image_index = index
        self.update_image_display()

    def prev_image(self):
        if self.image_index > 0:
            self.image_index -= 1
            self.update_image_display()

    def next_image(self):
        if self.image_index < len(self.image_paths) - 1:
            self.image_index += 1
            self.update_image_display()

    def create_navigation_ui(self):
        self.navigation_frame = tk.Frame(self)
        self.navigation_frame.pack(side=tk.BOTTOM)

        self.prev_button = tk.Button(
            self.navigation_frame, text="Previous", command=self.prev_image)
        self.prev_button.pack(side=tk.LEFT)

        self.next_button = tk.Button(
            self.navigation_frame, text="Next", command=self.next_image)
        self.next_button.pack(side=tk.RIGHT)

    def init_labelled_images(self):
        training_data_dir = "training_data"
        for root, dirs, files in os.walk(training_data_dir):
            for file in files:
                if file.endswith(".png") and not file.endswith("_segmentation.png"):
                    img_path = os.path.join(root, file)
                    labelled_img_path = img_path.replace(
                        '.png', '_segmentation.png')
                    if not os.path.exists(labelled_img_path):
                        img = Image.open(img_path)
                        labelled_img = Image.new("RGB", img.size, "blue")
                        labelled_img.save(labelled_img_path)

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
        radius = simpledialog.askinteger(
            "Pen Radius", "Enter pen radius:", initialvalue=self.pen_radius)
        if radius:
            self.pen_radius = radius


if __name__ == "__main__":
    app = LabelingTool()
    app.mainloop()
