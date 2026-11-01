---
id: CMU-006
title: Thermal Analysis
rev: 0.1
status: simulation-scope-closed
phase: post-layout
applies_to: bms-cmu-bq79616-hardware rev 0.1
license: CERN-OHL-P-2.0
---

# CMU-006 — Thermal Analysis

**Simulation scope closed on 2026-10-31: no further BMS thermal simulations are
planned.** Twelve resistor-only CPU steady cases are complete and their results
are ready for Git. Local detailed-region convergence failed, so the predictions
remain provisional. Scope closure records the decision to stop simulation work;
it does not convert unperformed or failed validation into a pass.

The [case documentation](../verification/source-snapshot.zip)
contains assumptions, temperatures, figures, reproduction commands and the
compact provenance snapshot. Native Elmer results and diagnostic logs remain
in the ignored thermal results area.

## 1. Completed scope

Only the 17 balancing resistors generate heat; the whole PCB conducts it.
Automatic cycle-averaged, continuous odd-only and continuous even-only heating
were solved at convection coefficients h = 5/10/20/50 W/m²K.

All twelve steady cases pass native solver completion, unchanged source and
artifact checks, matching converted-mesh checks and <1% heat imbalance.
Three mesh resolutions pass the selected numerical refinement criterion.
The limited automatic h=10 comparison at 10/20 mm detail margins completed,
but failed local hotspot convergence: R361 changes by 1.831 °C, or 5.03% of the
reference peak temperature rise. The acceptance limits remain <1 °C and <2%.
No additional detail refinement is planned for this project.

## 2. Inputs and interpretation

| Input | Recorded basis | Limitation |
|---|---|---|
| Resistor power | 4.2 V cells, 20 Ω resistors, 1.45 Ω switch resistance; verified CB connectivity; 3.285485 W resistor heat | Fixed-voltage, resistor-only operating assumption |
| Ambient/cooling | 25 °C; exposed-surface convection h = 5/10/20/50 | Assumed coefficients, not measured airflow |
| Geometry | Saved revision 0.1 board; whole-board hybrid model; 10 mm production detail margin | Remote copper/via properties are averaged; detail sensitivity remains unresolved |
| Materials | Editable engineering constants, 25 µm barrel plating, 100 µm solder | Supplier and environmental inputs are not fully confirmed |
| Other heat paths | Radiation, enclosure and mounting conduction omitted | Real assembly cooling is not established |

The largest steady prediction is about 85.08 °C for odd-only heating at h=5;
automatic h=10 predicts 61.24 °C. These are model temperatures under the stated
conditions. They do not establish warm-up time, switching ripple, a universal
maximum, component junction temperatures or a measured operating envelope.
The wider component dissipation estimates remain in [CMU-002](CMU-002-power-budget.md).
The saved stackup and supplier assumptions remain in
[CMU-005](CMU-005-layout-constraints.md#51-eurocircuits-physical-stackup-source).

## 3. Removal of remaining simulation plans

The following items were identified in the previous plan and are now excluded,
not queued or marked as passed. No remaining thermal simulation blocks publication
of the completed provisional results.

| Previously planned work | Final disposition |
|---|---|
| 1,800 s balancing + 1,800 s cooling; half-step verification | Canceled; transient case file and unused steady-case transient settings removed |
| Further 10/20/30 mm detail, cropped and fully explicit domain studies | Removed from the BMS plan; the observed detail-convergence failure remains a limitation |
| BMS CPU/CUDA agreement and GPU tuning | Removed; published cases use CPU; small-fixture GPU checks do not validate the BMS mesh |
| Direct-solver/transient performance experiments | Removed from the BMS plan; existing diagnostic evidence retained locally |
| Additional ambient, voltage, tolerance and duty-cycle thermal corners | Excluded; published cases cover only the documented operating assumptions |
| Combined supply/AFE heating: Q201, LTC3639, BQ79616 and tap fuses | Excluded; their junction temperatures and thermal derating are not established by this study |
| D601 sustained mis-regulation and other fault-heating cases | Excluded; fault energy, failure mode and protection effectiveness remain unverified |
| Enclosure, mounting and mechanical cooling variants | Excluded; no mechanical cooling assembly was simulated |
| NTC error and nearby-component thermal models | Excluded; reported PCB temperatures do not establish sensor measurement error |

Reusable transient, crop and backend functionality in the standalone thermal
lab is retained for other work. It is not an active BMS test plan.

## 4. Evidence retained for publication

- [Steady cases and figures](../verification/source-snapshot.zip).
- [Twelve-case CSV](../verification/source-snapshot.zip).
- [Provenance and numerical comparisons](../verification/source-snapshot.zip).

No numerical results, image contents, source hashes or acceptance thresholds
were changed to close the scope. Failed and interrupted native evidence remains
local and ignored. No further simulation is required by this publication scope.

## 5. Hardware validation remains separate

Measured temperatures, material/environmental correlation, junction derating,
NTC accuracy, fuse derating and thermal qualification have not been established.
These remain unresolved engineering evidence, outside the closed simulation
plan. This document does not close the criticality assessment in
[CMU-003](CMU-003-fmea.md) or any hardware acceptance requirement.
