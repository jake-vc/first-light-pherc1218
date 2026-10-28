# Decisions, problems and known gaps

## Main decisions
- **Target PHerc. 1218:** scanned in the same session and protocol as PHerc. 343, with the same surface and normal
  predictions available, and no public ink search found.
- **My own meshes:** the public 1218 meshes have a median 16% of their surface on the predicted sheet; the winner's
  343 meshes have 71-75%.
- **The 343 winner's fitting chain** (villa `0fb38c45`): the only chain shown to give readable letters on a scroll
  from this session; villa main no longer has its spacing mode.
- **Scope:** a turn is screened when >= 70% of it lies on the sheet and it covers >= 1 cm² (calibrated on the winner's
  meshes, 71-75%). Below that a turn mostly images the gaps between sheets.
- **Windows:** 1,000 slices each, overlapping by 460 slices (4 mm) so a letter is not cut at a window edge; 10,000
  fit steps per window (the loss was still falling slightly at the end, so placement was checked directly).
- **Flatten before rendering**, as the winner did: the ink models were trained on evenly spaced surfaces; unflattened,
  my meshes were stretched up to ~3.5×.
- **Screen:** reader-v3, dense_native and reader-v2 with thresholds from the 343 control; a spot counts when 2 of 3
  agree in the same 4 mm square.
- **Human review:** every flag judged by eye; the ink-like ones re-rendered at full resolution with both neighbouring
  turns, six models and depths -8..+8; the strongest five swept over depths -15..+15.
- **Held-out refit dropped:** not a First Letters requirement (no model was trained on this scroll) and not worth
  its cost; a surface-integrity check at each candidate instead.
- **Fixed method:** inference batch size 4 throughout; the screen gives the same result on current villa main
  (reader-v3 byte-identical; the others within 1/255 on < 0.3% of pixels).

## Problems and fixes
- **The shared disk filled twice:** fits and screens died mid-write. Bigger volume, everything affected rerun, every
  copy size-checked; a turn with missing model maps is never scored.
- **VC3D's download cache filled the pod disks:** the command-line tools have no cache limit. Trimmed by script, and
  fixed upstream in [ScrollPrize/villa#2290](https://github.com/ScrollPrize/villa/pull/2290).
- **Ink inference ran 3-7× slow:** a coarse occupancy scan and thread caps brought a map pair from 250-750 s to ~100 s.
- **Dead workers left claimed turns:** claims older than 45 minutes without a result are released.
- **Neighbour boxes near a mesh seam spanned a whole turn:** the review keeps only the largest connected piece.

## Known gaps
- The seam pass is partial: about 2 mm each side of some winding seams was not screened.
- Turns under 70% on the sheet are "no data", not "no ink"; 60-70% was screened only as an exploratory pass.
- The depth sweep was not run on plain 1218 papyrus or on 343's letters as a reference.
