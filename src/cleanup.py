"""Point cloud cleanup with Open3D: statistical outlier removal, optional plane removal."""
import numpy as np


def scene_size(pcd):
    """Robust scene diagonal (5th-95th percentile box). SfM units are arbitrary, so thresholds use this."""
    xyz = np.asarray(pcd.points)
    return float(np.linalg.norm(np.percentile(xyz, 95, axis=0) - np.percentile(xyz, 5, axis=0)))


# --- Statistical outlier removal ---

def remove_outliers(pcd, nb_neighbors=20, std_ratio=2.0):
    """Drop points whose mean distance to their neighbours is > std_ratio std devs above average."""
    clean, _ = pcd.remove_statistical_outlier(nb_neighbors=nb_neighbors, std_ratio=std_ratio)
    return clean


# --- Far-point crop ---

def remove_far_points(pcd, factor=2.0):
    """Drop points farther from the median than factor * (95th-percentile distance).

    Catches small far-away clumps that survive outlier removal because they have close neighbours.
    """
    xyz = np.asarray(pcd.points)
    d = np.linalg.norm(xyz - np.median(xyz, axis=0), axis=1)
    keep = np.flatnonzero(d <= factor * np.percentile(d, 95))
    return pcd.select_by_index(keep)


# --- Plane removal (floor / table) ---

def remove_largest_plane(pcd, rel_threshold=0.01):
    """RANSAC-fit the biggest plane and delete its points. Returns (cloud, num_removed)."""
    dist = rel_threshold * scene_size(pcd)
    _, inliers = pcd.segment_plane(distance_threshold=dist, ransac_n=3, num_iterations=1000)
    return pcd.select_by_index(inliers, invert=True), len(inliers)
