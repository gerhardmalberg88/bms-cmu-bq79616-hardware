# BQ79616 cell-voltage input filter — simulation plan

**Status: planning only.** This is the only planned transient/SPICE study in this
repository. No Qucs-S schematic, ngspice netlist, behavioral model, launcher or
simulation result has been implemented. Qucs-S will provide the editable circuit
GUI and ngspice the numerical backend on Linux. Future case parameters and model
provenance will use JSON.

## Objective and scope

Reconstruct the fitted 16S path from the cell terminals through J401 and its tap
fuses to U201's VC inputs, then determine which realistic nonidealities cause
measurement errors, delayed settling or unexpected interaction between channels.
First reproduce the present circuit; evaluate improvements against that baseline.
A useful outcome is a reproducible failure envelope or a justified improvement,
not a claim of novelty based only on adding components.

This study supports the cell-measurement error budget in
[CMU-004 §4](../../../docs/CMU-004-stress-and-wcca.md) and the accuracy/latency
requirements still to be defined in [CMU-001](../../../docs/CMU-001-requirements.md).
Buck failure, supply startup/inrush, OTP rail transitions, connector mis-mating,
fuse clearing and broad ESD/surge qualification are outside the active simulation
plan. The existing EM and thermal studies remain separate, with their recorded
limitations. Removing other simulation plans does not validate those hazards.

Cell-to-connector wiring is an editable source-boundary equivalent within this
study. Record its actual length, conductor arrangement, contacts and return path
when known; otherwise sweep explicitly hypothetical bounds. This does not create
a separate cable-design study or revive the removed communication-cable scope.

## Verified starting circuit

The reference is the **fitted PCB population**, cross-checked against a fresh,
read-only KiCad schematic netlist. Schematic-only connector alternatives and DNP
links must not become conductive connections in the model.

| Item | Observed baseline |
|---|---|
| AFE | U201, BQ79616PAPRQ1 |
| Cell connector | J401, Harwin M80-5002042; 17 used taps, interleaved pin order |
| Tap fuses | F401–F417, Littelfuse 0470.500DRSNP, fitted 500 mA parts |
| Sense resistors | 17 fitted 100 Ω, 0.1%, Vishay TNPW0603100RBEEA; mapped below |
| Sense capacitors | 16 differential 470 nF capacitors plus C332 from VC0 to local GND/AVSS |
| Capacitor part | TDK CGA3E3X7R1E474K080AE, nominal 470 nF, 25 V X7R |
| Balancing branch | 17 fitted 20 Ω RCL122520R0FKEG resistors, 16 differential CB capacitors plus C331 from CB0 to GND |
| DNP links | All 0 Ω R3xx option links are DNP; retain their pads/stubs as parasitic geometry only |

A capacitor listed in row n bridges VCn to VC(n−1), except the explicitly marked
VC0 termination. Channel numbers must follow nets and U201 pins, not the order of
reference designators. J401's physical pin adjacency differs from cell order.

| Tap | J401 pin | Fuse | Sense resistor | VC capacitor | U201 VC pin |
|---|---:|---|---|---|---:|
| 0 | 1 | F417 | R357 | C332 (VC0–GND) | 35 |
| 1 | 11 | F416 | R350 | C328 | 33 |
| 2 | 2 | F415 | R343 | C324 | 31 |
| 3 | 12 | F414 | R336 | C320 | 29 |
| 4 | 3 | F413 | R329 | C316 | 27 |
| 5 | 13 | F412 | R322 | C312 | 25 |
| 6 | 4 | F411 | R315 | C308 | 23 |
| 7 | 14 | F410 | R306 | C304 | 21 |
| 8 | 5 | F409 | R301 | C302 | 19 |
| 9 | 15 | F408 | R358 | C334 | 17 |
| 10 | 6 | F407 | R351 | C330 | 15 |
| 11 | 16 | F406 | R344 | C326 | 13 |
| 12 | 7 | F405 | R337 | C322 | 11 |
| 13 | 17 | F404 | R330 | C318 | 9 |
| 14 | 8 | F403 | R323 | C314 | 7 |
| 15 | 18 | F402 | R316 | C310 | 5 |
| 16 | 9 | F401 | R307 | C306 | 3 |

The VC and CB ladders share cell taps and their source impedances. They are not
17 independent single-ended RC channels. Preserve the VC0/CB0 termination,
AVSS connection and both ends of the stack. Start with all 16 cells; a three-cell
interior slice may be a debugging aid only after comparison with the full ladder.

For a deliberately isolated differential RC sanity check with two ideal-source
100 Ω legs and one 470 nF capacitor, τ = (100 + 100) × 470 nF = **94 µs** and
fc ≈ **1.69 kHz**. These are not the full-board transfer function or an ADC
settling guarantee. The 47 µs product of one resistor and one capacitor cannot
justify a claim that every channel settles independently.

