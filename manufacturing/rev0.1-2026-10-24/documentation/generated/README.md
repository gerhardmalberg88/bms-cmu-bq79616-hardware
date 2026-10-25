# Supporting generated records

Copyright (C) 2021-2026 Gerhard Malberg.
SPDX-License-Identifier: CERN-OHL-P-2.0

The dated manufacturing package is the authoritative set for production and
purchasing. These files support source review; do not hand-edit their data.

| File | Origin |
|---|---|
| `bom.csv` | All 194 physical component positions, grouped into 34 MPN rows; `tools/manufacturing_release.py --phase bom` |
| `schematic.pdf` | Copy of the verified seven-sheet release schematic PDF |
| `netlist.net` | Copy of the release's native KiCad schematic netlist; includes schematic-only alternatives |
| `erc_report.rpt` | Human-readable summary generated from the release ERC JSON; the original JSON is retained in the package |
| `library-provenance.csv` | Matching upstream provenance rows plus imported file hashes; `tools/export_library_provenance.py` |

From the BMS repository root, with the shared library checked out alongside it:

```console
python tools/export_library_provenance.py --upstream ../kicad-libraries
python tools/export_library_provenance.py --upstream ../kicad-libraries --check
```

The actual upstream path may differ in a nested workspace. This check compares
content and recorded licensing metadata; it does not invent a commit ID.
Original symbol blocks must match, and each footprint/model file must be
byte-identical. The manifest's Git blob IDs must also match the source bytes.

Use KiCad's Python for `tools/gen_doc_tables.py --check`; that separate check
verifies the generated Markdown tables against schematic and PCB population.
