"""confirm_images.py <box target dir>... - depth-sweep read-out for a swept box.
After confirm_box.sh: per model (winner's four + reader-v2 + reader-v3), reading side (reverse) maps at every depth
d = -15..+15 are turned into z-scores over the box's valid papyrus (same statistic as review_images.py, over all
depths of that model), averaged across the six models per depth (the per-model z-score ensemble), and written as:
  confirm_depths.png  - the ensemble at each depth, 31 tiles in a grid (scan at the top), shared z -1..3 scale
  confirm_max.png     - ensemble max over depth, yellow over the dimmed scan (same look as highlight.png)
  confirm.json        - per depth: share of papyrus with ensemble z >= 2, and the longest run of consecutive
                        depths where that share is above 2x its median ("appears at consecutive depths", prereg)
A read-out aid: whether a mark is a letter stays the human's call."""
import glob, json, sys
import cv2, numpy as np, tifffile, zarr

MODELS = ("dnative", "hybrid_3d2d-seed42", "hybrid_3d2d-seed43", "hecate", "readerv2", "readerv3")
DEPTHS = list(range(-15, 16))


def load(d, m, depth, shape):
    if m == "hecate":
        f = glob.glob(f"{d}/maps/*__hecate__L66zc{32.5 + depth:.2f}_reverse.png")
        return cv2.resize(cv2.imread(f[0], 0), (shape[1], shape[0])).astype(np.float32) / 255 if f else None
    f = glob.glob(f"{d}/maps/*__{m}__L66s{depth + 25}_reverse.tif")
    return tifffile.imread(f[0]).astype(np.float32) / 255 if f else None


for d in sys.argv[1:]:
    z = zarr.open(f"{d}/render.zarr", mode="r"); a = z["0"] if "0" in z else z
    ct = np.asarray(a[31:36]).astype(np.float32).mean(0); valid = ct > 0
    lo, hi = np.percentile(ct[valid], [1, 99]); scan = np.clip((ct - lo) / max(hi - lo, 1e-6), 0, 1)
    ens, missing = [], []
    zsum = np.zeros((len(DEPTHS),) + ct.shape, np.float32); n = np.zeros(len(DEPTHS))
    for m in MODELS:
        st = [load(d, m, k, ct.shape) for k in DEPTHS]
        have = [i for i, s in enumerate(st) if s is not None]
        missing += [f"{m} d={DEPTHS[i]}" for i in range(len(DEPTHS)) if st[i] is None]
        if not have: continue
        v = np.stack([st[i][valid] for i in have]); mu, sd = v.mean(), max(v.std(), 1e-6)
        for i in have: zsum[i] += (st[i] - mu) / sd; n[i] += 1
    e = zsum / np.maximum(n, 1)[:, None, None]
    share = [float((e[i][valid] >= 2).mean()) for i in range(len(DEPTHS))]
    med = float(np.median(share)); hot = [s > 2 * med for s in share]
    run = best = 0
    for h in hot: run = run + 1 if h else 0; best = max(best, run)
    json.dump({"depths": DEPTHS, "models_per_depth": n.tolist(), "share_z_ge_2": share, "longest_consecutive_run": best,
               "missing": missing}, open(f"{d}/confirm.json", "w"), indent=1)
    tile = lambda img: cv2.resize((np.clip(img, 0, 1) * 255).astype(np.uint8), None, fx=0.25, fy=0.25)
    tiles = [tile(scan)] + [tile((e[i] + 1) / 4) for i in range(len(DEPTHS))]
    for t, txt in zip(tiles, ["scan"] + [f"d={k}" for k in DEPTHS]):
        cv2.putText(t, txt, (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, 255, 1)
    cols = 8; h, w = tiles[0].shape; rows = -(-len(tiles) // cols)
    grid = np.zeros((rows * (h + 4), cols * (w + 4)), np.uint8)
    for k, t in enumerate(tiles):
        r, c = divmod(k, cols); grid[r * (h + 4):r * (h + 4) + h, c * (w + 4):c * (w + 4) + w] = t
    cv2.imwrite(f"{d}/confirm_depths.png", grid)
    emax = np.clip((e.max(0) + 1) / 4, 0, 1); al = np.clip((emax - 0.6) / 0.2, 0, 1)
    al = cv2.GaussianBlur(al, (0, 0), 1.5)[..., None]
    grey = np.repeat((scan * 255 * 0.45)[..., None], 3, 2)
    cv2.imwrite(f"{d}/confirm_max.png", (grey * (1 - al) + np.array([130, 220, 245]) * al).astype(np.uint8))
    print(f"{d}: models/depth {int(n.min())}-{int(n.max())}, longest consecutive run {best}, missing {len(missing)}")
