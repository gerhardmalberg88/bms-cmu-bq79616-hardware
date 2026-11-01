# COMH/COML transformer-to-connector 3D models

Copyright (C) 2021-2026 Gerhard Malberg.
SPDX-License-Identifier: CERN-OHL-P-2.0

[comh.json](comh.json) and [coml.json](coml.json) model the actual transformer
secondary pads through the saved PCB copper to J501/J502 contact heads. They
exclude cables, mating connectors, package windings and connector housings.
Contacts are editable 0.5 mm square, 5 mm tall approximations. Copper is PEC;
material properties and masks remain estimates.

Two half-ports terminate at the transformer positive/center/negative pads.
Their signed series connection uses `Z_reduced = Cᵀ Z C`, imposing equal
half-port currents and zero external center-tap current. No physical ground
connection is added to SC_CT. The output is a 100 Ω differential connector port.
J501 pin 1 is positive / pin 2 negative; J502 pin 2 is positive / pin 1 negative.

These successful PCB networks are combined with the [2D-derived primary-side
line equivalents](../isospi-2d/README.md) and the [balanced component
model](../transformer-coupling/README.md). Dense 3D IC/filter models were attempted
and rejected for degenerate tetrahedra; they are not supplied as completed cases.
Their local diagnostic logs remain under ignored results. The published study
contains no validated 3D field solution from U201 to the transformer primary.

From the hardware repository root with installed `pcb-em`:

```bash
pcb-em run sim/em/isospi-3d/comh.json --backend cpu
pcb-em run sim/em/isospi-3d/coml.json --backend cpu
```

The solved frequencies are 1, 4 and 10 MHz. Native BREP/MSH, physical tags,
Palace inputs/CSV/PVD/VTU, logs and ParaView states remain under
`sim/results/em/{comh,coml}-connector-3d/`. Three samples do not support a
qualified transient fit or interpolation claim.

Field images show the first half-port excitation with other ports terminated,
not a populated-board operating field. The main linear tolerance is 1e-8; the
approximate flux-error estimator uses 1e-2 after a same-mesh comparison preserved
saved port values. Positive tetrahedron orientation is checked. Very thin
positive elements remain; 3D mesh/domain convergence and local field peaks are
unqualified. No EMC, receiver, driver or electrical-isolation acceptance follows.
