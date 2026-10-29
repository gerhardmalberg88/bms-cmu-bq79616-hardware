# Cell balancing resistors — thermal simulation placeholder

Copyright (C) 2021-2026 Gerhard Malberg.
SPDX-License-Identifier: CERN-OHL-P-2.0

**Status: documentation only.** No geometry export, mesh, Elmer case,
temperature prediction or validated result is supplied. Implementation will
follow the [thermal Mermaid workflow](../../../../pcb-em-lab/README.md#thermal-workflow).

## Purpose and traceability

Evaluate the distributed balancing resistors in
[CMU-006 §§4–5](../../../docs/CMU-006-thermal-analysis.md): resistor and board
temperature rise, effects on nearby components, and NTC measurement error from
local heating. Heat inputs must come from a verified operating case tied to
[CMU-002 §8](../../../docs/CMU-002-power-budget.md).

The current 17 × 20 ohm resistors, approximately 0.22 W each / 3.7 W total,
are a **preliminary allocation**, not a validated simultaneous balancing case.
Verify resistor references, shared-node currents, permitted channel schedules,
duty cycles and voltage/resistance corners before assigning watts per body or
pad. Ambient, enclosure conditions and acceptance limits remain open inputs.

## Planned workflow

| Stage | Planned work and handoff |
|---|---|
| Configuration | `config.yaml` records resistor references/watts, balancing schedule, ambient, convection coefficient, materials, crop box and mesh sizes. `run.py` will drive each stage or the complete sequence. |
| KiCad 10 | Export board, copper including inner layers, balancing resistors and positions using one fixed drill/grid origin. CLI exports and the GUI STEP export will use the same coordinates. |
| FreeCAD, optional | Model heatsink, thermal pad, standoffs or enclosure walls as separate STEPs in board coordinates. Preserve the KiCad STEP; merge mechanical parts at the meshing stage. |
| Gmsh | Merge board/mechanical geometry, crop the region, fragment bodies to share faces and tag volumes/surfaces. Keep all copper in the region regardless of net, and refine around the resistors. Hand off `board.msh`. |
| Elmer | Convert the mesh with ElmerGrid and solve the shared `case.sif` with ElmerSolver. The SIF is the authoritative solver setup; use ResultOutputSolve for VTU output. ElmerGUI will inspect the same case. |
| ParaView | Inspect temperature fields, hotspots and cross-sections. Save `view.pvsm` so GUI review and scripted `pvpython` PNG rendering use the same view. |

The diagram also describes cropped and hybrid models: explicit copper near
the resistors, with a homogenized orthotropic slab outside for the hybrid
option. Treat its 2–3 thermal-length crop margin as an initial heuristic;
check crop-size sensitivity and insulated cut-edge assumptions before relying
on the temperatures. Include other relevant heat sources, such as the AFE,
with documented losses and pad/body assignments.

Tool versions, export completeness, mesh conversion settings and solver
configuration will be verified during implementation. This page records the
attached workflow rather than a tested run procedure.

## Inputs and cases to resolve

- Saved PCB revision/hash, resistor references/positions, copper geometry and
  stackup from [`design/`](../../../design/) and
  [CMU-005](../../../docs/CMU-005-layout-constraints.md).
- Per-resistor losses for the maximum permitted simultaneous balancing
  schedule, plus duty-cycle/transient cases where required.
- Material properties, component thermal representation and contact
  resistances, including any pads, heatsinks and mounting paths.
- Ambient range, airflow/convection, enclosure and other boundary conditions
  from [CMU-001](../../../docs/CMU-001-requirements.md), with assumptions explicit.
- Temperature evaluation points at the resistors, PCB, nearby components and
  relevant sensor locations; derating limits and the NTC error budget.

## Planned artifacts and review

Only this README exists in the case directory. The following paths are
reserved for later implementation; no runnable stubs are supplied:

| Future path, relative to this directory | Purpose |
|---|---|
| `config.yaml`, `run.py` | Case inputs and staged driver |
| `geometry.py` | Gmsh construction, cropping and physical groups |
| `case.sif` | Authoritative Elmer solver configuration |
| `view.pvsm` | Shared ParaView state for review/rendering |
| `expected/` | Reviewed baseline figures, once available |
| `../../results/thermal/cell-balancing-resistors/` | Generated exports, meshes, solver files, logs, VTU fields and images; already gitignored |

Before reporting a result, record source hashes, tool versions, the power
budget, boundary conditions, mesh/crop convergence and heat balance. Compare
temperatures and NTC impact with the agreed CMU-006 limits and return reviewed
findings there. Thermal-camera/thermocouple correlation remains a later
validation step; this placeholder closes no thermal acceptance items.
