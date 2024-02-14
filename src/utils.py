import asyncio
import logging
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import simpledialog

from PIL import Image, ImageDraw, ImageFont, ImageTk



@dataclass
class AnnotatedPoint:
    x: float
    y: float
    label: str


class ImagesToAnnotate:
    def __init__(self, imgs_dir: Path, logger: logging.Logger = None, outdir: Path = None):
        
        self.imgs_paths = [p for p in imgs_dir.iterdir() if p.suffix in [".jpg", ".png", ".jpeg"]]

        # Sort the images by name
        self.imgs_paths.sort(key=lambda p: p.name)
        self.annotated_points = [[] for _ in range(len(self.imgs_paths))]

        self.logger = logger or logging.getLogger(__name__)

        if len(self.imgs_paths) == 0:
            raise Exception(f"No image files found in {imgs_dir}")

        self.logger.info(f"Found {len(self.imgs_paths)} image files in {imgs_dir}")

        first_image = Image.open(self.imgs_paths[0])
        first_img_res = f"W: {first_image.width}, H: {first_image.height}"
        logger.info(f"First image has resolution {first_img_res}")

        self.outdir = outdir
        self._setup_output_file()

    def _setup_output_file(self):
        
        out_fpath = self.outdir / "points2D.txt"

        # Check if the dir exists
        if not out_fpath.parent.exists():
            out_fpath.parent.mkdir(parents=True)
        else:
            # Check there is no file with the same name
            if out_fpath.exists():
                raise Exception(f"Output file {out_fpath} already exists")

        # Write headers
        with open(out_fpath, "w") as f:
            f.write("img_name point_label x y\n")

        self.out_fpath = out_fpath

    def load_img_from_idx(self, idx: int) -> Image:
        if idx >= len(self.imgs_paths):
            raise Exception(f"Image index {idx} is out of bounds")
        img_path = self.imgs_paths[idx]
        img = Image.open(img_path)
        self.last_loaded_idx = idx
        return img

    def save_point(self, point: AnnotatedPoint):
        self.annotated_points[self.last_loaded_idx].append(point)
        img_name = self.imgs_paths[self.last_loaded_idx].name
        with open(self.out_fpath, "a") as f:
            f.write(f"{img_name} {point.label} {point.x} {point.y}\n")


