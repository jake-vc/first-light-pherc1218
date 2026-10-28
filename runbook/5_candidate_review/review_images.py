"""review_images.py <review dir> - native-resolution review panels for every planned box (see review_run.sh).
Per box: target panel = CT surface layers | reader-v2 | dense_native | reader-v3 (each max over d -8..+8, flagged
direction) | ensemble (mean of per-model z-scores, max over depth); neighbour panels (w-1, w+1) = same at d = 0.
All probability panels share one fixed 0..1 scale; 1 cm scale bar. Writes <box>/panel_<role>.png and summary.md."""
import glob, json, os, sys
import numpy as np, tifffile, cv2, zarr

R = sys.argv[1]; plan = json.load(open(f"{R}/plan.json"))
MODELS = tuple(os.environ.get("REVIEW_MODELS", "readerv3 dnative readerv2 hybrid_3d2d-seed42 hybrid_3d2d-seed43 hecate").split()); ENSEMBLE = ("readerv2", "dnative", "readerv3"); BAR = int(round(10 / 8.64e-3))  # 1 cm in px


def label(img, text):
    img = np.pad(img, ((34, 0), (0, 0))); cv2.putText(img, text, (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 255, 2); return img


def save_tile(d, name, img):  # individual tiles for the human-readable report (morning_report.py)
    os.makedirs(f"{d}/tiles", exist_ok=True); cv2.imwrite(f"{d}/tiles/{name}.png", img)


def panel(d, direction):
    z = zarr.open(f"{d}/render.zarr", mode="r"); a = z["0"] if "0" in z else z
    ct = np.asarray(a[31:36]).astype(np.float32).mean(0); valid = ct > 0
    lo, hi = np.percentile(ct[valid], [1, 99]) if valid.any() else (0, 1)
    ctimg = (np.clip((ct - lo) / max(hi - lo, 1e-6), 0, 1) * 255).astype(np.uint8); save_tile(d, "scan", ctimg)
    tiles = [label(ctimg, "CT d0")]
    suf = "_reverse.tif" if direction == "reverse" else ".tif"
    zs = []
    for m in MODELS:
        if m == "hecate":  # PNG maps on Hecate's 9.6 um grid: resized to the render below
            sfx = "_reverse.png" if direction == "reverse" else ".png"
            fs = [f for f in glob.glob(f"{d}/maps/*__hecate__L66zc*{sfx}") if (sfx != ".png" or not f.endswith("_reverse.png"))]
        else:
            fs = [f for f in glob.glob(f"{d}/maps/*__{m}__L66s*{suf}") if (suf != ".tif" or not f.endswith("_reverse.tif"))]
        if not fs:
            tiles.append(label(np.zeros_like(tiles[0][34:]), f"{m}: none")); continue
        rd = lambda f: (cv2.resize(cv2.imread(f, cv2.IMREAD_GRAYSCALE), (ct.shape[1], ct.shape[0]), interpolation=cv2.INTER_LINEAR)
                        if f.endswith(".png") else tifffile.imread(f)).astype(np.float32) / 255
        stack = np.stack([rd(f) for f in sorted(fs)])
        mimg = (np.clip(stack.max(0), 0, 1) * 255).astype(np.uint8); save_tile(d, m, mimg)
        tiles.append(label(mimg, f"{m} max of {len(fs)} d"))
        lit = [round(float((s_ > 0.4).mean()), 4) for s_ in stack]  # share of pixels above 0.4 at each depth
        json.dump({"depth_files": [os.path.basename(f) for f in sorted(fs)], "frac_above_0.4": lit}, open(f"{d}/tiles/{m}_depths.json", "w"))
        if m in ENSEMBLE:  # the ensemble image is always the three calibrated screen models
            v = stack[:, valid] if valid.any() else stack.reshape(len(fs), -1)
            zs.append((stack - v.mean()) / max(v.std(), 1e-6))
    if zs:
        e = np.mean([z.max(0) for z in zs], axis=0); e = np.clip((e + 1) / 4, 0, 1)  # z -1..3 -> 0..1
        eimg = (e * 255).astype(np.uint8); save_tile(d, "ensemble", eimg)
        tiles.append(label(eimg, "ensemble z (max d)"))
    w = max(t.shape[1] for t in tiles)
    out = np.vstack([np.pad(t, ((0, 6), (0, w - t.shape[1]))) for t in tiles])
    bar = np.zeros((30, w), np.uint8); cv2.rectangle(bar, (6, 10), (6 + BAR, 20), 255, -1)
    cv2.putText(bar, "1 cm", (14 + BAR, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 255, 1)
    return np.vstack([out, bar])


lines = ["# Detail review of flagged areas", "", "Panels are native resolution (8.64 µm/px); probability panels share a fixed 0..1 scale.", ""]
for j in plan:
    d = f"{R}/{j['box_id']}/{j['role']}"
    if j.get("missing"):
        lines.append(f"- {j['box_id']} {j['role']}: no matching region on this neighbour turn"); continue
    if not os.path.isdir(f"{d}/render.zarr"):
        lines.append(f"- {j['box_id']} {j['role']}: render missing"); continue
    p = panel(d, j["direction"]); f = f"{R}/{j['box_id']}/panel_{j['role']}.png"; cv2.imwrite(f, p)
    extra = f" z {j['z_range'][0]:.0f}–{j['z_range'][1]:.0f}, θ {j['theta_deg'][0]:.0f}°…{j['theta_deg'][1]:.0f}°, EDGE (letters may be cut: taller refit)" if j["role"] == "target" and j.get("edge") else \
            (f" z {j['z_range'][0]:.0f}–{j['z_range'][1]:.0f}, θ {j['theta_deg'][0]:.0f}°…{j['theta_deg'][1]:.0f}°" if j["role"] == "target" else "")
    lines.append(f"- {j['box_id']} {j['role']} ({j['direction']}, {j['w']}×{j['h']} px):{extra} → `{os.path.relpath(f, R)}`")
open(f"{R}/summary.md", "w").write("\n".join(lines) + "\n")
print(f"{R}/summary.md")
