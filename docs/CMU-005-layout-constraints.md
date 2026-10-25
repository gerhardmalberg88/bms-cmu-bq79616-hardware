---
id: CMU-005
title: Layout Constraints
rev: 0.1
status: layout-record-engineering-review-open
phase: pre-layout constraints and post-layout record
applies_to: bms-cmu-bq79616-hardware rev 0.1
license: CERN-OHL-P-2.0
---

# CMU-005 — Layout Constraints

> **2026-10-24 status:** the routed PCB passes the configured, refilled DRC and its manufacturing files are prepared. Historical routing entries below are retained; the current build and open supplier confirmations are recorded in CMU-009. See [CMU-009](CMU-009-manufacturing.md).


> **This is the document layout is executed against.** It aggregates the
> layout-relevant *outputs* of CMU-002, CMU-003, CMU-004 and CMU-008 into one
> place, so routing means checking one document rather than four. It
> **references** those analyses; it does not restate their reasoning.

The routed prototype is complete; unchecked engineering constraints remain
open for review. Dated setup/DRC results below are historical, not current
release results. Every constraint should trace to a source document.

## 1. Electrical clearance and creepage

**Status: partially derived.**

| Constraint | Value | Source |
|---|---|---|
| Worst-case voltage between adjacent tap nets | **67 V** at 16S full charge | CMU-008 §3 |
| Worst adjacent pair with interleaved pin order | ~8.4 V (2 cells) | CMU-008 §3.1 |
| Pack-to-daisy-chain isolation | Full pack potential; higher when modules stack | CMU-008 §4 |

- [ ] Fix creepage and clearance per the pollution degree and altitude in
      CMU-001, for the 67 V worst pair and for the isolation barrier
- [ ] **The T501/T502 isolation barrier is a keep-out.** No copper, no
      component, no via crossing it on any layer. Establish the barrier
      geometry before placement.
- [ ] `SC_CT` stays unconnected. Do not add a ground reference on the cable
      side (CMU-008 §4.1)

## 2. Thermal placement

**Status: distributed placement implemented; thermal performance unverified.**

The board's entire thermal story is the balance network:

| Element | Total | Source |
|---|---|---|
| 17 × 20R 2W balance resistors | **3.7 W** preliminary allocation; balancing schedule unverified | CMU-002 §8 |
| Everything else combined | < 0.5 W | CMU-002 §8 |

- [x] Distribute the 17 balance resistors along two board sides; temperature
      rise and allowed duty cycle still require CMU-006 validation
- [ ] Copper area per resistor
- [ ] **D601 needs maximum practical copper.** It may sit at ~1.4 W during a
      mis-regulation fault; the land is already oversized against datasheet
      minima for heat sinking (CMU-003 F-06)
- [ ] Q201 SOT-223 tab is its thermal path — full solder coverage
- [ ] Keep the 20 R resistors away from the NTC inputs and the AFE, so
      self-heating does not corrupt temperature measurement

## 3. Placement driven by failure modes

Each traces to a [CMU-003](CMU-003-fmea.md) row.

- [ ] **C601/C602 (F-03).** A cracked MLCC fails short and puts the pack across
      L601. Keep away from board edges, mounting holes and depanel routes;
      orient so board flex acts along rather than across the part. This is why
      they are 2× 1210 instead of 1× 2220.
- [ ] **F601 and D601 (F-01).** Adjacent, with a tight clamp loop — the fuse
      must see the fault current the clamp draws.
- [ ] **Tap fuses (F-08).** Star topology is already in the schematic. Preserve
      it physically: one fuse per connector pin, no shared copper upstream.
- [ ] **Tap pin order (F-14).** Each connector's ordering is chosen to minimise
      the voltage between adjacent pins for its own geometry — interleaved on the
      2x10 J401, sequential on the 1x20 J402/J403. It is a protection feature.
      **Do not reorder for routing convenience.**
- [ ] Fuses need thermal isolation from each other — a blowing fuse should not
      heat its neighbours into opening.

## 4. Signal integrity constraints

