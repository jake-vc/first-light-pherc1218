"""box_in_segment.py <box target dir> <old tifxyz> <old_crop_x> <old_crop_y> <segment dir> <out prefix>
Find a review box inside a large segment (seg_big.sh output). Every 10th pixel of the box's render is turned into a
scroll-voxel point through the old flattened surface (render px = tifxyz node / scale minus nothing: full px = crop
offset + box px); a KD-tree over the segment's flattened surface (flat/tifxyz/flatten.tifxyz) gives the nearest node
per point and its distance; segment render px = node / scale - the segment's auto-crop offset (from render.log).
Writes <out>_ctx.png (yellow, 3x the box, box outlined), <out>_box.png (yellow at the box), <out>_ct.png (CT layer at
the box) and prints the mapped rectangle, the share of points within 10 voxels and the median distance.
A read-out aid only: whether a mark is a letter stays the human's call."""
import json, re, sys
import cv2, numpy as np, tifffile, zarr
from scipy.spatial import cKDTree

box, old, ox, oy, seg, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6]
TOL, STEP = 10, 10


def surface(d):
    x, y, z = (tifffile.imread(f"{d}/{c}.tif").astype(np.float64) for c in "xyz")
    return x, y, z, 1 / json.load(open(f"{d}/meta.json"))["scale"][0]


def bilinear(a, r, c):
    r0, c0 = np.floor(r).astype(int), np.floor(c).astype(int); fr, fc = r - r0, c - c0
    r0 = np.clip(r0, 0, a.shape[0] - 2); c0 = np.clip(c0, 0, a.shape[1] - 2)
    return (a[r0, c0] * (1 - fr) * (1 - fc) + a[r0 + 1, c0] * fr * (1 - fc) + a[r0, c0 + 1] * (1 - fr) * fc
            + a[r0 + 1, c0 + 1] * fr * fc)


ob = zarr.open(f"{box}/render.zarr", mode="r")["0"]; bh, bw = ob.shape[1:]
vv, uu = np.mgrid[0:bh:STEP, 0:bw:STEP]; vv, uu = vv.ravel(), uu.ravel()
x, y, z, px = surface(old)
r, c = (vv + oy) / px, (uu + ox) / px
ok = bilinear((x > -0.5).astype(float), r, c) > 0.999  # only where all four nodes are valid
pts = np.stack([bilinear(a, r[ok], c[ok]) for a in (x, y, z)], 1)

sx, sy, sz, spx = surface(f"{seg}/flat/tifxyz/flatten.tifxyz")
valid = (sx > -0.5) & (sy > -0.5) & (sz > -0.5); rows, cols = np.nonzero(valid)
d, idx = cKDTree(np.stack([sx[valid], sy[valid], sz[valid]], 1)).query(pts)
m = re.search(r"from \((\d+),(\d+)\)", open(f"{seg}/render.log").read()); cx, cy = int(m.group(1)), int(m.group(2))
near = d <= TOL
su, sv = cols[idx] * spx - cx, rows[idx] * spx - cy
print(f"points {len(pts)}; within {TOL} vox {near.mean():.2f}; median distance {np.median(d):.1f} vox")
if not near.any():
    sys.exit("box not on this segment")
u0, u1, v0, v1 = (int(np.percentile(a[near], q)) for a, q in ((su, 1), (su, 99), (sv, 1), (sv, 99)))
print(f"segment render rectangle: x {u0}..{u1}, y {v0}..{v1} (box {bw}x{bh} px -> {u1 - u0}x{v1 - v0})")
# the orientation of the mapping (box x/y -> segment x/y), to read the crops the same way round
A = np.linalg.lstsq(np.stack([uu[ok][near], vv[ok][near], np.ones(near.sum())], 1),
                    np.stack([su[near], sv[near]], 1), rcond=None)[0]
print("box->segment linear part [[du/dx du/dy] [dv/dx dv/dy]]:", np.round(A[:2].T, 2).tolist())

yel = cv2.imread(f"{seg}/yellow.png")
H, W = yel.shape[:2]; mw, mh = u1 - u0, v1 - v0
cu0, cu1, cv0, cv1 = max(0, u0 - mw), min(W, u1 + mw), max(0, v0 - mh), min(H, v1 + mh)
ctx = yel[cv0:cv1, cu0:cu1].copy()
cv2.rectangle(ctx, (u0 - cu0, v0 - cv0), (u1 - cu0, v1 - cv0), (255, 255, 255), 3)
cv2.imwrite(f"{out}_ctx.png", ctx)
cv2.imwrite(f"{out}_box.png", yel[v0:v1, u0:u1])
ct = zarr.open(f"{seg}/render.zarr", mode="r")["0"]
cv2.imwrite(f"{out}_ct.png", np.asarray(ct[33, v0:v1, u0:u1]))
print(f"wrote {out}_ctx.png {out}_box.png {out}_ct.png (yellow image {W}x{H})")
