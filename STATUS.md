# Status

Last updated: 2026-09-29 (Step 1)

## Works
- Project skeleton: `src/`, `data/`, `results/`, venv (Python 3.12), `requirements.txt`
- Image loader (`src/data_loader.py`): loads 10 fountain images, 3072 x 2048
- Sanity check (`src/check_data.py`): prints image count, resolution, K; exits 1 if K is missing or invalid

## Partially works
- Intrinsics loader: parser and validation are written, but untested on a real K
  file because **the sample dataset has no valid K.txt**. `data/sample/K (1).txt`
  is a JPEG image, not a calibration file.

## Blocked
- Everything that needs K (Step 3 onward) until a valid `K.txt` is supplied.

## Not started
- Step 2: feature matching (SIFT + FLANN + ratio test + RANSAC); does not need K
- Step 3: sparse reconstruction + `view.py`
- Step 4: own photos (optional)
- Step 5: `run.py`, turntable GIF, metrics, README polish
