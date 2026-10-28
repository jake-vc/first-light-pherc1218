"""whole_turn_yellow.py <screen turn dir> - whole-turn yellow view (see whole_turn_yellow.sh).
Average of the turn's screen maps (reading side, d = 0) in pale yellow over the dimmed CT (mean of the 5 surface
layers in ct5.zarr), same colours and ramp as highlight_tiles.py; a 1 cm bar bottom left."""
import glob, sys
import cv2, numpy as np, tifffile, zarr

LO, HI, DIM, YELLOW = 0.45, 0.60, 0.45, np.array([130, 220, 245], np.float32)
BAR = int(round(10 / 8.64e-3))
d = sys.argv[1]
z = zarr.open(f"{d}/ct5.zarr", mode="r"); a = z["0"] if "0" in z else z
ct = np.asarray(a[:]).astype(np.float32).mean(0); valid = ct > 0
lo, hi = np.percentile(ct[valid], [1, 99]); scan = np.clip((ct - lo) / max(hi - lo, 1e-6), 0, 1)
maps = [tifffile.imread(f).astype(np.float32) / 255 for f in sorted(glob.glob(f"{d}/maps/*__L66s25_reverse.tif"))]
if not maps or any(m.shape != ct.shape for m in maps):
    sys.exit(f"{d}: maps missing or shape {[m.shape for m in maps]} != CT {ct.shape}")
avg = np.mean(maps, axis=0)
al = cv2.GaussianBlur(np.clip((avg - LO) / (HI - LO), 0, 1), (0, 0), 1.5)[..., None] * valid[..., None]
grey = np.repeat((scan * 255 * DIM)[..., None], 3, 2)
img = (grey * (1 - al) + YELLOW * al).astype(np.uint8)
cv2.rectangle(img, (20, img.shape[0] - 30), (20 + BAR, img.shape[0] - 20), (255, 255, 255), -1)
cv2.putText(img, "1 cm", (30 + BAR, img.shape[0] - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
cv2.imwrite(f"{d}/whole_yellow.png", img)
print(f"{d}: {img.shape[1]}x{img.shape[0]} px, {len(maps)} screen models")
