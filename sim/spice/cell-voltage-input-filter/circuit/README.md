# Wired NMC / balancing-loop review

**Status: visual review approved; SPICE study authorized.** Open [cell-filter-16-cells-with-wires.sch](cell-filter-16-cells-with-wires.sch)
in Qucs-S. Values are visible and connections are drawn as wires. Use zoom to
inspect the repeated cell channels and the switching loops on the right.

From the repository root, using the installed Qucs-S application:

```bash
build/cell-voltage-input-filter/tools/squashfs-root/AppRun \
  sim/spice/cell-voltage-input-filter/circuit/cell-filter-16-cells-with-wires.sch
```

The sheet contains 643 components, no analysis blocks and no timed stimuli.
`V_enable1` through `V_enable16` are static **0 V**, so every balancing switch is
OFF. They represent abstract 0/1 logic relative to the lower CB die node, not the
physical gate voltage. The Qucs-S relay-shaped symbols are electrical
voltage-controlled SPST switches, not additional PCB relays. Their controls are
wired explicitly, without hidden node labels or ground shortcuts.

The public study.py workflow now runs this approved wired model. See the
[study instructions](../README.md) and [current results](../report/README.md).
The component values, positions and wires are unchanged. Obsolete captions were
updated. The sheet retains static OFF controls and no analysis blocks; the single
scripted repeated-cycle study imposes waveforms in the exported numerical deck.

## Cell and component evidence

The selected cell is **LG INR21700-M50**, using
[LG Chem's manufacturer specification, hosted by Conrad](https://asset.conrad.com/media10/add/160267/c1/-/en/002114679DS01/datenblatt-2114679-lg-chem-inr21700-50t-spezial-akku-21700-flat-top-li-ion-36-v-5000-mah.pdf)
(document LRB-PS-CY18.2Wh-M50, 2017-09-22, **Tentative**, pages 4 and 6).
It gives 3.63 V nominal, 18.2 Wh nominal energy, AC impedance <=25 mOhm at
1 kHz after standard charge, and DC resistance 30 +/- 6 mOhm at 50% SOC with a
0.5C load for 30 s at 25 +/- 2 C. The document describes M50, not M50LT,
despite the distributor's filename. Its 0.2C = 970 mA convention implies a
4.85 Ah C-rate reference; capacity is metadata only.

This sheet retains 16 series groups and assumes one cell per group; it does not
assert the parallel count of your future pack. The 3.63 V source is a chosen
nominal operating point, not a calibrated 50%-SOC OCV or an OCV-versus-SOC model.
The assumed split is `R_cell = 20 mOhm` and `R_relax = 10 mOhm`, summing to
the nominal 30 mOhm DC resistance after relaxation. The split is not uniquely
determined by the specification. `C_relax = 1 F` (10 ms relaxation) and cell
inductance remain unfitted assumptions. Cell transient recovery is therefore
not manufacturer-calibrated. The circuit structure, layout and wiring are unchanged.

| Element | Review value | Basis |
|---|---:|---|
| VC resistors | 100 Ohm | Fitted PCB/BOM |
| CB resistors | 20 Ohm | Fitted PCB/BOM |
| VC/CB capacitors | 470 nF | Fitted TDK CGA3E3X7R1E474K080AE, nominal |
| Capacitor ESR / ESL / leakage | 14.3 mOhm / 0.420 nH / 1.06 GOhm | [TDK simple model, page 2](https://product.tdk.com/system/files/dam/technicalsupport/tvcl/pdf/capacitor_mlcc_auto_soft_cga3_ecm.pdf) |
| Internal switch Ron | 2.5 Ohm | Assumed nominal; TI limits are 1.45–4.6 Ohm for VCn >2.8 V, -40 < TA <125 C |
| Internal switch Roff | 10 GOhm | Assumed |
| Package L per CB pin | 3 nH | Assumed, shared by adjacent internal switches |
| Internal switch Cds | 100 pF | Assumed constant capacitance; not a TI Coss/Qoss model |
| PCB inductance coefficient / via L | 0.6 nH/mm / 1 nH | Assumed, not EM-extracted |

The TDK nominal simple model uses 470 nF without an automatic DC-bias
multiplier. Each parameter's manufacturer evidence or assumption is recorded in
[wired-review.json](wired-review.json). The single nominal study does not establish
tolerance, temperature or capacitor-voltage-bias bounds.

## The visible switching loop

For channel n, follow the loop from its external CB capacitor through
`R_CBloop[n]`, `L_CBloop[n]`, `L_CBpin[n]`, `S_cell[n]`, the corresponding lower
pin/route elements, and back to the capacitor. `C_ds[n]` is across the internal
switch; the 470 nF capacitor is outside the package. There is one package
inductor per CB pin, rather than a duplicate for each adjacent switch.

[wired-review-geometry.json](wired-review-geometry.json) records track-graph
paths from each capacitor's upper pad to the corresponding U201 CB pin, including
the actual pin numbers, coordinates, layers and source hashes. These routes are
16.65–40.70 mm long. Via planar length is zero in this inventory; resistance and
inductance per via are explicit assumptions. The copper resistance calculation
uses actual track widths, 18 um thickness and an assumed 2 mOhm per via.

The former total CB route impedance is partitioned into the upstream feed and
the capacitor-bank-to-IC path, so it is not counted twice. Adjacent capacitor
landing stubs collapse to one bank node per net; this is still a lumped
approximation, not the full distributed copper network. The model also includes
assumed CB route capacitance to AVSS and 0.2 pF VC-to-CB coupling. Detailed harness
mutual coupling and IC internal analog/digital filters are outside this sheet.

TI does not provide the CBFET capacitance, switching edge or CB package
inductance in the sources inspected. No unrelated discrete MOSFET model has been
substituted. The native SPST model changes resistance at a threshold; it does
not reproduce a finite FET conductance transition. The scripted study uses an
explicit 10 us finite-conductance-edge surrogate and timestep verification.

## Measurement scope

One repeated odd / OFF / even / OFF sequence checks all 16 VC inputs and CB-bank
voltages. The 5 ms quiet intervals are judged against a 0.1 mV dynamic-error band
around independently solved final OFF-state offsets. Cell-terminal voltages are
the reference. The remaining absolute DC error is reported separately.

No internal ADC, acquisition-phase or digital-filter model is applied. A usable
external pin-level window does not establish register timing or a guaranteed
hardware wait. See the [single-study report](../report/README.md).

## Regeneration and checks

Generate to a new filename to preserve manual GUI edits:

```bash
python3 sim/spice/cell-voltage-input-filter/prepare-wired-review.py \
  --output /tmp/cell-filter-review.sch
/usr/bin/python3 sim/spice/cell-voltage-input-filter/extract-wired-routes.py \
  --output /tmp/cb-review-geometry.json
```

Both commands refuse to overwrite an existing output unless `--force` is passed.
Neither runs a simulator. Tests compare the complete drawn-wire graph with the
native Qucs-S export, including switch polarity and separate CB package paths.

The numerical deck evaluates the prescribed switch controls as equivalent time
expressions and solves exact perturbations about the initial odd DC state.
Physical voltages/currents are restored in the outputs; switched bias-current
terms are retained. An absolute-coordinate transient through the first OFF
transition cross-checks this algebraic translation.
