"""Load a dataset folder: images (*.jpg/*.png, filename order) + K.txt (3x3 intrinsics).

K is never guessed. A missing or malformed K.txt raises CalibrationError.
"""
import re
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


class CalibrationError(RuntimeError):
    pass


# --- Images ---

def list_images(folder):
    folder = Path(folder)
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS)


def read_image(path):
    # imdecode instead of imread: imread breaks on non-ASCII Windows paths
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise IOError(f"Could not decode image: {path}")
    return img


def load_images(folder):
    """Return (names, images). Images are BGR uint8 (OpenCV order)."""
    paths = list_images(folder)
    if not paths:
        raise FileNotFoundError(f"No .jpg/.jpeg/.png images found in {folder}")
    return [p.name for p in paths], [read_image(p) for p in paths]


# --- Downscale (image + K together) ---

def downscale_factor(width, height, max_dim):
    if not max_dim or max(width, height) <= max_dim:
        return 1.0
    return max_dim / max(width, height)


def resize_image(img, s):
    if s == 1.0:
        return img
    h, w = img.shape[:2]
    return cv2.resize(img, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)


def scale_intrinsics(K, s):
    # fx, fy, cx, cy are in pixels, so they shrink with the image
    K = K.copy()
    K[:2] *= s
    return K


# --- K.txt (intrinsics) ---

def find_calibration_file(folder):
    """K.txt if present, else first K*.txt, else None."""
    folder = Path(folder)
    exact = folder / "K.txt"
    if exact.is_file():
        return exact
    candidates = sorted(p for p in folder.iterdir()
                        if p.is_file() and re.fullmatch(r"k.*\.txt", p.name, re.IGNORECASE))
    return candidates[0] if candidates else None


def load_intrinsics(path, image_size=None):
    """Parse + validate K. image_size=(w, h) also checks the principal point is inside the image."""
    path = Path(path)
    raw = path.read_bytes()

    # catch image files saved with a .txt name
    if raw[:3] == b"\xff\xd8\xff":
        raise CalibrationError(f"'{path.name}' is a JPEG image, not a text K matrix.")
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        raise CalibrationError(f"'{path.name}' is a PNG image, not a text K matrix.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise CalibrationError(f"'{path.name}' is a binary file, not a text K matrix.")

    # accepts plain rows, commas, or [[...]] brackets: just grab the 9 numbers
    numbers = [float(x) for x in NUMBER_RE.findall(text)]
    if len(numbers) != 9:
        raise CalibrationError(
            f"'{path.name}' contains {len(numbers)} numbers; a 3x3 K matrix needs exactly 9.")
    K = np.array(numbers).reshape(3, 3)

    # K = [[fx, skew, cx], [0, fy, cy], [0, 0, 1]]
    if not np.allclose(K[2], [0, 0, 1]):
        raise CalibrationError(f"'{path.name}': last row of K is {K[2]}, expected [0 0 1].")
    if K[0, 0] <= 0 or K[1, 1] <= 0:
        raise CalibrationError(f"'{path.name}': focal lengths must be positive (fx={K[0, 0]}, fy={K[1, 1]}).")
    if not np.isclose(K[1, 0], 0):
        raise CalibrationError(f"'{path.name}': K is not upper-triangular.")
    if image_size is not None:
        w, h = image_size
        cx, cy = K[0, 2], K[1, 2]
        if not (0 < cx < w and 0 < cy < h):
            raise CalibrationError(
                f"'{path.name}': principal point ({cx:.1f}, {cy:.1f}) lies outside the "
                f"{w}x{h} image. K may be for a different image resolution.")
    return K


# --- Full dataset ---

def load_dataset(folder, max_dim=None):
    """Return (names, images, K), downscaled so max(w, h) <= max_dim, with K scaled to match."""
    names, images = load_images(folder)
    sizes = {img.shape[:2] for img in images}
    if len(sizes) > 1:
        raise ValueError(f"Images in {folder} have different resolutions {sizes}; one K cannot fit all.")
    h, w = images[0].shape[:2]

    k_path = find_calibration_file(folder)
    if k_path is None:
        raise CalibrationError(f"No K.txt in {folder}. K will not be guessed.")
    K = load_intrinsics(k_path, image_size=(w, h))

    s = downscale_factor(w, h, max_dim)
    return names, [resize_image(img, s) for img in images], scale_intrinsics(K, s)
