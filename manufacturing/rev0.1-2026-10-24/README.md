# CMU revision 0.1 — 16S prototype package

Exported 2026-10-24 with KiCad 10.0.4. Target: Eurocircuits.
**Files prepared and checked; supplier/process confirmations remain open.**
Read [readiness](verification/readiness.md) before ordering.

- [fabrication.zip](fabrication.zip): bare-board production data and instructions.
- [complete-package.zip](complete-package.zip): all deliverables and verification.
- [Fabrication instructions](fabrication/fabrication-notes.pdf).
- [Fitted BOM](assembly/bom.xlsx), [assembly instructions](assembly/assembly-instructions.pdf)
  and [placement CSV](assembly/placement.csv).
- [DigiKey workbook](procurement/digikey-order.xlsx) and [import CSV](procurement/digikey-import.csv):
  **194 pieces, including all 37 DNP parts which must remain unfitted**.
- [Seven-sheet schematic PDF](documentation/schematic.pdf).
- [Populated STEP](3d/CMU-rev0.1-16S.step), [board STEP](3d/CMU-rev0.1-board.step),
  [GitHub-viewable STL](3d/CMU-rev0.1-16S.stl).
- [Ray-traced PCB image](3d/CMU-rev0.1-16S-raytraced.png).
- [Verification report](verification/readiness.pdf), [manifest](manifest.json)
  and [checksums](SHA256SUMS).

The fitted assembly contains 157 components; all are on top. Purchasing
includes another 37 DNP components; there are no extra spares or alternative
MPNs. Cable harness parts and mounting hardware are outside this PCB BOM.

Retained design issue date: 2026-09-04. Exact source hashes and a source ZIP
identify the saved design. There is no source Git commit/tag yet. No design
files were modified, no order placed and no files uploaded/published.

Open items: construction/finished-thickness confirmation; assembler review
of exposed-pad paste over open vias; live part availability; unfinished
thermal/SI/fault/bring-up validation. The supplied stencil is a candidate.
See [CMU-009](documentation/CMU-009-manufacturing.md) for reproduction commands.
See [NOTICE.md](NOTICE.md) for license/provenance notices. Full source,
documentation and simulation scaffolding are in verification/source-snapshot.zip.
Copied documentation links that require the full repository point to that ZIP.
SHA256SUMS covers package contents except itself and the complete ZIP; that
ZIP has its own adjacent SHA-256 file. The fabrication ZIP contains one
single-board revision only.
