# Status

Last updated: 2026-09-29 (Step 1 complete)

## Works
- Project skeleton: `src/`, `data/`, `results/`, venv (Python 3.12), `requirements.txt`
- Image loader (`src/data_loader.py`): loads 10 fountain images, 3072 x 2048
- Intrinsics loader: reads and validates `data/sample/K.txt`
  (fx=2759.48, fy=2764.16, cx=1520.69, cy=1006.81)
- Sanity check (`src/check_data.py`): prints image count, resolution, K; exits 1 if K is missing or invalid

## Partially works
- Sample dataset: 10 of 11 fountain-P11 views usable. `data/sample/K (1).txt` is
  a mislabeled JPEG (probably the 11th view) and is currently ignored.

## Not started
- Step 2: feature matching (SIFT + FLANN + ratio test + RANSAC)
- Step 3: sparse reconstruction + `view.py`
- Step 4: own photos (optional)
- Step 5: `run.py`, turntable GIF, metrics, README polish
