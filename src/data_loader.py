"""Load a folder of multi-view images and its camera intrinsics matrix K.

Expected folder layout (fountain-P11 style):
    <folder>/*.jpg | *.png   the views, processed in filename order
    <folder>/K.txt           3x3 intrinsics matrix, 9 numbers, row-major

K is never guessed: if the calibration file is missing or malformed,
load_intrinsics raises CalibrationError and the caller must stop.
"""
import re
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


class CalibrationError(RuntimeError):
    """The intrinsics file is missing, unreadable, or not a valid K matrix."""


def list_images(folder):
    folder = Path(folder)
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS)


def read_image(path):
    # np.fromfile + imdecode instead of cv2.imread: imread fails on some
    # Windows paths (non-ASCII characters).
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise IOError(f"Could not decode image: {path}")
    return img


def load_images(folder):
    """Return (names, images) with images as BGR uint8 arrays."""
    paths = list_images(folder)
    if not paths:
        raise FileNotFoundError(f"No .jpg/.jpeg/.png images found in {folder}")
    return [p.name for p in paths], [read_image(p) for p in paths]


def find_calibration_file(folder):
    """Return K.txt if present, else the first K*.txt match, else None."""
    folder = Path(folder)
    exact = folder / "K.txt"
    if exact.is_file():
        return exact
    candidates = sorted(p for p in folder.iterdir()
                        if p.is_file() and re.fullmatch(r"k.*\.txt", p.name, re.IGNORECASE))
    return candidates[0] if candidates else None


def load_intrinsics(path, image_size=None):
    """Parse and validate a 3x3 K matrix.

    image_size: optional (width, height); if given, the principal point
    must lie inside the image (catches K files meant for a different
    resolution).
    """
    path = Path(path)
    raw = path.read_bytes()

    if raw[:3] == b"\xff\xd8\xff":
        raise CalibrationError(f"'{path.name}' is a JPEG image, not a text K matrix.")
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        raise CalibrationError(f"'{path.name}' is a PNG image, not a text K matrix.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise CalibrationError(f"'{path.name}' is a binary file, not a text K matrix.")

    numbers = [float(x) for x in NUMBER_RE.findall(text)]
    if len(numbers) != 9:
        raise CalibrationError(
            f"'{path.name}' contains {len(numbers)} numbers; a 3x3 K matrix needs exactly 9.")
    K = np.array(numbers).reshape(3, 3)

    if not np.allclose(K[2], [0, 0, 1]):
        raise CalibrationError(f"'{path.name}': last row of K is {K[2]}, expected [0 0 1].")
    if K[0, 0] <= 0 or K[1, 1] <= 0:
        raise CalibrationError(f"'{path.name}': focal lengths must be positive (fx={K[0, 0]}, fy={K[1, 1]}).")
    if not (np.isclose(K[1, 0], 0) and np.isclose(K[2, 0], 0) and np.isclose(K[2, 1], 0)):
        raise CalibrationError(f"'{path.name}': K is not upper-triangular.")
    if image_size is not None:
        w, h = image_size
        cx, cy = K[0, 2], K[1, 2]
        if not (0 < cx < w and 0 < cy < h):
            raise CalibrationError(
                f"'{path.name}': principal point ({cx:.1f}, {cy:.1f}) lies outside the "
                f"{w}x{h} image. K may be for a different image resolution.")
    return K
