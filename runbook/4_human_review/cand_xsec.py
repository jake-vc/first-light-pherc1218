"""cand_xsec.py <out dir> <label> [<label> ...] - placement check at each ink candidate: for a flagged turn
(label "C4f/w049"), take its largest flag box on the face with the most 2-of-3 agreement, map the box centre to the
surface (render px -> mesh node, 20 px per node, crop origin from render_crop.txt) and cut a full-resolution CT
cross-section (z plane through that point, +-HALF voxels) with cross_section.py: the window's other flattened turns
in cyan, the candidate turn in magenta on top. Shows whether the surface under the strokes lies on a papyrus sheet.
Writes <out dir>/<window>_<turn>.png and prints the box, node and 3D point used."""
import json, os, re, subprocess, sys
import numpy as np, tifffile

HALF = 175  # voxels: a ~3 mm square around the candidate
PX = 20     # render px per mesh node
S = "/workspace/p8/scripts"; PY = "/workspace/venv/bin/python"
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for label in sys.argv[2:]:
    W, turn = label.split("/"); d = f"/workspace/screen/{W}/{turn}"
    st = json.load(open(f"{d}/stats.json"))
    face = max(("forward", "reverse"), key=lambda f: st["both_models_hit_frac"].get(f, 0))
    boxes = [b for b in st.get("flag_boxes", []) if b["direction"] == face] or st.get("flag_boxes", [])
    if not boxes:
        print(f"{label}: no flag boxes"); continue
    b = max(boxes, key=lambda b: (b["x1"] - b["x0"]) * (b["y1"] - b["y0"]))
    m = re.search(r"from \((\d+),(\d+)\)", open(f"{d}/render_crop.txt").read()) if os.path.exists(f"{d}/render_crop.txt") else None
    ox, oy = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    mesh = open(f"{d}/mesh_path.txt").read().strip()
    X, Y, Z = (tifffile.imread(f"{mesh}/{c}.tif").astype(np.float64) for c in "xyz")
    ok = (X > 0) & (Y > 0) & (Z > 0)
    r, c = int(((b["y0"] + b["y1"]) / 2 + oy) / PX), int(((b["x0"] + b["x1"]) / 2 + ox) / PX)
    if not (0 <= r < X.shape[0] and 0 <= c < X.shape[1] and ok[r, c]):  # nearest valid node
        rr, cc = np.nonzero(ok); k = int(np.argmin((rr - r) ** 2 + (cc - c) ** 2)); r, c = int(rr[k]), int(cc[k])
    x, y, z = X[r, c], Y[r, c], Z[r, c]
    base = W.rstrip("fxs")
    png = f"{out}/{W}_{turn}.png"
    print(f"{label}: face {face}, box {b['x0']}-{b['x1']} x {b['y0']}-{b['y1']}, node ({r},{c}), point x {x:.0f} y {y:.0f} z {z:.0f}")
    # other turns first (cyan), the candidate last (magenta) so it is drawn on top of its own entry in the glob
    subprocess.run([PY, f"{S}/cross_section.py", png, "z", str(z), "0",
                    str(x - HALF), str(x + HALF), str(y - HALF), str(y + HALF), "--",
                    f"other turns=/workspace/flat/{base}/mesh/w*", f"candidate {label}={mesh}"], check=False,
                   env={**os.environ, "XS_COLOURS": "255,220,0;255,0,255"})
