"""Generate instructions/drawings that accompany the manufacturing artwork.
Copyright (C) 2021-2026 Gerhard Malberg; SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape


def pdf_text(path, title, body):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    styles=getSampleStyleSheet();styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    flow=[Paragraph(escape(title),styles['Title']),Spacer(1,12)]
    for line in body.splitlines():
        if not line.strip():flow.append(Spacer(1,6));continue
        style=styles['Heading2'] if line.startswith('#') else styles['BodyText']
        flow.append(Paragraph(escape(line.lstrip('# ').replace('**','')),style))
    SimpleDocTemplate(str(path),pagesize=A4,title=title,author='Gerhard Malberg').build(flow)


def write_documents(release):
    out=release.out;root=out.parents[1]
    report=json.loads((out/'verification/export-readback.json').read_text())
    rows=json.loads((out/'verification/component-inventory.json').read_text())
    stamp=release.args.date
    fabrication=f'''# Eurocircuits fabrication instructions — CMU rev 0.1

Export: {stamp}. Single PCB, 99.0 x 61.0 mm, outline corner radius 3.5 mm.
Use the Edge.Cuts centreline. The native job file reports 99.05 x 61.05 mm
because it includes outline stroke; this is not the routed outline dimension.
The data is a single board, not a customer panel. Supplier panelization may
add tooling/fiducials on the panel frame without changing the board artwork.

## Layer order and construction
L1 F.Cu: 0.035 mm finished copper, 0.018 mm starting foil.
L1-L2: 0.190 mm prepreg (PR1080 0.070 + PR2116 0.120).
L2 In1.Cu: 0.018 mm copper.
L2-L3: 0.200 mm core.
L3 In2.Cu: 0.018 mm copper.
L3-L4: 0.240 mm prepreg (PR2116 0.120 + 0.120).
L4 In3.Cu: 0.018 mm copper.
L4-L5: 0.200 mm core.
L5 In4.Cu: 0.018 mm copper.
L5-L6: 0.240 mm prepreg (PR2116 0.120 + 0.120).
L6 In5.Cu: 0.018 mm copper.
L6-L7: 0.200 mm core.
L7 In6.Cu: 0.018 mm copper.
L7-L8: 0.190 mm prepreg (PR2116 0.120 + PR1080 0.070).
L8 B.Cu: 0.035 mm finished copper, 0.018 mm starting foil.

FR-4 Improved, Tg 145-150 C; selected Eurocircuits 1.55 mm nominal menu row.
Material total: 1.604 mm (dielectric + starting foil, not delivered thickness).
Model before mask: 1.638 mm including finished copper.
KiCad total: 1.708 mm including 0.035 mm estimated mask on each side.
The automatic Gerber job BoardThickness is a CAD-model value, NOT an order
for a nominal 1.708 mm construction. Confirm this exact buildup, finished
thickness/tolerance and material with Eurocircuits before fabrication.
No controlled-impedance tolerance has been agreed; 100 ohm communication
routing is a preliminary design estimate, not a guaranteed production test.

## Finish, holes and legend
HAL lead-free finish; green soldermask on both sides; white top silkscreen.
No bottom silkscreen. No blind/buried vias. All vias open on both faces;
no filling, plugging, capping or tenting requested.
448 PTH: 368 x 0.400 mm; 32 x 0.500 mm; 44 x 0.900 mm; 4 x 3.200 mm.
0 NPTH. The empty NPTH drill/map explicitly indicate none are required.
The four 3.2 mm mounting holes are PLATED and electrically tied to GND.
Connector locking areas marked NO COPPER are not drill instructions.
No extra connector bolt holes or board cutouts are specified.
LICENSE, NOTICE.md and LICENSES/ accompany these standalone fabrication files.
Minimum project copper clearance 0.190 mm, track width 0.200 mm,
copper-to-edge 0.500 mm, hole-to-hole 0.450 mm.
Do not add component references to the production silkscreen: assembly
references are in the assembly drawing. Existing connector labels are retained.

## File interpretation
Gerber X2 plus native job file. Gerbers and Excellon drills use mm.
Common lower-left export origin corresponds to source (226.5,158.1) mm;
X right, Y up. No fabrication file is mirrored. Bottom layers are supplied
in normal top-view coordinates for CAM, not mirrored artwork.
The IPC-D-356 test file declares CUST 0 (0.0001 inch); its coordinates/net
partition were checked against the same origin. Its via soldermask fields
were normalized from the actual open-via settings after a KiCad 10.0.4
export defect; geometry and net tokens are unchanged.
Use copper/mask/outline files as the fabrication data; PDFs are drawings.
The paste Gerber belongs to assembly/stencil, not bare-board copper.

References:
https://www.eurocircuits.com/technical-guidelines/pcb-design-guidelines/input-data-formats/
https://www.eurocircuits.com/user-guides/visualizer-user-guides/buildup-editor-user-guide/
'''
    assembly=f'''# Assembly instructions — CMU rev 0.1, 16S

Export: {stamp}. Fit exactly the 157 components in bom-fitted.csv/xlsx.
All fitted components are on top. placement.csv includes the four through-hole
connectors as well as SMD parts. Coordinates are mm from the lower-left board
bounding corner, X right, Y up. Rotation is the native KiCad placement angle;
confirm feeder zero-angle and pin 1 in the assembly review. Do not infer
orientation from packaging alone. No bottom components are fitted.

## Purchased parts that MUST remain unfitted
All 37 DNP positions are purchased at user request, but excluded from the
fitted BOM, placements, populated STEP/STL and paste export. Use the separate
37-position DNP list. This comprises 28 unused-cell zero-ohm links,
R219-R226 (8 onboard NTCs), and R604 (OTP programming option).
R604 must remain absent for normal 8.8 V operation.
Do not fit MPN_alt entries or substitute alternative component parts.
J402/J403 and F418-F451 do not exist on this PCB and are not ordered.

## Polarity and connector orientation
J401: pin 1 = B-/GND; pin 9 = B+/+BATT. Use the documented full tap schedule.
J501 (COMH): pin 1 = P, pin 2 = N.
J502 (COML): pin 1 = N, pin 2 = P. This reversal is intentional.
Use the pin-1 labels, F.Fab references and body/polarity marks in the supplied
assembly drawing. DNP parts are crossed out in that drawing.
Preserve diode and IC orientation; verify transistor and transformer pins
against the PCB-specific assembly drawing and exact MPN data.

## Stencil and soldering review REQUIRED before stencil production
The supplied stencil is the saved footprint paste with all 74 DNP pad
apertures omitted. There is no bottom paste. U201 has one 6.5 x 6.5 mm
exposed-pad aperture and five open 0.4 mm vias inside that pad area.
U601 has one 1.651 x 2.845 mm exposed-pad aperture and two open 0.4 mm vias
inside that pad area. Agree windowing/paste volume, solder wicking control,
stencil thickness, reflow and inspection with the assembler. The source
design and aperture geometry have NOT been changed to assume a process.
This is a candidate stencil export, not an approved stencil order.

No dedicated board fiducials are present. Eurocircuits adds panel fiducials
and can use board features locally; confirm the assembly setup. Four Harwin
connectors require through-hole soldering. The purchasing quantities include
no feeder setup/attrition allowance; agree any extra parts before assembly.
Validate first-board power-up and firmware on current-limited test equipment
before pack operation; thermal/SI/fault qualification remains open.

https://www.eurocircuits.com/tips-tricks/finding-fiducials/
'''
    procurement='''# DigiKey purchasing — one board, including purchased DNP parts

Upload digikey-import.csv, or the DigiKey Import sheet of digikey-order.xlsx.
34 exact manufacturer part numbers; 194 pieces = 157 fitted + 37 DNP.
No spares are included. Keep DNP items separate and do not fit them.
The workbook has an editable board count and per-line additional spares.
Export its import sheet after changing quantities; the supplied CSV is static.
Map DigiKey Part Number, Quantity and Customer Reference. Manufacturer and
Manufacturer Part Number are cross-check columns. Review all matches in
DigiKey before adding to a cart. No order or upload has been performed.

Part-verification.json records exact MPNs, selected packaging SKUs, original
listing sources and the verification date. Only distributor packaging changed;
the PCB/schematic sourcing fields were not edited. Cut tape/single pieces
are selected for the same MPN, never an electrical substitute.

Listing observations to check live: CGA3E2X7R1H104K080AE,
CRCW060349R9FKEAHP, M80-5T10442MC and NCU18XH103F6SRB showed possible
backorders/zero stock. Cached regional listings can differ. Importing this
list does not guarantee current stock, pricing, lead time or quantity acceptance.
Mating harness parts and mounting hardware are not in the PCB purchasing BOM.
'''
    for folder,name,body,title in [('fabrication','fabrication-notes',fabrication,'CMU rev 0.1 fabrication instructions'),('assembly','assembly-instructions',assembly,'CMU rev 0.1 assembly instructions')]:
        (out/folder/(name+'.md')).write_text(body,encoding='utf-8')
        pdf_text(out/folder/(name+'.pdf'),title,body)
    (out/'procurement/README.md').write_text(procurement,encoding='utf-8')
    # Preserve existing fabrication drawing bytes during documentation refreshes.
    if not (out/'fabrication/dimensions.pdf').exists():
        # Dimensioned mechanical overview; all dimensions are source coordinates.
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import landscape,A4
        from reportlab.lib.units import mm
        c=canvas.Canvas(str(out/'fabrication/dimensions.pdf'),pagesize=landscape(A4))
        c.setTitle('CMU rev 0.1 outline and mounting dimensions');c.setFont('Helvetica-Bold',13)
        c.drawString(20*mm,195*mm,'CMU rev 0.1 - outline and mounting dimensions (mm)')
        scale=2.25*mm;ox=35*mm;oy=39*mm
        c.setLineWidth(.6);c.roundRect(ox,oy,99*scale,61*scale,3.5*scale)
        c.setFont('Helvetica',9);c.drawCentredString(ox+49.5*scale,oy-6*mm,'99.0')
        c.drawString(ox-15*mm,oy+30.5*scale,'61.0');c.drawString(ox,oy+61*scale+4*mm,'4 outline corners R3.5')
        c.line(ox,oy-3*mm,ox+99*scale,oy-3*mm)
        for x in (ox,ox+99*scale):c.line(x,oy-4*mm,x,oy-2*mm)
        c.line(ox-4*mm,oy,ox-4*mm,oy+61*scale)
        mounts=[]
        for r in rows:
            if r['ref'] in ('H1','H2','H3','H4'):
                x=r['x']-226.5;y=158.1-r['y'];mounts.append(f"{r['ref']}: X{x:.3f}, Y{y:.3f}")
                c.circle(ox+x*scale,oy+y*scale,1.6*scale)
                c.drawCentredString(ox+x*scale,oy+y*scale-4*mm,r['ref'])
        c.setFont('Helvetica',8);c.drawString(20*mm,21*mm,'4 x diameter 3.200 PLATED mounting holes to GND; origin lower-left bounding corner.')
        c.drawString(20*mm,16*mm,'; '.join(mounts));c.drawString(20*mm,11*mm,'Connector lock clearance markings are NOT additional holes. Finished thickness: confirm buildup in fabrication-notes.pdf.')
        c.save()
    readiness=f'''# Manufacturing readiness — {stamp}

## Passed file checks
- Configured ERC: 0 violations.
- Refilled DRC: 0 violations, 0 unconnected, 0 schematic/PCB mismatches.
- Source hashes unchanged; 18 unique model paths resolved.
- 157 fitted components; 37 purchased DNP positions; 194 purchased pieces.
- All 448 plated drill locations/sizes match the source within native
  Excellon rounding (maximum {report['drill_max_coordinate_quantization_mm']:.6f} mm); no NPTH.
- 157 STEP component occurrences match fitted BOM and placements.
- Both STEP files contain valid solids; assembly STEP/STL bounds agree.
- STL: {report['stl_facets']} native facets, {report['stl_bytes']} bytes; no simplification.
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
'''
    (out/'verification/readiness.md').write_text(readiness,encoding='utf-8')
    pdf_text(out/'verification/readiness.pdf','CMU rev 0.1 manufacturing readiness',readiness)
    (out/'3d/README.md').write_text('''# Mechanical exports

All files use mm, common lower-left board origin, and native KiCad component
positions. CMU-rev0.1-16S.step and .stl contain the 157 fitted components.
CMU-rev0.1-board.step contains only the board. DNP models are omitted.
The binary STL is below 10 MB and retains the native mesh without decimation.
Keep it as a normal Git file for GitHub's built-in STL viewer.

[Ray-traced PCB image](CMU-rev0.1-16S-raytraced.png): 2400 x 1600 pixels,
native KiCad high-quality angled top view with stackup colours and a neutral
grey background. It shows the 157 fitted components; DNP models are excluded.
Only an empty-background border is cropped to correct KiCad's output-size
quantisation; no resampling or geometry changes. See
[reproduction commands](../documentation/CMU-009-manufacturing.md#reproducing-the-pcb-image)
and [render verification](../verification/pcb-render.json).

Native STEP board body is 1.568 mm thick; surface copper/mask solids are not
included. The CAD stackup total is 1.708 mm including estimated masks; supplier
finished thickness/tolerance is still to be confirmed. Use those allowances
for enclosure fit. These models do not include mating cables or screw travel.
''',encoding='utf-8')
    readme=f'''# CMU revision 0.1 — 16S prototype package

Exported {stamp} with KiCad 10.0.4. Target: Eurocircuits.
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
'''
    (out/'README.md').write_text(readme,encoding='utf-8')
