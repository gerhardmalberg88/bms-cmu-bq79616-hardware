# CMU simulations

Simulation cases and results for the CMU design in `../design/`.
[EM](em/README.md) is limited to the on-board COMH/COML paths from U201 to
J501/J502, including their filters and isolation transformers. Cables, mating
connectors, unrelated magnetics and other EM studies are outside this repository's
simulation scope. Native results stay under ignored `sim/results/em/`; compact
reviewable outputs are published beside the EM cases.
[Thermal](thermal/README.md) contains twelve completed steady cases and their
provisional results; its BMS simulation scope is closed.
The circuit cases below use the existing Qucs-S/ngspice scaffolding.

> **Every planned simulation must verify a claim made in `../docs/`.** A simulation
> that verifies nothing is a toy. The claim is named in the netlist header and in
> the index below, and the cited document carries a back-reference.

## Tooling

**No completed transient circuit simulation is supplied.** Each transient case currently contains notes
and a launcher, with no circuit netlist, checked baseline or validated model.
`run.sh` exits 2 until its netlist exists. The routed PCB and manufacturing
exports do not change this status. Local tool installation is not a property
of the published repository; install dependencies when implementing a case.

| Tool | Version target | Role | Repository status |
|---|---|---|---|
| ngspice | 39 or newer | simulation engine | external dependency; no validated run |
| Qucs-S | 25.1 or newer | schematic capture, netlist generation | external dependency; sources pending |
| OpenVAF | select when required | Verilog-A to `.osdi`, if used | no Verilog-A model supplied |
| Python | 3.11+ | planned post-processing, `check.py` | checks pending |

Set Qucs-S to the **ngspice** backend, not Qucs's own. The two are not
interchangeable and the netlists differ.

ngspice **39 or newer** specifically, because that is where OSDI arrived; below
it there is no Verilog-A path.

### KiCad and vendor tools

KiCad's Linux GUI simulator uses the ngspice shared library and distribution-provided
XSPICE code models. Do not vendor these standard libraries into `lib/`.
The scripts require the standalone `ngspice` executable on PATH; `kicad-cli`
does not provide a simulation subcommand.

The LTC3639 vendor model targets LTspice. No compatible ngspice model is
distributed here. Any translated or behavioral model needs its own validation
and provenance review — see [`lib/README.md`](lib/README.md).

## Layout

```text
sim/
├─ README.md                   this file
├─ lib/                        see lib/README.md
│  ├─ models/                  original behavioural subcircuits - committed
│  ├─ va/                      original Verilog-A source - committed
│  ├─ vendor/                  third-party models - GITIGNORED, fetched at run time
│  ├─ MODELS_PROVENANCE.csv    one row per model, including absent vendor ones
│  └─ common.inc               shared params, traced to ../docs/
├─ em/                         COMH/COML cases; installed pcb-em toolchain
│  ├─ isospi-2d/               COMH/COML cross-section inputs
│  ├─ isospi-3d/               COMH/COML IC, filter and connector PCB regions
│  └─ transformer-coupling/    balanced component model joining the PCB networks
├─ thermal/                    completed steady thermal scope; provisional results
│  └─ cell-balancing-resistors/ completed steady cases and compact result snapshot
├─ transient/
│  ├─ buck-fail-short/
│  ├─ cell-tap-mis-mate/
│  └─ startup-inrush/
└─ results/                    generated output; gitignored
```

The following is the intended structure once a case is implemented. Currently
only `run.sh` and `notes.md` are present in each circuit case. EM includes case
inputs for its shared pipeline; thermal includes completed steady inputs and
results with documented limitations.
The EM model flow is shown in [em/README.md](em/README.md). The table below
applies to transient circuit cases:

| File | Committed? | Why |
|---|---|---|
| `<name>.sch` | yes | Qucs-S source, editable |
| `<name>.cir` | **yes** | generated netlist — lets a reviewer with only ngspice run it |
| `run.sh` | yes | one command, no GUI |
| `check.py` | yes | extracts figures and compares against the baseline |
| `models.txt` | if needed | `<filename> <url>` per line; vendor models to fetch |
| `expected/` | yes | baseline figures, once reviewed |
| `notes.md` | yes | what it models, what it simplifies, what it proves |

