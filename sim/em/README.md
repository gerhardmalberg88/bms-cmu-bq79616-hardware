# EM simulations — coming soon

Copyright (C) 2021-2026 Gerhard Malberg.
SPDX-License-Identifier: CERN-OHL-P-2.0

This directory is reserved for electromagnetic models and reviewed SI/PI
results. No board-level simulation, solver setup or validated result is
supplied yet. The preliminary communication cross-section estimates remain
in [CMU-007 — Signal and Power Integrity Analysis](../../docs/CMU-007-si-pi-analysis.md).

Planned scope: COMH/COML coupling and impedance, isolation keepouts and return
paths, supply distribution, decoupling and relevant coupling into sense lines.
Inputs will include the saved PCB, confirmed stackup/material properties,
component parasitics, cable geometry and excitation/load conditions.

Future results must identify the source revision/hashes, assumptions, solver
and convergence checks, and the claim being evaluated. Only reviewed figures
will replace the README gallery's “Coming soon” entry. These simulations will
not by themselves establish EMC compliance or hardware qualification.
