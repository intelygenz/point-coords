Simple GUI that lets you annotate images by labeling and capturing the coordinates of different points on an image. 

A file is exported containing each point's label points coordinates.

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
