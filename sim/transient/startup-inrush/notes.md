# startup-inrush

**Verifies:** CMU-002 §4 and §6
**Status:** skeleton — no netlist

## What it must model

The BQ79616 transition from SHUTDOWN to ACTIVE, drawing `ISTARTUP` = 20 mA,
against the rail and the VCollector floor.

- LTC3639 as a behavioural buck: `vrail` 8.8 V output, `ipeak` 230 mA limit
- `c_out` (C601 ∥ C602, 9.4 µF nominal); also run the 6.3 µF corner from
  CMU-004 §3.2
- `r_fuse` (F601) and `r_pass` (R201 4R7) in the path to the Q201 collector
- AFE as a current step from 23 µA to 20 mA

## What it simplifies

_To be written._ The buck is behavioural, so switching ripple and the Burst
Mode boundary are not represented.

## Pass criteria

| Figure | Expected | Tolerance | Source |
|---|---|---|---|
| VCollector during the step | **at or above 8.0 V throughout** | hard limit | CMU-002 §6 |
| Steady-state VCollector at 25 mA | 8.67 V | ±2 % | CMU-002 §6 |
| Rail sag on the 20 mA step | recovers without crossing 8.0 V | hard limit | CMU-002 §6 |
| Single-cycle output step at the 6.3 µF corner | 1.2 % of VOUT or less | ±20 % | CMU-004 §3.2 |

The 8.0 V floor is TI's requirement for holding LDOIN at 6 V. Crossing it even
briefly during startup is a finding, not a rounding error.
