# Multi-view 3D Reconstruction

Work in progress: 3D reconstruction from multiple calibrated photos using
OpenCV and Open3D. See [STATUS.md](STATUS.md) for what works right now.

## Layout

```
src/        pipeline code
data/       input image folders (not in git; see data/README.md)
results/    outputs (point clouds, images, metrics)
```

## Setup (Windows, PowerShell)

Requires Python 3.12 (Open3D does not reliably ship wheels for the newest
Python versions).

```powershell
py -V:Astral/CPython3.12.13 -m venv .venv   # or any Python 3.12: py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Usage

Check that a dataset folder loads (image count, resolution, intrinsics):

```powershell
python -m src.check_data --data data/sample
```

Match all image pairs (SIFT + FLANN + ratio test + RANSAC), print the inlier
matrix, and save a match picture:

```powershell
python -m src.match_pairs --data data/sample --out results/sample
```

Sparse reconstruction (pycolmap) to a colored point cloud, then view it:

```powershell
python run.py --images data/sample --out results/sample
python view.py results/sample/sparse_clean.ply
```

Own photos (no `K.txt`): K is built from the EXIF focal length (fallback guess
f = 1.2 x max(w, h), printed as a warning) and refined by bundle adjustment.
Images are rotated upright from EXIF and downscaled to 1600 px.

```powershell
python run.py --images <photo folder> --out results/<name> --k-from-exif
python run.py --images <photo folder> --out results/<name> --k-from-exif --remove-plane
```

`--remove-plane` deletes the single largest plane (a table or floor under an
object). On scenes where the main subject is itself a wall, it removes the wall.

A dataset folder holds the images (`.jpg`/`.png`, processed in filename order)
and a `K.txt` with the 3x3 intrinsics matrix. Intrinsics are never guessed: if
`K.txt` is missing or invalid, the script says so and exits with code 1.
