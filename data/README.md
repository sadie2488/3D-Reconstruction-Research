# Data

Image folders are not committed to git (see `.gitignore`).

## data/sample/

fountain-P11 (Strecha et al.), taken from the
[Yashas120/Multiview-3D-Reconstruction](https://github.com/Yashas120/Multiview-3D-Reconstruction) repo.

Expected contents:

- `*.jpg`: the views, 3072 x 2048, processed in filename order
- `K.txt`: 3x3 camera intrinsics matrix (9 numbers, row-major)

Current state (2026-09-29): 10 images (`0001 (1).jpg` to `0010 (1).jpg`).
The file named `K (1).txt` is actually a JPEG of the fountain (most likely the
11th view), **not** a calibration file. A valid `K.txt` is still needed.
