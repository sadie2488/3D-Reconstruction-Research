"""Feature matching between image pairs.

SIFT keypoints -> FLANN nearest neighbours -> Lowe ratio test -> RANSAC (fundamental matrix).
"""
import cv2
import numpy as np


# --- SIFT features ---

def detect_sift(images, max_features=0):
    """List of (keypoints, descriptors), one per image. max_features=0 = no limit."""
    return detect(images, cv2.SIFT_create(nfeatures=max_features))


# --- ORB features (fast binary alternative, used in the SIFT vs ORB comparison) ---

def detect_orb(images, max_features=5000):
    return detect(images, cv2.ORB_create(nfeatures=max_features))


def detect(images, detector):
    feats = []
    for img in images:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        feats.append(detector.detectAndCompute(gray, None))
    return feats


# --- FLANN matching + Lowe ratio test ---

FLANN_INDEX_KDTREE = 1


def ratio_test_matches(desc1, desc2, ratio=0.75):
    if desc1.dtype == np.uint8:
        # binary descriptors (ORB): Hamming distance, brute force
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    else:
        # float descriptors (SIFT): approximate nearest neighbours with a KD-tree
        matcher = cv2.FlannBasedMatcher(dict(algorithm=FLANN_INDEX_KDTREE, trees=5), dict(checks=50))
    knn = matcher.knnMatch(desc1, desc2, k=2)
    # ratio test: keep a match only if it is clearly better than the 2nd-best candidate
    return [p[0] for p in knn if len(p) == 2 and p[0].distance < ratio * p[1].distance]


# --- RANSAC outlier rejection ---

def ransac_inliers(kp1, kp2, matches, thresh_px=1.0):
    """Keep matches that agree with a single fundamental matrix F. Returns (inliers, F).

    Uses F rather than E so this step does not depend on K being right.
    thresh_px = max distance from a point to its epipolar line.
    """
    if len(matches) < 8:  # 8-point minimum for F
        return [], None
    pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])
    F, mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC, thresh_px, 0.999)
    if F is None:
        return [], None
    return [m for m, keep in zip(matches, mask.ravel()) if keep], F


def match_pair(feat1, feat2, ratio=0.75, thresh_px=1.0):
    """Returns (ratio_test_matches, ransac_inliers) for one image pair."""
    (kp1, d1), (kp2, d2) = feat1, feat2
    if d1 is None or d2 is None:
        return [], []
    good = ratio_test_matches(d1, d2, ratio)
    inliers, _ = ransac_inliers(kp1, kp2, good, thresh_px)
    return good, inliers


# --- Match visualization ---

def draw_matches(img1, kp1, img2, kp2, matches, max_draw=300, seed=0):
    """Side-by-side image with up to max_draw match lines (random subset so it stays readable)."""
    if len(matches) > max_draw:
        idx = np.random.default_rng(seed).choice(len(matches), max_draw, replace=False)
        matches = [matches[i] for i in sorted(idx)]
    return cv2.drawMatches(img1, kp1, img2, kp2, matches, None,
                           flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
