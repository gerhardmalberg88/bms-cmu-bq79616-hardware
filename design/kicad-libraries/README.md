# Project library

Imported copies of the parts this board uses, from
[`kicad-libraries`](https://github.com/gerhardmalberg88/kicad-libraries).

Copyright (C) 2021-2026 Gerhard Malberg
SPDX-License-Identifier: CERN-OHL-P-2.0

The licence text is the repository root `LICENSE`. Every file here is
`cleared_original` Covered Source with no third-party CAD content; manufacturer
names and marks belong to their owners and are used descriptively only.

## What is here, and what is not

The upstream library holds 23 symbols, 50 footprints and 41 models. This
project contains 5 symbols, 21 footprint copies and 12 original models,
including retained full-outline counterparts of the minimal-silkscreen
variants. Generic passive variants reference installed KiCad models without
copying those model files into this project.

Not copied: the FreeCAD and CadQuery model sources, the asset generators,
`ASSET_PROVENANCE.csv`, and the upstream `README`. Clone `kicad-libraries` when
any of those are needed.

`custom_symbols.kicad_sym` is **this project's own library**, holding imported
copies. Upstream each symbol is its own library — `ltc3639:LTC3639` —
but the project keeps one library so its `lib_id`s stay stable. The symbol
blocks are copied without a byte changed, so each one still identifies against
the file it came from.

## Imported files

The `Blob` column is the SHA-1 git gives that content. It is derived from the
bytes themselves, so it identifies a file regardless of which commit carries it
and stays valid however the upstream repository's history is arranged. No
commit is recorded here by hand; `identify_asset.py` resolves each blob to the
commit that introduced it, against whatever clone it is pointed at.

| File here | Upstream file | Blob |
|---|---|---|
| `footprints/custom_footprints.pretty/Harwin_Datamate_M80-5001642_2x08_P2.00mm_Vertical_MinimalSilkscreen.kicad_mod` | `footprints/custom_footprints.pretty/Harwin_Datamate_M80-5001642_2x08_P2.00mm_Vertical_MinimalSilkscreen.kicad_mod` | `eb206910cc61` |
| `footprints/custom_footprints.pretty/Harwin_Datamate_M80-5T10442MC_2x02_P2.00mm_Vertical_MinimalSilkscreen.kicad_mod` | `footprints/custom_footprints.pretty/Harwin_Datamate_M80-5T10442MC_2x02_P2.00mm_Vertical_MinimalSilkscreen.kicad_mod` | `24c7ab7b374b` |
| `footprints/custom_footprints.pretty/L_Wuerth_WE-PD-Robust-7332_MinimalSilkscreen.kicad_mod` | `footprints/custom_footprints.pretty/L_Wuerth_WE-PD-Robust-7332_MinimalSilkscreen.kicad_mod` | `3828cad32762` |
| `footprints/custom_footprints.pretty/LTC3639_MSE16-12_MinimalSilkscreen.kicad_mod` | `footprints/custom_footprints.pretty/LTC3639_MSE16-12_MinimalSilkscreen.kicad_mod` | `ca2761f6867a` |
| `footprints/custom_footprints.pretty/Bourns_CDSOD323-TxxC_SOD-323_Compact_MinimalSilkscreen.kicad_mod` | `footprints/custom_footprints.pretty/Bourns_CDSOD323-TxxC_SOD-323_Compact_MinimalSilkscreen.kicad_mod` | `f5110d5b5c79` |
| `footprints/custom_footprints.pretty/R_0603_1608Metric_NoSilkscreenBody.kicad_mod` | `footprints/custom_footprints.pretty/R_0603_1608Metric_NoSilkscreenBody.kicad_mod` | `f3dd4fcd1e1c` |
| `footprints/custom_footprints.pretty/C_0603_1608Metric_NoSilkscreenBody.kicad_mod` | `footprints/custom_footprints.pretty/C_0603_1608Metric_NoSilkscreenBody.kicad_mod` | `15907398ccda` |
| `footprints/custom_footprints.pretty/C_0805_2012Metric_NoSilkscreenBody.kicad_mod` | `footprints/custom_footprints.pretty/C_0805_2012Metric_NoSilkscreenBody.kicad_mod` | `bc67979132b9` |
| `footprints/custom_footprints.pretty/C_1206_3216Metric_OneSideSilkscreen.kicad_mod` | `footprints/custom_footprints.pretty/C_1206_3216Metric_OneSideSilkscreen.kicad_mod` | `d21e02c136c0` |
| `footprints/custom_footprints.pretty/Bourns_CDSOD323-TxxC_SOD-323_Compact.kicad_mod` | `footprints/custom_footprints.pretty/Bourns_CDSOD323-TxxC_SOD-323_Compact.kicad_mod` | `b3aa57527a79` |
| `footprints/custom_footprints.pretty/BQ79616-Q1.kicad_mod` | `footprints/custom_footprints.pretty/BQ79616-Q1.kicad_mod` | `0c4da7f5c26e` |
| `footprints/custom_footprints.pretty/Bourns_SMBJ-Q_DO-214AA.kicad_mod` | `footprints/custom_footprints.pretty/Bourns_SMBJ-Q_DO-214AA.kicad_mod` | `639f4edfb48c` |
| `footprints/custom_footprints.pretty/Harwin_Datamate_M80-5001642_2x08_P2.00mm_Vertical.kicad_mod` | `footprints/custom_footprints.pretty/Harwin_Datamate_M80-5001642_2x08_P2.00mm_Vertical.kicad_mod` | `1b19d830bf89` |
| `footprints/custom_footprints.pretty/Harwin_Datamate_M80-5002042_2x10_P2.00mm_Vertical.kicad_mod` | `footprints/custom_footprints.pretty/Harwin_Datamate_M80-5002042_2x10_P2.00mm_Vertical.kicad_mod` | `0b5dc07aefd6` |
| `footprints/custom_footprints.pretty/Harwin_Datamate_M80-5T10442MC_2x02_P2.00mm_Vertical.kicad_mod` | `footprints/custom_footprints.pretty/Harwin_Datamate_M80-5T10442MC_2x02_P2.00mm_Vertical.kicad_mod` | `c35ff269dba2` |
| `footprints/custom_footprints.pretty/JST_XH_B20B-XH-A_1x20_P2.50mm_Vertical.kicad_mod` | `footprints/custom_footprints.pretty/JST_XH_B20B-XH-A_1x20_P2.50mm_Vertical.kicad_mod` | `59ca1daeee49` |
| `footprints/custom_footprints.pretty/LTC3639_MSE16-12.kicad_mod` | `footprints/custom_footprints.pretty/LTC3639_MSE16-12.kicad_mod` | `22eff815355c` |
| `footprints/custom_footprints.pretty/L_Wuerth_WE-PD-Robust-7332.kicad_mod` | `footprints/custom_footprints.pretty/L_Wuerth_WE-PD-Robust-7332.kicad_mod` | `8e9bfc38e890` |
| `footprints/custom_footprints.pretty/Littelfuse_470-Series_Fuse_1206.kicad_mod` | `footprints/custom_footprints.pretty/Littelfuse_470-Series_Fuse_1206.kicad_mod` | `8ad7c7785a1e` |
| `footprints/custom_footprints.pretty/SM91502AL.kicad_mod` | `footprints/custom_footprints.pretty/SM91502AL.kicad_mod` | `99c3d3d9af2f` |
| `footprints/custom_footprints.pretty/Vishay_RCL1225_2W_3.2x6.3mm.kicad_mod` | `footprints/custom_footprints.pretty/Vishay_RCL1225_2W_3.2x6.3mm.kicad_mod` | `c90749809343` |
| `3d_models/custom_3dmodels.3dshapes/Bourns_CDSOD323-TxxC_SOD-323.step` | `3d_models/custom_3dmodels.3dshapes/Bourns_CDSOD323-TxxC_SOD-323.step` | `c1a642d648be` |
| `3d_models/custom_3dmodels.3dshapes/BQ79616-Q1.step` | `3d_models/custom_3dmodels.3dshapes/BQ79616-Q1.step` | `b4d04f174864` |
| `3d_models/custom_3dmodels.3dshapes/Bourns_SMBJ-Q_DO-214AA.step` | `3d_models/custom_3dmodels.3dshapes/Bourns_SMBJ-Q_DO-214AA.step` | `bc96a02eee01` |
| `3d_models/custom_3dmodels.3dshapes/Harwin_Datamate_M80-5001642.step` | `3d_models/custom_3dmodels.3dshapes/Harwin_Datamate_M80-5001642.step` | `d115cb41d4b9` |
| `3d_models/custom_3dmodels.3dshapes/Harwin_Datamate_M80-5002042.step` | `3d_models/custom_3dmodels.3dshapes/Harwin_Datamate_M80-5002042.step` | `4fc5e7c526f6` |
| `3d_models/custom_3dmodels.3dshapes/Harwin_Datamate_M80-5T10442MC.step` | `3d_models/custom_3dmodels.3dshapes/Harwin_Datamate_M80-5T10442MC.step` | `4600ba12b346` |
| `3d_models/custom_3dmodels.3dshapes/JST_XH_B20B-XH-A_1x20_P2.50mm_Vertical.step` | `3d_models/custom_3dmodels.3dshapes/JST_XH_B20B-XH-A_1x20_P2.50mm_Vertical.step` | `2b35404b66a8` |
| `3d_models/custom_3dmodels.3dshapes/LTC3639_MSE16-12.step` | `3d_models/custom_3dmodels.3dshapes/LTC3639_MSE16-12.step` | `9cbfb35b3761` |
| `3d_models/custom_3dmodels.3dshapes/L_Wuerth_WE-PD-Robust-7332.step` | `3d_models/custom_3dmodels.3dshapes/L_Wuerth_WE-PD-Robust-7332.step` | `3c9dad6a2acc` |
| `3d_models/custom_3dmodels.3dshapes/Littelfuse_470-Series_Fuse.step` | `3d_models/custom_3dmodels.3dshapes/Littelfuse_470-Series_Fuse.step` | `b922e2adb4fe` |
| `3d_models/custom_3dmodels.3dshapes/SM91502AL.step` | `3d_models/custom_3dmodels.3dshapes/SM91502AL.step` | `8662beeedbe0` |
| `3d_models/custom_3dmodels.3dshapes/Vishay_RCL1225_2W.step` | `3d_models/custom_3dmodels.3dshapes/Vishay_RCL1225_2W.step` | `3c1c3e630dba` |
| `symbols/custom_symbols.kicad_sym (+8V8)` | `symbols/8v8.kicad_sym` | `68e1a4feac92` |
| `symbols/custom_symbols.kicad_sym (BQ79616-Q1)` | `symbols/bq79616_q1.kicad_sym` | `b694a6b832e9` |
| `symbols/custom_symbols.kicad_sym (LTC3639)` | `symbols/ltc3639.kicad_sym` | `0b2cfc955fcb` |
| `symbols/custom_symbols.kicad_sym (L_Wuerth_WE-PD-Robust-7332)` | `symbols/l_wuerth_we_pd_robust_7332.kicad_sym` | `c45e76165264` |
| `symbols/custom_symbols.kicad_sym (SM91502AL)` | `symbols/sm91502al.kicad_sym` | `9f14f2fb86c9` |

## Fabrication display

The 21 custom footprint copies include the shared library fabrication standard
from the 2026-10-18 BMS cleanup: hidden values/descriptions and body-fitted
references. They are byte-identical to the current shared footprint files.
The generator, fit checker and authoring rules live in the
[shared library standard](https://github.com/gerhardmalberg88/kicad-libraries#fabrication-layer-standard).
Stock KiCad footprints remain separate; their BMS-specific display edits are
retained in the board. Updating these library copies does not alter placed
footprints, board routing or schematic data.

D501–D504 are assigned in both schematic and PCB to
`custom_footprints:Bourns_CDSOD323-TxxC_SOD-323_Compact_MinimalSilkscreen`. The reusable original
footprint and its original STEP model come from the shared library. Its
0.60 × 0.45 mm pads at 2.10 mm pitch preserve the existing routed geometry;
this compact variant differs from Bourns' recommended land pattern. The
fabrication box, pad-one marker and 0.25 mm reference are library graphics,
so their display no longer relies on board-only edits to a stock footprint.

## Minimal silkscreen assignments

The 2026-10-23 cleanup uses nine reusable variants from the shared library:

- R219-R226 and C210-C217: no body-outline bars in the dense rows.
- C205, C502 and C505: no body-outline bars; C201 retains one clear side bar.
- J201, J501 and J502: short corner arms, with pin-one and lock guides retained.
- L601 and U601: a central gap in the affected outline, with orientation dots retained.
- D501-D504: a common minimal pad-one end tick for the bidirectional TVS family.

All 29 PCB identifiers and schematic Footprint fields use the matching library
variants. Placed fabrication graphics, references, courtyards, models, pads,
nets, vias, traces and mechanical keepouts are unchanged. The generic passive
variants are original parametric artwork with optional external KiCad model
links; their existing installed models are retained in the board. Base
full-outline library files are retained for reuse.

## Verifying and updating

Never edit anything here in place: a change made here is invisible to every
other board, and a save through the KiCad editor rewrites UUIDs and the
generator string, which breaks byte-level identification. Make library changes
upstream, commit them there, then re-import.

To check every file against the library, from the repository root:

```console
python ../kicad-libraries/tools/identify_asset.py \
    --upstream ../kicad-libraries --manifest design/kicad-libraries/README.md
```

`EXACT` means byte-identical to a commit. `EQUIVALENT` means the design matches
but the bytes do not, which is an editor save or a KiCad format migration rather
than a design change. `DIVERGED` means the part was genuinely edited — re-run
with `--show-diff` to see what. Exit codes: 0 all identified, 1 something
diverged, 2 something is not from this library, 3 the upstream path is not a
git repository.

How those three methods work is documented once, in the
[library README](https://github.com/gerhardmalberg88/kicad-libraries#version-checking).
