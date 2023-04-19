import os
import json
import tkinter as tk
import glob
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk, ImageDraw
import math


class RailDetector(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Rail Line Detection Tool")
        self.image_path = None

        self.line_width = 10
        self.line_color = (0, 0, 255, 80)
        self.line_notch_color = (0, 0, 255, 200)
        self.snap_distance = 20
        self.start_pos = None
        self.current_line = None
        self.selected_notch = None
        self.notch_click_radius = 10
        self.selected_rail_line_index = None

        self.canvas = tk.Canvas(self, bg="white", width=1024, height=1024)
        self.canvas.pack(side=tk.RIGHT)

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<ButtonRelease-1>", self.end_line)
        self.canvas.bind("<B1-Motion>", self.on_canvas_move)
        self.canvas.bind("<Delete>", self.delete_selected_line)

        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        self.file_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Save", command=self.save_image)

        self.line_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="Line", menu=self.line_menu)
        self.line_menu.add_command(
            label="Set Line Width", command=self.set_line_width)

        self.image_paths = self.load_image_list()
        self.image_index = 0
        self.create_side_panel()

        self.show_lines = tk.BooleanVar()
        self.show_lines.set(True)
        self.toggle_lines_button = tk.Checkbutton(
            self.side_panel, text="Show Rail Lines", variable=self.show_lines,
            command=self.update_image_display)
        self.toggle_lines_button.pack(side=tk.TOP)

        self.update_image_display()

    def load_image_list(self):
        data_path = 'data'
        image_paths = sorted(glob.glob(os.path.join(
            data_path, "**", "*.png"), recursive=True))
        image_paths = [
            path for path in image_paths if not path.endswith('_segmentation.png')]
        return image_paths

    def draw_lines(self, image):
        rail_lines = self.load_rail_lines()

        for rail_line in rail_lines:
            x1, y1, x2, y2 = rail_line["coordinates"]

            # Draw rail lines with multiple lines with varying widths and decreasing opacity
            line_image = Image.new(
                'RGBA', image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(line_image)
            draw.line((x1, y1, x2, y2), fill=self.line_color,
                      width=self.line_width, joint='curve')
            image = Image.alpha_composite(image, line_image)

            # Draw rail line notches
            # Draw notches between line segments
            notch_radius = self.line_width * 0.75
            draw = ImageDraw.Draw(line_image)
            draw.ellipse((x1 - notch_radius, y1 - notch_radius, x1 + notch_radius, y1 + notch_radius),
                         fill=self.line_notch_color)
            draw.ellipse((x2 - notch_radius, y2 - notch_radius, x2 + notch_radius, y2 + notch_radius),
                         fill=self.line_notch_color)
            # Change notch color when selected
            if self.selected_notch and self.selected_rail_line_index is not None:
                selected_notch_color = (255, 255, 0, 200)
                selected_x, selected_y = rail_lines[self.selected_rail_line_index]["coordinates"][
                    0 if self.selected_notch == "start" else 2
                ], rail_lines[self.selected_rail_line_index]["coordinates"][
                    1 if self.selected_notch == "start" else 3
                ]
                draw.ellipse((selected_x - notch_radius,
                              selected_y - notch_radius,
                              selected_x + notch_radius,
                              selected_y + notch_radius), fill=selected_notch_color)
            image = Image.alpha_composite(image, line_image)

        return image

    def update_image_display(self):
        if self.image_paths:
            image_path = self.image_paths[self.image_index]
            unlabelled_image = Image.open(image_path).convert('RGBA')

            if self.show_lines.get():
                unlabelled_image = self.draw_lines(unlabelled_image)

            self.current_image = unlabelled_image
            self.photo = ImageTk.PhotoImage(self.current_image)
            self.canvas.config(width=self.current_image.width,
                               height=self.current_image.height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    def create_side_panel(self):
        self.side_panel = tk.Frame(self, width=200)
        self.side_panel.pack(side=tk.LEFT, fill=tk.Y)

        self.image_list = tk.Listbox(self.side_panel)
        self.image_list.pack(fill=tk.BOTH, expand=True)

        for index, image_path in enumerate(self.image_paths):
            self.image_list.insert(
                tk.END, f"{index}: {os.path.basename(image_path)}")

        self.image_list.bind("<<ListboxSelect>>", self.on_image_select)

        self.prev_button = tk.Button(
            self.side_panel, text="Previous", command=self.prev_image)
        self.prev_button.pack(side=tk.TOP)

        self.next_button = tk.Button(
            self.side_panel, text="Next", command=self.next_image)
        self.next_button.pack(side=tk.TOP)

        self.generate_segmentation_button = tk.Button(
            self.side_panel, text="Generate Segmentation Mask", command=self.generate_segmentation_mask)
        self.generate_segmentation_button.pack(side=tk.TOP)

        # Prevent the side panel from resizing with its contents
        self.side_panel.pack_propagate(0)

    def on_image_select(self, event):
        index = int(self.image_list.curselection()[0])
        self.image_index = index
        self.update_image_display()

    def delete_selected_line(self, event):
        if self.selected_rail_line_index is not None:
            rail_lines = self.load_rail_lines()
            rail_lines.pop(self.selected_rail_line_index)
            self.save_rail_lines(rail_lines)
            self.selected_notch = None
            self.selected_rail_line_index = None
            self.update_image_display()

    def on_canvas_move(self, event):
        if self.selected_notch is not None and self.selected_rail_line_index is not None:
            rail_lines = self.load_rail_lines()
            rail_lines[self.selected_rail_line_index]["coordinates"][self.selected_notch *
                                                                     2:self.selected_notch * 2 + 2] = [event.x, event.y]

            for index, rail_line in enumerate(rail_lines):
                if index != self.selected_rail_line_index:
                    for coord_index in range(0, 4, 2):
                        x, y = rail_line["coordinates"][coord_index:coord_index + 2]
                        distance = math.sqrt(
                            (event.x - x) ** 2 + (event.y - y) ** 2)
                        if distance <= self.snap_distance:
                            rail_lines[self.selected_rail_line_index]["coordinates"][self.selected_notch *
                                                                                     2:self.selected_notch * 2 + 2] = [x, y]

            self.save_rail_lines(rail_lines)
            self.update_image_display()

    def on_canvas_click(self, event):
        self.canvas.focus_set()
        rail_lines = self.load_rail_lines()

        # Check if the user clicked on a notch
        for index, rail_line in enumerate(rail_lines):
            for coord_index in range(0, 4, 2):
                x, y = rail_line["coordinates"][coord_index:coord_index + 2]
                distance = math.sqrt(
                    (event.x - x) ** 2 + (event.y - y) ** 2)
                if distance <= self.notch_click_radius:
                    self.selected_notch = coord_index // 2
                    self.selected_rail_line_index = index
                    return

        if self.selected_notch:
            self.unselect_notch()
        else:
            self.start_line(event)

    def start_line(self, event):
        self.start_pos = (event.x, event.y)
        self.current_line = self.canvas.create_line(
            *self.start_pos, *self.start_pos, fill=self.line_notch_color, width=self.line_width
        )
        self.canvas.bind("<B1-Motion>", self.update_line)

    def update_line(self, event):
        if self.current_line:
            self.canvas.coords(self.current_line, *
                               self.start_pos, event.x, event.y)

    def end_line(self, event):
        if self.start_pos and self.current_line:
            # Check if the end point is close to another notch and combine them
            rail_lines = self.load_rail_lines()
            for line_index, rail_line in enumerate(rail_lines):
                x1, y1, x2, y2 = rail_line["coordinates"]
                distance1 = math.sqrt(
                    (event.x - x1) ** 2 + (event.y - y1) ** 2)
                distance2 = math.sqrt(
                    (event.x - x2) ** 2 + (event.y - y2) ** 2)
                if distance1 <= self.notch_click_radius:
                    self.start_pos = (x1, y1)
                    self.combine_notches(line_index, 0)
                    break
                elif distance2 <= self.notch_click_radius:
                    self.start_pos = (x2, y2)
                    self.combine_notches(line_index, 1)
                    break
                x1, y1 = self.start_pos
                x2, y2 = event.x, event.y

                self.canvas.delete(self.current_line)
                self.current_line = None
                self.canvas.unbind("<B1-Motion>")

                rail_line = {
                    "coordinates": [x1, y1, x2, y2],
                }

                rail_lines = self.load_rail_lines()
                rail_lines.append(rail_line)
                self.save_rail_lines(rail_lines)
                self.update_image_display()

    def combine_notches(self, line_index, notch_index):
        rail_lines = self.load_rail_lines()
        self.selected_rail_line_index = line_index
        self.selected_notch = notch_index
        self.end_line(tk.Event())

    def unselect_notch(self):
        self.selected_notch = None
        self.selected_rail_line_index = None
        self.update_image_display()

    def set_line_width(self):
        width = simpledialog.askinteger(
            "Line Width", "Enter line width:", initialvalue=self.line_width)
        if width:
            self.line_width = width

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

    def start_line(self, event):
        self.start_pos = event.x, event.y

    def end_line(self, event):
        if self.start_pos:
            x1, y1 = self.start_pos
            x2, y2 = event.x, event.y
            self.start_pos = None

            rail_line = {
                "id": len(self.load_rail_lines()),
                "type": "rail",
                "color": self.line_color,
                "coordinates": (x1, y1, x2, y2)
            }

            rail_lines = self.load_rail_lines()
            rail_lines.append(rail_line)
            self.save_rail_lines(rail_lines)
            self.update_image_display()

    def set_line_width(self):
        width = simpledialog.askinteger(
            "Line Width", "Enter line width:", initialvalue=self.line_width)
        if width:
            self.line_width = width

    def save_image(self):
        print("Rail lines saved")

    def generate_segmentation_mask(self):
        # TODO: Implement segmentation mask generation from rail lines
        print("Generating segmentation mask")

    def load_rail_lines(self):
        rail_lines_path = self.get_rail_lines_path()
        if os.path.exists(rail_lines_path):
            with open(rail_lines_path, "r") as f:
                rail_lines = json.load(f)
        else:
            rail_lines = []
        return rail_lines

    def save_rail_lines(self, rail_lines):
        rail_lines_path = self.get_rail_lines_path()
        with open(rail_lines_path, "w") as f:
            json.dump(rail_lines, f)

    def get_rail_lines_path(self):
        return self.image_paths[self.image_index].replace(".png", "_rail_lines.json")

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = RailDetector()
    app.run()
