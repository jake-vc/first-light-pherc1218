"""seam_strip.py <winding w dir> <winding w+1 dir> <out tifxyz> [k] - the strip across the spiral seam (theta 360|0)
between two consecutive snapped windings of one fit: the last k valid columns of w and the first k of w+1, row by row
(rows are the same z sampling in both: checked to within a few voxels), written as one tifxyz (x/y/z.tif, meta.json with
scale 0.05 and area_cm2). Our per-winding screen cannot place a 4 mm window within ~2 mm of either mesh edge, and a
letter across the seam is split; the winner joined their two windings for the same reason (build_concat.py)."""
import json, os, sys
import numpy as np, tifffile
a_dir, b_dir, out = sys.argv[1:4]; K = int(sys.argv[4]) if len(sys.argv) > 4 else 25
ld = lambda d: np.stack([tifffile.imread(f"{d}/{c}.tif").astype(np.float32) for c in "xyz"], -1)
A, B = ld(a_dir), ld(b_dir); R = min(A.shape[0], B.shape[0])
S = np.full((R, 2 * K, 3), -1, np.float32)
for r in range(R):
    ia = np.nonzero((A[r] > -0.5).all(-1))[0]; ib = np.nonzero((B[r] > -0.5).all(-1))[0]
    if len(ia) == 0 or len(ib) == 0: continue
    if ia[-1] < A.shape[1] - 3 or ib[0] > 2: continue  # this row does not reach the seam on both sides
    ta = A[r, ia[-1] - K + 1: ia[-1] + 1] if ia[-1] + 1 >= K else A[r, :ia[-1] + 1]
    S[r, K - len(ta):K] = ta; tb = B[r, ib[0]: ib[0] + K]; S[r, K:K + len(tb)] = tb
v = (S > -0.5).all(-1)
if v.sum() < 50: sys.exit(f"no seam overlap between {a_dir} and {b_dir}")
os.makedirs(out, exist_ok=True)
for i, c in enumerate("xyz"): tifffile.imwrite(f"{out}/{c}.tif", S[..., i])
# area: sum of quad areas (cm2) over cells with four valid nodes; 1 voxel = 8.64 um
q = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
d1 = np.linalg.norm(S[1:, :-1] - S[:-1, :-1], axis=-1); d2 = np.linalg.norm(S[:-1, 1:] - S[:-1, :-1], axis=-1)
area = float((d1 * d2)[q].sum()) * (8.64e-4) ** 2
json.dump({"scale": [0.05, 0.05], "area_cm2": area, "seam_of": [os.path.basename(a_dir), os.path.basename(b_dir)], "k": K},
          open(f"{out}/meta.json", "w"))
print(f"{out}: {int(v.sum())} nodes, {area:.2f} cm2")
