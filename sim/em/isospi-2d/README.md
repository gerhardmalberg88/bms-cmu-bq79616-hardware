# COMH/COML local sections and primary-side line equivalents

Copyright (C) 2021-2026 Gerhard Malberg.
SPDX-License-Identifier: CERN-OHL-P-2.0

Four Palace BoundaryMode cases read the saved PCB copper, stackup and fills:

| Cases | Position | Pair |
|---|---|---|
| `comh.json`, `coml.json` | y=123 / 132.5 mm | U201-side COMHP/HN and COMLP/LN |
| `comh-filter.json`, `coml-filter.json` | x=303.8 mm | FILT_COMHP/HN and FILT_COMLP/LN |

All solve at 4 MHz. The IC-side routed pair is 0.45 mm wide with a 0.20 mm gap;
netclass defaults are not substituted for saved geometry. The filtered-side
spacing differs. Materials remain estimates; source extraction never saves or
refills the PCB. Voltage parity screens the differential candidate, with native
fields retained for inspection. The auxiliary mode is not a qualified common-mode
impedance result.

From the hardware repository root with installed `pcb-em`:

```bash
pcb-em run sim/em/isospi-2d/comh.json --backend cpu
pcb-em run sim/em/isospi-2d/coml.json --backend cpu
pcb-em run sim/em/isospi-2d/comh-filter.json --backend cpu
pcb-em run sim/em/isospi-2d/coml-filter.json --backend cpu
```

The [board-path model](../transformer-coupling/README.md) uses each selected
section's real per-length L/C and the mean saved positive/negative centerline
route length to construct a lossless uniform transmission line. The IC-to-series-
resistor and resistor-to-primary paths have separate local sections. Real 4 MHz
L/C are held constant at the combined model's 1, 4 and 10 MHz sample frequencies.
This approximation includes the route length, but does not resolve bends, pad
transitions, neck-downs, asymmetric lengths, common-mode conversion or varying
cross-sections along the route. It replaces rejected dense 3D primary meshes
within the agreed time budget; it is not a full 3D primary-field solution.

The IC-side sections also have limited 0.05/0.035/0.025 mm mesh and 6/9 mm
vertical-domain sensitivity checks. These do not qualify the lateral domain,
filtered-side sections, material uncertainty or populated board response.
Native results remain ignored under `sim/results/em/`; compact outputs and
limitations are published in [the report](../report/README.md).

The COML filtered section remains diagnostic-only: four computed modes include
an automatic parity-screened candidate near 4.5 Ω, whose field is dominated by
ground-plane edges. It is not accepted as the signal impedance. The combined
model explicitly uses the accepted COMH filtered-section L/C as a COML proxy;
this leaves the different COML spacing and surrounding copper unqualified.
