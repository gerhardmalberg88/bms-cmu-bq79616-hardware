# CMU documentation index

Engineering documentation for the **BMS Cell Monitoring Unit (CMU)**, module 1
of 3 in a three-repository battery management system.

| Repository | Module | Role |
|---|---|---|
| `bms-cmu-bq79616-hardware` | **CMU** (this one) | BQ79616-Q1 cell monitoring, 6S–16S, no MCU |
| `bms-bmu-stm32-bq79600-hardware` | BMU | STM32H757 + BQ79600-Q1 master, CAN-FD, SoC/SoH |
| `bms-bjb-bq79631-hardware` | BJB | BQ79631-Q1, shunt, contactor and precharge drivers |

## Current stage — 2026-10-24

The schematic and PCB are complete for the saved 16S prototype population.
The configured ERC/DRC pass; the manufacturing package is prepared under
[`../manufacturing/rev0.1-2026-10-24/`](../README.md).
This does not complete the draft engineering analyses listed below. Supplier
construction/process confirmation and hardware bring-up remain open.

[CMU-009 — Manufacturing and release record](CMU-009-manufacturing.md) records
what was exported, verified, and left unresolved. Purchase 157 fitted components
plus all 37 DNP parts; the latter remain excluded from assembly.

[NOTICE.md](../NOTICE.md) records licensing and imported-asset provenance.
The [latest STL](../3d/CMU-rev0.1-16S.stl)
and [PCB image](../3d/CMU-rev0.1-16S-raytraced.png)
show the fitted assembly.

## Documents by phase

Grouped by the analyses' role, not completion status. Pre-layout inputs that
remain drafts are outstanding engineering work even though routing is complete.

### Pre-layout — these are *inputs* to layout

| Doc | Title | Status | Why it comes first |
|---|---|---|---|
| [CMU-001](CMU-001-requirements.md) | Requirements and System Context | skeleton | Everything else needs its pass/fail criteria |
| [CMU-008](CMU-008-interface-control.md) | Interface Control Document | draft | **The BMU and BJB repos are blocked on this** |
| [CMU-002](CMU-002-power-budget.md) | Power Budget and Load Analysis | draft | Feeds thermal; sizes the supply chain |
| [CMU-003](CMU-003-fmea.md) | Design FMEA | draft | Its output *is* layout constraint |
| [CMU-004](CMU-004-stress-and-wcca.md) | Stress and Worst-Case Circuit Analysis | skeleton | Tolerance stack-up; sets component values |
| [CMU-005](CMU-005-layout-constraints.md) | Layout Constraints | implemented layout record; engineering review open | Aggregates the above into what routing obeys |

The [Eurocircuits stackup source record](CMU-005-layout-constraints.md#51-eurocircuits-physical-stackup-source)
identifies the selected eight-layer build, its KiCad values, and the material
and coating assumptions still awaiting fabrication confirmation.
The [Eurocircuits fabrication constraints review](CMU-005-layout-constraints.md#52-eurocircuits-fabrication-constraints-and-review)
records the applied KiCad limits, custom rules, manufacturer sources,
and remaining layout verification.
The [1.6 mm target and routing decision](CMU-005-layout-constraints.md#54-16-mm-target-and-communication-routing-decision-2026-09-20)
records the 0.21/0.25 mm `CMU_COM_TOP` routing defaults and the selected
35 um outer / 18 um inner copper construction: **1.604 mm material total**,
represented as **1.708 mm** in KiCad with finished copper and estimated masks.
The project text variable **`FAB_MATERIAL_THICKNESS = 1.604 mm`** and its
companion basis field record the Eurocircuits material total explicitly in
both the KiCad project and PCB file.
The [follow-up physical-thickness review](CMU-005-layout-constraints.md#55-request-for-a-1600-mm-physical-stackup-compatibility-review)
records the new 1.600 mm request, the conflicting 18/35 um inner-copper
attachments, passing Class 6C parameter checks and the construction data
needed before changing the physical stackup.

### Post-layout — need copper, stackup and placement

| Doc | Title | Status |
|---|---|---|
| [CMU-006](CMU-006-thermal-analysis.md) | Thermal Analysis | skeleton |
| [CMU-007](CMU-007-si-pi-analysis.md) | Signal and Power Integrity Analysis | draft SI estimate; PI work planned |
| [CMU-009](CMU-009-manufacturing.md) | Manufacturing and prototype release | files prepared; supplier/process confirmations open |

### Simulation

[`../sim/`](../verification/source-snapshot.zip) holds Qucs-S + ngspice circuit simulations. Each planned case names a claim to verify and is indexed against its document.
The current simulation scaffolding is not evidence of a completed validation run.
[EM simulations](../verification/source-snapshot.zip) and [thermal simulations](../verification/source-snapshot.zip)
are coming soon; neither contains simulated results.

### Generated

[`generated/`](generated) holds supporting source exports and the imported
library provenance inventory. The dated [manufacturing package](../README.md)
is the authoritative set for fabrication, assembly and purchasing. The export
README records which commands generate each file. **Never hand-edit generated
tables or CAD exports.**

## Conventions

**Front matter.** Every document carries `id`, `title`, `rev`, `status`,
`phase`, `applies_to` and `license`. `phase` describes its role in development;
`status` records completion. A phase label is not permission to treat an
unfinished analysis as passed.

**Document IDs are permanent.** Once another repository cites `CMU-008`, that
number cannot move. Add new documents at the next free number rather than
inserting, and preserve IDs when renaming files. Record dated decisions in
the affected analysis and release/configuration changes in CMU-009.
Historical acceptance does not establish verified performance.

**Generated blocks.** Tables that restate the schematic are produced by
`tools/gen_doc_tables.py` and delimited:

```markdown
<!-- BEGIN GENERATED: <block-id> (do not edit by hand) -->
<!-- END GENERATED -->
```

Block IDs currently implemented: `tap-connector-pinouts`, `daisy-chain-pinouts`,
`ntc-pinouts`, `dissipation-table`.

Run `python tools/gen_doc_tables.py --check` with KiCad's Python (`pcbnew` available) to fail on a stale block. Analysis
and conclusions are hand-written *around* those blocks, so the numbers can never
drift from the design while the reasoning is preserved.

**Self-documenting design.** Component `Description` fields in the schematic
carry the reasoning for individual part choices. These documents cite
designators and summarise; they do not duplicate the field text, so there is one
source of truth per fact.

## Licensing

Everything here is **CERN-OHL-P-2.0**, the same licence as the design and the
component library. There is no split between the analyses, the index and the
generated exports.

Copyright (C) 2021-2026 Gerhard Malberg.
