# COMH/COML 2D communication sections

Copyright (C) 2021-2026 Gerhard Malberg.
SPDX-License-Identifier: CERN-OHL-P-2.0

[comh.yaml](comh.yaml) and [coml.yaml](coml.yaml) configure Palace BoundaryMode
cross-sections of the saved PCB. Follow the shared [EM workflow](../../../../pcb-em-lab/README.md#em-workflow)
and check its [validation status](../../../../pcb-em-lab/docs/validation.md).
These are exploratory cases; no impedance acceptance claim is closed.

From the sibling workflow repository:

```bash
./pcb-em run ../bms-cmu-bq79616-hardware/sim/em/isospi-2d/comh.yaml --mode 2d --backend cpu
./pcb-em run ../bms-cmu-bq79616-hardware/sim/em/isospi-2d/coml.yaml --backend auto
```

The COMH section crosses y=123 mm; COML crosses y=132.5 mm. Both read actual copper,
layer heights, nearby conductors and saved keepouts. Their routed straight pairs
are 0.21 mm wide with 0.20 mm gap; netclass defaults are not substituted for geometry.
Dielectric and soldermask properties remain explicit estimates in the case files.

Evaluate [CMU-007 §§2.1/2.3 and §4](../../../docs/CMU-007-si-pi-analysis.md), including
the provisional 100 ohm differential target. Inspect modal field polarity before
selecting a differential result. Review modal impedance, propagation and per-length
L/C against mesh refinement, polynomial order and larger air domains. A uniform
2D section does not represent pads, bends, transformers or the complete link.

Results, mesh/configuration, fields, logs and source/tool hashes go to
`../../results/em/comh-2d/` and `../../results/em/coml-2d/`. The design is mounted
read-only. Confirm target tolerance and manufacturer stackup data before returning
reviewed conclusions to CMU-007.

The installed CPU/CUDA COMH comparison uses identical mesh bytes. Its selected
differential mode agrees within 0.003% in the recorded solver-tolerance probes.
The second mode exceeds the 0.02% comparison target (about 0.072% at the supplied
settings, 0.183% with tighter solvers); its precision remains unvalidated. CPU-only
rank/tolerance changes also affect it. See the shared validation record before
using that mode or interpreting solver residuals as an observable error bound.