**Commit the netlist, not just the schematic.** `.sch` is Qucs-S's own format;
someone with ngspice alone cannot open it, and a simulation nobody else can run
is not evidence.

## Index

| Simulation | Verifies | Status |
|---|---|---|
| [COMH/COML board-only EM](em/README.md) | CMU-007: U201 pads through filters/transformers to board connector contacts | CPU finite-element and balanced component model; provisional outputs and numerical limitations are recorded in the EM report |
| [Cell balancing resistors — thermal](thermal/cell-balancing-resistors/README.md) | CMU-006: resistor-only steady heating and PCB cooling | 12 CPU cases complete; simulation scope closed; domain-unconverged results published |
| `transient/buck-fail-short` | CMU-003 F-01 and CMU-002 §9 — 6.7 A through the ~8 Ω loop, F601 clearing in ~640 µs, energy into D601 | skeleton |
| `transient/cell-tap-mis-mate` | CMU-003 F-14 and CMU-004 §5.1 — re-derive the fault current and check the `CBn` to `CBn-1` excursion; the historical ~133 mA estimate is unverified | skeleton |
| `transient/startup-inrush` | CMU-002 §4 — 20 mA `ISTARTUP` against the rail and the VCollector ≥ 8 V floor | skeleton |

The mis-mate simulation matters most: it is the dominant hazard in the FMEA and
the only one whose mitigation (the two 20 R resistors) has never been checked
against anything but arithmetic.

## Model provenance — read before adding a model

The full rules are in [`lib/README.md`](lib/README.md). In short: vendor SPICE
models are third-party content with licences, exactly like a datasheet PDF, so
they live in `lib/vendor/` which is gitignored and fetched at run time, while
original models live in `lib/models/` and `lib/va/` and are committed. Every
model gets a `MODELS_PROVENANCE.csv` row either way — the register records what
a simulation *depends on*, not merely what is present in the tree.

### Where this library is heading

It stays inside this repository for now. A shared repository earns its cost once
several boards depend on the same models, as `kicad-libraries` does; this one
has a single consumer and few models. Extracting it early buys nothing and adds
a second repository to keep in step, which is how copies of a shared library
drift apart.

**Extraction trigger: a second module needs these models.** At that point
extract `lib/` as **one** repository, keeping the provenance split. Do not split
it by language into separate XSPICE and Verilog-A repositories — they would
always be cloned together, which is the signature of a seam that should not
exist, and a model rewritten from one language to the other would move between
repositories instead of evolving in place.

## Running

```console
cd transient/buck-fail-short
./run.sh
```

`run.sh` fetches any vendor models listed in `models.txt`, invokes ngspice in
batch mode on the committed `.cir`, writes raw output to `../../results/<name>/`,
and calls `check.py` to compare extracted figures against `expected/`.

Exit codes, so the simulations can gate a release the way ERC does:

| Code | Meaning |
|---|---|
| 0 | ran, and every figure is within tolerance |
| 1 | ran, but a figure moved outside tolerance |
| **2** | **no netlist yet — this simulation is still a skeleton** |
| 3 | ngspice not found |
| 4 | ran, but there is no `check.py`, so nothing was verified |

The three transient skeletons currently exit 2. The EM workflow has its own
bounded study runner and native results.

## Limits of the planned circuit simulations

- **Thermal behaviour.** Junction temperatures need copper geometry and
  enclosure conditions — see [completed steady thermal scope](thermal/README.md).
- **Real fuse clearing.** `I²t` is a datasheet figure; a SPICE fuse is a switch
  with a threshold, so a clearing time from simulation is arithmetic dressed up
  as a waveform. Treat it as a sanity check, not evidence.
- **Signal integrity from the stackup.** Requires geometry/material analysis
  beyond these circuit models — see [COMH/COML EM scope](em/README.md).

## Open items

- **`Q201` is the only component in the schematic carrying `Sim.Device` and
  `Sim.Pins` fields.** KiCad's built-in simulator uses those to build its
  netlist, so a half-configured schematic produces one that silently omits every
  other part. Either populate them across everything that matters or remove them
  from Q201 — a partial setup is the worst of the three states. Tracked in
  CMU-004 §4.
- No `check.py` exists yet for any simulation. Until one does, `run.sh` exits 4
  rather than reporting a pass.

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
