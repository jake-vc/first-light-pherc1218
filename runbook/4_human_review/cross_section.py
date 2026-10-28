"""cross_section.py - CT cross-sections with fitted surfaces drawn on top, for a human to judge whether each surface
follows a papyrus sheet (the admin's "CT cross-sections with the surface intersection overlaid").
Reads the open-data CT straight from the bucket (uncompressed 128^3 uint8 chunks; missing chunks = fill 0), only the
chunks the plane crosses. Surfaces: tifxyz dirs (x/y/z.tif in level-0 voxels, invalid points <= 0). Where a surface
crosses the plane, crossings are interpolated on the grid edges and joined cell by cell into curves.
Usage: python cross_section.py <out.png> <axis z|y> <level-0 coordinate> <level> [x0 x1 y0 y1 | x0 x1 z0 z1 in level-0
       voxels, default whole slice] -- <label>=<glob of surface dirs> [<label>=<glob> ...]
Colours: first set yellow, second cyan, third magenta. Scale bar 1 cm, or 2 mm on narrow crops (8.64 um/voxel at level 0)."""
import csv, glob, json, os, sys, urllib.error, urllib.request
import cv2, numpy as np, tifffile

B = ("https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1218/volumes/"
     "20250521120456-8.640um-1.2m-116keV-masked.zarr")
VOX_MM, C = 8.64e-3, 128
SHAPE0 = (23247, 7593, 7593)  # level-0 (z, y, x)
COLOURS = [(0, 220, 255), (255, 220, 0), (255, 0, 255)]  # BGR: yellow, cyan, magenta
if os.environ.get("XS_COLOURS"):  # e.g. "255,220,0;255,0,255": override the per-set colours (BGR), later sets drawn on top
    COLOURS = [tuple(int(v) for v in c.split(",")) for c in os.environ["XS_COLOURS"].split(";")]

