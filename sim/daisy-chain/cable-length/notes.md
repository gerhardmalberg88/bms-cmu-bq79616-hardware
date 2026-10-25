# cable-length

**Verifies:** CMU-008 open item O-4
**Status:** skeleton — no netlist

## What it must model

The same link as `transformer-coupling`, with a transmission-line model of the
inter-module cable, swept over length to find where the daisy chain stops
working.

- Reuse the transformer and termination from `transformer-coupling`
- Cable as a lossy transmission line: characteristic impedance and per-metre
  loss from the chosen cable type
- Sweep length; find where amplitude or edge rate fails the receive criterion

## What it simplifies

_To be written._ Depends on a cable specification that CMU-001 has not fixed
yet, so any answer is provisional until it does.

## Pass criteria

| Figure | Expected | Tolerance | Source |
|---|---|---|---|
| Maximum length meeting the receive criterion | **the answer O-4 needs** | report with margin | CMU-008 O-4 |
| Amplitude at maximum length | within the BQ79600 receive threshold | hard limit | CMU-008 §4.2 |

## Blocked on

CMU-001 §2 has not yet fixed the daisy-chain data rate or the cable type. Both
change the answer, so this simulation cannot produce a usable number until they
are decided. Do not run it and quote a length before then.
