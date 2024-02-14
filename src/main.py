import argparse
import logging
import tkinter as tk
from pathlib import Path

from utils import ImageAnnotator, ImagesToAnnotate


def launch(args):
    logger = logging.getLogger(__name__)

    root = tk.Tk()
    root.title("Points Annotator")
    canvas = tk.Canvas(root)
    canvas.pack(fill="both", expand=True)

    imgs = ImagesToAnnotate(args.imgs_dir, logger=logger, outdir=args.outdir)
    daa = ImageAnnotator(canvas, all_imgs=imgs)

    def show_next_img_on_canvas():
        daa.save_annotated_img()
        if daa.loaded_img_idx + 1 >= len(daa.all_imgs.imgs_paths):
            logger.info("No more images to show")
            # Close the canvas
            root.quit() 
        else:
            daa.load_new_img(daa.loaded_img_idx + 1)

    next_button = tk.Button(root, text="Next", command=show_next_img_on_canvas)
    next_button.pack(side="right")

    # Change the root window size to fit the image
    root.geometry(f"{daa.original_image.width}x{daa.original_image.height}")

    root.mainloop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("imgs_dir", help="Path to the directory containing images that you want to annotate", type=Path)
    parser.add_argument(
        "--outdir",
        help="Path to the output directory where the points2D.txt and annotated images will be saved",
        type=Path,
        default="./output",
    )
    args = parser.parse_args()
    launch(args)
