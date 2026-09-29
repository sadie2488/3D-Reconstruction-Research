# Data

Images are not committed to git (see `.gitignore`); `K.txt` files are.

## data/sample/

fountain-P11 (Strecha et al.), taken from the
[Yashas120/Multiview-3D-Reconstruction](https://github.com/Yashas120/Multiview-3D-Reconstruction) repo.

Expected contents:

- `*.jpg`: the views, 3072 x 2048, processed in filename order
- `K.txt`: 3x3 camera intrinsics matrix (9 numbers, row-major)

Current state (2026-09-29): 10 images (`0001 (1).jpg` to `0010 (1).jpg`) and
`K.txt` (fx=2759.48, fy=2764.16, cx=1520.69, cy=1006.81; supplied by the user,
consistent with the 3072 x 2048 images). The file named `K (1).txt` is actually
a JPEG of the fountain (most likely the 11th view), not a calibration file; the
loader ignores it because `K.txt` takes priority.
