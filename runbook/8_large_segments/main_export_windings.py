"""main_export_windings.py <checkpoint> <out dir> <umbilicus.json> <first> <last> - export a villa-MAIN spiral checkpoint
as one tifxyz per winding (w010, w011, ...), using main's own flatten_spiral_checkpoint reconstruction but without its
Lasagna flatten, so the windings can go through the same snap + on-sheet check as our August fits.
Run from main's spiral-fitting folder with its venv. Main's in-fit export found no windings because its range comes from
patches / point collections, which PHerc1218 does not have; here the range is given explicitly."""
import sys
from pathlib import Path

import torch

import flatten_spiral_checkpoint as fsc
from checkpoint_io import load_checkpoint_cpu

ck_path, out, umb, first, last = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
checkpoint = load_checkpoint_cpu(ck_path)
config = fsc._checkpoint_config(checkpoint)
config["preview_first_winding"] = first
checkpoint["preview_first_winding"] = first
config["shell_outer_winding_idx"] = last
orig_save = fsc.save_combined_tifxyz


def per_winding(winding_grids, destination, surface_id, step, voxel_size_um, **kw):
    manifest = None
    for w, grid in sorted(winding_grids.items()):
        kw["first_winding"] = w
        name = f"w{w:03d}_main"  # main's save_combined_tifxyz writes the surface AT destination (must not exist)
        manifest = orig_save({w: grid}, Path(destination) / name, name, step, voxel_size_um, **kw)
        print(f"saved w{w:03d}", flush=True)
    return manifest


fsc.save_combined_tifxyz = per_winding
out.mkdir(parents=True, exist_ok=True)
fsc._export_source_surface(checkpoint, config, umb, out, device=torch.device("cuda"), voxel_size_um=8.64, chunk_size=65536)
print("done", flush=True)
