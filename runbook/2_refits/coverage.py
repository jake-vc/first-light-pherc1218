"""coverage.py - screened papyrus per window and pass, from the result files only (every non-empty stats.json under
/workspace/screen). Pass: P = preregistered flattened (<W>f), U = unflattened first pass (<W>), X = exploratory 0.60-0.70
(<W>x), S = seams (<W>s), SX = exploratory seams (<W>sx). Prints a TSV: window, then layers and cm2 per pass."""
import glob, json, os, re, collections
T = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0.0]))
for f in glob.glob("/workspace/screen/*/w*/stats.json"):
    if "TEST" in f or not os.path.getsize(f): continue
    b = f.split("/")[-3]; m = re.fullmatch(r"([A-Z]\d*)(f|x|s|sx)?", b)
    if not m: continue
    w, k = m.group(1), {"f": "P", "x": "X", "s": "S", "sx": "SX", None: "U"}[m.group(2)]
    s = json.load(open(f)); T[w][k][0] += 1; T[w][k][1] += s.get("valid_cm2", 0)
keys = ["P", "U", "X", "S", "SX"]; print("window\t" + "\t".join(f"{k}_layers\t{k}_cm2" for k in keys))
tot = {k: [0, 0.0] for k in keys}
for w in sorted(T, key=lambda x: (x[0], int(x[1:]) if x[1:] else 0)):
    print(w + "\t" + "\t".join(f"{T[w][k][0]}\t{T[w][k][1]:.0f}" for k in keys))
    for k in keys: tot[k][0] += T[w][k][0]; tot[k][1] += T[w][k][1]
print("TOTAL\t" + "\t".join(f"{tot[k][0]}\t{tot[k][1]:.0f}" for k in keys))
