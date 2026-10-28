"""review_page.py - build evidence/P8/review_page.html: one local page to judge every flagged turn quickly.
Runs on a local machine against a copy of the pod outputs (paths set at the top). Reads (summary.jsonl,
sheet.png, review/*/panel_*.png). Main-pass flags (<W>f) first, then the rest; strongest first (largest share of the
turn where 2 of 3 models agree, either face). Verdicts are kept in the browser and exported as ink_verdicts.json.
Rerun after each backup to pick up new flags and review panels (verdicts already given are kept by label)."""
import glob, json, os, re

K = os.path.expanduser("~/vesuvius-kit"); E = f"{K}/evidence/P8"; M = f"{E}/pod_mirror"
PASS = {"f": "main (flattened, >=70%)", "": "first pass (unflattened)", "x": "exploratory (60-70%)",
        "s": "seam strip", "sx": "exploratory seam"}
items = []
SHEETS = {}  # screen window -> turn (wNNN) -> contact sheet, for every screened turn (flagged or not): neighbour view
for summ in sorted(glob.glob(f"{M}/*/screen/*/summary.jsonl")):
    wdir = os.path.dirname(summ); W = os.path.basename(wdir)
    m = re.fullmatch(r"([A-Z]+\d*)(f|x|s|sx)?", W)
    if not m or W.startswith("TEST") or W.startswith("CTRL"):
        continue
    SHEETS[W] = {os.path.basename(os.path.dirname(p)): os.path.relpath(p, E)
                 for p in sorted(glob.glob(f"{wdir}/w*/sheet.png"))}
    boxes = {}  # winding -> detailed review panels
    cand = set()  # windings with a candidate (human-flagged) detail review
    lights = {}  # winding -> yellow highlights (highlight_tiles.py), target first, then the neighbour turns
    for b in sorted(glob.glob(f"{wdir}/review/w*_*") + glob.glob(f"{wdir}/review_cand/w*_*")):  # automatic + candidate reviews
        w = os.path.basename(b).split("_")[0]
        boxes.setdefault(w, []).extend(os.path.relpath(p, E) for p in sorted(glob.glob(f"{b}/panel_*.png")))
        if "/review_cand/" in b: cand.add(w)
        hl = sorted(glob.glob(f"{b}/*/tiles/highlight.png"), key=lambda p: "/target/" not in p)
        lights.setdefault(w, []).extend(os.path.relpath(p, E) for p in hl)
    for line in open(summ):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if not r.get("candidate"):
            continue
        w = r["label"].split("/")[1]
        sheet = f"{wdir}/{w}/sheet.png"
        hf = r.get("both_models_hit_frac", {})
        items.append({"label": r["label"], "window": m.group(1), "pass": PASS[m.group(2) or ""],
                      "main": m.group(2) == "f", "cm2": r.get("valid_cm2"),
                      "fwd": hf.get("forward", 0), "rev": hf.get("reverse", 0),
                      "sheet": os.path.relpath(sheet, E) if os.path.exists(sheet) else None,
                      "panels": boxes.get(w, []), "lights": lights.get(w, []), "cand": w in cand,
                      "whole": next((os.path.relpath(p, E) for p in glob.glob(f"{M}/*/screen/{W}/{w}/whole_yellow.png")), None),
                      "xsec": (f"candidates_xsec/{m.group(1)}{m.group(2) or ''}_{w}.png"
                               if os.path.exists(f"{E}/candidates_xsec/{m.group(1)}{m.group(2) or ''}_{w}.png") else None)})
# same papyrus spot seen from two overlapping windows (dup_check.py; >= 20 % within 0.5 mm = same spot)
same = {}
dc = f"{E}/candidate_checks/dup_check.tsv"
for r in (open(dc).read().splitlines()[1:] if os.path.exists(dc) else []):
    a, b, frac = r.split("\t")[:3]
    if float(frac) >= 0.2:
        same.setdefault(a, []).append(b); same.setdefault(b, []).append(a)
for i in items:
    i["same"] = same.get(i["label"], [])
# "Your candidates" = main-pass flags with a candidate review, plus every main-pass flag the human marked as anything but
# "not ink" in the latest exported verdicts (evidence/P8/verdicts/*.json), e.g. ones reviewed by older runs
vfiles = sorted(glob.glob(f"{E}/verdicts/*.json"), key=os.path.getmtime)
marked = {r["label"] for r in json.load(open(vfiles[-1])) if r.get("v") not in (None, "no")} if vfiles else set()
for i in items:
    i["cand"] = i["cand"] or (i["main"] and i["label"] in marked)
items.sort(key=lambda i: (not i["main"], -max(i["fwd"], i["rev"])))
# per letter turn: its reverse-face ink panels, then the raw CT along the same surface (cropped from the control sheets)
ctrl = [p for w in ("w047", "w048") for p in (f"ctrl343_images/ref_{w}_readerv3_reverse.png",
        f"ctrl343_images/ref_{w}_readerv2_reverse.png", f"ctrl343_images/ref_{w}_ct.png") if os.path.exists(f"{E}/{p}")]
ctrl = [p for p in ["ctrl343_images/announce_343_yellow.png"] if os.path.exists(f"{E}/{p}")] + ctrl  # the announcement figure first
# then PHerc. 343's real letter turns run through our own candidate review (job review_R343): yellow views made exactly
# like the candidates', the like-for-like reference
ctrl = ctrl[:1] + [os.path.relpath(p, E) for p in sorted(glob.glob(f"{M}/c1/screen/R343/review_cand/*/target/tiles/highlight.png"))] + ctrl[1:]
html = open(f"{K}/work/pod/review_page_template.html").read()
html = html.replace("/*DATA*/", "const ITEMS = " + json.dumps(items) + "; const CTRL = " + json.dumps(ctrl) + "; const SHEETS = " + json.dumps(SHEETS) + ";")
open(f"{E}/review_page.html", "w").write(html)
print(f"{len(items)} flagged turns ({sum(i['main'] for i in items)} main pass, "
      f"{sum(bool(i['panels']) for i in items)} with detail panels) -> {E}/review_page.html")
