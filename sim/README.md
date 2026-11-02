# CMU simulations

Supported platform: Linux. The active circuit study is the
[BQ79616 cell-voltage input filter](spice/cell-voltage-input-filter/README.md),
with an editable full 16S Qucs-S circuit and one repeated-cycle ngspice study.
Its results are exploratory predictions with explicit cell, wiring and AFE
assumptions, not hardware-correlated accuracy claims.

## Scope and status

| Study | Scope | Status |
|---|---|---|
| [Cell-voltage input filter](spice/cell-voltage-input-filter/README.md) | Fitted 16S cell terminals through J401, tap fuses, VC/CB networks and realistic loading/coupling to U201 measurement inputs | One repeated odd/OFF/even/OFF cycle study with timestep verification |
| [COMH/COML EM](em/README.md) | On-board U201-to-J501/J502 communication paths, filters and transformers; excludes communication cables | Completed CPU cases and component-network composition; provisional results with documented limitations |
| [Balancing-resistor thermal](thermal/cell-balancing-resistors/README.md) | Resistor-only steady heating and PCB cooling | Twelve completed CPU cases; BMS thermal scope closed; domain-convergence limitation retained |

The input-filter study tests 5 ms balancing-off windows, external VC/CB recovery
and residual DC offsets. It includes no internal ADC or digital-filter model.
Other electrical hazards remain engineering open items, not additional SPICE
simulation commitments.

## Layout

```text
sim/
├─ spice/
│  └─ cell-voltage-input-filter/
│     ├─ circuit/               full editable Qucs-S schematic and ngspice netlist
│     ├─ case.json              single repeated-cycle settings
│     ├─ study.py               export/run/verify/report/all/gui commands
│     └─ report/                compact predictions and verification evidence
├─ em/                         COMH/COML inputs, workflows and compact results
│  ├─ MODELS_PROVENANCE.csv     provenance for the existing EM component model
│  └─ transformer-coupling/    existing balanced component-network composition
├─ thermal/                    completed steady cases and provisional reports
├─ source-normalization.json   historical source-hash migration evidence
├─ source_normalization.py     verifier used by the existing EM workflow
└─ results/                    ignored native outputs
```

## Circuit workflow

From the repository root:

```bash
/usr/bin/python3 sim/spice/cell-voltage-input-filter/setup.py
/usr/bin/python3 sim/spice/cell-voltage-input-filter/study.py gui
/usr/bin/python3 sim/spice/cell-voltage-input-filter/study.py all
```

The case README describes prerequisites, model assumptions, source-preserving
extraction and verification. Raw outputs
remain ignored under `sim/results/cell-voltage-input-filter/`; compact results
live beside the case. No sibling checkout is required.

The case supports the measurement-error budget in
[CMU-004](../docs/CMU-004-stress-and-wcca.md) and the accuracy/latency requirements
in [CMU-001](../docs/CMU-001-requirements.md). A plotted waveform is not a passed
requirement until numerical checks and the physical model's limits are documented.

### Verifying results after the LF source migration

The saved FEM records retain their original source and artifact hashes. The
2026-11-01 line-ending migration is recorded in
[source-normalization.json](source-normalization.json): verification reads the
named historical Git blobs and requires that replacing CRLF with LF produces
exactly the current source bytes. Any other edit fails. A shallow checkout
without the recorded historical objects cannot perform this verification;
fetch the recorded history first. Fresh simulations still use exact current hashes.

To republish existing EM evidence without rerunning FEM, from the repository root:

```bash
bash sim/em/transformer-coupling/run.sh --source-normalization /project/sim/source-normalization.json
python3 sim/em/publish.py --source-normalization sim/source-normalization.json
```

The first command only recomposes the completed PCB networks with the component
model. During migration verification, the pinned container reproduced the previous CSV
and both Touchstone files byte-for-byte; no physical parameters changed.
Published provenance includes both original source hashes and verified current
hashes. The thermal publisher accepts the same explicit `--source-normalization`
option. Existing domain-convergence and hardware-correlation limitations still apply.
