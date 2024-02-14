Simple GUI that lets you annotate points in images by labeling and capturing the coordinates of different points on a set 
of images. 

A `.txt` file is exported containing each point's label and coordinates. Specifically, it has the following format:

```
# Points2D.txt
img_name point_label x y
<name_of_img_1> <label_of_point1> <x coord> <y coord>
<name_of_img_1> <label_of_point2> <x coord> <y coord>
...
<name_of_img_N> <label_of_pointM> <x coord> <y coord>
```

Additionally, the annotated images are saved in the output directory.

## Installation

You need a python version that supports tkinter (python 3.6+). In Ubuntu, you can install it with:

```bash
sudo apt install python3-tk
```

Then, install the requirements:

```bash
pipenv shell # To create the virtual environment
pipenv sync # To install the libraries as specified by the Pipfile.lock
```

## Usage

Within the newly created python environment, run `main.py` with the following arguments:

- `path`: The path to the folder containing the images to annotate.
- (optional) `--output`: The path to the output directory where the points2D.txt and annotated images will be saved.
  Default: `./output`

For example:

```bash
cd point-coords
python3 src/main.py ./test_imgs
```

After running the command, a window will appear with the first image in the folder. COntrols are:

- `Left click and drag`: Move the image around
- `Scroll in/out`: Zoom in/out
- `Right click`: Add a point
- `Next button`: Go to the next image

After right-clicking, a window will appear asking for the label of the point. After entering the label, the point will 
be added to the image.


