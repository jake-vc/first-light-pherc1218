"""dup_check.py <review plan.json>... - are any two candidates the same papyrus spot seen from two overlapping windows?
For each plan's target boxes, takes the mesh points (scroll voxel coordinates) inside
the box, and for every pair of boxes from different windows measures how much of the smaller box lies within TOL
voxels of the other (KD-tree nearest neighbour). Overlap >= 20 % = duplicate (same spot); 0 < overlap < 20 % = touching.
Same-window pairs are skipped (different turns of one fit cannot be the same sheet). Prints a TSV and a summary."""
import itertools, json, os, sys
import numpy as np, tifffile
from scipy.spatial import cKDTree

PX, TOL = 20, 58  # render px per mesh node (review_plan.py); 58 voxels = 0.5 mm at 8.64 um

boxes = []
for plan in sys.argv[1:]:
    win = plan.split("/screen/")[1].split("/")[0]
    for j in json.load(open(plan)):
        if j.get("role") != "target": continue
        x, y, z = (tifffile.imread(f"{j['mesh']}/{c}.tif").astype(np.float64) for c in "xyz")
        r0, r1 = j["y"] // PX, -(-(j["y"] + j["h"]) // PX); c0, c1 = j["x"] // PX, -(-(j["x"] + j["w"]) // PX)
        sel = (x[r0:r1, c0:c1] > -0.5) & (y[r0:r1, c0:c1] > -0.5) & (z[r0:r1, c0:c1] > -0.5)
        p = np.stack([a[r0:r1, c0:c1][sel] for a in (x, y, z)], 1)
        if len(p): boxes.append((f"{win}/{j['turn']}", win, p, p.mean(0)))

print("a\tb\toverlap_frac\tmin_dist_vox\tcentroid_dist_mm")
dups = touch = 0
for (la, wa, pa, ca), (lb, wb, pb, cb) in itertools.combinations(boxes, 2):
    if wa == wb: continue
    small, big = (pa, pb) if len(pa) <= len(pb) else (pb, pa)
    d, _ = cKDTree(big).query(small, distance_upper_bound=10 * TOL)
    frac = float(np.mean(d <= TOL)); dmin = float(np.min(d))
    if frac > 0 or dmin < 10 * TOL:
        print(f"{la}\t{lb}\t{frac:.2f}\t{dmin:.0f}\t{np.linalg.norm(ca - cb) * 8.64e-3:.1f}")
        dups += frac >= 0.2; touch += 0 < frac < 0.2
print(f"# {len(boxes)} target boxes; {dups} duplicate pairs (>=20% within 0.5 mm), {touch} touching pairs", file=sys.stderr)
