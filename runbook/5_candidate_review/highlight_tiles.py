"""highlight_tiles.py <tiles dir>... - yellow ink highlight for the human's review, in the
style of the PHerc. 343 First Letters announcement figure: "the average of the four models, in yellow over a dimmed CT
so the fibres stay visible". The four models are the winner's: ink_9um seeds 42 and 43 (our hybrid_3d2d-seed42/43),
Hecate and dense_native; each tile (written by review_images.py) is that model's probability, max over depth, on the
shared 0..1 scale. Pale yellow, opacity ramping from 0 at LO to full at HI so weak evidence stays hidden.
Writes highlight.png next to the tiles. A reading aid only: it shows where the models agree on ink, not which letter."""
import os, sys
import cv2
import numpy as np

MODELS = ("hybrid_3d2d-seed42", "hybrid_3d2d-seed43", "hecate", "dnative")
LO, HI = float(os.environ.get("HL_LO", 0.45)), float(os.environ.get("HL_HI", 0.60))
DIM, YELLOW = 0.45, np.array([130, 220, 245], np.float32)  # BGR pale yellow, as in the 343 figure

for d in sys.argv[1:]:
    scan = cv2.imread(f"{d}/scan.png", 0)
    probs = [cv2.imread(f"{d}/{m}.png", 0) for m in MODELS]
    if scan is None or any(p is None or p.shape != scan.shape for p in probs):
        print(f"skip {d}: scan or a model tile missing / different size"); continue
    avg = np.mean([p / 255.0 for p in probs], axis=0)
    a = np.clip((avg - LO) / (HI - LO), 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), 1.5)[..., None]  # soft edges
    grey = np.repeat(scan[..., None], 3, 2).astype(np.float32) * DIM
    cv2.imwrite(f"{d}/highlight.png", (grey * (1 - a) + YELLOW * a).astype(np.uint8))
    print(f"ok {d}")