class ImageNavigator:
    """ 
    Class to handle image navigation in Tkinter given a set of mouse events. Currently implemented:
    - Right click and dragging
    - Zooming in and out with the scroll wheel
    """

    def __init__(self, canvas: tk.Canvas, all_imgs: ImagesToAnnotate):
        
        self.canvas = canvas        
        self.drag_start_x, self.drag_start_y = 0, 0
        
        # accum_x and accum_y keep track (in screen coords) of the top-left corner of the image (if negative or higher than the screen resolution, it is out of the screen)
        self.accum_x, self.accum_y = 0, 0

        self.dragging = False
        self.zoom_lvl = 1.0
        self.all_imgs = all_imgs
        self.loaded_img_idx = 0

        self.last_zoom_ts = time.time()

        self.load_new_img(self.loaded_img_idx)

        # Bind the mouse events to the functions
        canvas.bind("<ButtonPress-1>", self.start_drag)
        canvas.bind("<ButtonRelease-1>", self.stop_drag)
        canvas.bind("<B1-Motion>", self.execute_drag)

        # Bind de scroll wheel to zoom
        canvas.bind("<Button-4>", self.zoom)  # Zoom-in
        canvas.bind("<Button-5>", self.zoom)  # Zoom-out

    def update_img_on_canvas(self, is_zooming=False, center_x=0, center_y=0):
        """
        center_x, center_y: what point of the canvas should appear at the center of the screen, in canvas coordinates
        """
        if self.zoom_lvl != 1.0:
            new_size = (int(self.original_image.width * self.zoom_lvl), int(self.original_image.height * self.zoom_lvl))
            pil_img = self.original_image.resize(new_size, Image.LANCZOS)
        else:
            pil_img = self.original_image
        tk_image = ImageTk.PhotoImage(pil_img)
        self.canvas.image = tk_image
        self.canvas.create_image(0, 0, image=tk_image, anchor="nw")
        # Center the image on the canvas
        if is_zooming:
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            # top_left_x/y times -1 is the position in canvas coordinates of the top-left corner of the screen
            top_left_x = int(canvas_w / 2 - center_x)
            top_left_y = int(canvas_h / 2 - center_y)
            self.canvas.scan_dragto(top_left_x, top_left_y, gain=1)
            self.accum_x = top_left_x
            self.accum_y = top_left_y

    def load_new_img(self, img_idx: int):
        self.loaded_img_idx = img_idx
        img = self.all_imgs.load_img_from_idx(img_idx)
        self.original_image = img
        self.zoom_lvl = 1.0
        self.accum_x, self.accum_y = 0, 0
        self.update_img_on_canvas()

    def start_drag(self, event):
        self.dragging = True
        self.drag_start_x = event.x  # event.x and .y are the screen-coordinates of the mouse
        self.drag_start_y = event.y

    def stop_drag(self, event):
        self.accum_x += event.x - self.drag_start_x
        self.accum_y += event.y - self.drag_start_y
        print(f"Accumulated X: {-self.accum_x}, Accumulated Y: {-self.accum_y}")
        self.dragging = False

    def execute_drag(self, event):
        if self.dragging is True:
            delta_x = event.x - self.drag_start_x + self.accum_x
            delta_y = event.y - self.drag_start_y + self.accum_y
            self.canvas.scan_dragto(delta_x, delta_y, gain=1)

    def _convert_to_original_pixel_coords(self, pixel_x, pixel_y):
        """
        Given the pixel of a resized image, return the pixel in the original image. Returns a float value
        """
        return pixel_x / self.zoom_lvl, pixel_y / self.zoom_lvl

    def _convert_to_resized_pixel_coords(self, pixel_x, pixel_y):
        """
        Given the pixel of am image in, return the pixel coords in the resized image. Returns a float value
        """
        return pixel_x * self.zoom_lvl, pixel_y * self.zoom_lvl

    def zoom(self, event):
        """Zoom in or out of the image"""
        # Do not apply many resize operations in a short time
        if (time.time() - self.last_zoom_ts) > 0.1:
            # Get the pixel (in original size) that the mouse is pointing to
            pixel_x = event.x - self.accum_x
            pixel_y = event.y - self.accum_y
            pixel_x_original, pixel_y_original = self._convert_to_original_pixel_coords(pixel_x, pixel_y)

            if event.num == 5:
                self.zoom_lvl -= 0.5 if self.zoom_lvl > 0.6 else 0

            elif event.num == 4:
                self.zoom_lvl += 0.5 if self.zoom_lvl < 5.0 else 0

            print(f"Zoom level: {self.zoom_lvl}")

            # Get the new canvas coordinates of the pixel the mouse is pointing to
            pixel_x_new, pixel_y_new = self._convert_to_resized_pixel_coords(pixel_x_original, pixel_y_original)

            self.update_img_on_canvas(is_zooming=True, center_x=pixel_x_new, center_y=pixel_y_new)

            self.last_zoom_ts = time.time()


class ImageAnnotator(ImageNavigator):
    def __init__(self, canvas: tk.Canvas, all_imgs: ImagesToAnnotate):
        super().__init__(canvas, all_imgs)
        self.annotated_imgs_path = all_imgs.outdir / "annotated_imgs"
        self.annotated_imgs_path.mkdir(exist_ok=True)

        # Bind the right click to annotate points
        canvas.bind("<Button-3>", self.annotate_point)

    def annotate_point(self, event):
        """
        When a pixel of the image is clicked, draw a red cross on that point, and
        print the coordinates of the pixel on the screen
        """
        x, y = event.x - self.accum_x, event.y - self.accum_y
        x_original, y_original = self._convert_to_original_pixel_coords(x, y)

        label = simpledialog.askstring("Input", "Enter point label", parent=self.canvas)
        point = AnnotatedPoint(x_original, y_original, label)

        self.draw_point_on_image(point)

        # Save point coords in txt file
        self.all_imgs.save_point(point)

        print(f"Clicked pixel coordinates: ({x}, {y})")
        print(f"Original pixel coordinates: ({x_original}, {y_original})")

    def draw_point_on_image(self, point: AnnotatedPoint):
        """ 
        Draws a red cross and the label of the point on the image
        """        
        pixels_map = self.original_image.load()
        for i in range(int(point.x) - 5, int(point.x) + 5):
            pixels_map[i, int(point.y)] = (255, 0, 0)
        for j in range(int(point.y) - 5, int(point.y) + 5):
            pixels_map[int(point.x), j] = (255, 0, 0)

        draw = ImageDraw.Draw(self.original_image)
        draw.text((int(point.x) + 7, int(point.y) - 20), point.label, fill="red", font=ImageFont.load_default(size=20))
        self.update_img_on_canvas()


    def save_annotated_img(self):
        # Get img_name
        img_name = self.all_imgs.imgs_paths[self.loaded_img_idx].name
        self.original_image.save(self.annotated_imgs_path / img_name)

