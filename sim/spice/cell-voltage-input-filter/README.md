# Cell-voltage input filter — one repeated balancing cycle

The sole SPICE study is **odd ON → OFF for 5 ms → even ON → OFF for 5 ms**,
repeated three times. Each ON plateau lasts 20 ms. These short diagnostic
plateaus are not claimed firmware timings or a periodic steady-state solution.
The initial state is the odd-balancing DC operating point.

- [Results, plot and verification](report/README.md)
- [Approved wired Qucs-S circuit](circuit/cell-filter-16-cells-with-wires.sch)
- [Component evidence and assumptions](circuit/README.md)
- [Study settings](case.json)

All component values and connections follow the approved LG INR21700-M50 / 16S
circuit. Only obsolete drawing captions were updated. The schematic retains
static OFF controls for inspection; the scripted netlist applies the sequence.
Qucs-S supplies the native connectivity export, ngspice solves the circuit,
and Python measures the saved waveforms. No internal ADC or digital-filter
postprocessing is included.

## Run on Linux

From the repository root:

```bash
sudo apt install ngspice python3-numpy python3-scipy python3-matplotlib xvfb xauth
/usr/bin/python3 sim/spice/cell-voltage-input-filter/setup.py
python3 sim/spice/cell-voltage-input-filter/study.py doctor
python3 sim/spice/cell-voltage-input-filter/study.py gui
python3 sim/spice/cell-voltage-input-filter/study.py all
python3 -m unittest discover -s sim/spice/cell-voltage-input-filter/tests -v
```

`all` runs the nominal timestep and its half-step verification, verifies results,
and generates the report. They are two numerical resolutions of **one study**.
`run`, `verify` and `report` also work separately. `--force` reruns cached results.
The installed baseline is ngspice 42 and Qucs-S 26.1.1. KiCad and its Python
bindings are needed for installation checks and optional design re-extraction.
After a deliberate schematic edit, use `study.py export` to refresh the native
Qucs-S netlist. Graph tests detect disagreement with the maintained circuit
layout generator; GUI edits require corresponding review of that generator.

## Measurements and acceptance

For every OFF gap, measure all 16 differential VC errors against instantaneous
cell-terminal voltages, CB-bank recovery, balancing currents and residual DC
offsets. Dynamic settling requires every channel to stay within **0.1 mV of its
final OFF-state offset** for the remainder of the gap. The next ON edge is
excluded. Waiting cannot remove the remaining DC offset.

Require timestep agreement within 10 uV for VC waveforms, 1 mV for CB-bank
waveforms and 5 us for settling times. Verify native-export connectivity,
independent DC/KCL, source/artifact hashes and successful solver completion.
Failed or stale verification blocks publication. Runs are sequential and each
solver subprocess has a ten-minute timeout with owned-process cleanup.

The numerical model uses equivalent scaled states for floating cell R||C pairs
and assumed 10 us smoothstep conductance edges for switches. The electrical
ports are preserved. These are not transistor-level TI switching models.
Cell relaxation, parasitic values and load-current assumptions remain unfitted.
The result establishes a modeled external pin-level window, not guaranteed ADC
accuracy, register-read timing or a hardware wait requirement.

Only this study's compact report is maintained under `report/`. Native decks,
logs and full waveforms remain ignored under
`sim/results/cell-voltage-input-filter/repeated-cycle/`. Other SPICE study
scripts, configurations, publications and native results have been removed.

The numerical deck evaluates the prescribed switch controls as equivalent time
expressions and solves exact perturbations about the initial odd DC state.
Physical voltages/currents are restored in the outputs; switched bias-current
terms are retained. An absolute-coordinate transient through the first OFF
transition cross-checks this algebraic translation.