**Status: preliminary communication routing defaults updated 2026-09-20,
clearance updated 2026-09-23;
the selected Eurocircuits buildup is entered; post-layout verification remains open.** Calculations and applicability are
recorded in [CMU-007 section 2.1](CMU-007-si-pi-analysis.md#21-preliminary-communication-netclass).

| Communication setting | Value / scope |
|---|---|
| Netclass | `CMU_COM_TOP`; COMH/COML, FILT_COMH/FILT_COML and ISO_COMH/ISO_COML, both P and N |
| Differential target | 100 ohm project intent where a plane-referenced pair can be implemented; not a numerical BQ79616 requirement |
| DP Width / DP Gap | **0.21 / 0.25 mm**; gap is edge-to-edge |
| Track Width / Clearance | 0.21 / 0.19 mm; clearance is a manufacturing floor, not an isolation distance |
| Via Size / Via Hole / DP Via Gap | 0.80 / 0.40 / 0.25 mm; contingency defaults, not an impedance-designed via transition |
| Geometry model | F.Cu over continuous local-GND In1.Cu, 0.190 mm dielectric, 0.035 mm copper, provisional Dk 4.5; illustrative coated estimates in CMU-007 |

The same dimensions are routing defaults in the isolation keepout region;
**no 100 ohm prediction applies there**. The microstrip model does not apply
without its reference plane. Retain the all-layer daisy-chain keepouts and the
floating cable side. Do not add ground to make a calculator model fit.

- [ ] Confirm pressed stackup, Dk, soldermask loading, impedance tolerance and
      the final routed geometry before treating the target as verified
- [ ] Intra-pair length matching tolerance
- [ ] Finalize layer stackup and reference plane assignment; preliminary
      selection and source are recorded in §5.1
- [ ] Keep each pair short, symmetric and on one layer; analyse the transition
      into the plane-free isolation region and the complete transformer/cable link
- [ ] Keep the LTC3639 SW node small and away from the tap filters and the
      daisy chain
- [ ] RC filter placement: the 100 R / 470 nF cell filters belong close to the
      AFE, not the connector

## 5. Manufacturing

### 5.1 Eurocircuits physical stackup source

**Updated: 2026-09-20. Status: screenshot-based build selection entered in
KiCad; final pressed dimensions and material properties require the
fabricator's production build record.**

The subsequent request for a **1.600 mm physical stackup** is reviewed in
section 5.5. Its new attachments conflict on inner copper thickness; the
construction below remains the saved baseline until that input and a suitable
replacement buildup are resolved.

The reference is the user's latest Eurocircuits **Buildup Editor screenshot
supplied 2026-09-20**, including its visible **Total material thickness:
1.604 mm**. The highlighted row is **eight layers, 0.200 mm cores, 18 um
starting outer foil (35 um finished), and 18 um inner copper**, under the
**1.55 mm nominal board-thickness category**. This supersedes the earlier
35 um inner-copper selection. The screenshot shows **FR-4 Improved**;
**Tg 145-150 C** is retained from the associated material configurator image.
The construction has normal buildup, no defined impedance,
no blind/buried runs, no extra press cycles, and no special buildup selected.
The shared session could not be loaded during this review; no online order or
configuration was changed.

The [Eurocircuits Buildup Editor guide](https://www.eurocircuits.com/user-guides/visualizer-user-guides/buildup-editor-user-guide/)
explains the row selection and layer preview. The
[configurator material guide](https://www.eurocircuits.com/user-guides/visualizer-user-guides/pcb-configurator-user-guide/material/)
distinguishes starting outer foil from finished outer copper and the nominal
thickness label from calculated material thickness.

The following values are entered in
[`battery_management_system_cell_monitoring_unit.kicad_pcb`](../design/battery_management_system_cell_monitoring_unit.kicad_pcb).
F.Cu and B.Cu are **0.035 mm finished thickness**; In1.Cu through In6.Cu
are **0.018 mm**. Each pair of prepreg
plies is represented by two KiCad dielectric sublayers in the displayed
top-to-bottom order.

| KiCad dielectric | Between copper layers | Type and material | Sublayer thicknesses (mm) | Total (mm) |
|---|---|---|---|---:|
| 1 | F.Cu / In1.Cu | FR-4 Improved PR1080 + PR2116 prepreg | 0.070 + 0.120 | 0.190 |
| 2 | In1.Cu / In2.Cu | FR-4 Improved Tg 145-150 C core | 0.200 | 0.200 |
| 3 | In2.Cu / In3.Cu | FR-4 Improved PR2116 + PR2116 prepreg | 0.120 + 0.120 | 0.240 |
| 4 | In3.Cu / In4.Cu | FR-4 Improved Tg 145-150 C core | 0.200 | 0.200 |
| 5 | In4.Cu / In5.Cu | FR-4 Improved PR2116 + PR2116 prepreg | 0.120 + 0.120 | 0.240 |
| 6 | In5.Cu / In6.Cu | FR-4 Improved Tg 145-150 C core | 0.200 | 0.200 |
| 7 | In6.Cu / B.Cu | FR-4 Improved PR2116 + PR1080 prepreg | 0.120 + 0.070 | 0.190 |

**Thickness accounting.** These values use different measurement bases:

| Quantity | Calculation (mm) | Thickness (mm) |
|---|---|---:|
| Dielectric material | 0.190 + 0.200 + 0.240 + 0.200 + 0.240 + 0.200 + 0.190 | 1.460 |
| Eurocircuits total material | 1.460 + 8 x 0.018 starting copper | **1.604** |
| Model with finished outer copper, before mask | 1.460 + 6 x 0.018 + 2 x 0.035 | **1.638** |
| KiCad stackup and general board thickness | 1.638 + 2 x 0.035 estimated mask | **1.708** |

The 1.604 mm calculation exactly reproduces the screenshot's displayed total.
The follow-up screenshot was checked against the saved construction and
confirms the same selected row and **1.604 mm** material total. No layer
dimensions need changing to reproduce that manufacturing specification.

**KiCad project record:** `FAB_MATERIAL_THICKNESS = 1.604 mm` and
`FAB_MATERIAL_THICKNESS_BASIS` are stored in the project's **Board Setup >
Text Variables**, with matching properties embedded in the PCB file.
These record the fabrication material total explicitly; they do not override
KiCad's physical layer sum. Use `${FAB_MATERIAL_THICKNESS}` together with
its basis when preparing fabrication notes. Order the selected Eurocircuits
row by its full construction, not by a thickness number alone.

The 1.708 mm value is the sum of KiCad's entered layers, not a measured or
guaranteed delivered thickness. Neither value should be replaced by the
1.55 mm menu label or an arbitrary 1.600 mm total.

[KiCad's physical-stackup documentation](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html)
states that the displayed board thickness is calculated from the layer table.
Using Adjust Dielectric Thickness to force **1.604 mm** while retaining the
finished copper and mask entries would remove **0.104 mm of dielectric**
from this model, contradicting the supplied core/prepreg dimensions and
potentially changing the communication-pair geometry. Likewise, entering
18 um as finished outer copper would confuse starting foil with the selected
35 um finished copper. Neither substitution is part of this construction.

Eurocircuits states that base-material thickness excludes copper. Its
[finished-thickness guidance](https://www.eurocircuits.com/finished-pcb-thickness-tolerances/)
also gives approximately 25-45 um for DI soldermask; the model uses the
35 um midpoint per side. These mask values are estimates, not an
order-specific coating specification. Silkscreen and finish thickness are
not added to KiCad's total.

The [Eurocircuits PCB thickness explanation](https://www.eurocircuits.com/electronic-manufacturing-technology/the-complex-story-of-pcb-thickness/)
distinguishes the nominal category from the calculated raw-material total;
plating, coatings, pressing and copper distribution affect the finished board.
Retain the selected plies without rescaling them. For mechanical fit, agree
the measurement basis and finished thickness tolerance with the fabricator.

The copper-layer functions remain project design choices:

| Board layer | KiCad layer | Finished copper (mm) | Function |
|---|---|---:|---|
| L1 | F.Cu | 0.035 | Components and signals |
| L2 | In1.Cu | 0.018 | Ground/reference |
| L3 | In2.Cu | 0.018 | Signals, preferred horizontal routing |
| L4 | In3.Cu | 0.018 | Ground/reference |
| L5 | In4.Cu | 0.018 | Signals, preferred vertical routing |
| L6 | In5.Cu | 0.018 | Ground/reference |
| L7 | In6.Cu | 0.018 | Power planes |
| L8 | B.Cu | 0.035 | Ground/reference |

The isolation keepouts in section 1 still apply on every copper layer.

**Material-property limits.** FR-4 Improved is a procurement family.
[Eurocircuits' material catalogue](https://www.eurocircuits.com/downloads/)
lists several mid-Tg materials selected at its discretion. The screenshots
do not select a unique laminate product or supply frequency-specific Dk/Df.
KiCad therefore uses **EpsilonR 4.5 and LossTg 0.02 for all eleven dielectric
sublayers as generic placeholders**, not Eurocircuits-qualified electrical
properties. Soldermask retains KiCad's default electrical assumptions
(EpsilonR 3.3, LossTg 0). Replace these with the actual construction data
before using the stackup for quantitative loss or impedance analysis.

**Coatings and via treatment.** The original screenshot selected green mask
on both sides, white top legend, no bottom legend, and Any lead-free finish.
On 2026-09-20 the saved board already specifies **HAL lead-free**; retain that
current user selection. The new material/technology screenshots do not show
a finish selection, so confirm it in the order. The unused bottom legend is
excluded from the saved plot layer selection.

Via filling/plugging is **No** in the configuration. Eurocircuits'
[soldermask guidance](https://www.eurocircuits.com/technical-guidelines/pcb-design-guidelines/soldermask/)
says unfilled vias are opened rather than reliably tented. Accordingly,
front and back via tenting are disabled; filling, capping, covering and
plugging are not requested. There were no existing vias to alter.

**Ordering at another fabricator.** Retained project margins are intended
to keep the artwork manufacturable across suppliers. Provide this build
record and obtain acceptance of the construction, thickness tolerance,
lead-free finish and open-via treatment. Standard build menus need not be
identical. A substituted dielectric construction requires updating the
KiCad stackup and dependent analyses; these settings alone cannot guarantee
an identical physical board or signal response.

### 5.2 Eurocircuits fabrication constraints and review

**Historical setup record.** Dimensions, pad counts and DRC totals in this
section describe the September state. The October export has a 99 x 61 mm
outline, 448 plated holes and a clean configured DRC. Actual drill sizes and
open manufacturing confirmations are recorded in [CMU-009](CMU-009-manufacturing.md).
Statements below about absent routing or outline do not describe that export.

**Recorded: 2026-09-12; copper clearance updated 2026-09-23. Status: applied; completed-layout verification and
fabricator acceptance remain release tasks.**

The configurator screenshots select **technology class 6C**, 0.150 mm outer
and inner track/spacing, 0.125 mm outer and inner annular rings, 0.25 mm
smallest finished hole, and 0.45 mm for "Holes <= may be reduced".
The project retains larger dimensions where already selected.

The key interpretation is **finished-hole size versus production tool**.
Eurocircuits' [annular-ring definition](https://www.eurocircuits.com/oar-outer-annular-ring/)
measures the ring from the production tool. Its
[drilling rules](https://www.eurocircuits.com/technical-guidelines/pcb-design-guidelines/drilled-holes/)
use `TOOLSIZE = ENDSIZE + 0.100 mm` for plated holes, with 0.05 mm hole-size
increments. KiCad's hole dimension is the nominal finished size. Therefore
a 0.125 mm production-tool ring requires at least **0.175 mm in KiCad**;
the selected global minimum is **0.200 mm**, retaining additional margin.

Eurocircuits'
[classification guidance](https://www.eurocircuits.com/technical-guidelines/pcb-design-guidelines/classification/)
requires inner hole isolation of at least `IAR + 0.075 mm`, with a
0.200 mm floor, measured from the tool. Adding the 0.050 mm radial drilling
allowance gives a 0.250 mm finished-hole-based minimum; the project uses
**0.300 mm**. These conversions do not add a second allowance to KiCad's
exported drill sizes: export the intended finished holes normally.

All dimensions below are mm, stored under **Board Setup > Design Rules >
Constraints** in
[`battery_management_system_cell_monitoring_unit.kicad_pro`](../design/battery_management_system_cell_monitoring_unit.kicad_pro).

| Constraint | Applied | Basis |
|---|---:|---|
| Minimum clearance | 0.19 | Uniform board/netclass rule; margin above 0.150 mm class-6 spacing; see section 5.6 |
| Minimum track width | 0.20 | Retained project margin above 0.150 mm class-6 tracks |
| Minimum connection width | 0.20 | Retained check for narrow copper connections |
| Minimum annular width | 0.20 | At least 0.175 mm needed after converting the tool-based requirement |
| Minimum via diameter | 0.70 | 0.30 mm finished hole plus two 0.20 mm rings |
| Copper to hole clearance | 0.30 | Margin above the converted 0.250 mm inner-hole isolation |
| Copper to edge clearance | 0.40 | Covers the stricter inner-layer routed-edge requirement globally |
| Minimum drill size | 0.30 | Retained margin above the selected 0.25 mm finished hole |
| Hole to hole clearance | 0.45 | Retained margin; two plated-hole tools reduce this to 0.35 mm |
| Minimum silk item clearance | 0.10 | Legend clearance to exposed copper and holes |
| Minimum text height | 1.00 | Eurocircuits legend readability minimum |
| Minimum text thickness | 0.15 | Retained margin above Eurocircuits' 0.10 mm legend stroke |

Eurocircuits' [manufacturing tolerances](https://www.eurocircuits.com/technical-guidelines/understanding-manufacturing-tolerances-on-a-pcb/tolerances-on-a-pcb/)
specify 0.25 mm between production holes and routed copper-to-edge spacing
of 0.25 mm outer / 0.40 mm inner. The global 0.45 mm finished-hole gap
exceeds the 0.35 mm needed for two tools each enlarged by 0.10 mm.
This profile assumes routed single boards; scored edges require at least
0.45 mm copper clearance and a revised panel definition.

The companion
[`battery_management_system_cell_monitoring_unit.kicad_dru`](../design/battery_management_system_cell_monitoring_unit.kicad_dru)
contains two additional checks:

- **Plated component pad annular ring: 0.254 mm.** This is a retained project
  margin, not Eurocircuits' class minimum. It corresponds to 0.204 mm from
  the production tool and is stricter than the global via minimum.
- **Legend to routed edge: 0.25 mm.** This implements the separate edge
  requirement in Eurocircuits'
  [legend-print rules](https://www.eurocircuits.com/technical-guidelines/pcb-design-guidelines/legend-print/).
  Legend placement relative to component bodies for assembly still requires
  layout review.

The Default net class uses **0.80 mm via diameter / 0.40 mm
finished hole**, giving **0.20 mm KiCad ring / 0.15 mm production-tool ring**.
It also uses 0.25 mm tracks and 0.19 mm clearance. Larger finished holes
need larger copper diameters to preserve the selected annular width.
Microvias and blind/buried vias remain disabled.

The saved component pads comprise 44 holes of 0.90 mm with 1.50 mm pads
(0.30 mm KiCad ring / 0.25 mm tool-based ring), and 40 holes of 1.00 mm
with 1.80 x 2.00 mm pads (0.40 mm / 0.35 mm minimum ring respectively).
These nominal dimensions meet the applied hole and annular limits.

**Other screenshot selections and release checks.** The quoted 100 x 100 mm
size is an order input; the board currently has no outline, so that size is
not yet verified in artwork. Hole density below 1000/dm2 and component pitch
of at least 0.50 mm also require validation of the completed data. Bare-board
electrical testing is selected. The "Holes <= may be reduced" setting allows
manufacturing changes to small holes; check the final drill classification
and preserve component-hole dimensions. The present 0.90/1.00 mm component
holes exceed that threshold. These are order/review items rather than
automatically enforced global KiCad constraints.

Green DI soldermask has a 0.075 mm minimum web and 0.030 mm mask-to-pad
expansion in Eurocircuits'
[soldermask rules](https://www.eurocircuits.com/technical-guidelines/pcb-design-guidelines/soldermask/).
The existing global 0.050 mm expansion and 0.190 mm minimum copper spacing leave
0.090 mm between adjacent nominal pad openings; footprint overrides and the
final mask artwork still need review. No soldermask or footprint geometry
was rewritten to conceal DRC violations.

These are manufacturing rules. Battery-voltage clearance, creepage, the
isolation barrier and aerospace assurance requirements need their own
analysis; the configurator's "High-Voltage board: No" does not establish
electrical safety. Existing DRC severities remain in place, and no
DRC exclusions have been added. Section 5.6 records the global clearance decision.

**Verification: KiCad 10.0.4, 2026-09-20.** KiCad loaded the board and both
custom rules without parse errors. Loading and saving a temporary copy
preserved eight copper layers, the four additional prepreg sublayers,
the 1.708 mm model thickness and the HAL lead-free finish. Read-back checks
compare the documentation with the stored parameters. The checksum of the
board content after the setup section is unchanged: no footprint, pad,
placement, net, track, zone or outline geometry was edited.

The DRC run used temporary configuration/document directories and did not
refill zones or save the project board. Its report is outside the repository.
It reported **552 violations and 447 unconnected items**:

| DRC category | Count | Review result |
|---|---:|---|
| Copper clearance | 4 | 0.195 mm pad gaps below the retained 0.200 mm project requirement |
| Invalid outline | 1 | No Edge.Cuts outline; edge clearances and quoted dimensions cannot yet be verified |
| Footprint-library issues | 149 | Isolated CLI configuration lacks standard library registrations; library parity is not established |
| Silkscreen overlap | 199 | Requires placement cleanup under the new silk-clearance setting |
| Silkscreen over exposed copper | 199 | Requires placement cleanup |

No hole-size or annular-ring violations were reported for the existing pads.
There are no routed tracks or vias, and schematic parity was not requested.
This is configuration validation, not a clean DRC or manufacturing-release
approval. Review all warnings as well as errors before release.

The 2026-09-20 counts above are historical. The 2026-09-23 clearance update
and its verification are recorded in section 5.6.

### 5.3 Manufacturing release items

**Current status, 2026-10-24:**

- [x] Verify the 99 x 61 mm outline and eight-layer file set; distinguish
      1.604 mm starting-material total from the 1.708 mm KiCad model estimate
- [ ] Confirm Eurocircuits calculated build thickness, final pressed layer
      dimensions, actual laminate Dk/Df and the delivered lead-free finish
- [ ] Size inner tracks and power/ground planes using **18 um copper**;
      update current, voltage-drop and thermal checks for the actual layout
- [x] Enter sourced fabrication constraints and the component-pad annular rule
      from section 5.2
- [x] Refill and check completed artwork with DRC; inspect exported files
- [ ] Obtain fabricator order review and assembler stencil/process acceptance
- [x] Assembly instructions identify J401 as the only fitted cell connector,
      require every tap once, and leave R604 unfitted for normal 8.8 V operation;
      J402/J403 are schematic-only alternatives
- [x] Connector pin-1 markings and communication polarity labels are present;
      harness continuity/orientation still needs assembly verification
- [ ] Test points for bring-up: 8V8, LDOIN, node A, a representative tap

### 5.4 1.6 mm target and communication routing decision, 2026-09-20

**Historical plane-referenced routing decision.** The later plane-free model
is documented in CMU-007 section 2.3; the current release is recorded in CMU-009.

**Implemented selection, preceding the new request in section 5.5:**
eight layers, **35 um finished outer / 18 um inner copper**, three 0.200 mm
cores, and the prepreg sequence in section 5.1. This provides the displayed
**1.604 mm material total** in the 1.55 mm nominal category without a custom
core arrangement. It does not guarantee an exactly 1.600 mm coated board;
the saved KiCad model is **1.708 mm** including estimated masks.
The communication target remains 100 ohm differential on F.Cu referenced to
local GND on In1.Cu. Thickness measurement basis and acceptable thickness and
impedance tolerances still need to be agreed with the fabricator.

**Applied now:** `CMU_COM_TOP` DP Width and Track Width are reduced from
0.24 to **0.21 mm**; DP Gap remains **0.25 mm**. The coated cross-section
estimate in CMU-007 supports this as a preliminary candidate when the
F.Cu-to-In1.Cu dielectric is 0.190 mm. That separation and the 35 um top trace
are unchanged by the new inner-copper selection. Global constraints,
via dimensions, layer count, footprint placement and routing are retained.
The user confirms the intention to place In1.Cu ground beneath the microstrip
lane; actual plane geometry and isolation keepouts remain layout work.

**Checked against the new Eurocircuits screenshots and current design
(copper clearance updated 2026-09-23):**

| Item | Eurocircuits selection / requirement | Project | Finding |
|---|---|---|---|
| Layers / material / Tg | 8 / FR-4 Improved / 145-150 C | Same selection recorded | Matches selected family; exact Dk/Df unresolved |
| Outer copper | 18 um starting foil, approximately 35 um finished | 35 um finished | Matches |
| Inner copper | 18 um in the latest selected row | 18 um on six inner layers | Updated to match |
| Track width, outer / inner | 0.150 / 0.150 mm | 0.200 mm minima; pair 0.210 mm | Compatible |
| Copper spacing, outer / inner | 0.150 / 0.150 mm | 0.190 mm minimum; pair gap 0.250 mm | Compatible |
| OAR / IAR | 0.125 mm from production tool | 0.200 mm minimum from finished hole; default via gives 0.150 mm from tool | Compatible after drill allowance |
| Smallest finished hole | 0.250 mm | 0.300 mm global; 0.400 mm default via hole | Compatible |
| Via pad / hole | Ring and hole limits above | 0.800 / 0.400 mm | Compatible |
| Blind/buried runs / extra press cycles | 0 / 0 | No blind/buried vias or microvias | Compatible |
| Special / reversed buildup | No / No | Normal build | Matches the selected predefined construction |
| Board thickness | 1.55 mm category; **1.604 mm material total** | **1.708 mm** with finished copper and estimated masks | Same physical plies; different thickness accounting |
| Size / hole density / component pitch | 100 x 100 mm / below 1000 per dm2 / 0.50 mm or greater | Unfinished placement and no outline | Completed-artwork checks remain open |

The screenshot limits are order-specific evidence. Interpret the annular
ring and hole values using the [Eurocircuits classification guidance](https://www.eurocircuits.com/technical-guidelines/pcb-design-guidelines/classification/)
and [drilled-hole rules](https://www.eurocircuits.com/technical-guidelines/pcb-design-guidelines/drilled-holes/);
section 5.2 records the finished-hole to tool-size conversion and the retained
edge, hole-clearance and legend margins. Passing these parameter comparisons
does not establish that the unfinished artwork is ready for manufacture.

**Effect of thinner inner copper:** the top microstrip calculation treats
In1.Cu as an ideal continuous reference surface; reducing its thickness does
not change that surface separation. Real conductor loss and plane resistance
are outside the model. At equal geometry and temperature, an 18 um inner
conductor has approximately 35/18 = **1.94 times** the DC resistance of the
previous 35 um conductor. Current capacity, voltage drop and heat spreading
must therefore use 18 um in the eventual layout analysis. No routed inner
tracks or copper planes existed to resize during this update.

That screenshot resolved the previously missing construction evidence.
The project follows this selected row; no hypothetical 0.100 mm core
substitution is used. The order must retain this row's **18 um inner foil**,
even though earlier configurator images selected 35 um.

### 5.5 Request for a 1.600 mm physical stackup: compatibility review

**Reviewed 2026-09-20. Status: manufacturing limits and current netclass
checked; replacement physical stackup awaits consistent construction data.**

The new Buildup Editor image highlights **18 um inner copper**, while the
new main material configurator selects **35 um inner copper**. The
classification image also identifies 35 um inner foil. Those images therefore
do not specify one consistent order. Both copper options can meet the selected
Class 6C routing dimensions, but their thickness and current/thermal models
differ. Resolve the inner-copper selection and apply the chosen buildup in
the configurator before using the order data as a fabrication specification.

For the dielectric plies shown, the calculated totals are:

| Quantity (mm) | 18 um inner copper | 35 um inner copper |
|---|---:|---:|
| Dielectrics shown in the image | 1.460 | 1.460 |
| Starting copper, including two 18 um outer foils | 0.144 | 0.246 |
| Material total, excluding plating/coatings | 1.604 | 1.706 |
| Finished copper, including two 35 um outer layers | 0.178 | 0.280 |
| Existing mask estimate, both sides | 0.070 | 0.070 |
| Physical stackup sum with these assumptions | **1.708** | **1.810** |
| Dielectric budget for a 1.600 mm physical sum | **1.352** | **1.250** |
| Required dielectric reduction from the image | **0.108** | **0.210** |

These last two rows are **design budgets, not approved Eurocircuits plies**.
Preserving 0.190 mm F.Cu-to-In1.Cu spacing would preserve the present ideal
microstrip cross-section. The reduction could then be allocated below that
reference plane, preferably in a symmetric construction chosen by the
fabricator. The screenshot does not establish the availability of such a
construction. A different confirmed outer spacing requires recalculating
`CMU_COM_TOP` before routing.

The [Eurocircuits material guide](https://www.eurocircuits.com/user-guides/visualizer-user-guides/pcb-configurator-user-guide/material/)
distinguishes the nominal category from the calculated build and states a
standard thickness tolerance. It also describes special buildups as requiring
a technical proposal. Neither the nominal label nor a tolerance authorizes
substituting invented per-layer dimensions in this model.

**Limits check (clearance updated 2026-09-23):** the 0.200 mm global track-width
minimum, 0.190 mm global copper-clearance minimum and
`CMU_COM_TOP` 0.210 mm width / 0.250 mm gap exceed the selected 0.150 mm
track/spacing limits. The 0.800/0.400 mm via gives a 0.150 mm ring from the
0.500 mm production tool, exceeding the selected 0.125 mm. The 0.300 mm
global finished-hole minimum exceeds the selected 0.250 mm. No constraint
needs relaxing to meet these Class 6C settings. Final size, hole density,
component pitch, placement, copper geometry and electrical isolation still
require completed-artwork review; the project has no outline or routing.

**Information needed to complete the physical change:**

1. One agreed inner foil thickness: 18 or 35 um.
2. Whether 1.600 mm is a finished mechanical target including coatings,
   with its acceptable tolerance, or the nominal/material category is sufficient.
3. For a changed physical target, a Eurocircuits construction with the seven
   pressed dielectric gaps, finished copper, mask thickness basis and finished
   thickness tolerance. Prefer retaining the 0.190 mm outer reference spacing.
4. For an impedance claim, the actual laminate and soldermask Dk/profile,
   and an accepted differential-impedance tolerance. Defined impedance remains
   unselected in the attached order.

Until these are resolved, the saved physical construction remains the
documented 18 um-inner baseline. `FAB_MATERIAL_THICKNESS` records its
1.604 mm raw-material total; it is not a change to the physical layer sum.

### 5.6 Global copper-clearance decision, 2026-09-23

Set **Minimum clearance**, **Default clearance** and **CMU_COM_TOP clearance**
to **0.190 mm**, as requested. U601's existing 0.195 mm pad gaps then meet the
same rule used for ordinary copper throughout the board. The selected
Eurocircuits class-6 0.150 mm spacing remains below this requirement by 0.040 mm.
No component-specific clearance rule or DRC exclusion is used.

The footprint geometry, stackup, 0.200 mm minimum track width, via/hole rules,
and communication pair's 0.210 mm width / 0.250 mm gap are retained. Existing
larger local clearances still apply. Electrical isolation and creepage require
separate rules; 0.190 mm is a fabrication baseline, not a voltage rating.

The nominal U601 pad gap is `0.500 - 0.305 = 0.195 mm`, from the lead pitch
and recommended land width in the [ADI LTC3639 datasheet, Rev. E, page 24](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc3639.pdf).
The uniform rule avoids a component-specific exception. Historical validation
on **2026-09-23**, using KiCad CLI 10.0.4, reduced copper-clearance findings
from four to zero (U601 pad pairs 5/6, 9/10, 10/11 and 11/12). Total findings
fell from 548 to 544, with 447 unconnected items still present and no schematic
parity check. That was a local rule-change check, not overall layout acceptance.
The completed layout's later checks are recorded in
[CMU-009](CMU-009-manufacturing.md).

## 6. Acceptance

- [ ] Every constraint traces to a source document
- [ ] Creepage and clearance fixed and encoded as DRC rules
- [x] Distributed balance-resistor placement recorded; thermal performance unverified
- [x] Communication keepouts present; electrical isolation qualification remains open
- [x] Selected stackup entered for CMU-007; production material confirmation remains open
