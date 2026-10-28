"""build_submission_images.py <verdicts.json> <out dir> [later_verdicts.json] - collect every image of the ink-like spots for the submission.
Copies, never moves; source files are untouched. Reads the Mac's pod mirror
(evidence/P8/pod_mirror/<pod>/...) and evidence/P8, writes:
  <out>/candidates/<window>_<turn>/  whole-turn sheet view, whole-turn yellow view, review panels (target and both
                                     neighbouring turns), depth-sweep confirmation, cross-section, where they exist
  <out>/large_segments/<winding>/    whole-winding yellow view (full and 2000 px) and candidate boxes located in it
  <out>/control_343/                 PHerc. 343's known letters through the same pipeline (positive control)
  <out>/INDEX.md                     one row per spot: human verdict, note, files
Spots included: every verdict other than "not ink". later_verdicts.json: {spot: text} for verdicts the human gave
after the export (shown in their own column; the exported verdict is kept as it was). Fails if a file is over 95 MB (GitHub's limit is 100 MB)."""
import glob, json, os, shutil, sys
from pathlib import Path

E = Path.home() / "vesuvius-kit/evidence/P8"; MIRROR = E / "pod_mirror"
LABEL = {"letters": "letters", "maybe": "possible letter", "strokes": "ink, no letter", "ink": "ink (earlier scale)",
         "unsure": "unsure"}
ORDER = list(LABEL)
MAX_BYTES = 95 * 1024 * 1024
verdicts, out = json.load(open(sys.argv[1])), Path(sys.argv[2])
later = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
copied = []


def put(src, dst):
    src = Path(src)
    if not src.is_file():
        return None
    if src.stat().st_size > MAX_BYTES:
        sys.exit(f"too large for GitHub: {src} ({src.stat().st_size / 1e6:.0f} MB)")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not (dst.exists() and dst.stat().st_size == src.stat().st_size):
        shutil.copy2(src, dst)
    copied.append(dst)
    return dst


def screen_dir(window, turn):
    for pod in ("c1", "a"):
        d = MIRROR / pod / "screen" / window / turn
        if d.is_dir():
            return MIRROR / pod / "screen" / window, d
    return None, None


rows = []
spots = sorted((v for v in verdicts if v.get("v") in LABEL), key=lambda v: (ORDER.index(v["v"]), v["label"]))
for v in spots:
    window, turn = v["label"].split("/"); turn = turn.split("_")[0]
    D = out / "candidates" / f"{window}_{turn}"
    wdir, tdir = screen_dir(window, turn)
    files = []
    if tdir:
        for name, new in (("sheet.png", "turn_sheet.png"), ("whole_yellow.png", "turn_yellow.png")):
            files.append(put(tdir / name, D / new))
        for rc in sorted(glob.glob(f"{wdir}/review_cand/{turn}_*")):
            for p in sorted(glob.glob(f"{rc}/panel_*.png")):
                files.append(put(p, D / f"review_{Path(p).name}"))
            for name in ("confirm_depths.png", "confirm_max.png", "confirm.json"):
                files.append(put(f"{rc}/target/{name}", D / name))
    for pod in ("c1", "a"):
        files.append(put(MIRROR / pod / f"p8/out/candxsec/{window}_{turn}.png", D / "cross_section.png"))
    files = [f.name for f in files if f]
    rows.append(f"| {v['label']} | {LABEL[v['v']]} | {later.get(v['label'], '')} | {v.get('note', '').replace('|', '/')} | "
                f"{', '.join(files) if files else 'no images found'} |")

for w in sorted(p.name for p in (E / "seg_big").iterdir() if p.is_dir()):
    for f in (E / "seg_big" / w).rglob("*.png"):
        put(f, out / "large_segments" / w / f.relative_to(E / "seg_big" / w))

for f in sorted((E / "ctrl343_images").glob("ctrl343_*.png")) + sorted((E / "ctrl343_images").glob("ref_*.png")):
    put(f, out / "control_343" / f.name)
for p in sorted(glob.glob(f"{MIRROR}/c1/screen/R343/review_cand/*/panel_*.png")):
    put(p, out / "control_343" / f"review_{Path(p).parent.name}_{Path(p).name}")

index = ["# Renders index", "",
         "Every spot the human judged as anything other than \"not ink\" (verdict file in `analysis/`), strongest "
         "category first. File names:", "",
         "- `turn_sheet.png`: the whole flattened turn; `turn_yellow.png`: the winner's models in yellow over it",
         "- `review_panel_target.png` / `review_panel_wNNN.png`: the flagged box and the same place on both neighbouring "
         "turns, per model",
         "- `confirm_depths.png` / `confirm_max.png` / `confirm.json`: six-model ensemble at depths -15..+15 (shortlist)",
         "- `cross_section.png`: where the surface sits in the CT at that spot", "",
         "`large_segments/`: whole windings of an independent villa-main fit; `<box>/` subfolders are candidate boxes "
         "located in that winding (`*_mirrored.png`: flipped left-right to match the original orientation).",
         "`control_343/`: PHerc. 343's known letters through the same pipeline.", "",
         f"{len(spots)} spots, {len(copied)} files.", "",
         "| spot | human verdict (export) | later verdict | note | files |", "|---|---|---|---|---|"] + rows
(out / "INDEX.md").write_text("\n".join(index) + "\n")
total = sum(f.stat().st_size for f in set(copied))
print(f"{len(spots)} spots, {len(set(copied))} files, {total / 1e6:.0f} MB -> {out}")
