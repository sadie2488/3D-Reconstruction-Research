"""Sanity-check a dataset folder: image count, resolution, and K matrix.

Usage:
    python src/check_data.py --data data/sample

Exit code 0 if images and a valid K were loaded, 1 otherwise.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

from data_loader import (CalibrationError, find_calibration_file,
                         list_images, load_images, load_intrinsics)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", default="data/sample", help="dataset folder")
    args = parser.parse_args()
    folder = Path(args.data)

    print(f"Dataset: {folder.resolve()}")
    if not folder.is_dir():
        print("  ERROR: folder does not exist.")
        return 1

    # Images
    names, images = load_images(folder)
    sizes = Counter((img.shape[1], img.shape[0]) for img in images)
    print(f"\nImages: {len(images)}")
    print(f"  first: {names[0]}   last: {names[-1]}")
    for (w, h), n in sizes.items():
        print(f"  resolution: {w} x {h}  ({n} image{'s' if n != 1 else ''})")
    if len(sizes) > 1:
        print("  WARNING: images have different resolutions; a single K cannot fit all of them.")

    image_paths = set(list_images(folder))
    others = sorted(p.name for p in folder.iterdir() if p.is_file() and p not in image_paths)
    if others:
        print(f"  other files (not loaded as images): {', '.join(others)}")

    # Intrinsics
    print("\nCalibration (K):")
    k_path = find_calibration_file(folder)
    if k_path is None:
        print("  ERROR: no calibration file found (looked for K.txt or K*.txt).")
        print("  K will not be guessed. Add a K.txt with the 3x3 intrinsics matrix.")
        return 1
    print(f"  file: {k_path.name}")
    image_size = next(iter(sizes)) if len(sizes) == 1 else None
    try:
        K = load_intrinsics(k_path, image_size=image_size)
    except CalibrationError as e:
        print(f"  ERROR: {e}")
        print("  No valid intrinsics. K will not be guessed. Add a valid K.txt "
              "(3x3 matrix, 9 numbers) to continue.")
        return 1

    fx, fy, cx, cy, skew = K[0, 0], K[1, 1], K[0, 2], K[1, 2], K[0, 1]
    print("  K =")
    for row in K:
        print("    [" + "  ".join(f"{v:12.4f}" for v in row) + " ]")
    print(f"  fx={fx:.2f}  fy={fy:.2f}  cx={cx:.2f}  cy={cy:.2f}  skew={skew:.4f}")
    if image_size is not None:
        w, h = image_size
        print(f"  principal point offset from image center: "
              f"({cx - w / 2:+.1f}, {cy - h / 2:+.1f}) px")
    print("\nOK: images and intrinsics loaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
