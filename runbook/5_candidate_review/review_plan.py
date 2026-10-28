"""review_plan.py <screen dir> <umbilicus.json> [max_boxes] - plan the detail review of flagged screen areas.
For every turn whose stats.json is a candidate: merge its flag boxes (per direction), pad 2 mm, and map each box to
 - the turn's own full-render pixel frame (screen render was auto-cropped: add the recorded crop origin),
 - the same theta/z region on the neighbouring turns w-1 / w+1 (mesh nodes: 20 render px per node; theta about the
   Dopico axis at each node's z; largest connected piece, so a region across the neighbour's seam is not a whole-turn box),
 - an edge flag when the box's z range lies within 2 mm of the turn's top/bottom (letters may be cut: taller refit).
Writes <screen dir>/review/plan.json: list of render jobs {turn, mesh, x, y, w, h, role, direction, box_id, edge}."""
import glob, json, math, os, re, sys
import numpy as np, tifffile
from scipy import ndimage

sd, umb = sys.argv[1], sys.argv[2]; max_boxes = int(sys.argv[3]) if len(sys.argv) > 3 else 12
PX = 20; PAD = 231; EDGE = 231  # render px per mesh node; 2 mm at 8.64 um
pts = sorted(json.load(open(umb))["control_points"], key=lambda c: c["z"])
AZ, AX, AY = (np.array([p[k] for p in pts], float) for k in ("z", "x", "y"))


def load(mesh):
    x, y, z = (tifffile.imread(f"{mesh}/{c}.tif").astype(np.float64) for c in "xyz")
    v = (x > -0.5) & (y > -0.5) & (z > -0.5)
    th = np.full(x.shape, np.nan); th[v] = np.arctan2(y[v] - np.interp(z[v], AZ, AY), x[v] - np.interp(z[v], AZ, AX))
    return x, y, z, v, th


def merge(boxes):
    boxes = [list(b) for b in boxes]; changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]:
                    boxes[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]), a[4] + b[4]]
                    del boxes[j]; changed = True; break
            if changed: break
    return boxes


items = []
for st in glob.glob(f"{sd}/w*/stats.json"):
    s = json.load(open(st)); d = os.path.dirname(st)
    if not s.get("candidate"): continue
    crop = open(f"{d}/render_crop.txt").read() if os.path.exists(f"{d}/render_crop.txt") else ""
    m = re.search(r"from \((\d+),(\d+)\)", crop); ox, oy = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    mesh = open(f"{d}/mesh_path.txt").read().strip()
    for direction in ("forward", "reverse"):
        bs = [(b["x0"] + ox, b["y0"] + oy, b["x1"] + ox, b["y1"] + oy, (b["x1"] - b["x0"]) * (b["y1"] - b["y0"]))
              for b in s.get("flag_boxes", []) if b["direction"] == direction]
        for b in merge(bs):
            items.append((b[4], os.path.basename(d), mesh, direction, b))
items.sort(key=lambda t: -t[0])
# ONLY_TURNS="w023 w065": review just these turns (e.g. the human's ink verdicts), largest flagged area of each only
only = os.environ.get("ONLY_TURNS", "").split()
if only:
    seen = set()
    items = [t for t in items if t[1] in only and not (t[1] in seen or seen.add(t[1]))]
    max_boxes = len(items)
sub = os.environ.get("REVIEW_SUBDIR", "review")  # separate folder: box ids restart at 0 and must not reuse old results
jobs = []
for k, (_, turn, mesh, direction, b) in enumerate(items[:max_boxes]):
    x, y, z, v, th = load(mesh)
    H, W = v.shape
    x0, y0, x1, y1 = max(0, b[0] - PAD), max(0, b[1] - PAD), min(W * PX, b[2] + PAD), min(H * PX, b[3] + PAD)
    r0, r1, c0, c1 = y0 // PX, -(-y1 // PX), x0 // PX, -(-x1 // PX)
    sel = v[r0:r1, c0:c1]
    zz, tt = z[r0:r1, c0:c1][sel], th[r0:r1, c0:c1][sel]
    if zz.size == 0: continue
    zt0, zt1 = zz.min(), zz.max(); ref = float(np.angle(np.mean(np.exp(1j * tt))))
    dt = np.angle(np.exp(1j * (tt - ref))); dt0, dt1 = dt.min(), dt.max()
    edge = bool(zt0 - z[v].min() < EDGE or z[v].max() - zt1 < EDGE)
    bid = f"{turn}_{direction[0]}{k}"
    jobs.append(dict(box_id=bid, role="target", turn=turn, mesh=mesh, direction=direction, x=x0, y=y0, w=x1 - x0, h=y1 - y0,
                     edge=edge, z_range=[float(zt0), float(zt1)], theta_deg=[math.degrees(ref + dt0), math.degrees(ref + dt1)]))
    n = int(re.match(r"w(\d+)", turn).group(1))
    for nb in (n - 1, n + 1):
        cand = glob.glob(os.path.join(os.path.dirname(mesh), f"w{nb:03d}_*")) or glob.glob(os.path.join(os.path.dirname(mesh), f"w{nb}_*"))
        if not cand:
            jobs.append(dict(box_id=bid, role=f"w{nb:03d}", missing=True)); continue
        X, Y, Z, V, TH = load(cand[0])
        hit = V & (Z >= zt0) & (Z <= zt1) & (np.abs(np.angle(np.exp(1j * (TH - ref)))) <= max(abs(dt0), abs(dt1)))
        if not hit.any():
            jobs.append(dict(box_id=bid, role=f"w{nb:03d}", missing=True)); continue
        # A theta window that straddles the neighbour's seam (+-180 deg) matches nodes at both ends of its grid; one
        # bounding box would then span the whole turn. Keep the largest connected piece; "partial" when another piece
        # holds >= 20% as many nodes (the rest of the region lies across the seam).
        lab, n = ndimage.label(hit, structure=np.ones((3, 3)))
        sizes = ndimage.sum(hit, lab, range(1, n + 1)); order = np.argsort(sizes)[::-1]
        rr, cc = np.nonzero(lab == order[0] + 1)
        partial = bool(n > 1 and sizes[order[1]] >= 0.2 * sizes[order[0]])
        jobs.append(dict(box_id=bid, role=f"w{nb:03d}", turn=os.path.basename(cand[0]).split("_")[0], mesh=cand[0], direction=direction,
                         x=int(cc.min()) * PX, y=int(rr.min()) * PX, w=int(cc.max() - cc.min() + 1) * PX, h=int(rr.max() - rr.min() + 1) * PX,
                         partial=partial))
os.makedirs(f"{sd}/{sub}", exist_ok=True)
json.dump(jobs, open(f"{sd}/{sub}/plan.json", "w"), indent=1)
print(f"{len(items)} flagged areas, {sum(j['role'] == 'target' for j in jobs)} planned (max {max_boxes}), {len(jobs)} render jobs")
