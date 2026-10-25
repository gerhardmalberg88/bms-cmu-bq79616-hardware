# buck-fail-short

**Verifies:** CMU-003 F-01, CMU-002 §9
**Status:** skeleton — no netlist

## What it must model

The LTC3639 high-side switch failing short, so the pack drives node A directly.

- Pack as an ideal source, swept 15 V (6S low) to 80 V (`VBAT` max)
- The fault loop: `r_inrush` (R601 4R7) + `dcr_buck` (L601 1.65 Ω) +
  `r_fuse` (F601) + two tap fuses, about 8 Ω total
- `l_buck` (220 µH) in series — it saturates at 0.42 A, so above that it is
  resistive and the inductance must be collapsed, not left ideal
- D601 as a 12 V standoff clamp, VBR 13.3 V min, VC 19.9 V at 30.2 A
- F601 as a behavioural I²t element, `i2t_fuse` = 0.0287 A²s

## What it simplifies

_To be written._ At minimum: the failure is instantaneous, the pack has no
internal impedance, and the fuse model is a threshold rather than a real melting
element.

## Pass criteria

| Figure | Expected | Tolerance | Source |
|---|---|---|---|
| Fault current at 16S (67.2 V) | 6.7 A | ±15 % | CMU-002 §9 |
| Fault current at `VBAT` max (80 V) | 8.3 A | ±15 % | CMU-002 §9 |
| F601 clearing time at 6.7 A | ~640 µs | order of magnitude | CMU-002 §9 |
| Energy into D601 before clearing | ~69 mJ | ±30 % | CMU-004 §5.1 |
| Peak current against F601 interrupting rating | far below 50 A | hard limit | CMU-003 F-01 |

## Caution on the fuse result

`I²t` is a datasheet figure and a SPICE fuse is a switch with a threshold, so a
clearing time out of this simulation is arithmetic wearing a waveform's
clothes. Treat it as a sanity check that the loop resistance and the clamp
interact as expected — not as evidence about the fuse itself.
