---
id: CMU-009
title: Manufacturing and Prototype Release Record
rev: 0.1
status: files-prepared-confirmations-open
phase: post-layout
applies_to: bms-cmu-bq79616-hardware rev 0.1, current 16S population
license: CERN-OHL-P-2.0
---

# CMU-009 — Manufacturing and prototype release

The 2026-10-24 package targets Eurocircuits and preserves revision **0.1** and
the design issue date **2026-09-04**. The saved schematic/PCB are routed and
consistent; this supersedes the former README description of an obsolete PCB.
Source files, routing, placement, footprint geometry, stackup and rules were
not edited during package generation.

The same unpublished package was refreshed on **2026-10-24** with consolidated
documentation, license notices and a native KiCad ray-traced PCB image.
Manufacturing artwork, BOM quantities, placements, schematic PDF and STEP/STL
geometry remain unchanged. [NOTICE.md](../NOTICE.md) records licensing and
imported-asset provenance. The complete package, source snapshot and
fabrication-only ZIP each carry `LICENSE`, `NOTICE.md` and `LICENSES/`.

## Configuration and purchasing

The project text variables `REV`, `BOARD_TITLE`, `ISSUE_DATE`, `LICENSE`,
`COPYRIGHT`, `SOURCE` and `MODULE` provide the common title-block metadata;
each sheet refers to them explicitly. Revision **0.1** identifies this
unfabricated prototype. The established scheme uses `0.x` before fabrication
and `A`, `B`, `C` for fabricated revisions. A matching Git tag is intended
when a release is actually committed; none exists for this snapshot.

Reference designators use per-sheet hundreds blocks: `bq79616` 200,
`balance` 300, `cells` 400, `com` 500 and `batterypositive_to_8V8` 600.
If reannotation is required, update all documentation and schematic-text
references with the same annotation map. These configuration conventions were
consolidated on **2026-10-24**, without changing design metadata.

The PCB contains **198 footprints**: **157 fitted components**, **37 DNP
positions**, and **four plated mounting holes**. All fitted components are on
the top side. There are 31 fitted MPNs and 34 purchased MPNs after including
the DNP parts. Purchase **194 pieces for one board**, with zero additional
spares. Purchasing a DNP part does not authorize fitting it.

- Fit J401, J201, J501/J502 and F401–F417/F601. There are 18 fitted fuses.
- Leave the 28 unused-cell zero-ohm links, eight R219–R226 NTC positions and
  R604 unfitted. They are included in purchasing, explicitly labelled
  **PURCHASE, DO NOT POPULATE**. R604 is an OTP programming option; it must not
  be fitted for normal 8.8 V operation.
- J402/J403 and F418–F451 are schematic-only alternatives, absent from this
  PCB. They are not part of the 37 physical DNP positions or purchasing list.
- Cable-side connectors, crimp contacts, wire, screws and standoffs are not
  silently added: their exact assembly selections are outside this PCB BOM.

The DigiKey workbook includes board-count and per-line spare inputs, and a
separate import sheet. The CSV contains fixed one-board quantities; changing
the workbook does not change that CSV. After changing quantities, export the
workbook's **DigiKey Import** sheet as CSV and upload that file. Map supplier
part number, quantity and customer reference. Check all matches before adding
to a cart. No upload, order or purchase was performed.

The 34 exact MPN/SKU mappings were checked against DigiKey public product
listings; links and packaging changes are recorded in `part-verification.json`
and the workbook. No electrical substitutes were selected. Listings showed
possible availability issues for CGA3E2X7R1H104K080AE, CRCW060349R9FKEAHP,
M80-5T10442MC and NCU18XH103F6SRB. These are cached listing observations, not
a live stock reservation, price quotation or assurance of exact-quantity supply.

## Files and coordinates

The package is under [`../manufacturing/rev0.1-2026-10-24/`](../README.md).
It contains bare-board Gerbers/drills, Gerber job metadata, electrical test
netlist, fabrication notes/drawings, fitted and DNP BOMs, placements, assembly
drawings, variant paste, seven-sheet schematic PDF, STEP/STL and verification
reports. Both a fabrication-only ZIP and a complete-package ZIP are provided.

