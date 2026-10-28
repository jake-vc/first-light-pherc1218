"""Does the prereg screen trigger (4 mm x 4 mm window mean >= control letter-box median) fire on the 343 letters?"""
import json, sys, numpy as np, tifffile, cv2
N = "concat_w047-w048_R5B2_z9500-11000"; W = 463  # 4 mm at 8.64 um
a = json.load(open(f"/workspace/pherc343/outputs/{N}.json"))["area"]["raw_render_px"]
boxes = json.load(open(f"/workspace/pherc343/inputs/{N}_letter_boxes.json"))["letters"]
for model, d, thr, mdir in [("readerv2", 0, 0.3608, "maps"), ("dnative", 0, 0.4235, "maps2")]:
    s = 25 + d
    p = tifffile.imread(f"/workspace/ctrl/{mdir}/{N}_66__{model}__L66s{s}_reverse.tif").astype(np.float32) / 255
    valid = np.zeros(p.shape, np.float32); valid[a["row0"]:a["row1"], a["col0"]:a["col1"]] = 1
    num = cv2.boxFilter(p * valid, -1, (W, W), normalize=False); den = cv2.boxFilter(valid, -1, (W, W), normalize=False)
    m = np.where(den > 0.9 * W * W, num / np.maximum(den, 1), 0)
    letters = np.zeros(p.shape, bool)
    for b in boxes:
        x0, y0, x1, y1 = [int(round(v)) for v in b["box"]]; letters[y0:y1, x0:x1] = True
    hit = m >= thr
    print(model, "thr", thr, "max 4mm-window mean %.3f" % m.max(), "| window centres over threshold: %d px" % hit.sum(),
          "| of which on letters: %d" % (hit & letters).sum())
