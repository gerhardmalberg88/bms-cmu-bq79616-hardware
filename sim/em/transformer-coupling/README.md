# Balanced COMH/COML board-path model

Copyright (C) 2021-2026 Gerhard Malberg.
SPDX-License-Identifier: CERN-OHL-P-2.0

This replaces the former transformer-coupling skeleton under `sim/daisy-chain/`.
It joins two 2D-derived primary-side line equivalents and one 3D secondary/contact
network per channel with the actual 49.9 Ω series
resistors, 1 kΩ differential shunt and 220 pF bypass values, plus a linear
SM91502AL equivalent. Its endpoints are U201 COM pads and board-mounted J501/J502
contact heads. Cables and mating connectors are excluded.

The two exported wave ports use 100 Ω references; this is a network convention,
not a model of the BQ79616 driver output resistance or operating waveform.

The saved PCB pad connectivity, part values, route continuity, completed stage
manifests and design hashes are checked before generating a combined network.
`model.json` contains the editable assumptions and component/terminal mapping;
`model.py` generates Touchstone, CSV, JSON and a comparison plot. It runs in the
pinned numerical tools image without a sibling source checkout:

```bash
# From the hardware repository root, after all six PCB cases finish:
bash sim/em/transformer-coupling/run.sh
```

The line equivalents use real 4 MHz per-length L/C and the mean saved positive/
negative route lengths; the same L/C are held constant over 1, 4 and 10 MHz.
They approximate varying routes as uniform and lossless. Dense 3D primary meshes
failed quality checks and are excluded, so this is not a full 3D field model of
the IC-to-transformer path.

The transformer is a 1:1 differential equivalent with 150 µH magnetizing
inductance, 0.5 µH series leakage and 0.45/0.85 Ω primary/secondary resistance.
These inputs use the OCL minimum, leakage maximum and listed DCR limits from the
[Bourns SM91502AL datasheet](https://www.bourns.com/docs/product-datasheets/SM91502AL.pdf).
They are assumptions extrapolated from the datasheet's test conditions, not a
manufacturer-validated broadband SPICE model. The DCR assignment to the two
differential series branches is an editable assumption. The manufacturer
schematic gives matching polarity at primary pin 1 and secondary pin 6; COML
reverses both pairs. The implementation is original;
no proprietary vendor model is redistributed.

Two equal 220 pF capacitors to ground give 110 pF in the balanced differential
reduction. Their load and the 1 kΩ shunt are collapsed to the resistor input
plane. The primary 100 pF center-tap bypass has zero differential current in
this ideal balance. Center taps receive no physical ground connection through
the EM port reduction. A limited Lm/leakage sensitivity envelope is included;
it does not bound device tolerances, core loss or frequency dependence.

Omitted effects include TVS off-state capacitance and nonlinear clamps,
transformer interwinding capacitance/core loss, component package parasitics,
asymmetry/common-mode conversion and coupling between separate PCB crops.
The PCB meshes and finite air domains remain unqualified for absolute accuracy.
Three frequencies establish neither transient bandwidth nor an eye/BER result.
A successful run is not measured hardware correlation or isolation/EMC approval.

`test_model.py` checks resistor/capacitor closed forms, power-preserving port
reduction and component-network passivity/reciprocity. The generated report keeps
these numerical checks separate from physical-model limitations.

COML filtered-section modes are ambiguous. The explicit `filtered_line_proxy`
setting uses COMH filtered L/C with the saved COML length. Changing that proxy's
impedance by factors 0.5 and 2 at fixed propagation velocity changes sampled S21
by less than 0.001 dB in this circuit. This is only an assumed-parameter sensitivity;
it does not bound real geometry errors, mode conversion or component parasitics.
