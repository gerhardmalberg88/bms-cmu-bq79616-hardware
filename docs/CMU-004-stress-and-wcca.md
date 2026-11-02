---
id: CMU-004
title: Stress and Worst-Case Circuit Analysis
rev: 0.1
status: skeleton
phase: pre-layout
applies_to: bms-cmu-bq79616-hardware rev 0.1
license: CERN-OHL-P-2.0
---

# CMU-004 — Stress and Worst-Case Circuit Analysis

> **2026-10-24 status:** the PCB is routed and manufacturing files are
> prepared. The worked cases below are provisional calculations under their
> stated assumptions; their PASS labels are not board qualification. The
> environmental requirements, fault transients and measurements remain open.

## 1. Scope

Applied stress against rating, and tolerance stack-up against requirement.
Transient risks remain recorded here alongside component stress. The only
active circuit simulation plan is the cell-voltage input filter described in
§5.1; other transient risks in §5.2 are outside that plan.

**Pass/fail criteria come from [CMU-001](CMU-001-requirements.md)**, which is
not yet complete. Until the environmental range is fixed, the temperature terms
below are provisional.

## 2. Method

Extreme value analysis: every contributing tolerance at its worst simultaneous
corner. Where that proves too pessimistic to pass, fall back to root-sum-square
with the reasoning recorded.

Contributors: initial tolerance, temperature coefficient, DC bias (ceramics),
ageing, and end-of-life drift.

## 3. Worked cases already established

### 3.1 8V8 rail against the VCollector floor — **PASS**

TI require VCollector ≥ 8 V to hold LDOIN at 6 V.

| Contributor | Worst case |
|---|---|
| Rail nominal (`VFB` 0.800 V × 11.0) | 8.80 V |
| LTC3639 feedback accuracy + 1 % divider | rail floor ~8.50 V |
| F601 drop at 25 mA (0.5455 Ω) | −14 mV |
| R201 drop at 25 mA (4.7 Ω) | −118 mV |
| **VCollector worst case** | **8.36 V** |

Margin 360 mV. See [CMU-002](CMU-002-power-budget.md) §6.

### 3.2 Output capacitance at the corner — **PASS with reduced margin**

LTC3639 single-cycle step: COUT > (L/2)(IPEAK/VOUT)² × 100 = **7.5 µF** at
`IPEAK` 230 mA.

| Condition | C601 ∥ C602 |
|---|---|
| Nominal | 9.4 µF |
| At 8.8 V DC bias | ~8.9 µF |
| −10 % tolerance and −22 % X7S over temperature | **~6.3 µF** |

At the corner the step widens from 1.0 % to 1.2 % of VOUT (88 mV → 106 mV),
absorbed by the 800 mV headroom. Note the superseded 10 µF 25 V 1206 part was
worse — ~3.7 µF at its own corner once DC bias took roughly half.

**ISET selection rationale:** U601 pin 11 is left unconnected, selecting
200 mA typical / 230 mA maximum peak current. The historical alternatives were
100 kΩ for approximately 100 mA, or GND for approximately 17 mA. The open-pin
choice sets the 7.5 µF nominal requirement above. Its earlier acceptance relied
on the VCollector headroom; it does not replace a transient/tolerance check.

**Capacitor derating rationale:** C601/C602 are 100 V X7S parts upstream of
F601. They see 8.8 V normally, but the post-fault analysis assumes approximately
67 V continuously after a high-side fail-short and fuse opening (67% of rating;
80% at the AFE's 80 V VBAT limit). The historical ≤50% derating target would
require a higher voltage class; a 200 V solution was rejected for size. Two
4.7 µF 1210 parts were chosen instead of one large 2220 part to reduce flex-crack
exposure. This is an accepted design tradeoff, not verified post-fault endurance;
revisit for higher stack voltage or a stricter derating policy. See F-03 in
[CMU-003](CMU-003-fmea.md).

These two historical decisions were consolidated **2026-10-24**; their original
acceptance dates were not recorded. The current design remains unchanged.

### 3.3 D601 standoff against the OTP rail — **PASS**

| Condition | Voltage |
|---|---|
| Normal rail | 8.80 V |
| **OTP rail with R604 fitted** | **11.1 V** |
| OTP rail at resistor tolerance | ~11.34 V |
| D601 VRWM | 12 V |
| D601 VBR minimum | 13.3 V |

Margin to VBR min is 2.0 V. A 10 V part (VBR min 11.1 V) would conduct on the
OTP rail — see [CMU-003](CMU-003-fmea.md) F-07.

## 4. To be completed

- [ ] **Cell measurement error chain** — 100 R 0.1 % filters, 470 nF, BQ79616
      ADC gain/offset over temperature, against the accuracy requirement in
      CMU-001. This is the CMU's primary function and its accuracy budget is
      not yet written.
- [ ] Balance current tolerance: 20 R 2W parts, tempco, plus copper resistance
      extracted from the saved layout
- [ ] NTC divider accuracy over the temperature range
- [ ] Daisy-chain termination tolerance
- [ ] Component stress table: every part's applied voltage, current, power and
      temperature against its rating, with derating percentages
- [ ] Confirm no part exceeds the derating policy CMU-001 sets
The [cell-voltage input-filter study](../sim/spice/cell-voltage-input-filter/README.md)
is the only active circuit simulation. It addresses the first item above; the
other stress/tolerance questions are engineering open items, not additional
SPICE studies. Its Qucs-S model maps the fitted population and does not rely on
the partial KiCad simulation fields currently present on Q201. Numerical checks
do not close the measurement error budget or replace bench correlation.

## 5. Circuit simulation scope and outstanding transient risks

### 5.1 Active study — cell-voltage input filter

The [implemented circuit study](../sim/spice/cell-voltage-input-filter/README.md)
uses the full 16-cell VC ladder, actual tap fuses, shared CB network and local
reference path. One repeated odd/OFF/even/OFF study checks external VC/CB
recovery during 5 ms quiet windows and reports residual DC offsets. Cell/wiring
impedance, input-current return paths and effective capacitance require physical
characterization. There is no internal ADC or digital-filter model; the study
does not close the measurement accuracy budget or guarantee firmware timing.

The fitted circuit has 17 sense resistors, 16 differential VC capacitors and a
separate VC0-to-GND capacitor. The former description of 17 independent 47 µs
cell filters was not valid for this coupled network. Even an isolated differential
pair with two 100 Ω legs and 470 nF has a 94 µs time constant; the full ladder
and AFE measurement chain require their own analysis.

### 5.2 Risks outside the active simulation plan

The buck-failure, tap-mis-mate and supply-startup simulation plans have been
removed. No other transient/SPICE study is scheduled. Correct-order insertion,
mis-mating, buck-fault energy, supply startup, OTP rail transitions, conducted
transients, ESD and switching-node immunity remain unvalidated hardware risks;
removing a planned simulation is not an acceptance decision.

In particular, the historic mis-mate current estimate remains unverified:
four 4.2 V cells across 40 Ω alone give 420 mA, while the actual path depends on
connection order and protection behavior. Preserve the VC/CB pin constraints in
[CMU-008 §3.1](CMU-008-interface-control.md) and the open FMEA findings. Do not
infer a clamp characteristic or survivability from absolute-maximum ratings.

## 6. Acceptance

- [ ] Every worst case has a stated criterion from CMU-001 and a pass/fail
- [ ] No component exceeds its derating policy
- [ ] Cell measurement accuracy meets requirement at the corner
Mis-mate survivability remains unvalidated and outside the active simulation plan.
