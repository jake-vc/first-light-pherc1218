"""shape_stats.py <label=tiles dir>... - size of the "ink marks" in a review box, to compare candidates with PHerc. 343's
real letters processed the same way. Uses the same map as the yellow view (highlight_tiles.py):
the average of the winner's four models (max over depth), thresholded at T. Each connected mark (>= MIN_AREA px) gets:
height and width (bounding box, mm), stroke width (2 x median distance-to-edge along the mark's skeleton, mm) and
fill. Per box: number of marks, medians, and the marks' share of the valid papyrus. 8.64 um per pixel.
Prints one TSV row per box. A size check only: it cannot say whether a mark is a letter."""
import os, sys
import cv2
import numpy as np
from scipy import ndimage
from skimage.morphology import skeletonize

MODELS = ("hybrid_3d2d-seed42", "hybrid_3d2d-seed43", "hecate", "dnative")
T, MIN_AREA, UM = float(os.environ.get("SS_T", 0.5)), 400, 8.64e-3  # px area floor ~0.03 mm^2

print("label\tvalid_mm2\tmarks\tink_share\theight_mm_med\twidth_mm_med\tstroke_mm_med\theight_mm_p90")
for arg in sys.argv[1:]:
    label, d = arg.split("=", 1)
    scan = cv2.imread(f"{d}/scan.png", 0)
    probs = [cv2.imread(f"{d}/{m}.png", 0) for m in MODELS]
    if scan is None or any(p is None for p in probs):
        print(f"{label}\tmissing tiles"); continue
    avg = np.mean([p / 255.0 for p in probs], axis=0); valid = scan > 0
    lab, n = ndimage.label((avg >= T) & valid)
    rows = []
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        m = lab[sl] == k; area = int(m.sum())
        if area < MIN_AREA: continue
        h, w = m.shape; dist = ndimage.distance_transform_edt(m); sk = skeletonize(m)
        stroke = 2 * float(np.median(dist[sk])) if sk.any() else 0.0
        rows.append((h * UM, w * UM, stroke * UM, area))
    vmm2 = valid.sum() * UM * UM
    if not rows:
        print(f"{label}\t{vmm2:.1f}\t0\t0\t\t\t\t"); continue
    hh, ww, st, ar = (np.array(c) for c in zip(*rows))
    print(f"{label}\t{vmm2:.1f}\t{len(rows)}\t{ar.sum() / valid.sum():.3f}\t{np.median(hh):.2f}\t{np.median(ww):.2f}\t"
          f"{np.median(st):.2f}\t{np.percentile(hh, 90):.2f}")
