# Runbook

Every script that produced a result, copied as run and grouped by step. They expect a RunPod GPU pod with a network
volume at `/workspace` and call each other from one folder, so to run them copy every script into
`/workspace/p8/scripts` (job markers go to `/workspace/p8/state`, logs to `/workspace/p8/out`). Every long step was
started through the launcher, which runs a job at most once at a time and records done / failed:

```bash
cd /workspace/p8 && setsid nohup bash scripts/launch.sh <job name> <command...> >/dev/null 2>&1 </dev/null &
```

**Software versions**

| What | Version |
|---|---|
| Spiral fit and ink inference (as the 343 winner) | villa `0fb38c45` |
| Fit for the large segments | villa main `e2254eb` |
| Renderer (bit-identical on the control) | VC3D `359bbed` and main `15db7cd` |
| Model checkpoints | sha256 in [`../analysis/model_sha256.txt`](../analysis/model_sha256.txt) |

**Data** (all public)
- PHerc. 1218 volume `20250521120456-8.640um-1.2m-116keV-masked`, with its m7 surface prediction, lasagna fields and
  umbilicus.
- PHerc. 343's published letter segment, for the positive control.

| Step | Folder | Scripts |
|---|---|---|
| 0. Pod setup | [`0_pod_setup/`](0_pod_setup/) | `setup_pod.sh` (the winner's ink environment), `setup_extra.sh` (VC3D, spiral fit, the winner's shell-optional patch), `aptlibs.sh` |
| 1. Positive control on 343 | [`1_control/`](1_control/) | `ctrl343.sh` (inputs), `ctrl_343.sh` / `ctrl_v3.sh` (render + screen models), `calib_343.py` (letter vs background), `win4mm_343.py` (4 mm trigger), `letters_343.py` (neighbouring-sheet reference) |
| 2. Inputs and refits | [`2_refits/`](2_refits/) | `fetch_band.sh` + `fetch_subzarr.py`, `prep_band.sh` (`prep_C.sh` for band C), `fits_band.sh` → `run_fit.sh` per 1,000-slice window, `coverage.py` (share on the sheet) |
| 3. Flatten and screen | [`3_flatten_screen/`](3_flatten_screen/) | `flatten_pool.sh` / `flatten_one.sh`, `screens_band.sh` / `screen_pool.sh` → `screen_1218.sh` (claims windings) → `screen_one.sh` (66-layer render, three models), `screen_sheet.py` (2-of-3 flag rule), `seam_strip.py` / `seam_pool.sh` (partial seam pass) |
| 4. Human review of every flag | [`4_human_review/`](4_human_review/) | `review_page.py` + `review_page_template.html` (one page, verdicts exported as JSON), `cross_section.py` / `cand_xsec.py` (surface in the CT) |
| 5. Detail review | [`5_candidate_review/`](5_candidate_review/) | `review_plan.py` → `review_run.sh` (full-resolution box and both neighbours, six models, d -8..+8), `review_images.py` (panels), `highlight_tiles.py` / `whole_turn_yellow.*` (yellow view) |
| 6. Depth sweep | [`6_depth_sweep/`](6_depth_sweep/) | `confirm_box.sh` (six models, d -15..+15; `hecate_prep.py` for Hecate), `confirm_images.py` (z-score ensemble per depth) |
| 7. Checks against artifacts | [`7_artifact_checks/`](7_artifact_checks/) | `shape_stats.py` (mark size vs 343's letters), `dup_check.py` (same spot from two windows) |
| 8. Large segments | [`8_large_segments/`](8_large_segments/) | `autosteps_run.sh` (villa-main fit), `seg_export.sh` / `main_export_windings.py`, `seg_big.sh` + `seg_yellow.py`, `map_candidates.py` / `box_in_segment.py` (locate a box), `box_sweep.sh` (depth sweep there) |
| 9. Figures | [`9_figures/`](9_figures/) | `same_scale.py` (same-scale comparison), `build_submission_images.py` (`renders/` and its index) |
| Shared | [`common/`](common/) | `launch.sh` (job launcher), `waitfor.sh` (wait for other jobs), `retry.sh`, `killtree.sh` (stop a job by exact PID), `run_ink.sh` (one model, both directions), `run_depth_sweep.sh` (all models over a depth range), `tests/launch_test.sh` |

Usage of each script is in its header comment. Two run on a local machine against a copy of the pod outputs, with
paths set at the top: `review_page.py` and `build_submission_images.py`. `setup_pod.sh` also calls two scripts from other repositories: lasagna's `scripts/bootstrap_venv.py` (villa) and the 343 winner's `ink/scripts/fetch_checkpoints.sh` (pherc343-first-letters).
