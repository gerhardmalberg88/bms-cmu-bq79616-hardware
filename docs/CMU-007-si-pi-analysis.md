---
id: CMU-007
title: Signal and Power Integrity Analysis
rev: 0.1
status: draft
phase: pre-layout and post-layout
applies_to: bms-cmu-bq79616-hardware rev 0.1
license: CERN-OHL-P-2.0
---

# CMU-007 — Signal and Power Integrity Analysis

**EM simulations: coming soon.** Planned electromagnetic SI/PI models and
results will live in [`sim/em/`](../sim/em/README.md). The preliminary
cross-section calculations below are not a completed board-level EM validation.
The [isoSPI communication 2D cases](../sim/em/isospi-2d/README.md)
use the shared KiCad/Palace pipeline to evaluate the sections 2.1/2.3
cross-sections and provisional impedance target; numerical validation is in progress.

> **2026-10-24 status:** the routed PCB passes the configured, refilled DRC and its manufacturing files are prepared. This does not establish measured or supplier-guaranteed impedance. See [CMU-009](CMU-009-manufacturing.md).


> **Preliminary routing estimate recorded; post-layout analysis remains open.**
> Impedance comes from the stackup, coupling from the routing, and return paths
> from the actual copper geometry.
>
> The **constraints** SI imposes on layout are inputs, not results, and live in
> [CMU-005](CMU-005-layout-constraints.md) §4. Review them against the routed PCB.

## 1. Scope

The daisy chain (COMH/COML through T501/T502), the cell tap filters, and the
NTC sense lines.

Signals here are slow and the daisy chain is transformer-isolated, so SI is
modest — but the **isolation barrier is a safety dimension**, not just a signal
one, and that makes this document matter more than the data rate suggests.

## 2. Inputs

