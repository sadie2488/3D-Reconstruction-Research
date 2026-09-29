# Status

Last updated: 2026-09-29 (Step 2 complete)

## Works
- Project skeleton: `src/`, `data/`, `results/`, venv (Python 3.12), `requirements.txt`
- Dataset loader (`src/data_loader.py`): 11 fountain images (3072 x 2048) + `K.txt`;
  optional downscale that scales K to match
- Sanity check (`python -m src.check_data`)
- Feature matching (`python -m src.match_pairs`): SIFT + FLANN + ratio test +
  RANSAC on all 55 pairs at 1600 px, ~5 s. Neighbouring views get 1000-1800 inliers.
  Output: `results/sample/inlier_matrix.csv`, `results/sample/matches_0001_0002.jpg`

## Partially works
- Pairs far apart (e.g. 1 vs 11) still report 12-30 "inliers"; these are
  probably chance fits, not real matches. Nothing filters them by count yet.

## Not started
- Step 3: sparse reconstruction + `view.py`
- Step 4: own photos
- Step 5: `run.py`, turntable GIF, metrics, README polish
