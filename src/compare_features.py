"""Stretch: SIFT vs ORB match counts on the same image pairs.

    python -m src.compare_features --data data/sample --out results/sample

Prints a table and saves it as <out>/sift_vs_orb.md.
"""
import argparse
import time
from pathlib import Path

import numpy as np

from .data_loader import load_dataset
from .features import detect_orb, detect_sift, match_pair


def evaluate(feats, pairs):
    """Mean ratio-test matches, RANSAC inliers, inlier ratio over the given pairs."""
    kept, inl = [], []
    for i, j in pairs:
        good, inliers = match_pair(feats[i], feats[j])
        kept.append(len(good))
        inl.append(len(inliers))
    kept, inl = np.array(kept), np.array(inl)
    return kept.mean(), inl.mean(), inl.sum() / max(kept.sum(), 1)


def main():
    parser = argparse.ArgumentParser(description="SIFT vs ORB comparison.")
    parser.add_argument("--data", default="data/sample")
    parser.add_argument("--out", default="results/sample")
    parser.add_argument("--max-dim", type=int, default=1600)
    args = parser.parse_args()

    names, images, _ = load_dataset(args.data, max_dim=args.max_dim)
    n = len(images)
    near = [(i, i + 1) for i in range(n - 1)]  # neighbouring views
    far = [(i, i + 3) for i in range(n - 3)]   # 3 views apart: bigger viewpoint change

    rows = []
    for name, detect in [("SIFT", detect_sift), ("ORB (5000)", detect_orb)]:
        t0 = time.time()
        feats = detect(images)
        t_detect = time.time() - t0
        t0 = time.time()
        near_stats = evaluate(feats, near)
        far_stats = evaluate(feats, far)
        t_match = time.time() - t0
        kps = np.mean([len(kp) for kp, _ in feats])
        rows.append((name, kps, t_detect, t_match, *near_stats, *far_stats))

    header = ("| Detector | Keypoints/img | Detect (s) | Match (s) | Neighbour pairs: matches | inliers | inlier % "
              "| 3-apart pairs: matches | inliers | inlier % |")
    lines = [header, "|" + "---|" * 10]
    for r in rows:
        lines.append(f"| {r[0]} | {r[1]:.0f} | {r[2]:.1f} | {r[3]:.1f} | {r[4]:.0f} | {r[5]:.0f} | {r[6]:.0%} "
                     f"| {r[7]:.0f} | {r[8]:.0f} | {r[9]:.0%} |")
    table = "\n".join(lines)
    note = (f"\n\n{n} images at {images[0].shape[1]}x{images[0].shape[0]}. Same ratio test (0.75) and "
            f"RANSAC (fundamental matrix, 1 px) for both. Matches/inliers are means per pair.")
    print(table + note)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sift_vs_orb.md").write_text("# SIFT vs ORB\n\n" + table + note + "\n")
    print(f"\nSaved {out / 'sift_vs_orb.md'}")


if __name__ == "__main__":
    main()