## Model fidelity and parameter evidence

Use separate model layers so their contribution can be switched on and measured.
Every parameter will carry units, source/revision, nominal value, bounds,
temperature/voltage dependence and a label: **specified**, **measured**,
**geometry-estimated** or **assumed**. Missing data remain uncertainty ranges.
“All parasitics” cannot be known exactly from a schematic.

| Layer | Planned representation and evidence |
|---|---|
| Cells | One voltage source per cell plus measured/fitted series R and relaxation RC branches; add terminal inductance if supported. Use 2.5/3.7/4.2 V as initial operating points from the existing design assumptions, with unequal-cell cases. Chemistry, SOC, temperature and ageing impedance data are still required. Separate actual terminal-voltage movement under load from filter-induced error. |
| Wiring, contacts and fuses | Individual conductor/contact/fuse R and L, connector contact capacitance and coupling between adjacent conductors. Model the fuse as an intact impedance here; its nominal current rating is not a resistance or an opening model. Include the bottom return fuse F417. |
| PCB | Extract lengths, widths, layers, vias and return geometry from the saved board. Include trace/via resistance and self/mutual inductance, shunt capacitance and capacitance between relevant taps, VC/CB traces, planes and nearby aggressors. Preserve local reference impedance. DNP pads have capacitance even though their components are open. |
| Passive components | R tolerance/tempco, package L and shunt C where significant; capacitor effective C versus bias, temperature and ageing, ESR, ESL and leakage from the exact part's manufacturer data or measurement. Nominal 470 nF alone is insufficient. Use correlated and independent mismatch cases. |
| Balancing | Shared 20 Ω branch network, CB capacitors and switch states between the actual adjacent CB nodes. Include finite switch resistance/edge time and shared tap drops. Compare off, single-channel, odd/even groups and their transitions as disturbances of this same VC study. Do not replace shared resistors with unrelated per-cell duplicates. |
| Shared supply/reference paths | Represent loading on the top/bottom taps and local reference impedance. Include the BAT branch (R202/C208) where its measured or bounded loading matters; represent the remaining supply as a boundary impedance/current disturbance. This does not require a separate regulator/startup model. |
| BQ79616 loading | Begin with a transparent, bounded input-loading model using documented current/mismatch and mode dependence. Add pin/package capacitance and any sampling back-action only when supported by manufacturer information or measurement. Unknown internal current return paths must be exposed as assumptions. An ideal voltmeter is only a reference case. |
| Measurement chain | Keep VC-pin voltage, modeled analog filtering, ADC acquisition/timing and digital filtering as separate outputs. A response fit is a behavioral approximation, not a transistor-level device model. Register settings and balancing/diagnostic modes belong in each future case record. |

Use a physically meaningful reference: for example, cell-stack negative as SPICE
node 0 and **local AVSS as a separate node** behind F417 and its wiring impedance.
Grounding both ends of that path would bypass a real coupling mechanism. Common-mode
injection needs a defined chassis/return impedance; shifting an entirely floating
circuit without a return path is not a useful disturbance test.

Coupled networks must be physically realizable: document mutual-inductance sign
and winding/dot orientation; require a positive-semidefinite inductance matrix,
not just pairwise |k| ≤ 1. Build capacitances from a consistent conductor matrix
or passive pairwise elements. Avoid double-counting package/contact/PCB parasitics.
For any future broadband fit, check passivity, causality and its frequency range.
Use distributed wiring when propagation delay invalidates the lumped approximation.

The existing COMH/COML EM outputs describe different nets and cannot supply VC
parasitics. No new FEM work is scheduled by this plan. Geometry estimates or
measurements are the first inputs. Existing thermal results may inform explicitly
provisional local board-temperature corners; resistor hotspots are not VC-component
or AFE junction temperatures, and do not justify a new thermal solve.

## TI reference boundaries

