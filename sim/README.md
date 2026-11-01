# CMU simulations

Supported platform: Linux. The only planned circuit simulation is the
[BQ79616 cell-voltage input filter](transient/cell-voltage-input-filter/README.md),
using Qucs-S with ngspice. It is **a plan only**: no schematic, netlist, model,
launcher or circuit simulation result is supplied yet.

## Scope and status

| Study | Scope | Status |
|---|---|---|
| [Cell-voltage input filter](transient/cell-voltage-input-filter/README.md) | Fitted 16S cell terminals through J401, tap fuses, VC/CB networks and realistic loading/coupling to U201 measurement inputs | Single active circuit plan; topology inspected, implementation pending |
| [COMH/COML EM](em/README.md) | On-board U201-to-J501/J502 communication paths, filters and transformers; excludes communication cables | Completed CPU cases and component-network composition; provisional results with documented limitations |
| [Balancing-resistor thermal](thermal/cell-balancing-resistors/README.md) | Resistor-only steady heating and PCB cooling | Twelve completed CPU cases; BMS thermal scope closed; domain-convergence limitation retained |

The input-filter study will establish the actual multi-channel circuit first,
then investigate measurement error from component bias/tolerance, input loading,
shared impedance, capacitive/inductive coupling and balancing transitions. Its
preferred improvement hypothesis is a measurement quiet time based on the worst
channel, combined with matching effective filter capacitance. See the case plan
for alternatives, evidence requirements and the full scenario matrix.

The former buck-failure, tap-mis-mate and supply-startup circuit plans and their
launchers have been removed. Their shared SPICE parameter include and unused
model-library directories have also been removed. Related hardware hazards remain
unvalidated; they are not additional simulation commitments. Dated manufacturing
packages retain their historical documentation/source snapshots.

## Layout

```text
sim/
├─ transient/
│  └─ cell-voltage-input-filter/
│     └─ README.md              the single circuit plan; no implementation yet
├─ em/                         COMH/COML inputs, workflows and compact results
│  ├─ MODELS_PROVENANCE.csv     provenance for the existing EM component model
│  └─ transformer-coupling/    existing balanced component-network composition
├─ thermal/                    completed steady cases and provisional reports
├─ source-normalization.json   historical source-hash migration evidence
├─ source_normalization.py     verifier used by the existing EM workflow
└─ results/                    ignored native outputs
```

## Future circuit workflow

When implementation is requested, use one editable Qucs-S project and a
reproducible ngspice netlist for the same circuit. JSON will hold case parameters
and provenance. Record tested Linux tool versions then; no installation or model
implementation is part of this planning change. Place eventual raw outputs under
`sim/results/cell-voltage-input-filter/` and compact reviewed reports beside the
case documentation. Model sources, assumptions and licensing must be recorded
before importing third-party content.

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
