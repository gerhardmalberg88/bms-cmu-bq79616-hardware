# Simulation model library

Shared models and parameters for the simulations in `../`.

## Layout

| Directory | Holds | Committed? |
|---|---|---|
| `models/` | Original behavioural subcircuits, `.sub` | **yes** |
| `va/` | Original Verilog-A source, `.va` | **yes** |
| `vendor/` | Third-party models | **no — gitignored** |
| `common.inc` | Shared parameters, traced to `../../docs/` | yes |
| `MODELS_PROVENANCE.csv` | One row per model, including absent vendor ones | yes |

The split is by **provenance, not by language**. XSPICE and Verilog-A models
live together in this library because they are the same kind of asset in
different implementation languages — nothing is gained by separating them, and a
model rewritten from one to the other should evolve in place rather than move.

## Rules

**1. Commit source, never build output.**

`.va` is source and belongs in `va/`. The `.osdi` that OpenVAF produces is a
compiled, platform-specific shared library and must never be committed — it
would be wrong for anyone on a different platform and unreviewable for everyone.
This mirrors what the KiCad library already does: the generators are committed
alongside their output, and the output is reproducible from them.

**2. Vendor models are fetched, not stored.**

Manufacturer model terms vary; usage permission does not establish redistribution
permission. Keep vendor models in `vendor/`, which is gitignored, and record an
authorized retrieval method before implementing it in `run.sh`. Each still
gets a `MODELS_PROVENANCE.csv` row — the register records what a simulation
*depends on*, not merely what is present in the tree.

A model whose `redistribution_status` is anything other than `cleared_*` must
never be committed anywhere in this repository.

**3. Original models are CERN-OHL-P-2.0.**

Same licence as the rest of the repository. Put an SPDX header in every file:

```spice
* <name> - <one line on what it models>
* Copyright (C) 2021-2026 Gerhard Malberg
* SPDX-License-Identifier: CERN-OHL-P-2.0
* Verifies: <document and section this model is built to support>
```

Independently authored behavioral models may use cited datasheet parameters.
Record their authorship and sources; do not copy vendor model code, plots or
documents into the project under an assumed project license.

**4. Do not vendor the standard XSPICE code models.**

KiCad 10 ships ngspice together with `analog.cm`, `digital.cm`, `table.cm`,
`tlines.cm`, `xtradev.cm`, `xtraevt.cm` and `spice2poly.cm` in
`lib/ngspice/`. Those primitives are available already. `models/` is for models
of *this design's* parts, not for copies of a simulator's own libraries.

## Verilog-A workflow

```console
openvaf mymodel.va          # produces mymodel.osdi
```

Then in the netlist:

```spice
.osdi mymodel.osdi
N1 node1 node2 mymodel
```

Requires ngspice 39 or newer. ADMS is deprecated and should not be used.
OpenVAF runs on Windows and Linux; there is no macOS build.

`run.sh` compiles `.va` to `.osdi` on demand and writes it to
`../../results/`, which is gitignored — never into `va/`.

## What this library will need

Almost nothing in this design has a usable vendor ngspice model, so this is
mostly original modelling work rather than model collection:

| Part | Vendor model | What is needed here |
|---|---|---|
| LTC3639 | LTspice only, encrypted, LTspice-specific syntax | behavioural buck: switch, 230 mA current limit, feedback |
| BQ79616-Q1 | none exists | mode-dependent current sink plus the NPNB loop |
| Fuses | none exists | behavioural I²t element |
| SM91502AL | possibly | trivial from datasheet L and coupling k |
| TVS, diodes | sometimes redistributable | vendor model if cleared, else generic |

## When to extract this into its own repository

**Trigger: a second module needs these models.**

A separate repository is worth its cost once several boards share the same
models; `kicad-libraries` is at that point, with a large asset count and more
than one consumer. This library is not: it has one consumer and few models.
Extracting it early buys nothing and adds a second repository to keep in step,
which is how copies of a shared library drift apart.

When the trigger fires, extract **`sim/lib/` as one repository**, keeping this
provenance split. Do not split it by language into separate XSPICE and Verilog-A
repositories: they would always be cloned together, which is the signature of a
seam that should not exist.
