# Data

Images are not committed to git (see `.gitignore`); `K.txt` files are.

## data/sample/

fountain-P11 (Strecha et al.), taken from the
[Yashas120/Multiview-3D-Reconstruction](https://github.com/Yashas120/Multiview-3D-Reconstruction) repo.

Expected contents:

- `*.jpg`: the views, 3072 x 2048, processed in filename order
- `K.txt`: 3x3 camera intrinsics matrix (9 numbers, row-major)

Current state (2026-09-29): 11 images (`0001 (1).jpg` to `0011 (1).jpg`) and
`K.txt` (fx=2759.48, fy=2764.16, cx=1520.69, cy=1006.81; supplied by the user,
consistent with the 3072 x 2048 images).

`0011 (1).jpg` arrived misnamed as `K (1).txt`. It was renamed after checking
it is a JPEG of the fountain; Step 2 matching confirms it continues the
sequence (1664 RANSAC inliers with image 10).
