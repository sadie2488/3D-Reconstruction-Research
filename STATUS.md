# Status

Last updated: 2026-09-29 (Step 3 complete: demo floor reached)

## Works
- Project skeleton: `src/`, `data/`, `results/`, venv (Python 3.12), `requirements.txt`
- Dataset loader (`src/data_loader.py`): 11 fountain images (3072 x 2048) + `K.txt`;
  optional downscale that scales K to match
- Sanity check (`python -m src.check_data`)
- Feature matching (`python -m src.match_pairs`): SIFT + FLANN + ratio test +
  RANSAC on all 55 pairs at 1600 px, ~5 s
- Sparse reconstruction (`python run.py`): pycolmap 4.2.1 with fixed K.
  Sample: 11/11 images registered, ~15,100 points, 0.23 px mean reprojection
  error, ~30-50 s. Output `results/sample/sparse.ply`, upright and centered
- Viewer (`python view.py <ply>`)

## Partially works
- Stray far points (up to ~20 units away, main scene ~5) make the viewer's
  auto-fit start zoomed out. Cleanup comes in Step 4.
- Step 2 matching is a separate diagnostic; COLMAP runs its own SIFT and matching.

## Not started
- Step 4: own photos (EXIF K), point cloud cleanup
- Step 5: turntable GIF, metrics file, README polish
