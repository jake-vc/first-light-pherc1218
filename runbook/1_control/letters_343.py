"""letters_343.py <review box dir> <winner repo> <out dir> - neighbour-check reference from PHerc0343's known letters.
Uses the sample review tiles (target = concat w047-w048, neighbour = w048, both max over the rendered depths). Per
calibrated model: share of pixels above its threshold inside Nieuwlaar's 18 letter boxes, in the rest of his image
area (boxes dilated 40 px excluded), and on the neighbour tile's papyrus. Writes letters_343.json and an overlay PNG
(boxes drawn on the reader-v3 tile) to check the box placement by eye."""
import json, sys, os
import numpy as np, cv2
R, repo, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
N = "concat_w047-w048_R5B2_z9500-11000"
THR = {"readerv3": 0.4000, "dnative": 0.4235, "readerv2": 0.3608}
plan = {j["role"]: j for j in json.load(open(f"{R}/../plan.json")) if j["box_id"] == os.path.basename(R.rstrip("/"))}
ox, oy = plan["target"]["x"], plan["target"]["y"]  # tile = render crop starting at (x, y) of the full map grid
a = json.load(open(f"{repo}/outputs/{N}.json"))["area"]["raw_render_px"]
boxes = json.load(open(f"{repo}/inputs/{N}_letter_boxes.json"))["letters"]
sc = cv2.imread(f"{R}/target/tiles/scan.png", 0); H, W = sc.shape
letters = np.zeros((H, W), bool); excl = np.zeros((H, W), bool); area = np.zeros((H, W), bool)
area[max(0, a["row0"] - oy):a["row1"] - oy, max(0, a["col0"] - ox):a["col1"] - ox] = True
for b in boxes:
    x0, y0, x1, y1 = [int(round(v)) for v in b["box"]]; x0 -= ox; x1 -= ox; y0 -= oy; y1 -= oy
    letters[max(0, y0):y1, max(0, x0):x1] = True; excl[max(0, y0 - 40):y1 + 40, max(0, x0 - 40):x1 + 40] = True
bg = area & ~excl & (sc > 0)
nsc = cv2.imread(f"{R}/w048/tiles/scan.png", 0) > 0
res = {"letter_px": int(letters.sum()), "background_px": int(bg.sum()), "models": {}}
for m, t in THR.items():
    tm = cv2.imread(f"{R}/target/tiles/{m}.png", 0) >= t * 255; nm = cv2.imread(f"{R}/w048/tiles/{m}.png", 0) >= t * 255
    L, B, Nb = float(tm[letters].mean()), float(tm[bg].mean()), float(nm[nsc].mean())
    res["models"][m] = {"letters": round(L, 4), "background": round(B, 4), "neighbour": round(Nb, 4),
                        "letters_over_neighbour": round(L / max(Nb, 1e-6), 2), "background_over_neighbour": round(B / max(Nb, 1e-6), 2)}
json.dump(res, open(f"{out}/letters_343.json", "w"), indent=1); print(json.dumps(res, indent=1))
ov = cv2.cvtColor(cv2.imread(f"{R}/target/tiles/readerv3.png", 0), cv2.COLOR_GRAY2BGR)
for b in boxes:
    x0, y0, x1, y1 = [int(round(v)) for v in b["box"]]; cv2.rectangle(ov, (x0 - ox, y0 - oy), (x1 - ox, y1 - oy), (0, 0, 255), 6)
cv2.imwrite(f"{out}/letters_343_overlay.png", cv2.resize(ov, (W // 4, H // 4), interpolation=cv2.INTER_AREA))