The source ZIP preserves repository paths, including documentation, tools and
simulation scaffolding. Copied engineering documents link to other packaged
documents where available; links requiring the full repository point to that
source ZIP. The generator removes obsolete Markdown copies before packaging.
Release files use `.gitattributes` to prevent line-ending conversion from
invalidating checksums. `SHA256SUMS` covers all package files except itself and
the complete ZIP, whose checksum is supplied separately.

The export origin is the lower-left outline bounding corner, source KiCad
coordinates **(226.5, 158.1) mm**. X points right and Y up. Gerbers, drills,
placements and STEP/STL share this origin. The source origin is unchanged.
Gerbers/drills/placements/mechanical models use mm. **The native IPC-D-356
format declares CUST 0 (0.0001 inch)**; its positions were converted back to mm
and checked against the same origin. Do not interpret that file as mm.

The outline is **99.0 × 61.0 mm**, corner radius **3.5 mm**. The native Gerber
job size includes the 0.05 mm outline stroke and reports 99.05 × 61.05 mm;
manufacture to the outline centreline. There are **448 plated holes**:
368 × 0.4 mm, 32 × 0.5 mm, 44 × 0.9 mm and four × 3.2 mm. There are **no NPTH
holes**; the empty NPTH file explicitly records this. Connector locking-area
markings are copper clearance information, not instructions to drill holes.

## Construction and assembly confirmations

Use the eight-layer construction in CMU-005: 35 µm finished outer copper,
18 µm inner copper, and dielectric gaps 0.190/0.200/0.240/0.200/0.240/0.200/0.190 mm.
The Eurocircuits material total is **1.604 mm**, based on dielectric plus
starting foil. **1.638 mm** adds finished copper before masks; **1.708 mm** is
the KiCad total including estimated masks. Do not order an arbitrary nominal
1.708 mm stackup from the automatic Gerber job field. Confirm the selected
construction, finished thickness/tolerance and material with Eurocircuits.
Preserve HAL lead-free finish, green mask both sides, white top legend, no
bottom legend, and open vias without filling/capping/plugging.

Native STEP exports model the board body separately from omitted surface
copper/masks: the bare board solid is **1.568 mm** thick. This is consistent
with 1.460 mm dielectric plus six 0.018 mm inner copper layers; it is not a
delivered finished-board thickness. STEP and STL share the same native
geometry and component positions. Allow for the documented coatings and
confirmed fabrication tolerances when designing a close-fitting enclosure.

The populated STL is binary, below GitHub's 10 MB preview limit, and retains
the native facets without mesh simplification. STL has no colour or unit
metadata; interpret it in mm. The assembly STEP includes 157 fitted component
occurrences; the 37 DNP models are excluded.

**Assembler confirmation is required for the stencil/process:** the native
paste contains single exposed-pad apertures for U201 and U601, with five and
two open 0.4 mm via holes respectively inside those pad areas. DNP paste
apertures are omitted only on the export copy. No windowing, paste reduction,
via plugging or source edits were imposed. Agree paste deposition, reflow and
inspection with the assembler before producing the stencil.

