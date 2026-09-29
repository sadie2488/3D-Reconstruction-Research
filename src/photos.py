"""Own (phone) photos: fix EXIF rotation, build K from EXIF focal length, downscale.

K from EXIF FocalLengthIn35mmFilm. If missing: f = 1.2 * max(w, h), a rough guess
that gets printed loudly. Either way, bundle adjustment should refine the focal length.
"""
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from .data_loader import IMAGE_EXTS, downscale_factor, resize_image

EXIF_IFD = 0x8769        # sub-block holding camera settings
FOCAL_35MM_TAG = 0xA405  # FocalLengthIn35mmFilm
FALLBACK_FOCAL_FACTOR = 1.2
UNSUPPORTED_EXTS = {".heic", ".heif", ".dng"}


# --- EXIF focal length ---

def focal_35mm(pil_img):
    value = pil_img.getexif().get_ifd(EXIF_IFD).get(FOCAL_35MM_TAG)
    return float(value) if value else None


def focal_pixels(f35_mm, width, height):
    # 35 mm film is 36 mm wide, so f_px / long_side = f35 / 36
    return f35_mm / 36.0 * max(width, height)


# --- Load photos + build K ---

def load_photos(folder, max_dim=1600):
    """Returns (names, images_bgr, K, k_source). All images same size, upright, <= max_dim."""
    folder = Path(folder)
    files = sorted(p for p in folder.iterdir() if p.is_file())
    unsupported = [p.name for p in files if p.suffix.lower() in UNSUPPORTED_EXTS]
    if unsupported:
        print(f"WARNING: skipping {len(unsupported)} HEIC/DNG file(s); convert them to JPG first "
              f"(iPhone: Settings > Camera > Formats > Most Compatible).")
    paths = [p for p in files if p.suffix.lower() in IMAGE_EXTS]
    if not paths:
        raise FileNotFoundError(f"No .jpg/.jpeg/.png images found in {folder}")

    loaded = []  # (name, original (h, w), downscaled BGR image, f35 or None)
    for p in paths:
        with Image.open(p) as im:
            f35 = focal_35mm(im)
            im = ImageOps.exif_transpose(im).convert("RGB")  # phones store rotation in EXIF
            rgb = np.asarray(im)
        h, w = rgb.shape[:2]
        bgr = np.ascontiguousarray(rgb[:, :, ::-1])  # RGB -> BGR for OpenCV
        loaded.append((p.name, (h, w), resize_image(bgr, downscale_factor(w, h, max_dim)), f35))

    # --- One shared K needs one image size: keep the most common, drop the rest ---
    (h, w), _ = Counter(size for _, size, _, _ in loaded).most_common(1)[0]
    dropped = [name for name, size, _, _ in loaded if size != (h, w)]
    if dropped:
        print(f"WARNING: dropping {len(dropped)} image(s) with a different size/orientation "
              f"than the majority ({w}x{h}): {', '.join(dropped)}")
    loaded = [x for x in loaded if x[1] == (h, w)]

    f35s = [f for _, _, _, f in loaded if f]
    if f35s:
        f35 = float(np.median(f35s))
        f = focal_pixels(f35, w, h)
        k_source = f"EXIF (35mm-equivalent focal {f35:g} mm, {len(f35s)}/{len(loaded)} images)"
    else:
        f = FALLBACK_FOCAL_FACTOR * max(w, h)
        k_source = f"GUESS: no EXIF focal length, assuming f = {FALLBACK_FOCAL_FACTOR} * max(w, h)"
    s = downscale_factor(w, h, max_dim)
    # principal point assumed at the image center
    K = np.array([[f * s, 0, w * s / 2], [0, f * s, h * s / 2], [0, 0, 1]])
    return [x[0] for x in loaded], [x[2] for x in loaded], K, k_source
