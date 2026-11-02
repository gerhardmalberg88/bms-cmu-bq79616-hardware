# BMS CMU modal and PSD screening

Copyright (C) 2026 Gerhard Malberg. SPDX-License-Identifier: CERN-OHL-P-2.0

**[Read the results](report/README.md): completed CPU/GPU runs, provisional
because componentwise RMS mesh convergence failed.** The saved board and all
recorded stage artifacts were verified before publishing the existing
2026-11-02 studies. No FEM rerun was needed for this publication.

The [case](case.json) specifies the homogenized PCB, distributed fitted-component
masses, rigid annular H1–H4 contacts and synthetic independent X/Y/Z excitation.
Saved thickness is 1.708 mm. The report documents assumptions and numerical limits.
Historical uncached totals were **7.90 minutes CPU** and **53.20 minutes GPU**,
including both meshes and reporting, excluding installation and image builds.
These measurements are estimates for similar reruns, not runtime guarantees.

## Verify or republish

From the hardware repository root, with Python 3.11+ (standard library only):

```bash
python3 sim/mechanical/modal-psd/publish.py --verify-report
python3 -m unittest discover -s sim/mechanical/modal-psd -p 'test_*.py'
```

Reading or verifying the compact report requires no lab checkout, container,
GPU, or native archive. To republish the **existing** verified study:

```bash
python3 sim/mechanical/modal-psd/publish.py \
  --native-root /path/to/archived-native-results
```

The supplied directory must contain `cpu/{coarse,fine}`, `cuda/{coarse,fine}`,
both study/comparison records and the two backend-comparison JSON files.
The publisher verifies every artifact listed by the original stage manifests,
checks case/source consistency and preserves the failed mesh verdict. Changed
inputs or corrupt artifacts stop publication before replacing the report.
`--output /path/to/another/report` selects a new publication directory.

`report/provenance.json` records relative native-artifact paths and SHA-256
hashes, run times, image identities and the available original workflow
fingerprint. The historical run commit was not recorded. The later generic lab
revision below is for optional reproduction and is not claimed as the original
run revision. Historical source paths in the native archive are left unchanged.

## Optional new simulations

Use the separately installed, generic
[PCB Mechanical Lab](https://github.com/gerhardmalberg88/pcb-mechanical-lab)
CLI and its installed CPU/tools/CUDA images. The case-driven interface was
checked at revision `3c2232a8b95323f8ac1436c525a07656c6868692`.
This hardware case adds no board-specific dependency to that lab.

Run backends sequentially and select dedicated, initially empty working
directories **outside both the hardware checkout and the lab checkout**:

```bash
pcb-mechanical study --case sim/mechanical/modal-psd/case.json \
  --backend cpu --time-budget-minutes 60 --output /path/to/mechanical-work/cpu
pcb-mechanical study --case sim/mechanical/modal-psd/case.json \
  --backend cuda --time-budget-minutes 60 --output /path/to/mechanical-work/cuda
```

The CLI snapshots the saved board read-only. The case uses a 3 mm in-plane
mesh and the study compares it with 2 mm; both use two thickness layers and
quadratic solids. The original memory/unknown limits remain in the case.
The tool intentionally rejects native output inside a source hardware checkout.
`study` returns nonzero for failed convergence even when every solve completes.
The historical publisher is intentionally not a general acceptance tool for
changed models: new boards, assumptions or acceptance verdicts require a new
reviewed publication baseline. It does not launch backend comparison jobs.

## Storage

Only compact CSV/JSON evidence, the report and two plots are versioned here
(under 5 MiB). Existing raw meshes, matrices, modes and logs remain in the
external archive. No duplicate native output, container build, cache purge or
deletion was needed. Their original licenses and provenance are preserved.
