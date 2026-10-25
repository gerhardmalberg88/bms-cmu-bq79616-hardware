---
id: CMU-006
title: Thermal Analysis
rev: 0.1
status: skeleton
phase: post-layout
applies_to: bms-cmu-bq79616-hardware rev 0.1
license: CERN-OHL-P-2.0
---

# CMU-006 — Thermal Analysis

**Thermal simulations: coming soon.** Planned models and results will live in
[`sim/thermal/`](../sim/thermal/README.md). No thermal simulation result is supplied.

> **2026-10-24 status:** the routed PCB passes the configured, refilled DRC and its manufacturing files are prepared. This does not close the thermal analysis or establish a measured operating envelope. See [CMU-009](CMU-009-manufacturing.md).


> **Post-layout.** Junction and board temperatures need copper area, layer
> stackup, board outline, component placement and airflow. The preliminary
> Eurocircuits stackup is recorded in [CMU-005](CMU-005-layout-constraints.md#51-eurocircuits-physical-stackup-source);
> the routed layout is available, while supplier and environmental inputs
> still require confirmation.
>
> The preliminary per-component **dissipation** table lives in
> [CMU-002](CMU-002-power-budget.md) §8, deliberately pulled forward because it
> constrains placement. This document turns those watts into temperatures.

## 1. Scope

Junction, case and board temperatures at the worst-case ambient from
[CMU-001](CMU-001-requirements.md), and the resulting derating check.

Closing this document also unblocks the **criticality column in
[CMU-003](CMU-003-fmea.md)**, since part failure rates are temperature-driven.

## 2. Inputs

| Input | Source | Status |
|---|---|---|
| Per-component dissipation | CMU-002 §8 | preliminary estimates; balancing schedule/current sharing unverified |
| Ambient range | CMU-001 §3 | not yet fixed |
| Layer stackup | CMU-005 section 5.1 | Eurocircuits build entered: 35 um finished outer / 18 um inner copper; pressed dimensions unconfirmed |
| Copper area and placement | Saved revision 0.1 PCB | routed; balance resistors distributed along two sides; thermal extraction pending |
| Airflow and enclosure | CMU-001 §3 | not yet fixed |

## 3. Method

- [ ] First pass: datasheet θJA against the actual copper area per part
- [ ] Second pass: board-level spreading for the distributed balance resistors,
      using a verified operating envelope; 3.7 W is only the preliminary allocation
- [ ] Steady state at maximum ambient with all channels balancing
- [ ] Transient: the mis-regulation fault, where D601 sits at ~1.4 W

## 4. Cases to evaluate

- [ ] **17 × 20R:** first verify simultaneous-channel currents, duty cycle and
      voltage/tolerance corners, then temperature rise and effects on nearby parts
- [ ] Effect of balance-resistor self-heating on **NTC accuracy** — the CMU's
      job is measuring cell temperature, and heating its own sensors corrupts
      that
- [ ] Q201 SOT-223 in normal operation (0.07 W) and during faults
- [ ] D601 under sustained mis-regulation: evaluate the preliminary ~1.4 W
      case in CMU-003 F-06. Its failure mode and safe outcome are unverified;
      do not assume a reliable fail-short mechanism
- [ ] LTC3639 junction temperature
- [ ] Tap fuses: ambient at each fuse against the temperature rerating curve
      used in CMU-002 §7, which was read off a graph rather than tabulated
- [ ] BQ79616-Q1 against its 130–152 °C thermal shutdown and 85–115 °C warning

## 5. Acceptance

- [ ] No junction temperature exceeds the derating policy at maximum ambient
- [ ] NTC measurement error from self-heating within the CMU-001 budget
- [ ] Tap fuse derating confirmed at the measured local ambient
- [ ] Criticality column in CMU-003 closed

## 6. Validation (post-test)

- [ ] Thermal camera or thermocouple survey against the predicted map
- [ ] Distributed balance resistors at the maximum permitted duty/schedule
- [ ] Correlate and, if they disagree, revise this document rather than the
      measurement
