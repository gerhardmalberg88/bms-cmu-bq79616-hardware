# Thermal simulations — scope closed

Copyright (C) 2021-2026 Gerhard Malberg.
SPDX-License-Identifier: CERN-OHL-P-2.0

The completed study is [cell balancing resistor heating and PCB cooling](cell-balancing-resistors/README.md).
It contains twelve CPU steady cases: automatic, odd-only and even-only balancing
at h = 5/10/20/50 W/m²K, plus recorded mesh and limited detail comparisons.
Case inputs, figures and a compact CSV/provenance snapshot are ready for Git.
Large native results remain ignored under `sim/results/thermal/`.

**No further BMS thermal simulations are planned.** Transient heating/cooling,
additional domain refinement, backend experiments and other component/fault
thermal studies have been removed from the plan. See the
[scope-closure record](../../docs/CMU-006-thermal-analysis.md) for their disposition.
The standalone `pcb-thermal` CLI can reproduce the retained steady cases; no
sibling-checkout arrangement is required. The migrated case inputs explicitly
declare the balancing topology and write future runs beneath `configured/`;
[historical results and provenance remain unchanged](cell-balancing-resistors/README.md#configured-source-migration).

All twelve steady solves pass heat accounting, but the 10/20 mm detail check
fails local hotspot convergence (1.831 °C, 5.03% of rise). The results therefore
remain provisional. Closing the simulation scope does not resolve this model
limitation or establish measured temperatures, transient peaks, junction
limits, sensor accuracy or hardware qualification.
