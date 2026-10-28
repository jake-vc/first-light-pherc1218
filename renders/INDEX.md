# Renders index

Every human judged spot as anything other than "not ink" (verdict file in `analysis/`), strongest category first. After detailed review, none of the spots appeared to have true ink, but this could serve as a good starting point for others with follow-on manual segmentation work or analysis.

File names:
- `turn_sheet.png`: the whole flattened turn; `turn_yellow.png`: the winner's models in yellow over it
- `review_panel_target.png` / `review_panel_wNNN.png`: the flagged box and the same place on both neighbouring turns, per model
- `confirm_depths.png` / `confirm_max.png` / `confirm.json`: six-model ensemble at depths -15..+15 (the five strongest)
- `cross_section.png`: where the surface sits in the CT at that spot

`large_segments/`: whole windings of an independent villa-main fit; `<box>/` subfolders are candidate boxes located in that winding (`*_mirrored.png`: flipped left-right to match the original orientation).
`control_343/`: PHerc. 343's known letters through the same pipeline.

73 spots, 227 files.

| spot | human verdict (export) | later verdict | note | files |
|---|---|---|---|---|
| C10f/w038 | possible letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w037.png, review_panel_w039.png, cross_section.png |
| C2f/w081 | possible letter | no (human, after seeing the box in large segment w083: "clear no") |  | turn_sheet.png, turn_yellow.png, review_panel_target.png, review_panel_w080.png, review_panel_w082.png, confirm_depths.png, confirm_max.png, confirm.json, cross_section.png |
| C2f/w084 | possible letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w083.png, review_panel_w085.png, cross_section.png |
| C2f/w090 | possible letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w089.png, review_panel_w091.png, cross_section.png |
| C2s/w021 | possible letter |  |  | turn_sheet.png |
| C3f/w049 | possible letter | possibly, really not sure (human, after the detail panels with both neighbouring turns) |  | turn_sheet.png, review_panel_target.png, review_panel_w048.png, review_panel_w050.png, confirm_depths.png, confirm_max.png, confirm.json |
| C4f/w038 | possible letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w039.png, cross_section.png |
| C4f/w049 | possible letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w048.png, review_panel_w050.png, cross_section.png |
| C4f/w050 | possible letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w049.png, cross_section.png |
| C4f/w059 | possible letter |  |  | turn_sheet.png, turn_yellow.png, review_panel_target.png, review_panel_w058.png, review_panel_w060.png, confirm_depths.png, confirm_max.png, confirm.json, cross_section.png |
| C5f/w057 | possible letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w058.png, cross_section.png |
| C5f/w073 | possible letter |  |  | turn_sheet.png, review_panel_target.png, cross_section.png |
| C6f/w026 | possible letter | possibly, really not sure (human, after the detail panels with both neighbouring turns) |  | turn_sheet.png, review_panel_target.png, review_panel_w025.png, confirm_depths.png, confirm_max.png, confirm.json |
| C7f/w035 | possible letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w034.png, review_panel_w036.png, cross_section.png |
| C8f/w062 | possible letter |  |  | turn_sheet.png, review_panel_target.png, cross_section.png |
| C9f/w026 | possible letter |  |  | turn_sheet.png, turn_yellow.png, review_panel_target.png, confirm_depths.png, confirm_max.png, confirm.json, cross_section.png |
| D7x/w069 | possible letter |  |  | turn_sheet.png |
| D7x/w085 | possible letter |  |  | turn_sheet.png |
| E2x/w077 | possible letter |  |  | turn_sheet.png |
| E6x/w102 | possible letter |  |  | turn_sheet.png |
| E7x/w067 | possible letter |  |  | turn_sheet.png |
| E7x/w095 | possible letter |  |  | turn_sheet.png |
| E7x/w099 | possible letter |  |  | turn_sheet.png |
| C10f/w021 | ink, no letter |  |  | turn_sheet.png, turn_yellow.png, review_panel_target.png, review_panel_w020.png, review_panel_w022.png, cross_section.png |
| C1f/w054 | ink, no letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w053.png, review_panel_w055.png, cross_section.png |
| C4f/w073 | ink, no letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w072.png, review_panel_w074.png, cross_section.png |
| C6f/w022 | ink, no letter | no letter (human, after the detail panels with both neighbouring turns) |  | turn_sheet.png, review_panel_target.png, review_panel_w021.png, review_panel_w023.png |
| C6f/w034 | ink, no letter | no letter (human, after the detail panels with both neighbouring turns) |  | turn_sheet.png, review_panel_target.png, review_panel_w033.png, review_panel_w035.png |
| C7f/w064 | ink, no letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w065.png, cross_section.png |
| C8f/w040 | ink, no letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w041.png, cross_section.png |
| C8f/w067 | ink, no letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w066.png, cross_section.png |
| C9f/w044 | ink, no letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w043.png, review_panel_w045.png, cross_section.png |
| C9f/w047 | ink, no letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w046.png, review_panel_w048.png, cross_section.png |
| C9f/w080 | ink, no letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w079.png, cross_section.png |
| D1f/w044 | ink, no letter |  |  | turn_sheet.png, review_panel_target.png, review_panel_w043.png, review_panel_w045.png, cross_section.png |
| Af/w066 | ink (earlier scale) |  |  | turn_sheet.png |
| Af/w067 | ink (earlier scale) |  |  | turn_sheet.png |
| Af/w087 | ink (earlier scale) |  |  | review_panel_target.png, review_panel_w086.png |
| C1f/w023 | ink (earlier scale) |  |  | turn_sheet.png, cross_section.png |
| C1f/w065 | ink (earlier scale) |  |  | turn_sheet.png, cross_section.png |
| C1f/w066 | ink (earlier scale) |  |  | turn_sheet.png, cross_section.png |
| D1x/w037 | ink (earlier scale) |  |  | turn_sheet.png |
| D1x/w038 | ink (earlier scale) |  |  | turn_sheet.png |
| D1x/w057 | ink (earlier scale) |  |  | turn_sheet.png |
| D1x/w060 | ink (earlier scale) |  |  | turn_sheet.png |
| D1x/w061 | ink (earlier scale) |  |  | turn_sheet.png |
| D1x/w067 | ink (earlier scale) |  |  | turn_sheet.png |
| D2x/w049 | ink (earlier scale) |  |  | turn_sheet.png |
| D3x/w044 | ink (earlier scale) |  |  | turn_sheet.png |
| D3x/w045 | ink (earlier scale) |  |  | turn_sheet.png |
| E12x/w055 | ink (earlier scale) |  |  | turn_sheet.png |
| E12x/w068 | ink (earlier scale) |  |  | turn_sheet.png |
| E2x/w098 | ink (earlier scale) |  |  | turn_sheet.png |
| E5x/w068 | ink (earlier scale) |  |  | turn_sheet.png |
| E5x/w077 | ink (earlier scale) |  |  | turn_sheet.png |
| E5x/w080 | ink (earlier scale) |  |  | turn_sheet.png |
| E5x/w089 | ink (earlier scale) |  |  | turn_sheet.png |
| E5x/w093 | ink (earlier scale) |  |  | turn_sheet.png |
| E5x/w096 | ink (earlier scale) |  |  | turn_sheet.png |
| E8x/w079 | ink (earlier scale) |  |  | turn_sheet.png |
| E8x/w083 | ink (earlier scale) |  |  | turn_sheet.png |
| E8x/w084 | ink (earlier scale) |  |  | turn_sheet.png |
| E8x/w088 | ink (earlier scale) |  |  | turn_sheet.png |
| E8x/w089 | ink (earlier scale) |  |  | turn_sheet.png |
| E8x/w090 | ink (earlier scale) |  |  | turn_sheet.png |
| E8x/w100 | ink (earlier scale) |  |  | turn_sheet.png |
| E8x/w107 | ink (earlier scale) |  |  | turn_sheet.png |
| E9x/w070 | ink (earlier scale) |  |  | turn_sheet.png |
| E9x/w073 | ink (earlier scale) |  |  | turn_sheet.png |
| E9x/w084 | ink (earlier scale) |  |  | turn_sheet.png |
| E9x/w094 | ink (earlier scale) |  |  | turn_sheet.png |
| C5f/w060 | unsure |  |  | turn_sheet.png, review_panel_target.png, review_panel_w059.png, review_panel_w061.png, cross_section.png |
| E6x/w088 | unsure |  |  | turn_sheet.png |
