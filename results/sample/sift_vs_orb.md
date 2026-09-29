# SIFT vs ORB

| Detector | Keypoints/img | Detect (s) | Match (s) | Neighbour pairs: matches | inliers | inlier % | 3-apart pairs: matches | inliers | inlier % |
|---|---|---|---|---|---|---|---|---|---|
| SIFT | 4303 | 1.4 | 1.1 | 1776 | 1589 | 89% | 551 | 444 | 80% |
| ORB (5000) | 4997 | 0.4 | 1.0 | 1009 | 652 | 65% | 260 | 142 | 54% |

11 images at 1600x1067. Same ratio test (0.75) and RANSAC (fundamental matrix, 1 px) for both. Matches/inliers are means per pair.
