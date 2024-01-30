import argparse
import asyncio
import logging
import os
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, simpledialog

from PIL import Image, ImageDraw, ImageFont, ImageTk


@dataclass
class AnnotatedPoint:
    x: int
    y: int
    label: str


class ImagesToAnnotate:
    
    def __init__(self, imgs_dir: Path | str, logger: logging.Logger = None, output_fpath: Path | str = None):
        imgs_dir = Path(imgs_dir)
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

        self._setup_output_file(output_fpath)

    def _setup_output_file(self, output_file: Path | str):
        out_fpath = output_file or Path("./points2D.txt")
        # Check that it is a txt
        if out_fpath.suffix != ".txt":
            raise Exception(f"Output file {out_fpath} is not a txt file")

        # Check if the dir exists
        if not out_fpath.parent.exists():
            out_fpath.parent.mkdir(parents=True)
        else:
            # Check there is no file with the same name
            if out_fpath.exists():
                raise Exception(f"Output file {out_fpath} already exists")
            
        # Write headers
        with open(out_fpath, "w") as f:
            f.write("cam_idx point_id x y\n")
        
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
        with open(self.out_fpath, "a") as f:
            f.write(f"{self.last_loaded_idx + 1} {point.label} {point.x} {point.y}\n")


class DraggerAndAnnotator:
    def __init__(self, canvas: tk.Canvas, all_imgs: ImagesToAnnotate):
        self.canvas = canvas
        self.drag_start_x, self.drag_start_y = 0, 0
        self.accum_x, self.accum_y = 0, 0
        self.dragging = False
        self.zoom_lvl = 1.0
        self.all_imgs = all_imgs
        self.loaded_img_idx = 0
        self.annotated_imgs_path = Path("./annotated_imgs")
        self.annotated_imgs_path.mkdir(parents=True, exist_ok=True)

        self.last_zoom_ts = time.time()

        self.load_new_img(self.loaded_img_idx)

        # Bind the mouse events to the functions
        canvas.bind("<ButtonPress-1>", self.start_drag)
        canvas.bind("<ButtonRelease-1>", self.stop_drag)
        canvas.bind("<B1-Motion>", self.execute_drag)

        # Bind the right click to annotate points
        canvas.bind("<Button-3>", self.annotate_point)

        # Bind de scroll wheel to zoom
        canvas.bind("<Button-4>", self.zoom)  # Zoom-in
        canvas.bind("<Button-5>", self.zoom)  # Zoom-out

    def update_img_on_canvas(self):        
        if self.zoom_lvl != 1.0:
            new_size = (int(self.original_image.width * self.zoom_lvl), int(self.original_image.height * self.zoom_lvl))
            pil_img = self.original_image.resize(new_size, Image.LANCZOS)
        else:
            pil_img = self.original_image
        tk_image = ImageTk.PhotoImage(pil_img)
        self.canvas.image = tk_image
        self.canvas.create_image(0, 0, image=tk_image, anchor="nw")

    def load_new_img(self, img_idx: int):
        self.loaded_img_idx = img_idx
        img = self.all_imgs.load_img_from_idx(img_idx)
        self.original_image = img
        self.zoom_lvl = 1.0
        self.update_img_on_canvas()

    def start_drag(self, event):
        self.dragging = True
        self.drag_start_x = event.x
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

    def annotate_point(self, event):
        """
        When a pixel of the image is clicked, draw a red cross on that point, and
        print the coordinates of the pixel on the screen
        """
        x, y = event.x - self.accum_x, event.y - self.accum_y
        x_original = int(x / self.zoom_lvl)
        y_original = int(y / self.zoom_lvl)



        label = simpledialog.askstring("Input", "Enter point label", parent=self.canvas)
        point = AnnotatedPoint(x_original, y_original, label)

        pixels_map = self.original_image.load()
        for i in range(x_original - 5, x_original + 5):
            pixels_map[i, y_original] = (255, 0, 0)
        for j in range(y_original - 5, y_original + 5):
            pixels_map[x_original, j] = (255, 0, 0)


        draw = ImageDraw.Draw(self.original_image)
        draw.text((x_original + 7, y_original - 20), label, fill="red", font=ImageFont.load_default(size=20))
        self.update_img_on_canvas()

        self.all_imgs.save_point(point)

        print(f"Clicked pixel coordinates: ({x}, {y})")
        print(f"Original pixel coordinates: ({x_original}, {y_original})")

    def zoom(self, event):
        """Zoom in or out of the image"""
        # Do not apply many resize operations in a short time
        if (time.time() - self.last_zoom_ts) > 0.4:
            if event.num == 5:
                self.zoom_lvl -= 0.3 if self.zoom_lvl > 0.2 else 0

            elif event.num == 4:
                self.zoom_lvl += 0.3 if self.zoom_lvl < 3.0 else 0

            print(f"Resizing with zoom level {self.zoom_lvl}")

            self.update_img_on_canvas()
            self.last_zoom_ts = time.time()

    def save_annotated_img(self):
        # Get img_name
        img_name = self.all_imgs.imgs_paths[self.loaded_img_idx].name
        self.original_image.save(self.annotated_imgs_path / img_name)

def launch(args):
    logger = logging.getLogger(__name__)

    # Main window using Tkinter
    root = tk.Tk()
    root.title("Points Annotator")
    canvas = tk.Canvas(root)
    canvas.pack(fill="both", expand=True)

    imgs = ImagesToAnnotate(args.imgs, logger=logger)
    daa = DraggerAndAnnotator(canvas, all_imgs=imgs)
    def show_next_img_on_canvas():
        daa.save_annotated_img()
        daa.load_new_img(daa.loaded_img_idx + 1)
    
    next_button = tk.Button(root, text="Next", command=show_next_img_on_canvas)
    next_button.pack(side="right")

    # Change the root window size to fit the image
    root.geometry(f"{daa.original_image.width}x{daa.original_image.height}")

    root.mainloop()
    # imgs.show_next_img_on_canvas()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--imgs", help="Directory containing images", type=str, required=False)
    args = parser.parse_args()
    launch(args)