The datasheet recommends differential VC filtering with 100 Ω and 0.47 or 1 µF;
filter components also participate in insertion protection. It documents input
current and mismatch, internal analog filtering, conversion sequencing, digital
filtering and balancing pause controls. Those functions must not be collapsed
into the external RC network. Before implementation, transcribe the relevant
limits with their operating conditions and distinguish input loading from
end-to-end channel accuracy. [TI datasheet, SLUSE81F](https://www.ti.com/lit/ds/symlink/bq79616-q1.pdf),
§6.5, §7.3.2.1.1, §7.3.3 and §8.2.1.2.1.

Use the [BQ79616 EVM guide, SLUUC37D](https://www.ti.com/lit/ug/sluuc37d/sluuc37d.pdf)
§7 as an independent topology comparison, not as a substitute for this PCB's
population. Use [TI design recommendations, SLVAE87B](https://www.ti.com/lit/pdf/slvae87)
for implementation and layout review. These references were checked on 2026-11-01;
record document revisions again when implementing the study.

A suitable validated BQ79616 analog SPICE model has **not been established for
this study**. Check TI's available models/support before choosing a surrogate.
Do not invent an internal sample capacitor, clamp curve or proprietary topology.
Absolute-maximum ratings are comparison limits, not diode-clamp voltages. If
internal protection becomes relevant, record the unsupported region instead of
claiming device survival. Any vendor model requires documented use and
redistribution terms; independently authored models retain the repository license.

## One study, staged implementation

1. **Freeze topology and the error budget.** Review the tap map against the saved
   PCB/netlist, confirm all fitted/DNP states, record source hashes and collect
   component curves and cell/wiring data. Agree the external-filter error budget,
   total accuracy, permitted latency, disturbance amplitudes and temperature range.
2. **Build the nominal full ladder.** Later create one hierarchical Qucs-S circuit
   with an inspectable ngspice netlist. Establish DC and isolated-RC checks, then
   solve the actual 16-cell network and its channel-to-channel transfer functions.
3. **Add nonidealities incrementally.** Add source impedance, part tolerances and
   loading first, then PCB/wiring coupling and the balancing disturbance. Compare
   against the simpler model after each addition. Extend high-frequency coverage
   only as far as the component and interconnect models support it.
4. **Find failure envelopes.** Run the scenario matrix below on the same circuit.
   Rank sensitivities, sweep correlated corners and use reproducible Monte Carlo
   samples only with justified distributions. Search worst-case ADC sampling phase
   relative to disturbances. Refine cases around observed boundaries.
5. **Compare one improvement at a time.** Keep the fitted circuit as the baseline.
   Require an improvement to survive uncertainty and worst-case channel tests at
   the same error/latency constraints. Select a small bench experiment that can
   distinguish the predicted mechanism from a modeling artifact.

| Scenario within this study | Question and outputs |
|---|---|
| DC and leakage corners | Which channel has the largest filter-induced offset? Separate ADC loading, source drops and capacitor leakage; measure per-cell current drain and mismatch. |
| Differential disturbance | Apply a cell-terminal step, pulse and ripple to each cell in turn. Record every channel's attenuation, peaking, phase, overshoot and settling error. Test bottom, interior and top cells explicitly. |
| Common-mode conversion | Apply a defined common-mode disturbance through a physical coupling/return network. Sweep asymmetric C/L, contact R and component mismatch; identify differential errors that a symmetric one-channel model hides. |
| Balancing transitions | Turn balancing on/off and change odd/even groups. Separate real cell-terminal droop from sense-path error, and compare simultaneous-neighbor effects with isolated operation. This is not a balancing thermal study. |
| Capacitive versus inductive coupling | Drive a nearby measured/bounded voltage or current aggressor through coupling C or mutual L. Toggle each coupling mechanism separately and together; report the worst physically realizable alignment. |
| Noise contributions | Separate deterministic ripple/crosstalk from resistor thermal noise and supported device-noise models over the measurement bandwidth. Unknown AFE noise is not zero; an external-network noise calculation does not establish the complete ADC noise floor. |
| Sampling and filter interaction | Compare continuous pin error with modeled sampled/filtered error. Sweep event phase and register settings; establish quiet time after balancing changes without assuming that a small analog ripple guarantees a small reported error. |
| Degraded input-filter parts | Explore tolerance, reduced effective C, increased contact/fuse R and a leaky/partly disconnected filter element as sensitivity cases. An optional open-tap case addresses detection/measurement behavior only; no mis-mate or survival qualification is revived. |

Use a coarse low-frequency transfer sweep first, then refine around poles,
resonances and any switching-related frequencies. Choose transient duration from
measured settling and slowest modeled mode. Choose timestep from the fastest
retained edge/time constant and repeat critical cases with half the maximum step.
Do not resolve hypothetical nanosecond behavior over multi-second settling unless
both time scales are necessary for the result.

## Improvement hypotheses worth testing

**Preferred first investigation: channel-dependent quiet time and capacitance
matching.** Hypothesis: shared tap impedance and mismatched effective capacitance
make some channels recover much later after balancing transitions. Compare one
fixed measurement delay with a delay established from the worst channel and its
uncertainty. Evaluate matching effective capacitance at operating bias, rather
than merely tightening the printed nominal tolerance. Report the cost in balancing
duty cycle and measurement latency. This combines a circuit finding with an
operating strategy; any firmware change remains a later decision.
A later register read is not necessarily a later acquisition: respect the device
conversion sequence and analog/digital settling. Use only realizable pause,
conversion and readout controls; if individual acquisition timing cannot be
changed, derive a conservative common quiet interval from the worst channel.

**Second: asymmetric coupling and return-path control.** Hypothesis: a plausible
common-mode disturbance becomes differential error through unequal coupling,
including the bottom return path. Compare reduced/asymmetry-balanced coupling
and a lower shared return impedance with simply increasing filter capacitance.
A useful result could be a quantified layout/contact requirement rather than a
new filter topology.

**Third: noise-versus-settling trade-off.** Compare the fitted 470 nF baseline
with the datasheet's 1 µF option using real bias/ESR/ESL behavior. Only if a
measured or credible parasitic resonance remains, evaluate a damped additional
stage as an experimental alternative. Account for extra bias-current drop,
leakage, capacitor voltage stress, diagnostics and insertion behavior before
proposing a hardware change. Do not assume a larger capacitor or ferrite bead
is automatically better.

These are testable research hypotheses, not claims of a new invention or proven
improvements. A robust demonstration that the standard circuit fails in a
specific realistic corner is itself a useful outcome.

## Metrics, acceptance and future deliverables

Define the external-network error for cell n at the same physical instant as:

`e_pin,n(t) = [V(VCn) − V(VCn−1)] − [V(cell-terminal n) − V(cell-terminal n−1)]`.

Also report filter input/output values and source-path drops separately. For a
modeled ADC result, state timestamp, acquisition window and filter latency so
sampling delay is not silently counted as static offset. Report maximum and RMS
error, time to stay inside an error band, cross-channel transfer, overshoot,
component current/power and modeled sampled-error extrema.

For exploratory ranking only, plot settling to **0.1, 0.5 and 1 mV** bands.
These are proposed analysis thresholds, not established CMU acceptance limits;
CMU-001 currently leaves accuracy, temperature and latency requirements open.
A nominal improvement that fails a credible tolerance corner is not accepted.

Before accepting any future simulation:

- Verify node mapping, polarity, population, DC KCL and the isolated-RC analytic
  response; compare the coupled network with coupling disabled.
- Verify timestep, solver tolerance and frequency-grid refinement. Numerical
  changes must be well below the adopted error budget; set that numerical limit
  before interpreting small differences between candidates.
- Separate external-filter error from the device's specified conversion accuracy;
  avoid counting the same loading contribution twice. Treat unspecified model
  parameters as uncertainty, not zero and not a statistical guarantee.
- Compare every candidate on the full ladder, including edge channels, practical
  component limits, measurement latency and diagnostic compatibility.
- Label outputs as simulated predictions until a measured transfer/settling test
  confirms the relevant circuit behavior. Keep unverified internal ADC behavior
  explicit even when external pin waveforms have been validated.

When implementation is requested, the planned deliverables are one Qucs-S project,
its reproducible ngspice netlist, JSON parameters/provenance, a connectivity/model
validation report, CSV summaries, transfer/crosstalk heatmaps, waveform/error plots
and a comparison of the baseline with the chosen improvement. Raw outputs will be
ignored under `sim/results/cell-voltage-input-filter/`; compact reviewed results
will live beside this plan. No model-library or launcher scaffolding is needed
until implementation begins.

## Open inputs before implementation

- Actual cell chemistry/impedance data and the cell-to-J401 connection geometry.
- Manufacturer curves or measurements for the fitted capacitors, fuse/contact
  impedance and relevant resistor temperature behavior.
- Operating temperature, external measurement-error allocation and allowed latency.
- Intended ADC/filter/diagnostic register settings and balancing timing.
- Realistic aggressor amplitudes, edge rates and return/coupling paths.
- Available TI model/support information and a practical bench correlation method.

These missing inputs do not prevent drawing the actual circuit later, but they
limit how closely any resulting model can represent the physical assembly.

## Source inspection record

Inspected 2026-11-01 at Git revision `884e9f833f4aba30ceba0311b79456b8b17810d0`. A fresh KiCad
netlist and PCB pad-net comparison agreed for J401, F4xx, R3xx, C3xx and U201.
This verifies topology only; it is not a simulation result.

| Saved design source | SHA256 |
|---|---|
| `design/battery_management_system_cell_monitoring_unit.kicad_pcb` | `1b76b7c8ea7a128470f81970f650df91c0bca88da16263814eba0b1634ba51fa` |
| `design/balance.kicad_sch` | `5b1723f0d22500174c27d9a50a4ba4e81a19c1ec13e31e9046da29cffe651d0a` |
| `design/cells.kicad_sch` | `d35dfb457677ce2df19687c1916d51a770597b272269dc660e3319c4a92f2156` |
| `design/bq79616.kicad_sch` | `2f684b06aa036257138949e5af40e84399ad98686956f60aaf458b426e350088` |
