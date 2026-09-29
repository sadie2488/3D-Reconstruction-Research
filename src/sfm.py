"""Sparse reconstruction (structure from motion) with pycolmap.

COLMAP does its own SIFT + matching + incremental SfM (with bundle adjustment).
We feed it our K, take the largest model, and export a colored point cloud.
"""
import shutil
import time
from pathlib import Path

import cv2
import numpy as np
import open3d as o3d
import pycolmap

pycolmap.logging.minloglevel = 1  # hide COLMAP's INFO spam; keep warnings/errors


# --- Working copies of the images ---

def write_images(images, image_dir):
    """Write (possibly downscaled) images as 0000.jpg, 0001.jpg, ... Returns the new names.

    Plain names avoid COLMAP issues with spaces; imencode+tofile avoids non-ASCII path bugs.
    """
    image_dir = Path(image_dir)
    if image_dir.exists():
        shutil.rmtree(image_dir)
    image_dir.mkdir(parents=True)
    names = []
    for i, img in enumerate(images):
        name = f"{i:04d}.jpg"
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        buf.tofile(str(image_dir / name))
        names.append(name)
    return names


# --- COLMAP: features, matching, incremental mapping ---

def run_colmap(image_dir, K, work_dir, refine_intrinsics=False):
    """Returns (largest Reconstruction or None, timings dict).

    refine_intrinsics=False keeps K fixed (calibrated data).
    True lets bundle adjustment tune the focal length (EXIF / guessed K).
    """
    work_dir = Path(work_dir)
    db_path = work_dir / "database.db"
    sparse_dir = work_dir / "sparse"
    if db_path.exists():
        db_path.unlink()
    if sparse_dir.exists():
        shutil.rmtree(sparse_dir)
    sparse_dir.mkdir(parents=True)
    timings = {}

    # one shared PINHOLE camera with our K (fx, fy, cx, cy); no distortion model
    reader = pycolmap.ImageReaderOptions()
    reader.camera_model = "PINHOLE"
    reader.camera_params = f"{K[0, 0]},{K[1, 1]},{K[0, 2]},{K[1, 2]}"

    t0 = time.time()
    pycolmap.extract_features(db_path, image_dir, camera_mode=pycolmap.CameraMode.SINGLE,
                              reader_options=reader, device=pycolmap.Device.cpu)
    timings["features_s"] = time.time() - t0

    # exhaustive = every pair; fine for tens of images
    t0 = time.time()
    pycolmap.match_exhaustive(db_path, device=pycolmap.Device.cpu)
    timings["matching_s"] = time.time() - t0

    opts = pycolmap.IncrementalPipelineOptions()
    opts.min_model_size = 3                  # default 10 would drop small photo sets
    opts.ba_refine_focal_length = refine_intrinsics
    opts.ba_refine_principal_point = False
    opts.ba_refine_extra_params = False
    opts.mapper.abs_pose_refine_focal_length = refine_intrinsics

    t0 = time.time()
    models = pycolmap.incremental_mapping(db_path, image_dir, sparse_dir, opts)
    timings["mapping_s"] = time.time() - t0

    if not models:
        return None, timings
    # COLMAP can split into several models if the image chain breaks; keep the biggest
    return max(models.values(), key=lambda r: r.num_reg_images()), timings


# --- Orient for viewing ---

def viewing_rotation(rec):
    """Rotation into a frame where y = average camera 'up' and -z = average viewing direction.

    COLMAP's world axes are arbitrary (usually camera 1's frame, y pointing down),
    so without this the cloud often opens upside down in viewers.
    """
    ups, fwds = [], []
    for img in rec.images.values():
        if not img.has_pose:
            continue
        R = img.cam_from_world().rotation.matrix()  # world -> camera
        ups.append(-R[1])   # camera -y axis in world coords (image "up")
        fwds.append(R[2])   # camera +z axis in world coords (looking direction)
    y = np.mean(ups, axis=0)
    y /= np.linalg.norm(y)
    f = np.mean(fwds, axis=0)
    f -= f.dot(y) * y
    z = -f / np.linalg.norm(f)
    x = np.cross(y, z)
    return np.stack([x, y, z])


def to_point_cloud(rec):
    """Colored Open3D point cloud, centered on the median point and oriented upright."""
    pts = list(rec.points3D.values())
    xyz = np.array([p.xyz for p in pts])
    rgb = np.array([p.color for p in pts], dtype=float) / 255.0
    R = viewing_rotation(rec)
    xyz = (xyz - np.median(xyz, axis=0)) @ R.T
    pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz))
    pcd.colors = o3d.utility.Vector3dVector(rgb)
    return pcd


# --- Summary numbers ---

def summarize(rec, num_images):
    if rec is None:
        return {"images_total": num_images, "images_registered": 0, "points3d": 0,
                "mean_reprojection_error_px": None, "mean_track_length": None}
    return {
        "images_total": num_images,
        "images_registered": rec.num_reg_images(),
        "points3d": rec.num_points3D(),
        "mean_reprojection_error_px": round(rec.compute_mean_reprojection_error(), 3),
        "mean_track_length": round(rec.compute_mean_track_length(), 2),  # views per 3D point
    }
