# Assembly instructions — CMU rev 0.1, 16S

Export: 2026-10-24. Fit exactly the 157 components in bom-fitted.csv/xlsx.
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