No dedicated fiducials are fitted. Eurocircuits states that it adds panel
fiducials and can use board features for local registration, so this alone
does not require a layout change for the selected supplier. Confirm the
assembly setup and through-hole connector soldering/orientations in its
review. [Eurocircuits fiducial guidance](https://www.eurocircuits.com/tips-tricks/finding-fiducials/).

## Verification and remaining engineering work

Configured ERC and refilled DRC each report zero violations, with zero
unconnected items and zero schematic/PCB mismatches. Existing exclusions are
empty. All 18 referenced model paths resolve. Fresh native outputs and source
hashes are retained in the package.

Enabling previously disabled categories on the temporary project reports
71 four-way-junction notices and 28 schematic footprint-filter naming warnings;
the PCB audit reports 26 footprint-filter naming warnings. The custom
footprint names do not match stock wildcard filters. These reports are
included separately. They do not constitute newly waived violations, and
the authoritative rules remain unchanged. Pin connectivity and exported
population are verified independently.

KiCad 10.0.4 emitted invalid via soldermask numbers in its IPC-D-356 output.
The release tool corrects only those fields from each via's actual tenting
state, inserts the prescribed blank before the mask field and pads records
to 80 columns. The original output, correction record and net/coordinate
readback are included. This changes the derived test file, not the design.

The audit independently parses/renders all Gerbers, checks drills and
placements against the board, compares IPC net partitions, and checks STEP
solids, component references and STL bounds. Assembly/purchasing counts are
cross-checked. Source SHA-256 hashes must remain identical before/after.

**File preparation is complete; production qualification is not.** Supplier
stackup/finished thickness, stencil/process acceptance and live part
availability remain open. Thermal analysis, measured/guaranteed communication
impedance, EMC/isolation, fault behavior, firmware and first-board bring-up
remain at their recorded draft/unvalidated stages. No aerospace or system
qualification is implied by connector choice or a clean DRC.

## Reproducing the package

Use KiCad **10.0.4** with its standard libraries and Python, FreeCAD **1.1**
Python for independent STEP readback, and the dependencies pinned in
`tools/manufacturing-requirements.txt`. From the repository root, PowerShell:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -m pip install --target build/python-deps -r tools/manufacturing-requirements.txt
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -B tools/manufacturing_release.py --date YYYY-MM-DD
```

Use the actual export date. The tool creates an isolated build copy and local
standard-library configuration under ignored `build/`, refuses to overwrite
an existing package by default, and checks source hashes. `--resume` is for
finishing the same unpublished snapshot only. Never use it to replace a
published release. Run `--phase prepare`, `exports`, `bom`, `audit`, `render` or
`finalize` to inspect/retry a failed phase. `--kicad-cli` and `--freecad-python`
override tool locations. The mapping file is a dated source check; verify
live supply and refresh it deliberately for a future purchasing release.

### Reproducing the PCB image

The image uses [KiCad's native ray tracer](https://docs.kicad.org/10.0/en/cli/cli.html#pcb-render),
high quality, an angled top perspective, stackup colours and a neutral grey
background. The rendering copy comes from the matching filled manufacturing
snapshot. Its 37 DNP models are removed only in that disposable copy; all 157
fitted models remain. The renderer does not modify manufacturing geometry.

After preparing the snapshot, this command builds the rendering copy and local
appearance preset, verifies population and produces the 2400 × 1600 PNG:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -B tools/manufacturing_release.py --date 2026-10-24 --phase render --resume
```

The native invocation, with the build's `KICAD_CONFIG_HOME` and model paths, is:

```text
kicad-cli pcb render --width 2432 --height 1632 --side top --quality high --background opaque --preset "CMU neutral" --perspective --rotate 325,0,25 --zoom 1 -o <native.png> <render-copy.kicad_pcb>
```

Stackup colours are enabled by default. KiCad 10.0.4 quantises its ray-packet
buffer and produces 2408 × 1600 pixels for that request. The script trims four
empty-background pixels from each side to deliver exactly 2400 × 1600; no
resampling, model alteration or synthetic image content is applied. The
native command, dimensions, crop rectangle and image hashes are retained in
`verification/pcb-render.json`; the preset is defined in the export script.
This is a visualization, not evidence of thermal or electromagnetic performance.

For a documentation/image-only refresh of this unpublished package, use
`--phase render` and `--phase finalize --resume`; do not run the fabrication,
BOM or mechanical export phases. Finalization refreshes copied documentation,
license notices, source snapshot, archives and hashes.

Regenerate documentation with KiCad's Python and the build configuration:

```powershell
$env:KICAD_CONFIG_HOME = (Resolve-Path 'build/manufacturing-rev0.1-YYYY-MM-DD/config').Path
$env:KICAD_DOCUMENTS_HOME = (Resolve-Path 'build/manufacturing-rev0.1-YYYY-MM-DD/documents').Path
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -B tools/gen_doc_tables.py
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -B tools/gen_doc_tables.py --check
```

Current generated tables distinguish fitted PCB population from schematic-only
alternatives. Analysis prose still requires engineering review after changes.
Intentional release outputs and the STL preview may be committed; scratch
exports, editor state and dependency caches remain ignored. This repository
currently has no initial Git commit. Exact source hashes plus the source ZIP
identify this local package; no commit/tag/publication was created.
