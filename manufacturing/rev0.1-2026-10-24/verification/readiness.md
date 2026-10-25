# Manufacturing readiness — 2026-10-24

## Passed file checks
- Configured ERC: 0 violations.
- Refilled DRC: 0 violations, 0 unconnected, 0 schematic/PCB mismatches.
- Source hashes unchanged; 18 unique model paths resolved.
- 157 fitted components; 37 purchased DNP positions; 194 purchased pieces.
- All 448 plated drill locations/sizes match the source within native
  Excellon rounding (maximum 0.000500 mm); no NPTH.
- 157 STEP component occurrences match fitted BOM and placements.
- Both STEP files contain valid solids; assembly STEP/STL bounds agree.
- STL: 85598 native facets, 4279984 bytes; no simplification.
- All 13 Gerber plots independently parsed/rendered; eight copper layers.
- IPC: 912 pad/via records, coordinates and pin/net partition checked.

## Existing disabled categories audited separately
Supplemental ERC: 71 four-way-junction notices and 28 stock wildcard
footprint-filter mismatches. Supplemental PCB check: 26 footprint-filter
mismatches. These concern existing schematic presentation/library filters;
no source rule settings, exclusions, wiring or footprint geometry changed.
See the full supplemental reports for every affected item.

## Export-specific findings handled
The native KiCad IPC exporter produced invalid via soldermask integers.
The derived file was normalized to actual per-via tenting and 80-column
records. Original output and correction evidence are retained. IPC units
are CUST 0 (0.0001 inch); other manufacturing coordinates are mm.
The Gerber job outline size includes line stroke. Route to the 99 x 61 mm
outline centreline. Its 1.708 mm board thickness is a CAD estimate, not the
Eurocircuits 1.604 mm starting-material basis.
Bare-board STEP body thickness is 1.568 mm (native export excludes surface
copper/mask solids). This is not a finished-thickness guarantee.

## Open confirmations before ordering/assembly
1. Eurocircuits accepts the exact eight-layer buildup, finished thickness,
   tolerance, finish and open-via construction.
2. Assembler accepts or revises the stencil/process for U201/U601 exposed
   pads over open vias. Candidate paste is not production-approved.
3. Live DigiKey stock/MOQ and assembler feeder attrition are checked. No
   extras or substitutes are silently added.
4. Thermal performance, measured/guaranteed impedance, EMC/isolation,
   fault behavior, firmware and first-board bring-up remain unvalidated.

Status: manufacturing files prepared and checked; supplier/process review
and engineering qualification remain open. No order, publication or Git
commit/tag was made. This is not an unconditional production sign-off.
