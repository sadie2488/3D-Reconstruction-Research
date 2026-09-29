# Status

Last updated: 2026-09-29 (Steps 1-5 + one stretch complete)

## Works
- Dataset loader + sanity check (`python -m src.check_data`): 11 fountain images + `K.txt`
- Feature matching diagnostic (`python -m src.match_pairs`): SIFT + FLANN + ratio test +
  RANSAC, all 55 pairs, ~5 s, inlier matrix + match picture
- One command (`python run.py --images <folder> --out results/<name>`): pycolmap
  reconstruction -> `sparse.ply`, `sparse_clean.ply`, `turntable.gif`, `metrics.json`.
  Sample: 11/11 registered, ~15,100 points (~14,870 clean), 0.23 px mean
  reprojection error, ~33 s
- Viewer (`python view.py <ply>`)
- Own photos (`--k-from-exif`): EXIF rotation, EXIF-based K, fallback guess refined by
  bundle adjustment (recovered true focal to 0.1% from a 34% wrong start),
  HEIC/odd-size warnings, capture tips when registration fails
- Cleanup: statistical outlier removal + far-point crop; optional `--remove-plane`
- Turntable GIF: Open3D offscreen (2-4 s), matplotlib fallback tested
- Smoke test (`python tests/smoke_test.py`): passes
- README with GIF, results, usage, limitations, future work

## Partially works
- Own-photo mode not yet tried on real phone photos (only synthetic EXIF copies of the sample)
- `--remove-plane` removes the largest plane, whatever it is (on the fountain: the wall)

- Stretch (picked one): SIFT vs ORB table (`python -m src.compare_features`),
  in README and `results/sample/sift_vs_orb.md`

## Not started
- Other stretch goals (Poisson mesh, Gradio page): skipped, brief allows at most one
