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
Transient events are analysed here rather than in a separate document because
they are the same kind of question — stress versus rating — freeze at the same
point, and feed the same derating tables.

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
- [ ] **Resolve the partial KiCad simulator setup.** `Q201` is the only
      component carrying `Sim.Device` and `Sim.Pins` fields. KiCad's built-in
      simulator builds its netlist from those, so a half-configured schematic
      yields one that silently omits every other part. Either populate them
      across everything that matters or remove them from Q201; a partial setup
      is the worst of the three states. See [`../sim/`](../verification/source-snapshot.zip).

## 5. Transient events

### 5.1 Layout-independent — analyse now

- [ ] **Cell tap mis-mate / hot-plug.** The dominant hazard. Constraint is the
      asymmetry: `VCn` to `VCn-1` tolerates ±80 V, `CBn` to `CBn-1` only
      −0.3/+16 V. Re-derive the historical ~133 mA claim: four 4.2 V cells
      across 40 ohms alone give 420 mA; actual clamping and current paths matter.
      Interleaved pin order holds the worst adjacent pair to ~8.4 V.
      **Quantify the energy and confirm the 20 R sizing.** Simulation planned
      at [`../sim/transient/cell-tap-mis-mate/`](../verification/source-snapshot.zip).
- [ ] **Connecting a healthy pack, in the correct order.** Distinct from the
      mis-mate case above and currently unanalysed. A 20-way connector does not
      make all contacts simultaneously even when correctly oriented, so partial
      stack potentials appear across VC and CB pairs while it seats. Four
      things happen at once:

      1. **Contact sequencing.** Connecting from the bottom of the stack upward
         bounds each channel to a single cell step, because the node below is
         already at potential. Any other order allows several cells across one
         pair, which is the F-14 hazard rather than this one.
      2. **Filter charging.** Each channel charges `c_filt` 470 nF through
         `r_filt` 100 R, τ = 47 µs, peak 42 mA for a 4.2 V step. Seventeen
         channels, independent of one another.
      3. **BAT pin hot-plug filter.** R202 30 R 0.5 W 150 V in series to the
         BAT pin with C208 10 nF 250 V C0G to AVSS — a 531 kHz low-pass that
         slows the edge the pin sees and caps the current into its ESD
         structures at V/30, so 2.2 A initial at 67 V decaying with a 300 ns
         time constant. Stored energy is ½CV² = 22 µJ at 67 V, dissipated in
         R202 over roughly the same interval: ~75 W peak for 300 ns, which a
         pulse-proof 0805 absorbs, with negligible average power. **This filter
         exists for exactly this event and is otherwise undocumented.**
      4. **Buck and AFE start.** The LTC3639 starts into discharged
         C601 ∥ C602 with soft-start set by C605 on SS. `VBAT` crossing its
         minimum triggers POR into SHUTDOWN; ACTIVE needs a WAKE ping.

      Verify R202 pulse energy against its single-pulse rating, confirm the
      C208 edge rate against the BAT pin specification, and confirm no VC or CB
      pair exceeds its absolute maximum at any point in a correct-order
      insertion. Analysis by inspection until
      [`../sim/transient/cell-tap-mis-mate/`](../verification/source-snapshot.zip)
      exists, which can cover the correct-order case as a second scenario at
      near-zero extra cost.
- [ ] Buck fail-short energy into F601 and D601 — 6.7 A for ~640 µs, ~69 mJ
- [ ] Startup inrush, 20 mA `ISTARTUP`
- [ ] OTP programming rail step, 8.8 V → 11.1 V
- [ ] Conducted transients from the pack: contactor switching, load dump

### 5.2 Layout-dependent — after routing

- [ ] ESD immunity at every connector
- [ ] Surge coupling
- [ ] LTC3639 SW node ringing
- [ ] dV/dt coupling into the daisy chain

## 6. Acceptance

- [ ] Every worst case has a stated criterion from CMU-001 and a pass/fail
- [ ] No component exceeds its derating policy
- [ ] Cell measurement accuracy meets requirement at the corner
- [ ] Mis-mate transient survivable with margin
