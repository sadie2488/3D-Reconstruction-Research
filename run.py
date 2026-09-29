"""Photos + K.txt -> sparse colored point cloud.

    python run.py --images data/sample --out results/sample

Outputs in --out: sparse.ply (view with: python view.py <out>/sparse.ply)
Scratch files (resized images, COLMAP database/model) go to <out>/work/.
"""
import argparse
import time
from pathlib import Path

import open3d as o3d

from src import sfm
from src.data_loader import CalibrationError, load_dataset


def main():
    parser = argparse.ArgumentParser(description="Sparse 3D reconstruction from photos.")
    parser.add_argument("--images", required=True, help="folder with images and K.txt")
    parser.add_argument("--out", required=True, help="output folder, e.g. results/<name>")
    parser.add_argument("--max-dim", type=int, default=1600, help="downscale so max(w, h) <= this")
    args = parser.parse_args()
    out = Path(args.out)
    work = out / "work"
    t_start = time.time()

    # --- Load images + K ---
    try:
        names, images, K = load_dataset(args.images, max_dim=args.max_dim)
    except CalibrationError as e:
        raise SystemExit(f"ERROR: {e}")
    h, w = images[0].shape[:2]
    print(f"Loaded {len(images)} images, working size {w}x{h}")
    print(f"K (scaled): fx={K[0, 0]:.1f} fy={K[1, 1]:.1f} cx={K[0, 2]:.1f} cy={K[1, 2]:.1f}")

    # --- Sparse reconstruction ---
    image_dir = work / "images"
    sfm.write_images(images, image_dir)
    print("Running COLMAP (features -> matching -> incremental mapping)...")
    rec, timings = sfm.run_colmap(image_dir, K, work, refine_intrinsics=False)
    stats = sfm.summarize(rec, len(images))
    if rec is None:
        raise SystemExit("ERROR: no images could be registered; no model was built.")

    # --- Export point cloud ---
    pcd = sfm.to_point_cloud(rec)
    ply_path = out / "sparse.ply"
    o3d.io.write_point_cloud(str(ply_path), pcd)

    runtime = time.time() - t_start
    print(f"\nRegistered {stats['images_registered']}/{stats['images_total']} images")
    print(f"3D points: {stats['points3d']}")
    print(f"Mean reprojection error: {stats['mean_reprojection_error_px']} px")
    print(f"Mean track length: {stats['mean_track_length']} views/point")
    print("Timings: " + ", ".join(f"{k} {v:.1f}s" for k, v in timings.items()) + f", total {runtime:.1f}s")
    print(f"Saved {ply_path}")


if __name__ == "__main__":
    main()
