"""same_scale.py <out.png> <label=tiles dir>... [--plain <tiles dir>...] - same-scale comparison figure.
Every tile is the review pipeline's highlight.png (the winner's four models averaged, max over depth -8..+8, fixed
contrast 0.45 -> 0.60, yellow over the dimmed CT), so scale (8.64 um per pixel) and normalisation are identical.
One rule for every tile: the 1100 x 1050 px window (9.5 x 9.1 mm, the smallest box) with the most yellow. The plain
papyrus tile is the --plain candidate (same place on a neighbouring turn) with the least yellow. 2 mm bar on each."""
import sys
import cv2, numpy as np

UM, W, H, SCALE = 8.64, 1100, 1050, 0.6
YELLOW = np.array([130, 220, 245], np.float32)


def yellowness(img):  # how far each pixel has moved from grey towards the highlight colour
    b, g, r = (img[..., i].astype(np.float32) for i in range(3))
    return np.clip((r - b) / (YELLOW[2] - YELLOW[0]), 0, 1)


def best_window(img):
    y = cv2.integral(yellowness(img))
    h, w = img.shape[:2]; hh, ww = min(H, h), min(W, w)
    s = y[hh:, ww:] - y[:-hh, ww:] - y[hh:, :-ww] + y[:-hh, :-ww]
    r, c = np.unravel_index(np.argmax(s), s.shape)
    return img[r:r + hh, c:c + ww], float(s[r, c]) / (hh * ww)


def tile(img, title):
    crop = np.zeros((H, W, 3), np.uint8); crop[:img.shape[0], :img.shape[1]] = img
    t = cv2.resize(crop, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_AREA)
    bar = int(round(2000 / UM * SCALE)); y0 = t.shape[0] - 18
    cv2.rectangle(t, (12, y0), (12 + bar, y0 + 6), (255, 255, 255), -1)
    cv2.putText(t, "2 mm", (12, y0 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    head = np.zeros((40, t.shape[1], 3), np.uint8)
    cv2.putText(head, title, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    return np.vstack([head, t])


args = sys.argv[2:]; plain = args[args.index("--plain") + 1:] if "--plain" in args else []
named = args[:args.index("--plain")] if "--plain" in args else args
tiles = []
for a in named:
    label, d = a.split("=", 1); img = cv2.imread(f"{d}/highlight.png")
    if img is None:
        sys.exit(f"{label}: no highlight.png in {d}")
    win, share = best_window(img)
    tiles.append(tile(win, label)); print(f"{label}: yellow share {share:.3f}")
found = [(d, cv2.imread(f"{d}/highlight.png")) for d in plain]
for d, img in found:
    if img is None:
        print(f"plain: no highlight.png in {d}, skipped")
found = [(d, img) for d, img in found if img is not None]
if found:
    best = min(((best_window(img), d) for d, img in found), key=lambda x: x[0][1])
    (win, share), d = best
    tiles.append(tile(win, "plain papyrus (neighbouring turn)")); print(f"plain: {d} yellow share {share:.3f}")
cols = 3; rows = -(-len(tiles) // cols); th, tw = tiles[0].shape[:2]
grid = np.zeros((rows * (th + 10), cols * (tw + 10), 3), np.uint8)
for i, t in enumerate(tiles):
    r, c = divmod(i, cols); grid[r * (th + 10):r * (th + 10) + th, c * (tw + 10):c * (tw + 10) + tw] = t
cv2.imwrite(sys.argv[1], grid); print(f"wrote {sys.argv[1]} {grid.shape[1]}x{grid.shape[0]}")