sep = sys.argv.index("--")
out, axis, at, lvl = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
box = [float(v) for v in sys.argv[5:sep]]
sets = [a.split("=", 1) for a in sys.argv[sep + 1:]]
f = 2 ** lvl
shape = [(s + f - 1) // f for s in SHAPE0]  # (z, y, x) at this level


def chunk(cz, cy, cx):
    for attempt in range(5):
        try:
            raw = urllib.request.urlopen(f"{B}/{lvl}/{cz}/{cy}/{cx}", timeout=120).read()
            return np.frombuffer(raw, np.uint8).reshape(C, C, C)
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            if attempt == 4:
                raise
        except OSError:
            if attempt == 4:
                raise


# plane at this level: rows/cols = (y, x) for axis z, (z, x) for axis y
a = int(at // f)
if axis == "z":
    r0, r1, c0, c1 = (int(box[2] // f), int(box[3] // f), int(box[0] // f), int(box[1] // f)) if box else (0, shape[1], 0, shape[2])
else:
    r0, r1, c0, c1 = (int(box[2] // f), int(box[3] // f), int(box[0] // f), int(box[1] // f)) if box else (0, shape[0], 0, shape[2])
img = np.zeros((r1 - r0, c1 - c0), np.uint8)
for cr in range(r0 // C, (r1 - 1) // C + 1):
    for cc in range(c0 // C, (c1 - 1) // C + 1):
        ch = chunk(a // C, cr, cc) if axis == "z" else chunk(cr, a // C, cc)
        if ch is None:
            continue
        sl = ch[a % C] if axis == "z" else ch[:, a % C, :]
        rr0, cc0 = cr * C, cc * C
        ys, xs = max(r0, rr0), max(c0, cc0)
        ye, xe = min(r1, rr0 + C), min(c1, cc0 + C)
        img[ys - r0:ye - r0, xs - c0:xe - c0] = sl[ys - rr0:ye - rr0, xs - cc0:xe - cc0]

# contrast: stretch the 1st..99.5th percentile of the non-empty pixels
v = img[img > 0]
lo, hi = (np.percentile(v, 1), np.percentile(v, 99.5)) if v.size else (0, 255)
rgb = cv2.cvtColor(np.clip((img.astype(np.float32) - lo) * 255 / max(hi - lo, 1), 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
up = max(1, int(round(1400 / max(rgb.shape))))  # small crops are enlarged so the lines stay visible
if up > 1:
    rgb = cv2.resize(rgb, None, fx=up, fy=up, interpolation=cv2.INTER_NEAREST)

LINE = 1 if lvl >= 2 else 2  # px; turns are ~4 px apart at level 3, ~30 px at level 0
legend = []
# SCOPE_REPORT=<snap_report.tsv>: colour each surface by the screen's scope rule (on-sheet >= 0.70 and area x on-sheet
# >= 1 cm2, as in flatten_pool.sh / screen_1218.sh): green = screened, red = not screened
SCOPE = {}
if os.environ.get("SCOPE_REPORT"):
    for r in csv.DictReader(open(os.environ["SCOPE_REPORT"]), delimiter="\t"):
        SCOPE[r["winding"]] = float(r["frac_with_sheet"])
GREEN, RED = (60, 200, 60), (60, 60, 235)
n_in = n_out = 0
for k, (label, pattern) in enumerate(sets):
    dirs = sorted(glob.glob(pattern)); n_hit = 0
    for d in dirs:
        X, Y, Z = (tifffile.imread(f"{d}/{c}.tif").astype(np.float64) for c in "xyz")
        ok = (X > 0) & (Y > 0) & (Z > 0)
        S = Z if axis == "z" else Y  # coordinate across the plane
        # marching squares on the surface grid: in each grid cell, join the points where its edges cross the plane, so
        # every surface is drawn as a continuous curve (its grid points are 20 voxels apart: dots alone read as speckle)
        colour = COLOURS[k % len(COLOURS)]
        if SCOPE:
            fr = SCOPE.get(os.path.basename(d), 0.0); area = json.load(open(f"{d}/meta.json"))["area_cm2"]
            screened = fr >= 0.70 and area * fr >= 1
            colour = GREEN if screened else RED
        R = (Y, X) if axis == "z" else (Z, X)  # image (row, col) coordinates of each grid point, level-0 voxels

        def cross(a, b):  # crossing point on the edge from grid point set a to b (both index tuples): (mask, row, col)
            sa, sb = S[a], S[b]; m = ok[a] & ok[b] & ((sa - at) * (sb - at) <= 0) & (sa != sb)
            t = np.where(m, (at - sa) / np.where(sa == sb, 1, sb - sa), 0)
            return m, R[0][a] + t * (R[0][b] - R[0][a]), R[1][a] + t * (R[1][b] - R[1][a])
        n, m_ = S.shape; I0, I1, J0, J1 = slice(0, n - 1), slice(1, n), slice(0, m_ - 1), slice(1, m_)
        edges = [cross((I0, J0), (I0, J1)), cross((I1, J0), (I1, J1)),  # top, bottom
                 cross((I0, J0), (I1, J0)), cross((I0, J1), (I1, J1))]  # left, right
        M = np.stack([e[0] for e in edges]); PR = np.stack([e[1] for e in edges]); PC = np.stack([e[2] for e in edges])
        inside = False
        for ci, cj in zip(*np.nonzero(M.sum(0) >= 2)):
            ks = np.nonzero(M[:, ci, cj])[0]
            q = [((PR[k2, ci, cj] / f - r0) * up, (PC[k2, ci, cj] / f - c0) * up) for k2 in ks]
            for (ra, ca), (rb, cb) in zip(q[0::2], q[1::2]):  # 2 crossings: one segment; 4 (saddle, rare): two
                if max(ra, rb) < 0 or min(ra, rb) >= rgb.shape[0] or max(ca, cb) < 0 or min(ca, cb) >= rgb.shape[1]:
                    continue
                cv2.line(rgb, (int(ca), int(ra)), (int(cb), int(rb)), colour, LINE, cv2.LINE_AA)
                inside = True
        n_hit += inside
        if SCOPE and inside:
            n_in += screened; n_out += not screened
    legend.append(f"{label}: {n_hit} of {len(dirs)} surfaces cross this view")
if SCOPE:
    legend = [f"green: screened (>= 70% on papyrus), {n_in} in view", f"red: not screened (< 70%), {n_out} in view"]

# 1 cm scale bar and text
h, w = rgb.shape[:2]
bar_mm = 10 if 10 / (VOX_MM * f) * up <= w / 3 else 2  # 1 cm bar, or 2 mm on crops too narrow for it
px_bar = bar_mm / (VOX_MM * f) * up
cv2.rectangle(rgb, (20, h - 30), (20 + int(px_bar), h - 22), (255, 255, 255), -1)
cv2.putText(rgb, f"{bar_mm // 10} cm" if bar_mm == 10 else "2 mm", (20, h - 36), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            (255, 255, 255), 1, cv2.LINE_AA)
title = f"PHerc. 1218 CT, {'z' if axis == 'z' else 'y'} = {int(at)} (level {lvl}, {VOX_MM * f * 1000:.1f} um/px)"
lines = [title] + legend  # dark backing so the text stays readable on bright CT
cv2.rectangle(rgb, (0, 0), (min(w, 12 + 11 * max(len(t) for t in lines)), 12 + 24 * len(lines)), (0, 0, 0), -1)
for i, t in enumerate(lines):
    col = (255, 255, 255) if i == 0 else ((GREEN, RED)[i - 1] if SCOPE else COLOURS[(i - 1) % len(COLOURS)])
    cv2.putText(rgb, t, (12, 26 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 1, cv2.LINE_AA)
cv2.imwrite(out, rgb)
print(out, rgb.shape, *legend, sep="\n  ")
