# Status

Last updated: 2026-09-29 (Step 4 complete)

## Works
- Dataset loader + sanity check (`python -m src.check_data`): 11 fountain images + `K.txt`
- Feature matching (`python -m src.match_pairs`): SIFT + FLANN + ratio test + RANSAC, all 55 pairs, ~5 s
- Sparse reconstruction (`python run.py`): pycolmap 4.2.1 with fixed K.
  Sample: 11/11 registered, ~15,100 points, 0.23 px mean reprojection error, ~30 s
- Cleanup: statistical outlier removal + far-point crop -> `sparse_clean.ply`
  (~14,870 points, opens well framed); optional `--remove-plane`
- Viewer (`python view.py <ply>`)
- Own photos (`--k-from-exif`): EXIF rotation, K from 35mm-equivalent focal
  length, fallback guess, focal refined by bundle adjustment. Tested on synthetic
  EXIF copies of the sample (focal recovered to within 0.1%), including a rotated
  image; HEIC files and odd-sized images are skipped with warnings
- Registration errors: clear message + capture tips when < 3 images register;
  lists any images that did not register

## Partially works
- Own-photo mode has not been tried on real phone photos yet (none in the repo)
- `--remove-plane` removes the largest plane, whatever it is (on the fountain: the wall)
- Step 2 matching is a separate diagnostic; COLMAP runs its own SIFT and matching

## Not started
- Step 5: turntable GIF, metrics file, README polish
