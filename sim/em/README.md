# Electromagnetic simulations

Copyright (C) 2021-2026 Gerhard Malberg.
SPDX-License-Identifier: CERN-OHL-P-2.0

BMS-specific cases use the sibling [PCB EM Lab](../../../pcb-em-lab/README.md)
repository. Its root README contains the [EM Mermaid workflow](../../../pcb-em-lab/README.md#em-workflow)
and [thermal Mermaid workflow](../../../pcb-em-lab/README.md#thermal-workflow).
Reusable code, container recipes and Spack locks stay there; physical inputs stay here.

- [COMH/COML 2D sections](isospi-2d/README.md): Palace BoundaryMode.
- [Bounded communication PCB regions](isospi-3d/README.md): Palace Driven, ending at connector contacts.
- [Internal magnetics](internal-magnetics/README.md): approximate T501/T502, integrated common-mode chokes and L601.

Read the workflow repository's [validation status](../../../pcb-em-lab/docs/validation.md)
before using a case. All eight supplied CPU cases completed the pipeline; the
shared validation record tracks CUDA checks and model limitations. No engineering
acceptance result is supplied. The provisional targets remain in
[CMU-007](../../docs/CMU-007-si-pi-analysis.md).

The requested isoSPI label refers here to the BQ79616-Q1 COMH/COML transformer-isolated
daisy chain. Preserve its floating references and isolation keepouts. No cables or
external assemblies are part of the initial 3D PCB cases. All generated artifacts
and provenance go into ignored `sim/results/em/` directories. Reviewed findings
must distinguish numerical convergence from physical-model confidence.
