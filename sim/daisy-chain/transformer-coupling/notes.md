# transformer-coupling

**Verifies:** CMU-007, CMU-008 §4
**Status:** skeleton — no netlist

## What it must model

One COMH or COML link across its isolation transformer, from the AFE pin to the
connector.

- T501 and T502 as coupled inductors, using the SM91502AL datasheet inductance
  and coupling factor
- `SC_CT` left floating — this is the point of the topology and must not be
  grounded to make the simulation converge
- 49R9 1 % series resistors R501/R503/R504/R506 and 1k shunts R502/R505
- 220 pF and 100 pF C0G filtering
- CDSOD323-T15C clamps, D501–D504
- Differential drive representative of the BQ79616 COM output

## What it simplifies

_To be written._ Notably: an ideal coupled-inductor pair has no leakage
inductance, no interwinding capacitance and no core loss, all of which shape the
real edge.

## Pass criteria

| Figure | Expected | Tolerance | Source |
|---|---|---|---|
| Differential amplitude at the connector | within the BQ79600 receive threshold | hard limit | CMU-008 §4.2 |
| Edge integrity | no ringing that violates the receive window | qualitative | CMU-007 |
| DC isolation with `SC_CT` floating | no DC path across the barrier | hard limit | CMU-008 §4.1 |

## Convergence warning

If this refuses to converge, the usual fix is a large resistance to ground on
the isolated side. That belongs **inside the simulation only**, recorded above
as a simplification. It must never migrate into the design — the floating
`SC_CT` is a safety property, not an inconvenience.