| Input | Source | Status |
|---|---|---|
| Impedance target, pair matching | CMU-005 §4 and sections 2.1 / 2.3 below | provisional 100 ohm, with separate plane-referenced and plane-free models; matching tolerance open |
| Layer stackup | [CMU-005 section 5.1](CMU-005-layout-constraints.md#51-eurocircuits-physical-stackup-source) | Eurocircuits build entered; pressed dimensions and Dk/Df require confirmation |
| Data rate, cable length | CMU-001 §2 | not yet fixed |

### 2.1 Preliminary communication netclass

This section preserves the **plane-referenced** `CMU_COM_TOP` calculation.
It does not apply inside the later all-layer copper keepouts. See section 2.3
for `CMU_COM_TOP_WITH_KEEPOUTS`; neither model establishes the manufactured
impedance of the actual routed geometry.

**Updated 2026-09-20. This is a routing estimate, not an impedance-controlled
fabrication specification or a completed SI result.**

The existing routing note in `design/com.kicad_sch` calls for a 100 ohm
differential pair. That is retained as **project intent**, pending selection
and characterization of the cable and final layout. It must not be inferred
solely from the two 49.9 ohm series resistors.

TI's [BQ79616-Q1 datasheet, SLUSE81F, sections 8.2.1.2.7 and 10.1.4](https://www.ti.com/lit/ds/symlink/bq79616-q1.pdf)
does not establish a universal 100 ohm differential / 50 ohm single-ended PCB
requirement. Its approximately 120 ohm connection statement occurs in the
series-resistance guidance; it is not used here as a PCB characteristic
impedance target. Follow its short, symmetric, same-layer routing and
all-layer keepout around daisy-chain components. TI's
[SLVAEP4, sections 8 and 9](https://www.ti.com/lit/an/slvaep4/slvaep4.pdf)
also emphasizes layout and cable validation rather than a fixed PCB impedance
number.

For a balanced pair, **Zdiff = 2 Zodd**. A 100 ohm differential target means
50 ohm odd-mode impedance per conductor. This is not the impedance Z0 of one
trace with its partner removed, and it does not require grounding either
conductor. The floating transformer secondary has no prescribed trace-to-local-
ground impedance. See the mode definitions in the
[Qucs coupled-microstrip technical documentation](https://qucs.sourceforge.net/tech/node77.html).

The selected routing width is **0.210 mm**, with **0.250 mm edge-to-edge gap**.
This replaces the earlier 0.240 mm width after considering soldermask loading.
The final Eurocircuits selection changes inner copper from 35 to **18 um**;
the top signal copper and its separation from the reference plane stay the
same. Thus the ideal-reference cross-section retains these inputs:

| Input | Value |
|---|---|
| Signal / reference | F.Cu / continuous local-GND In1.Cu; local GND is not chassis |
| H, dielectric between copper surfaces | 0.070 + 0.120 = **0.190 mm**, section 5.1 of CMU-005 |
| T, finished signal copper | **0.035 mm**; reference plane is 0.018 mm |
| Er, both first-dielectric plies | **4.5**, placeholder requiring supplier confirmation |
| Target Zdiff | **100 ohm**, provisional project choice |
| W / S | **0.210 / 0.250 mm** |
| Assumed soldermask thickness / Er | **0.035 mm / 3.3**, coating profile and properties unconfirmed |

#### Uncoated cross-check

The original sizing used the closed-form approximation documented in the
[NI Ultiboard User Manual, chapter 6, page 6-9](https://download.ni.com/support/manuals/374488c.pdf#page=192):

```text
Z0    = 87 / sqrt(Er + 1.41) * ln(5.98 H / (0.8 W + T))
Zdiff = 2 Z0 * (1 - 0.48 exp(-0.96 S / H))
```

All dimensions use the same unit. This formula omits soldermask. Reproduce
this cross-check from the hardware repository root with
`python tools/estimate_com_impedance.py`. The script reads the saved stackup
and `CMU_COM_TOP` dimensions without modifying them. At 0.210 / 0.250 mm it
returns **Zdiff 106.537 ohm, Zodd 53.269 ohm and isolated-trace Z0 61.634 ohm**.
It synthesizes a bare-pair width of 0.238284 mm for 100 ohm. These are
**uncoated** values and are not the justification for the selected coated-pair
width.

#### Illustrative coated cross-section calculation

[`tools/estimate_com_cross_section.cpp`](../tools/estimate_com_cross_section.cpp)
preserves the independent two-dimensional electrostatic calculation used to
compare candidate widths. It solves `div(epsilon grad V) = 0` on an odd-mode
half-section: the positive conductor is at +1 V, the symmetry boundary and
bottom reference plane at 0 V. The mirrored partner is implicitly at -1 V.
Remote top and right boundaries are also 0 V. Rectangular copper cross-sections
and grid-aligned boundaries are used. From conductor charge per volt it finds
odd-mode capacitance Codd, then repeats with air everywhere for Codd_air:

```text
Zdiff = 2 / (c * sqrt(Codd * Codd_air))
```

Here capacitances are per unit length and c is the vacuum speed of light.
This is a quasi-TEM estimate with ideal conductors, not a qualified production
field solver. The code uses finite-volume coefficients and successive
over-relaxation, stopping when the maximum unrelaxed voltage update falls
below 2e-10 V. It exits unsuccessfully if convergence is not reached.

Two **assumed** mask shapes show sensitivity: a flat upper surface with
35 um above the trace (70 um over the substrate in the gap), and a conformal
35 um coating over the substrate and around the trace. Neither is a confirmed
Eurocircuits coating profile or a guaranteed bound on the real impedance.

| W / S (mm) | Grid / half-domain (mm) | Bare Zdiff (ohm) | Flat mask Zdiff (ohm) | Conformal mask Zdiff (ohm) |
|---|---|---:|---:|---:|
| Previous 0.240 / 0.250 | 0.005 / 1.0 | 101.337 | 93.327 | 95.248 |
| **Selected 0.210 / 0.250** | **0.005 / 1.0** | **107.576** | **98.555** | **100.699** |
| Selected, finer grid | 0.0025 / 1.0 | 107.855 | 98.744 | 100.894 |
| Selected, larger domain | 0.005 / 2.0 | 107.980 | 98.940 | 101.091 |

The selected width brings both illustrative coated results close to 100 ohm
while retaining the 0.250 mm gap and staying above the 0.200 mm project
minimum. For this geometry, grid refinement changes the coated estimates by
less than 0.20 ohm; doubling the domain changes them by less than 0.40 ohm.
Those numerical checks do not bound material or fabrication uncertainty.

To reproduce with a C++11 compiler, build outside the design directory and run:

```console
g++ -O3 -std=c++11 tools/estimate_com_cross_section.cpp -o estimate_com_cross_section
./estimate_com_cross_section 0.005 1.0 0.21 0.25
./estimate_com_cross_section 0.0025 1.0 0.21 0.25
./estimate_com_cross_section 0.005 2.0 0.21 0.25
```

Arguments are grid spacing, domain extent, width and gap, in mm. On Windows
use the corresponding `.exe`. The C++ calculation uses the fixed H, T, Er and
mask inputs listed above; unlike the Python cross-check it **does not read
KiCad**. Review its constants after a stackup change. No executable is stored
in the repository.

Both models exclude etch shape, copper roughness, conductor/dielectric losses,
dispersion, nearby top copper, finite reference-plane extent, pads, vias,
filters, transformers and cable. Confirm pressed dielectric thickness, Dk,
coating construction and impedance tolerance with Eurocircuits before
impedance sign-off. The order screenshot leaves **Defined impedance off**;
these estimates do not change that manufacturing service selection.

`CMU_COM_TOP` was assigned to these six patterns (12 nets). Section 2.3 records
their reassignment after the user added all-layer keepouts:

```text
/bq79616/COMH(N|P)      /bq79616/COML(N|P)
/com/FILT_COMH(N|P)     /com/FILT_COML(N|P)
/com/ISO_COMH(N|P)      /com/ISO_COML(N|P)
```

DP Width and Track Width are 0.21 mm; DP Gap is 0.25 mm; Clearance is 0.19 mm
(global clearance decision dated 2026-09-23, CMU-005 section 5.6).
Via Size / Via Hole remain 0.80 / 0.40 mm and DP Via Gap inherits 0.25 mm
from Default. Prefer no
layer transitions. These dimensions satisfy the existing manufacturing minima;
the clearance is not the required electrical clearance across an isolation
barrier. Microvias remain disabled globally.

**Applicability is determined by copper geometry, not by the net name.** The
microstrip calculation is valid only along sections above a continuous In1.Cu
reference. Around T501/T502 and on their isolated cable sides, maintain the
required plane-free region. The class provides consistent routing dimensions
there but does not predict 100 ohm: analyze that actual coplanar pair, pads,
transformers, filters and cable together. Do not extend a reference plane into
the keepout. Lengthen no trace merely to reproduce an ideal transmission line.

No impedance tuning profile is attached because one plane-referenced model
would be misleading across these different geometries. The netclass supplies
router defaults; it does not enforce impedance, matched length, layer choice,
or an exact width/gap through DRC. Pair skew, target tolerance and full-link
acceptance remain open engineering decisions.

### 2.2 Configuration verification, 2026-09-20

KiCad 10.0.4 loaded `CMU_COM_TOP` for exactly the 12 intended communication nets;
all other nets retained `Default`. The selected dimensions meet the current
global manufacturing minima. The only project JSON changes are the class's
track and differential widths, 0.24 to 0.21 mm. The board changes are the six
inner copper thicknesses, 0.035 to 0.018 mm, and the matching general thickness,
1.810 to 1.708 mm. Dielectric plies and all board geometry are unchanged;
custom rules and global constraints are unchanged. A temporary KiCad save
preserved the eight-layer stackup and its four additional dielectric sublayers.
The Python and C++ calculations reproduced the results above (GCC 6.3.0,
`-O3 -std=c++11` for C++).

KiCad CLI 10.0.4 DRC reported **552 violations and 447 unconnected items**, the
same counts as the pre-change baseline: 4 copper-clearance violations, 1
missing-outline violation, 149 footprint-library issues, 199 silkscreen
overlaps and 199 silkscreen-over-copper violations. The library issues come
from the temporary CLI configuration without the standard footprint libraries
registered. This board has no routed tracks or vias yet, so DRC cannot verify
pair impedance or skew. ERC was not rerun because schematics were unchanged.

**Clearance update, 2026-09-23:** the board minimum and both netclass clearances
are now 0.190 mm. The 2026-09-20 DRC counts above are historical; see
[CMU-005 section 5.6](CMU-005-layout-constraints.md#56-global-copper-clearance-decision-2026-09-23)
for the comparison. Pair width, pair gap, net assignments and
stackup are unchanged, so the modeled pair cross-section above is unchanged.
Clearance to surrounding copper remains part of the completed-layout review.

### 2.3 Plane-free communication netclass, 2026-10-18

**Nominal routing estimate: 0.450 mm trace width and 0.200 mm edge-to-edge
gap, approximately 100 ohm differential with the assumed soldermask.**
This is not a guaranteed fabricated impedance or a completed layout sign-off.

The user extended the keepouts to both COMH and COML and requested a separate
class for rerouting. `CMU_COM_TOP_WITH_KEEPOUTS` now supplies the defaults for
the six patterns / 12 nets listed in section 2.1. The original `CMU_COM_TOP`
definition remains unchanged, available for genuinely plane-referenced routing.
The PCB, schematics, copper fills, keepouts and existing routes were not edited.

| New class setting | Value |
|---|---|
| Track Width / DP Width | **0.450 / 0.450 mm** |
| DP Gap, edge to edge | **0.200 mm** |
| Pair centre-to-centre separation | **0.650 mm** |
| Total pair span, outside edge to outside edge | **1.100 mm** |
| Clearance to other nets | **0.190 mm**, inherited project choice |
| Via diameter / drill | **0.800 / 0.400 mm**, unchanged |
| DP Via Gap | Inherits **0.250 mm** from Default; not an impedance model for vias |

The 0.200 mm gap stays above the 0.190 mm project clearance. It permits a
smaller pair span than retaining the old 0.250 mm gap: the latter needs about
0.620 mm wide traces (1.490 mm span) for a similar coated estimate.
Netclass dimensions are router defaults; they do not enforce measured impedance
or an exact routed width/gap in DRC. No impedance-tuning profile is attached.

#### Model and inputs

The correct idealized cross-section is a **coplanar strip pair without a ground
plane**, not a differential microstrip over a distant assumed plane. Both
conductors, finite copper thickness, air above/below the board, the full
dielectric slab and soldermask enter the calculation. This distinction and the
zero-thickness analytical limit are described by
[Gevorgian and Berg, equations 4-8](https://amsacta.unibo.it/393/1/Eug_p114.pdf).
The importance of conductor side-wall coupling in a pair without a return plane
is also discussed in the original numerical study by
[Suresh et al.](https://www.signalintegrityjournal.com/articles/2859-ultra-fine-line-differential-pair-design-with-no-return-plane).

[`tools/estimate_com_keepout_impedance.py`](../tools/estimate_com_keepout_impedance.py)
reads the saved stackup and solves `div(epsilon grad V) = 0` using a nonuniform,
node-centred finite-volume mesh and a sparse direct linear solve. The positive
trace is at +1 V, its mirrored partner at -1 V; x=0 is the odd-mode symmetry
boundary. The distant outer boundaries are numerical truncations at zero
potential, **not PCB reference planes**. An identical air-only solve gives
`Zdiff = 2 eta0 / sqrt((Codd/eps0) (Codd_air/eps0))`.

| Input | Value / status |
|---|---|
| Signal layer / copper | F.Cu / **0.035 mm**, from the saved stackup |
| Dielectric slab thickness | **1.568 mm**: 1.460 mm dielectrics plus six 0.018 mm etched inner-layer spaces, assumed resin-filled |
| Substrate Dk | **4.5**, saved placeholder, unconfirmed by the manufacturer |
| Top / bottom mask thickness | **0.035 / 0.035 mm**, from the stackup |
| Mask Dk | **3.3**, retained assumption from section 2.1 |
| Mask shapes | Flat top at 0.070 mm above substrate, or conformal 0.035 mm coating; neither is a confirmed process profile |
| Other copper | Absent from the model: no plane, guard, neighbouring trace or nearby plane edge |

#### Results and numerical checks

All entries use 0.450 / 0.200 mm width/gap except the stated comparisons.
Mesh size refers to the fine cells near the traces; remote cells expand
geometrically. Extent is the half-domain in x and both positive/negative y.

| Mesh / extent (mm) | Bare Zdiff (ohm) | Flat mask Zdiff (ohm) | Conformal mask Zdiff (ohm) |
|---|---:|---:|---:|
| 0.005 / 8 | 106.706 | 98.493 | 100.563 |
| 0.0025 / 8 | 106.910 | 98.646 | 100.723 |
| 0.00125 / 8 | 106.999 | 98.708 | 100.788 |
| 0.0025 / 16 | 107.081 | 98.807 | 100.885 |
| **0.00125 / 16** | not rerun | **98.870** | **100.951** |
| 0.0025 / 32 | not rerun | 98.851 | 100.929 |

The final mesh refinement changes coated estimates by less than 0.07 ohm;
doubling extent from 16 to 32 mm changes them by less than 0.05 ohm at the
0.0025 mm mesh. These are numerical checks, not fabrication tolerances.
The zero-thickness, effectively infinite-substrate validation gives 115.475 ohm
at 0.00125 mm / 16 mm, versus 115.760 ohm from the independent elliptic-integral
formula (0.25% difference). The sparse-system residual was below 1e-8 in all runs.

For comparison, the old 0.210 / 0.250 mm geometry with no planes gives
125.934 / 129.018 ohm for flat / conformal mask on the 0.005 mm / 8 mm mesh.
The alternative 0.620 / 0.250 mm geometry gives 99.317 / 101.138 ohm on the
0.0025 mm / 8 mm mesh; it was not added as another class.

Sensitivity checks at 0.0025 mm / 16 mm give:

| Changed input | Flat / conformal Zdiff (ohm) |
|---|---|
| Substrate Dk 4.2, mask Dk 3.3 | 101.075 / 103.307 |
| Substrate Dk 4.8, mask Dk 3.3 | 96.688 / 98.628 |
| Substrate Dk 4.5, mask Dk 3.0 | 99.706 / 101.520 |
| Substrate Dk 4.5, mask Dk 3.6 | 97.941 / 100.277 |

These variations are illustrative, not supplier tolerance limits. Before
manufacturing, confirm the actual material, mask construction, copper profile
and controlled-impedance target with the selected fabricator.

Reproduce with Python 3, NumPy and SciPy, from the hardware repository root:

```console
python tools/estimate_com_keepout_impedance.py --width 0.45 --gap 0.20 --step 0.0025 --extent 16
python tools/estimate_com_keepout_impedance.py --width 0.45 --gap 0.20 --step 0.00125 --extent 16
python tools/estimate_com_keepout_impedance.py --width 0.45 --gap 0.20 --step 0.0025 --extent 32
python tools/estimate_com_keepout_impedance.py --width 0.45 --gap 0.20 --step 0.00125 --extent 16 --thin-check
```

#### Applying the new defaults

The saved fill was sampled along all 12 communication nets after the user's
update; no ground fill was found directly below those samples on any other
copper layer. This checks the premise, not the complete electromagnetic field.

**The 1.100 mm pair span needs a wider corridor than the previous 0.670 mm pair.**
Some existing keepout sections are approximately 1.0 mm wide, so the user must
expand those when rerouting. The keepout must cover both full trace widths on
every layer and provide additional separation from surrounding copper. The
0.190 mm net clearance is a manufacturing minimum, not evidence that nearby
ground-plane edges have negligible influence. Assess those edges and the
primary-side capacitor ground escape traces in the final geometry.

Use short, symmetric neck-downs at fine-pitch IC/filter pads where the new width
cannot fit. Pads, those transitions, bends, vias, filters, transformers, cable,
etch shape, losses and surrounding copper are outside this straight-pair model.
Do not introduce extra trace length merely to obtain a uniform cross-section.
Reopen the project so the router loads the new class, and use netclass-derived
differential-pair dimensions when rerouting.

KiCad 10.0.4 loaded the new class for exactly the 12 intended nets with
0.450 mm Track Width / DP Width and 0.200 mm DP Gap; all other nets retained
Default. A structural project comparison confirmed only the new class and six
assignment changes. The original class definition is identical, and hashes of
the other ten design files (including the PCB and schematics) are unchanged.
Full-board DRC was not rerun for this router-default change; rerouting and its
DRC verification remain with the user.

## 3. Cases to evaluate

### Planned power-integrity work

No power-integrity simulation or measured result is available. Evaluate supply
distribution and voltage drop through the stack input, buck output and AFE
preregulator; decoupling impedance and transient response at the ICs; and
return paths through planes, vias and local ground connections. Inputs must
include the saved stackup/layout, component parasitics and credible load cases
from CMU-002. Preserve communication isolation keepouts in the models.

### Signal-integrity cases

**Follow-up 1.600 mm request, 2026-09-20:** the saved netclass and stackup
were re-read and the two calculation tools rerun. The class still resolves
to the intended 12 nets, uses 0.210/0.250 mm width/gap, and meets the attached
Class 6C dimensions. The uncoated approximation returns 106.537 ohm; the
illustrative coated calculations return 98.555 and 100.699 ohm on the
0.005 mm grid / 1.0 mm half-domain. These confirm the earlier computation,
not the impedance of a manufactured board. There are still no reference
zones or routed tracks to analyse. The new attachments conflict on inner
copper and do not provide a 1.600 mm physical construction; see
[CMU-005 section 5.5](CMU-005-layout-constraints.md#55-request-for-a-1600-mm-physical-stackup-compatibility-review).
Recalculate if the confirmed replacement changes H, signal copper, Dk or
mask geometry. Until then the current class remains a preliminary candidate.

- [ ] Coated-pair impedance against the provisional target where the reference
      plane exists, from supplier-confirmed stackup and actual copper geometry
- [ ] Intra-pair skew
- [ ] **Return path across the isolation barrier.** The return cannot cross it,
      so the reference change must be deliberate and analysed, not incidental
- [ ] Transformer terminations: 49R9 series, 220 pF / 100 pF C0G filtering
- [ ] LTC3639 SW node dV/dt coupling into the tap filters and the daisy chain —
      the highest-energy switching edge on the board
- [ ] Cell tap RC filter corners against the AFE's sampling
- [ ] Crosstalk between adjacent tap nets, which sit at up to 67 V DC apart
- [ ] Maximum daisy-chain cable length (CMU-008 open item O-4)

## 4. Acceptance

- [ ] Target and tolerance agreed and verified for the applicable routed sections
- [ ] Transitions into plane-free isolation regions evaluated in full-link SI
- [ ] Isolation barrier uncrossed by any copper on any layer
- [ ] Filter corners consistent with the AFE sampling in CMU-004

## 5. Validation (post-test)

- [ ] Eye diagram on the daisy chain at maximum cable length
- [ ] Bit error rate over the operating temperature range
- [ ] Injected-noise margin
