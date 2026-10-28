"""map_candidates.py <export dir> <label=window/turn:x,y,w,h>... - find each candidate box in a NEW fit.
The box (render px of the old window's flattened turn, as in the review plans) is turned into scroll-voxel points via
the old turn's mesh (screen/<window>/<turn>/mesh_path.txt, PX=20 render px per node, as review_plan.py). Every winding
of the new fit (<export dir>/w*_main, tifxyz) is searched with a KD-tree; per candidate the best winding is the one
with the smallest median distance from the box points to its surface (share within TOL = 10 vox reported). Prints winding, share, median distance and
the box's node bounding box in that winding (row0 row1 col0 col1), so the large segment can be cut around it.
"""
import glob, os, sys
import numpy as np, tifffile
from scipy.spatial import cKDTree

PX, TOL = 20, 10  # tolerance below half the winding spacing (~20-25 vox), so neighbouring windings separate
exp = sys.argv[1]


def xyz(d):
    return [tifffile.imread(f"{d}/{c}.tif").astype(np.float64) for c in "xyz"]


new = {}
for d in sorted(glob.glob(f"{exp}/w*_main")):
    x, y, z = xyz(d); v = (x > -0.5) & (y > -0.5) & (z > -0.5)
    rows, cols = np.nonzero(v)
    new[os.path.basename(d)] = (cKDTree(np.stack([x[v], y[v], z[v]], 1)), rows, cols)
print("label\tbest_winding\tshare_within_10vox\tmedian_dist_vox\trow0\trow1\tcol0\tcol1\tsecond_best (median dist)")
for arg in sys.argv[2:]:
    label, spec = arg.split("=", 1); wt, box = spec.split(":"); bx, by, bw, bh = map(int, box.split(","))
    mesh = open(f"/workspace/screen/{wt}/mesh_path.txt").read().strip()
    x, y, z = xyz(mesh)
    r0, r1, c0, c1 = by // PX, -(-(by + bh) // PX), bx // PX, -(-(bx + bw) // PX)
    sel = (x[r0:r1, c0:c1] > -0.5) & (y[r0:r1, c0:c1] > -0.5) & (z[r0:r1, c0:c1] > -0.5)
    pts = np.stack([a[r0:r1, c0:c1][sel] for a in (x, y, z)], 1)
    if not len(pts):
        print(f"{label}\tno points"); continue
    scores = []
    for name, (tree, rows, cols) in new.items():
        d, idx = tree.query(pts, distance_upper_bound=10 * TOL)
        hit = d <= TOL
        scores.append((hit.mean(), name, float(np.median(d[np.isfinite(d)])) if np.isfinite(d).any() else np.inf,
                       idx[hit], rows, cols))
    scores.sort(key=lambda s: s[2])  # smallest median distance first
    share, name, med, idx, rows, cols = scores[0]
    bb = (rows[idx].min(), rows[idx].max(), cols[idx].min(), cols[idx].max()) if len(idx) else ("",) * 4
    print(f"{label}\t{name}\t{share:.2f}\t{med:.1f}\t" + "\t".join(map(str, bb)) + f"\t{scores[1][1]} ({scores[1][2]:.1f})")
