# Readout rules — PHerc. 1218

Fixed before the first ink run on PHerc. 1218. Each later change was made before the results it affected and is
listed under "Deviations" in the top-level README.

- **Positive control first.** The same render and ink stack runs on PHerc. 343's published letter segment (same scan
  session; no model trained on 343). Pass: letters legible by eye and a letter-vs-background separation >= 0.10 for at
  least two models. Result: pass (reader-v3 0.149, dense_native 0.129, reader-v2 0.102).
- **Scope.** A turn is screened when >= 70% of its flattened mesh lies within ±2 voxels of the predicted sheet (the
  winner's own 343 meshes score 71-75%). Turns below that are "no data", not "no ink". Turns at 60-70% are screened as
  an exploratory pass and reported separately.
- **Surfaces.** The 343 winner's fitting chain; every winding flattened before the 66-layer render, as the winner did.
- **Screen.** reader-v3, dense_native and reader-v2 on the reading side, at the surface.
- **A flag.** In a 4 mm × 4 mm window, the mean ink probability reaches that model's median inside 343's letters, in at
  least 2 of the 3 models.
- **What can count as letters (judged by eye).** Stroke-like marks 1.5-6 mm tall, along a row roughly parallel to the
  horizontal fibres, not repeated at the same place on the neighbouring turns.
- **What does not count.** Tile seams, render borders, mesh folds or holes, specks under 0.5 mm, fibre-grid texture,
  signal in only one model or at only one depth.
- **Detail review.** Every ink-like turn of the main pass is re-rendered at full resolution with both neighbouring
  turns and six models (the winner's four, reader-v2, reader-v3) at depths -8..+8.
