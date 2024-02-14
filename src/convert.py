""" 
Convert the info from the annotated points to the format that our pipeline expects
"""
from pathlib import Path
import json


POINTS_COORDS = {
    i: (-((i -1)%5), (i -1) // 5)
    for i in range(1,31)
}
ORIGIN_AT_POINT = 18
# Change coordinates to have the origin at ORIGIN_AT_POINT
POINTS_COORDS = {
    point_id: (x - POINTS_COORDS[ORIGIN_AT_POINT][0], y - POINTS_COORDS[ORIGIN_AT_POINT][1])
    for point_id, (x, y) in POINTS_COORDS.items()
}



TILE_LEN = 0.598 # In cms

def load_img_points(cam_idx: int, fpath: Path):
    points = []
    with open(fpath, "r") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            line = line.strip()
            line = line.split()
            if line[0].startswith("#"):
                continue
            if len(line) != 4:
                raise Exception(f"Line {line} does not have 4 elements")
            if int(line[0]) != cam_idx:
                continue
            point_id = int(line[1])
            x = float(line[2])
            y = float(line[3])
            points.append((point_id, x, y))
    return points

points2d_fpath = Path("./points2D_wide.txt")
out_dir = Path("./chessboard_wide")
# Check it does not exist
if out_dir.exists():
    raise Exception(f"Output dir {out_dir} already exists")
for i in range(8):
    keypoints3d = []
    keypoints2d = []
    cam_points = load_img_points(i+1, points2d_fpath)
    for point in cam_points:
        point_id, x, y = point
        keypoints3d.append([
            POINTS_COORDS[point_id][0]*TILE_LEN, 
            POINTS_COORDS[point_id][1]*TILE_LEN,
            0.0
        ])
        keypoints2d.append([x, y, 1.0])
    out_json = {
        "keypoints3d": keypoints3d,
        "keypoints2d": keypoints2d
    }
    out_fpath = out_dir / f"{i+1}"
    out_fpath.mkdir(parents=True)
    out_fpath = out_fpath / "000000.json"
    with open(out_fpath, "w") as f:
        json.dump(out_json, f, indent=4)

