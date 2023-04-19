import os
import tkinter as tk
import glob
from tkinter import filedialog, simpledialog
from tkinter import font
from PIL import Image, ImageTk, ImageDraw


class RailDetector(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Rail Line Detection Tool")
        self.image_path = None

        big_frame = tk.Frame(self)
        big_frame.pack(fill="both", expand=True)

        self.tk.call("source", "azure.tcl")
        self.tk.call("set_theme", "dark")

        self.canvas = tk.Canvas(self, bg="white", width=1024, height=1024)
        self.canvas.pack(side=tk.RIGHT)

        self.line_width = 10
        self.line_color = "red"
        self.start_pos = None
        self.current_line = None

        self.canvas.bind("<ButtonPress-1>", self.start_line)
        self.canvas.bind("<ButtonRelease-1>", self.end_line)

        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        self.file_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Save", command=self.save_image)

        self.line_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="Line", menu=self.line_menu)
        self.line_menu.add_command(
            label="Rail Line (Red)", command=self.set_line_red)
        self.line_menu.add_command(
            label="Set Line Width", command=self.set_line_width)

        self.init_labelled_images()
        self.image_paths, self.labelled_image_paths = self.load_image_list()
        self.image_index = 0
        self.create_side_panel()
        self.update_image_display()

    def load_image_list(self):
        data_path = 'data'
        image_paths = sorted(glob.glob(os.path.join(
            data_path, "**", "*.png"), recursive=True))
        image_paths = [
            path for path in image_paths if not path.endswith('_segmentation.png')]
        labelled_image_paths = [path.replace(
            '.png', '_segmentation.png') for path in image_paths]
        return image_paths, labelled_image_paths

    def update_image_display(self):
        if self.image_paths:
            image_path = self.image_paths[self.image_index]
            labelled_image_path = self.labelled_image_paths[self.image_index]

            unlabelled_image = Image.open(image_path).convert('RGBA')
            labelled_image = Image.open(labelled_image_path).convert('RGBA')

            # Create a binary mask by converting labelled_image to grayscale and
            # thresholding at a mid-range value
            mask = labelled_image.convert('L').point(
                lambda x: 255 if x > 128 else 0)

            # Colorize the mask with a fixed color
            color = (255, 0, 0, 128)  # red with 50% transparency
            mask_rgb = Image.new('RGBA', labelled_image.size, color)
            mask_rgb.putalpha(mask)

            # Combine unlabelled image with colorized mask
            combined_image = Image.alpha_composite(unlabelled_image, mask_rgb)

            self.current_image = combined_image
            self.photo = ImageTk.PhotoImage(self.current_image)
            self.canvas.config(width=self.current_image.width,
                               height=self.current_image.height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.draw = ImageDraw.Draw(self.current_image)

    def create_side_panel(self):
        self.side_panel = tk.Frame(self, width=200)
        self.side_panel.pack(side=tk.LEFT, fill=tk.Y)

        self.image_list = tk.Listbox(self.side_panel)
        self.image_list.pack(fill=tk.BOTH, expand=True)

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
        self.prev_button.pack(side=tk.TOP)

        self.next_button = tk.Button(
            self.side_panel, text="Next", command=self.next_image)
        self.next_button.pack(side=tk.TOP)

        # Prevent the side panel from resizing with its contents
        self.side_panel.pack_propagate(0)

    def on_image_select(self, event):
        index = int(self.image_list.curselection()[0])
        self.image_index = index
        self.update_image_display()

    def prev_image(self):
        if self.image_index > 0:
            self.image_index -= 1
            self.update_image_display()
            self.image_list.selection_clear(0, tk.END)
            self.image_list.selection_set(self.image_index)

    def next_image(self):
        if self.image_index < len(self.image_paths) - 1:
            self.image_index += 1
            self.update_image_display()
            self.image_list.selection_clear(0, tk.END)
            self.image_list.selection_set(self.image_index)

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
        data_dir = 'data'
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.png') and not file.endswith('_segmentation.png'):
                    img_path = os.path.join(root, file)
                    labelled_img_path = img_path.replace(
                        '.png', '_segmentation.png')
                    if not os.path.exists(labelled_img_path):
                        img = Image.open(img_path)
                        labelled_img = Image.new(
                            "RGBA", img.size, (0, 0, 0, 0))
                        labelled_img.save(labelled_img_path)

    def start_line(self, event):
        self.start_pos = event.x, event.y
        self.current_line = self.canvas.create_line(
            self.start_pos[0], self.start_pos[1], self.start_pos[0], self.start_pos[1],
            width=self.line_width, fill=self.line_color, capstyle=tk.ROUND, smooth=True)

    def end_line(self, event):
        if self.start_pos:
            x1, y1 = self.start_pos
            x2, y2 = event.x, event.y
            self.canvas.coords(self.current_line, x1, y1, x2, y2)
            self.start_pos = None

    def set_line_red(self):
        self.line_color = "red"

    def set_line_width(self):
        width = simpledialog.askinteger(
            "Line Width", "Enter line width:", initialvalue=self.line_width)
        if width:
            self.line_width = width

    def save_image(self):
        if self.image_path:
            labelled_image_path = self.labelled_image_paths[self.image_index]

            # Create a binary mask by converting the segmented image to grayscale and
            # thresholding at a mid-range value
            segmented_image = Image.open(labelled_image_path).convert('RGBA')
            mask = segmented_image.convert('L').point(
                lambda x: 255 if x > 128 else 0)

            # Colorize the mask with red for the lines
            color = (255, 0, 0, 255)  # red with 100% transparency
            mask_rgb = Image.new('RGBA', segmented_image.size, (0, 0, 0, 255))
            mask_rgb.putalpha(mask)
            mask_rgb = Image.composite(mask_rgb, Image.new(
                'RGBA', segmented_image.size, color), mask_rgb)

            # Save the colorized mask as the new segmented image
            mask_rgb.save(labelled_image_path)

            print(f"Segmentation saved to {labelled_image_path}")
            self.update_image_display()
        else:
            print("No image loaded")

    def create_tool_ui(self):
        self.tool_frame = tk.Frame(self)
        self.tool_frame.pack(side=tk.TOP)

        self.pen_label = tk.Label(self.tool_frame, text="Pen:")
        self.pen_label.pack(side=tk.LEFT)

        self.pen_blue_button = tk.Button(
            self.tool_frame, text="Non Rail (Blue)", command=self.set_pen_blue)
        self.pen_blue_button.pack(side=tk.LEFT)

        self.pen_red_button = tk.Button(
            self.tool_frame, text="Rail (Red)", command=self.set_pen_red)
        self.pen_red_button.pack(side=tk.LEFT)

        self.pen_radius_button = tk.Button(
            self.tool_frame, text="Set Pen Radius", command=self.set_pen_radius)
        self.pen_radius_button.pack(side=tk.LEFT)

        self.line_label = tk.Label(self.tool_frame, text="Line:")
        self.line_label.pack(side=tk.LEFT)

        self.line_red_button = tk.Button(
            self.tool_frame, text="Rail Line (Red)", command=self.set_line_red)
        self.line_red_button.pack(side=tk.LEFT)

        self.line_width_button = tk.Button(
            self.tool_frame, text="Set Line Width", command=self.set_line_width)
        self.line_width_button.pack(side=tk.LEFT)

        self.save_button = tk.Button(
            self.tool_frame, text="Save", command=self.save_image)
        self.save_button.pack(side=tk.LEFT)

    def run(self):
        self.create_tool_ui()
        self.create_navigation_ui()
        self.mainloop()


if __name__ == "__main__":
    app = RailDetector()
    app.mainloop()
