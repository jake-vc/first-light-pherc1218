# Mark size: candidates vs PHerc. 343's real letters, same pipeline

Method (`runbook/7_artifact_checks/shape_stats.py`): the yellow-view map (average of the winner's four
models, max over depth -8..+8, each depth reading 17 layers) thresholded at 0.5; marks = connected areas >= 400 px
(~0.03 mm²); height/width = bounding box; stroke = 2 x median distance-to-edge along the skeleton; 8.64 µm/px.
343 boxes: my exact candidate-review pipeline on the public PHerc. 343 letter turns w047/w048.

| box | papyrus mm² | marks | ink share | height median mm | width median mm | stroke median mm | height p90 mm |
|---|---|---|---|---|---|---|---|
| **343/w047 (letters)** | 236.4 | 31 | 0.126 | 0.59 | 0.49 | 0.12 | **2.17** |
| **343/w048 (letters)** | 70.3 | 7 | 0.137 | 0.54 | 0.69 | 0.18 | **2.55** |
| C4f/w038 | 79.9 | 18 | 0.079 | 0.49 | 0.56 | 0.10 | 1.57 |
| C4f/w059 | 70.8 | 30 | 0.138 | 0.45 | 0.51 | 0.09 | 1.39 |
| C2f/w081 | 110.4 | 23 | 0.075 | 0.56 | 0.44 | 0.11 | 1.36 |
| C9f/w026 | 100.7 | 23 | 0.076 | 0.48 | 0.47 | 0.10 | 1.22 |
| C5f/w073 | 69.2 | 24 | 0.110 | 0.41 | 0.39 | 0.11 | 1.16 |
| C8f/w062 | 58.9 | 22 | 0.107 | 0.41 | 0.47 | 0.11 | 1.10 |
| C10f/w021 (same spot as C9f/w026) | 76.9 | 29 | 0.104 | 0.45 | 0.44 | 0.10 | 0.96 |
| C2f/w084 | 106.3 | 48 | 0.122 | 0.52 | 0.50 | 0.10 | 0.87 |
| C4f/w050 | 133.0 | 41 | 0.081 | 0.42 | 0.53 | 0.10 | 0.83 |
| C2f/w090 | 99.9 | 30 | 0.061 | 0.40 | 0.42 | 0.09 | 0.82 |
| C4f/w049 | 102.3 | 28 | 0.092 | 0.38 | 0.42 | 0.09 | 0.76 |
| C10f/w038 | 98.9 | 18 | 0.035 | 0.43 | 0.51 | 0.10 | 0.74 |
| C5f/w057 | 108.1 | 24 | 0.035 | 0.46 | 0.41 | 0.10 | 0.74 |
| C7f/w035 | 60.1 | 12 | 0.046 | 0.48 | 0.57 | 0.13 | 0.70 |

Reading: the median mark is similar everywhere (small blobs dominate both), but the tallest marks differ: 343's real
letters reach 2.2-2.6 mm (p90), no candidate goes above 1.6 mm, and 11 of 14 stay under 1.4 mm; candidate strokes are
also thinner (0.09-0.13 vs 0.12-0.18 mm). With the method that finds 343's letters at their real size, the candidates
show no letter-sized marks. Caveats: one threshold (0.5); 343's w048 box is small (70 mm²); depth -8..+8 only
(the depth sweep adds -15..+15); size alone cannot rule a letter in or out; the human verdict decides.
