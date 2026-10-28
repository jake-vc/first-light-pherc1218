"""calib_343.py - prereg "Positive control" numbers from the PHerc0343 screen maps.
Per model, depth and direction: median ink probability inside Nieuwlaar's 18 letter boxes vs the rest of his image area
(boxes dilated by 40 px are excluded from the background). Also writes a reading-orientation contact sheet.
Usage: python calib_343.py <maps_dir> <winner_repo> <out_dir>"""
import json, re, sys, glob, os
import numpy as np, tifffile, cv2

maps, repo, out = sys.argv[1:4]
N = "concat_w047-w048_R5B2_z9500-11000"
side = json.load(open(f"{repo}/outputs/{N}.json"))
a = side["area"]["raw_render_px"]
boxes = json.load(open(f"{repo}/inputs/{N}_letter_boxes.json"))["letters"]
rows = []
sheet = []
files = sorted(glob.glob(f"{maps}/{N}_66__*__L66s*.tif"))
assert files, f"no maps found in {maps}"
for f in files:
    m = re.search(r"__(.+?)__L66s(\d+)(_reverse)?\.tif$", f)
    model, s, rev = m.group(1), int(m.group(2)), bool(m.group(3))
    d = s + 8 - 33
    p = tifffile.imread(f).astype(np.float32) / 255.0
    letters = np.zeros(p.shape, bool); excl = np.zeros(p.shape, bool)
    for b in boxes:
        x0, y0, x1, y1 = [int(round(v)) for v in b["box"]]
        letters[y0:y1, x0:x1] = True
        excl[max(0, y0 - 40):y1 + 40, max(0, x0 - 40):x1 + 40] = True
    inarea = np.zeros(p.shape, bool); inarea[a["row0"]:a["row1"], a["col0"]:a["col1"]] = True
    bg = inarea & ~excl
    ml, mb = float(np.median(p[letters])), float(np.median(p[bg]))
    rows.append(dict(model=model, d=d, side="reading" if rev else "blind", median_letters=round(ml, 4),
                     median_background=round(mb, 4), separation=round(ml - mb, 4), shape=list(p.shape)))
    if rev and d in (0, 1):
        img = p[a["row0"]:a["row1"], a["col0"]:a["col1"]][::-1, ::-1]  # reading orientation (flip_lr, flip_ud)
        img = cv2.resize(img, (img.shape[1] // 4, img.shape[0] // 4), interpolation=cv2.INTER_AREA)
        lo, hi = np.percentile(img, [1, 99.5]); img = np.clip((img - lo) / max(hi - lo, 1e-6), 0, 1)
        img = (img * 255).astype(np.uint8)
        cv2.putText(img, f"{model} d={d:+d} reading", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, 255, 2)
        sheet.append(img)
for r in sorted(rows, key=lambda r: (r["model"], r["side"], r["d"])):
    print(r)
os.makedirs(out, exist_ok=True)
json.dump(rows, open(f"{out}/ctrl_calibration.json", "w"), indent=1)
if sheet:
    w = max(i.shape[1] for i in sheet)
    cv2.imwrite(f"{out}/ctrl_contact.png", np.vstack([np.pad(i, ((0, 6), (0, w - i.shape[1]))) for i in sheet]))
    print("wrote", f"{out}/ctrl_contact.png")
