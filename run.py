"""Photos -> sparse colored point cloud.

    python run.py --images data/sample --out results/sample          (folder has K.txt)
    python run.py --images <phone photos> --out results/<name> --k-from-exif

Outputs in --out: sparse.ply (raw), sparse_clean.ply (outliers removed).
View with: python view.py <out>/sparse_clean.ply
Scratch files (resized images, COLMAP database/model) go to <out>/work/.
"""
import argparse
import time
from pathlib import Path

import open3d as o3d

from src import cleanup, photos, sfm
from src.data_loader import CalibrationError, load_dataset

CAPTURE_TIPS = """How to get more images to register:
  - more overlap: each photo should share ~60-80% of its view with the next one
  - move the camera around the object (don't just turn on the spot)
  - more texture: plain, shiny, or see-through surfaces give no features
  - even, bright lighting; avoid motion blur; keep the same zoom level"""


def main():
    parser = argparse.ArgumentParser(description="Sparse 3D reconstruction from photos.")
    parser.add_argument("--images", required=True, help="folder with images (and K.txt unless --k-from-exif)")
    parser.add_argument("--out", required=True, help="output folder, e.g. results/<name>")
    parser.add_argument("--max-dim", type=int, default=1600, help="downscale so max(w, h) <= this")
    parser.add_argument("--k-from-exif", action="store_true",
                        help="own photos: build K from EXIF focal length (fallback 1.2*max(w,h)); "
                             "focal length is refined during bundle adjustment")
    parser.add_argument("--remove-plane", action="store_true",
                        help="also remove the largest plane (floor/table) from the cleaned cloud")
    args = parser.parse_args()
    out = Path(args.out)
    work = out / "work"
    t_start = time.time()

    # --- Load images + K ---
    if args.k_from_exif:
        if (Path(args.images) / "K.txt").is_file():
            print("NOTE: K.txt found but ignored because --k-from-exif was given.")
        names, images, K, k_source = photos.load_photos(args.images, max_dim=args.max_dim)
        refine = True
    else:
        try:
            names, images, K = load_dataset(args.images, max_dim=args.max_dim)
        except CalibrationError as e:
            raise SystemExit(f"ERROR: {e}\nFor phone photos without a K.txt, add --k-from-exif.")
        k_source, refine = "K.txt", False
    if len(images) < 3:
        raise SystemExit(f"ERROR: only {len(images)} usable image(s); need at least 3.\n{CAPTURE_TIPS}")
    h, w = images[0].shape[:2]
    print(f"Loaded {len(images)} images, working size {w}x{h}")
    print(f"K source: {k_source}")
    print(f"K (working size): fx={K[0, 0]:.1f} fy={K[1, 1]:.1f} cx={K[0, 2]:.1f} cy={K[1, 2]:.1f}")

    # --- Sparse reconstruction ---
    image_dir = work / "images"
    sfm.write_images(images, image_dir)
    print("Running COLMAP (features -> matching -> incremental mapping)...")
    rec, timings = sfm.run_colmap(image_dir, K, work, refine_intrinsics=refine)
    stats = sfm.summarize(rec, len(images))

    # --- Registration check ---
    reg = sfm.registered_indices(rec)
    if len(reg) < 3:
        raise SystemExit(f"\nERROR: only {len(reg)}/{len(images)} images registered; "
                         f"no usable model.\n{CAPTURE_TIPS}")
    missing = [names[i] for i in range(len(images)) if i not in reg]
    if missing:
        print(f"\nWARNING: {len(missing)} image(s) did not register: {', '.join(missing)}")
        print(CAPTURE_TIPS)
    if refine:
        fx, fy = sfm.focal_after_ba(rec)
        print(f"Focal length after bundle adjustment: fx={fx:.1f} fy={fy:.1f} (started at {K[0, 0]:.1f})")

    # --- Export + cleanup ---
    pcd = sfm.to_point_cloud(rec)
    o3d.io.write_point_cloud(str(out / "sparse.ply"), pcd)
    clean = cleanup.remove_far_points(cleanup.remove_outliers(pcd))
    print(f"\nOutlier removal + far-point crop: {len(pcd.points)} -> {len(clean.points)} points")
    if args.remove_plane:
        clean, n_plane = cleanup.remove_largest_plane(clean)
        print(f"Plane removal: removed {n_plane} points, {len(clean.points)} left")
    o3d.io.write_point_cloud(str(out / "sparse_clean.ply"), clean)

    runtime = time.time() - t_start
    print(f"\nRegistered {stats['images_registered']}/{stats['images_total']} images")
    print(f"3D points: {stats['points3d']} ({len(clean.points)} after cleanup)")
    print(f"Mean reprojection error: {stats['mean_reprojection_error_px']} px")
    print(f"Mean track length: {stats['mean_track_length']} views/point")
    print("Timings: " + ", ".join(f"{k} {v:.1f}s" for k, v in timings.items()) + f", total {runtime:.1f}s")
    print(f"Saved {out / 'sparse.ply'} and {out / 'sparse_clean.ply'}")


if __name__ == "__main__":
    main()
