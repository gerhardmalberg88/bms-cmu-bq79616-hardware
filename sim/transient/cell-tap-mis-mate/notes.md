# cell-tap-mis-mate

**Verifies:** CMU-003 F-14, CMU-004 §5.1
**Status:** skeleton — no netlist

## Why this one matters most

F-14 is the dominant hazard in the FMEA, and its mitigation — the two 20 R
balance resistors — has never been checked against anything but arithmetic.
This is the simulation with the most to say.

## What it must model

A 20-way tap connector mated out of order, so several cells land across one
`CBn` / `CBn-1` pair at once.

- Cell stack as ideal sources at `vcell_max`, one per tap
- Per channel: 2 × `r_bal` (20 R) in the balance path, `r_filt` (100 R 0.1 %)
  and `c_filt` (470 nF) in the sense path
- Tap fuse as `r_fuse` (0.5455 Ω); the fuse does not open on this timescale
- Connector insertion as a switch closing at t = 0, one pin at a time in a
  deliberately wrong order
- BQ79616 `CB` and `VC` pins as clamps at their absolute maxima, so an excursion
  past them is visible rather than silently absorbed

## What it simplifies

_State every simplification here. An unstated one is a lie in a waveform._

Candidates to record once written: ideal cells with no internal impedance, no
harness inductance, instantaneous contact, and no AFE internal protection
structures beyond the abs-max clamps.

## Pass criteria

| Figure | Expected | Tolerance | Source |
|---|---|---|---|
| Peak current through a balance path | re-derive from the actual fault path; four 4.2 V cells across 40 ohms alone give 420 mA | not established | CMU-003 F-14 |
| `CBn` to `CBn-1` excursion | within −0.3 to +16 V | hard limit | CMU-008 §3.1 |
| `VCn` to `VCn-1` excursion | within ±80 V | hard limit | CMU-008 §3.1 |
| Worst adjacent-pin voltage, J401 | ~8.4 V (2 cells) | ±10 % | CMU-008 §3.1 |
| Worst adjacent-pin voltage, J402 and J403 (schematic-only alternatives) | ~4.2 V (1 cell) | ±10 % | CMU-008 §3.1 |

**The CB limit is the one that decides the design.** VC tolerates ±80 V; CB
tolerates 16 V, and a 4-cell mis-mate reaches ~16.8 V. If simulation confirms
the excursion exceeds 16 V, the cell-tap TVS evaluated in CMU-003 F-14/O-6 has to be
revisited on evidence rather than on the leakage argument alone.
