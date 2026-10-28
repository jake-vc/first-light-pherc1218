# Coverage: what was screened, and how to find a spot

## In short

- The scan has 23,247 slices. I fitted slices 1,380-20,960, windings 10 to 129 (counted from the centre outwards).
- **Main pass:** 3,095 cm² in 511 turns, every turn with at least 70% of its surface on the predicted papyrus sheet.
- **Exploratory pass:** 4,788 cm² in 615 other turns, at 60-70% on the sheet, reported separately. The two passes do
  not overlap: together they screened 7,883 cm² in 1,126 turns.
- Band C (slices 10,040-15,680) is the only band where every window got its main pass.

## By band

The fits run in 1,000-slice windows that overlap by 460 slices. Areas are papyrus actually rendered and screened.

| Band | Slices | Main pass | Exploratory pass |
|---|---|---|---|
| E | 1,380-9,620 | 15 turns, 59 cm² | 286 turns, 2,582 cm² |
| A | 9,700-10,500 | 1 turn, 8 cm² | — |
| C | 10,040-15,680 | 470 turns, 2,887 cm² | 15 turns, 84 cm² |
| D | 15,220-20,960 | 25 turns, 140 cm² | 314 turns, 2,122 cm² |
| **Total** | | **511 turns, 3,095 cm²** | **615 turns, 4,788 cm²** |

Seam strips (where two consecutive windings meet) were screened for some windows: 101 strips, 158 cm².

## Not covered

- The two ends of the scroll: slices 0-1,380 and 20,960-23,247.
- The centre (inside winding 10) and anything outside winding 129.
- Any turn with less than 60% on the sheet: "no data", not "no ink".
- Windows E3, E4, E10, E11, E14, E15, E16, D8 and D10: the main pass ran, but no turn reached 70% on the sheet, and
  the exploratory pass (60-70%) was not run there; only a few seam strips in E4 and D8 were screened.
- Most seams.

## Reading a label

Every spot is named `<window><pass>/w<winding>`. For example, `C3f/w049` is:
- `C3`: band C, window 3, slices 11,120-12,120 (table below);
- `f`: main pass, on flattened meshes;
- `w049`: winding 49, counted from the centre outwards.

| Pass ending | Meaning |
|---|---|
| `f` | main pass (>= 70% on the sheet), flattened meshes |
| `x` | exploratory pass (60-70% on the sheet) |
| `s`, `sx` | seam strip, main or exploratory |
| none | first pass on unflattened meshes; replaced by `f`, area not counted |

Windows that had turns screened:

| Band C | Slices | Band D | Slices | Band E | Slices |
|---|---|---|---|---|---|
| C1 | 10,040-11,040 | D1 | 15,220-16,220 | E2 | 8,620-9,620 |
| C2 | 10,580-11,580 | D2 | 15,760-16,760 | E5 | 7,000-8,000 |
| C3 | 11,120-12,120 | D3 | 16,300-17,300 | E6 | 6,460-7,460 |
| C4 | 11,660-12,660 | D4 | 16,840-17,840 | E7 | 5,920-6,920 |
| C5 | 12,200-13,200 | D5 | 17,380-18,380 | E8 | 5,380-6,380 |
| C6 | 12,740-13,740 | D6 | 17,920-18,920 | E9 | 4,840-5,840 |
| C7 | 13,280-14,280 | D7 | 18,460-19,460 | E12 | 3,220-4,220 |
| C8 | 13,820-14,820 | D9 | 19,540-20,540 | E13 | 2,680-3,680 |
| C9 | 14,360-15,360 | | | | |
| C10 | 14,680-15,680 | | | | |

Band A is one window, slices 9,700-10,500.

## Finding a spot

[`analysis/spot_locations.tsv`](analysis/spot_locations.tsv) has one row for each of the 29 spots that got a detail
review: its mesh, the face it was read from, its box in the mesh's render (pixels), its slices, its angle around the
scroll axis and the human verdicts. To look at one:

1. **Get the mesh** from the Hugging Face dataset (https://huggingface.co/datasets/Jake-Vc/first-light-pherc1218): `flat/<window>/mesh/<mesh name>`. Each mesh is a folder with
   `x.tif`, `y.tif` and `z.tif` (the 3D position of every mesh point).
2. **Render the box** with VC3D against the public volume:
   ```bash
   vc_render_tifxyz --volume <public volume url> --segmentation <mesh folder> --scale 1 --num-slices 66 \
     --crop-x <box_x> --crop-y <box_y> --crop-width <box_w> --crop-height <box_h> --zarr-output spot.zarr
   ```
3. **Turn a pixel into scroll coordinates:** one mesh point every 20 render pixels, so pixel (px, py) of that render
   is mesh row (box_y + py) / 20, column (box_x + px) / 20; read `x.tif`, `y.tif`, `z.tif` there.

The angle is measured around the scroll axis in `fits/fit1218C/umbilicus.json` (Hugging Face).

Any other flagged turn: its label gives the window and winding, so the mesh; its flagged squares are `flag_boxes` in
`screen/<label>/stats.json` on Hugging Face. Those are in the screen render's frame: add the crop origin in
`render_crop.txt` (same folder) to get the box for step 2.
