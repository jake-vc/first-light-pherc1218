# Analysis

- [`ink_verdicts.json`](ink_verdicts.json): human verdict on every flagged turn (557), exported from the review page.
- [`later_verdicts.json`](later_verdicts.json): human verdicts given after that export, from the detail panels and the
  depth sweeps.
- [`same_scale_comparison.png`](same_scale_comparison.png): PHerc. 343's letters, the four strongest 1218 candidates
  and plain papyrus at the same scale and normalisation.
- [`size_vs_343.md`](size_vs_343.md): mark size on 343's letters and on every 1218 candidate, measured the same way.
- [`dup_check.tsv`](dup_check.tsv): same-spot check between the reviewed candidate boxes (3D overlap and distance); one
  pair, C10f/w021 and C9f/w026, is the same spot and counts once.
- [`spot_locations.tsv`](spot_locations.tsv): where each spot of the detail review is: mesh, face, box in the full
  render, slice range, angle around the scroll axis, verdicts (how to use it: top-level README, "Finding a spot").
- [`model_sha256.txt`](model_sha256.txt): sha256 of every model checkpoint used.
