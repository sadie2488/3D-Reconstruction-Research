"""Step 2: match every image pair, print the inlier-count matrix, save one match picture.

    python -m src.match_pairs --data data/sample --out results/sample

Outputs in --out: inlier_matrix.csv, matches_<a>_<b>.jpg
"""
import argparse
import csv
import itertools
import time
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm

from .data_loader import load_dataset
from .features import detect_sift, draw_matches, match_pair


def print_matrix(matrix):
    n = len(matrix)
    print("      " + "".join(f"{j + 1:>6}" for j in range(n)))
    for i in range(n):
        cells = "".join(f"{'-' if i == j else matrix[i, j]:>6}" for j in range(n))
        print(f"{i + 1:>6}{cells}")


def main():
    parser = argparse.ArgumentParser(description="Pairwise SIFT matching.")
    parser.add_argument("--data", default="data/sample")
    parser.add_argument("--out", default="results/sample")
    parser.add_argument("--max-dim", type=int, default=1600, help="downscale so max(w, h) <= this")
    parser.add_argument("--ratio", type=float, default=0.75, help="Lowe ratio test threshold")
    parser.add_argument("--viz", type=int, nargs=2, default=[1, 2], metavar=("A", "B"),
                        help="1-based image indices of the pair to visualize")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # --- Load + SIFT ---
    names, images, _ = load_dataset(args.data, max_dim=args.max_dim)
    h, w = images[0].shape[:2]
    print(f"{len(images)} images at {w}x{h}")
    t0 = time.time()
    feats = detect_sift(tqdm(images, desc="SIFT"))
    counts = [len(kp) for kp, _ in feats]
    print(f"Keypoints per image: min {min(counts)}, mean {np.mean(counts):.0f}, max {max(counts)} "
          f"({time.time() - t0:.1f}s)")

    # --- Match all pairs ---
    n = len(images)
    inliers = np.zeros((n, n), dtype=int)
    ratio_kept = np.zeros((n, n), dtype=int)
    pair_inliers = {}
    t0 = time.time()
    for i, j in tqdm(list(itertools.combinations(range(n), 2)), desc="Matching"):
        good, inl = match_pair(feats[i], feats[j], ratio=args.ratio)
        ratio_kept[i, j] = ratio_kept[j, i] = len(good)
        inliers[i, j] = inliers[j, i] = len(inl)
        pair_inliers[(i, j)] = inl
    print(f"Matched {n * (n - 1) // 2} pairs in {time.time() - t0:.1f}s\n")

    # --- Inlier matrix ---
    print("Images:")
    for k, name in enumerate(names):
        print(f"  {k + 1:>2}: {name}")
    print("\nRANSAC inlier counts (row/col = image index):")
    print_matrix(inliers)
    upper = np.triu_indices(n, 1)
    kept_frac = inliers[upper].sum() / max(ratio_kept[upper].sum(), 1)
    print(f"\nOverall: {kept_frac:.0%} of ratio-test matches survive RANSAC")

    with open(out / "inlier_matrix.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([""] + names)
        for name, row in zip(names, inliers):
            writer.writerow([name] + list(row))

    # --- Match visualization ---
    a, b = sorted(k - 1 for k in args.viz)
    viz = draw_matches(images[a], feats[a][0], images[b], feats[b][0], pair_inliers[(a, b)])
    viz_path = out / f"matches_{a + 1:04d}_{b + 1:04d}.jpg"
    cv2.imwrite(str(viz_path), viz)
    print(f"\nSaved {out / 'inlier_matrix.csv'}")
    print(f"Saved {viz_path} ({len(pair_inliers[(a, b)])} inliers, up to 300 drawn)")


if __name__ == "__main__":
    main()
