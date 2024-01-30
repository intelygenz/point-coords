""" 
Convert the info from the annotated points to the format that our pipeline expects
"""
from pathlib import Path
import json

POINTS_COORDS = {
    1: (-1,3),
    6: (-1,1),
    8: (-2,0),
    4: (-3,0),
    7: (0,0),
    3: (2, 0),
    9: (-1,-1),
    2: (-1,-2),
    5: (-1,-3),
    10: (0,-1),
    11: (0,-2),
    12: (0,1),
    13: (-2,1),
    14: (-2,2),
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
            if len(line) != 4:
                raise Exception(f"Line {line} does not have 4 elements")
            if int(line[0]) != cam_idx:
                continue
            point_id = int(line[1])
            x = float(line[2])
            y = float(line[3])
            points.append((point_id, x, y))
    return points

points2d_fpath = Path("./points2D_NARROW.txt")
out_dir = Path("./chessboard")
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
            POINTS_COORDS[point_id][0]*TILE_LEN*-1.0, 
            POINTS_COORDS[point_id][1]*TILE_LEN*-1.0,
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

