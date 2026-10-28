"""screen_sheet.py - prereg screen for one rendered PHerc1218 winding.
Per model and direction: max over the screened depths, 4 mm x 4 mm window mean (>= 90% valid pixels), compared with the
control-derived thresholds (prereg Calibration). A winding is a CANDIDATE when at least two screen models fire at the
same window centre in the same direction (criteria 1 + 3); shape and neighbour-sheet checks (2, 4) are done by eye.
Writes stats.json and sheet.png (models x 2 directions + raw CT surface layers, CLAHE) in <out_dir>.
Usage: python screen_sheet.py <render.zarr> <maps_dir> <out_dir> <label>"""
import glob, json, os, re, sys
import numpy as np, tifffile, cv2, zarr

render, maps, out, label = sys.argv[1:5]
THR = {"readerv2": 0.3608, "dnative": 0.4235, "readerv3": 0.4000}  # prereg Calibration (PHerc0343 control)
W = 463  # 4 mm at 8.64 um
os.makedirs(out, exist_ok=True)
z = zarr.open(render, mode="r")
z0 = z["0"] if "0" in z else z
surf = np.asarray(z0[31:36]).astype(np.float32)  # layers 31..35 around the mesh (layer 33 = d 0)
valid = (surf.min(0) > 0).astype(np.float32)
den = cv2.boxFilter(valid, -1, (W, W), normalize=False)
ok = den > 0.9 * W * W
stats = {"label": label, "shape": list(valid.shape), "valid_cm2": round(float(valid.sum()) * (8.64e-4) ** 2, 3), "maps": {}}
panels, hits = [], {}
for model in THR:
    for direction, suf in (("forward", ""), ("reverse", "_reverse")):
        fs = [f for f in glob.glob(f"{maps}/*__{model}__L66s*{suf}.tif") if f.endswith(f"{suf}.tif") and (suf or not f.endswith("_reverse.tif"))]
        if not fs:
            continue
        p = np.max([tifffile.imread(f) for f in fs], axis=0).astype(np.float32) / 255
        m = np.where(ok, cv2.boxFilter(p * valid, -1, (W, W), normalize=False) / np.maximum(den, 1), 0)
        hit = m >= THR[model]
        hits[(model, direction)] = hit
        stats["maps"][f"{model}/{direction}"] = {"n_depths": len(fs), "max_window_mean": round(float(m.max()), 4),
                                                 "hit_frac": round(float(hit.sum() / max(ok.sum(), 1)), 5)}
        img = cv2.resize(p, (p.shape[1] // 4, p.shape[0] // 4), interpolation=cv2.INTER_AREA)
        img = (np.clip(img, 0, 1) * 255).astype(np.uint8)  # fixed scale 0..1, same for every winding
        cv2.putText(img, f"{label} {model} {direction} max d", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 255, 2)
        panels.append(img)
cand = {}
flag_boxes = []
for direction in ("forward", "reverse"):
    hs = [hits[(m, direction)] for m in THR if (m, direction) in hits]
    if len(hs) >= 2:
        votes = np.sum(hs, axis=0)  # candidate: at least two screen models fire at the same window centre
        cand[direction] = round(float((votes >= 2).sum() / max(ok.sum(), 1)), 5)
        n, lab, st, _ = cv2.connectedComponentsWithStats(((votes >= 2) & ok).astype(np.uint8))
        for k in range(1, n):  # flagged window-centre regions, in render pixels; the 4 mm window extends W/2 around them
            x, y, w, h = (int(v) for v in st[k, :4])
            flag_boxes.append({"direction": direction, "x0": max(0, x - W // 2), "y0": max(0, y - W // 2),
                               "x1": min(valid.shape[1], x + w + W // 2), "y1": min(valid.shape[0], y + h + W // 2)})
stats["both_models_hit_frac"] = cand
stats["candidate"] = any(v > 0 for v in cand.values())
stats["flag_boxes"] = flag_boxes
ct = surf.mean(0)
ct = cv2.resize(ct, (ct.shape[1] // 4, ct.shape[0] // 4), interpolation=cv2.INTER_AREA)
lo, hi = np.percentile(ct[ct > 0], [1, 99]) if (ct > 0).any() else (0, 1)
ct = (np.clip((ct - lo) / max(hi - lo, 1e-6), 0, 1) * 255).astype(np.uint8)
ct = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(ct)
cv2.putText(ct, f"{label} raw CT layers 31-35 (CLAHE)", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 255, 2)
panels.append(ct)
bar = np.zeros((40, panels[0].shape[1]), np.uint8)
px_cm = int(round(10 / 8.64e-3 / 4))  # 1 cm at the /4 sheet scale
cv2.rectangle(bar, (10, 15), (10 + px_cm, 25), 255, -1); cv2.putText(bar, "1 cm", (20 + px_cm, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 255, 1)
cv2.imwrite(f"{out}/sheet.png", np.vstack([np.pad(i, ((0, 4), (0, 0))) for i in panels] + [bar]))
json.dump(stats, open(f"{out}/stats.json", "w"), indent=1)
print(json.dumps({k: stats[k] for k in ("label", "valid_cm2", "both_models_hit_frac", "candidate")}))
