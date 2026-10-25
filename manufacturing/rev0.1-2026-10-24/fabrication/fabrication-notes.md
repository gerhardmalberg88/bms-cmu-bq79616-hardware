# Eurocircuits fabrication instructions — CMU rev 0.1

Export: 2026-10-24. Single PCB, 99.0 x 61.0 mm, outline corner radius 3.5 mm.
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
