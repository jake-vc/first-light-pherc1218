"""seg_yellow.py <segment dir> - yellow ink view over a whole large segment (see seg_big.sh).
The winner's four models at d = 0, reading side (reverse; Hecate resized from its 9.6 um grid), averaged, in pale yellow
over the dimmed CT (mean of the 5 surface layers of the 66-layer render): the 343 announcement style, same colours and
ramp as highlight_tiles.py. Writes yellow.png (full resolution) and yellow_small.png (2000 px wide), 1 cm bar."""
import glob, sys
import cv2, numpy as np, tifffile, zarr

LO, HI, DIM, YELLOW = 0.45, 0.60, 0.45, np.array([130, 220, 245], np.float32)
BAR = int(round(10 / 8.64e-3))
d = sys.argv[1]
z = zarr.open(f"{d}/render.zarr", mode="r"); a = z["0"] if "0" in z else z
ct = np.asarray(a[31:36]).astype(np.float32).mean(0); valid = ct > 0
lo, hi = np.percentile(ct[valid], [1, 99]); scan = np.clip((ct - lo) / max(hi - lo, 1e-6), 0, 1)
maps = []
for m in ("dnative", "hybrid_3d2d-seed42", "hybrid_3d2d-seed43"):
    f = glob.glob(f"{d}/maps/*__{m}__L66s25_reverse.tif")
    if f: maps.append(tifffile.imread(f[0]).astype(np.float32) / 255)
f = glob.glob(f"{d}/maps/*__hecate__L66zc32.50_reverse.png")
if f: maps.append(cv2.resize(cv2.imread(f[0], 0), (ct.shape[1], ct.shape[0])).astype(np.float32) / 255)
if len(maps) < 4 or any(m.shape != ct.shape for m in maps):
    print(f"{d}: WARNING {len(maps)} of 4 model maps (shapes {[m.shape for m in maps]}, CT {ct.shape})")
if not maps: sys.exit(1)
avg = np.mean([m for m in maps if m.shape == ct.shape], axis=0)
al = cv2.GaussianBlur(np.clip((avg - LO) / (HI - LO), 0, 1), (0, 0), 1.5)[..., None] * valid[..., None]
img = (np.repeat((scan * 255 * DIM)[..., None], 3, 2) * (1 - al) + YELLOW * al).astype(np.uint8)
cv2.rectangle(img, (20, img.shape[0] - 30), (20 + BAR, img.shape[0] - 20), (255, 255, 255), -1)
cv2.putText(img, "1 cm", (30 + BAR, img.shape[0] - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
cv2.imwrite(f"{d}/yellow.png", img)
s = 2000 / img.shape[1]; cv2.imwrite(f"{d}/yellow_small.png", cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA))
area = valid.sum() * (8.64e-3) ** 2 / 100
print(f"{d}: {img.shape[1]}x{img.shape[0]} px, {area:.1f} cm2 of papyrus, {len(maps)} models")
