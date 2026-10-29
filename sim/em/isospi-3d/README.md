# Bounded communication PCB models

[comh.yaml](comh.yaml) and [coml.yaml](coml.yaml) model the isolated-side PCB routing
and board-mounted J501/J502 contacts. Follow the [EM workflow](../../../../pcb-em-lab/README.md#em-workflow)
and its [validation status](../../../../pcb-em-lab/docs/validation.md).
Both CPU pipelines and their QucsatorRF/ngspice handoffs passed. The supplied
coarse meshes demonstrate the pipeline; they do not establish converged PCB
field predictions.

Both ports are differential. J501 pin 1 is COMHP and pin 2 COMHN; J502 pin 2 is
COMLP and pin 1 COMLN. The input calibration plane lies between straight,
parallel secondary traces near the connector, giving a rectangular uniform-port
gap. Copper extending back to the cropped transformer pads remains as open
stubs; this is not a network calibrated at the transformer terminals. Coordinates
are checked against the saved copper net. The output ends at connector contacts;
no cable, mating connector or external assembly is included.

The initial conductor model is PEC sheet copper and plated barrel surfaces.
Connector contacts are explicitly approximated square pins; plastic housing,
contact resistance and conductor losses are omitted. The mesh preserves PCB
layer heights, holes and nearby saved copper. Review each approximation before
interpreting coupling or absolute S parameters.

Run from the workflow checkout:

```bash
./pcb-em run ../bms-cmu-bq79616-hardware/sim/em/isospi-3d/comh.yaml --mode 3d --backend cpu
```

The driver excites every port, then assembles an ordered Touchstone network with
explicit polarity/reference impedance. The eight-frequency 1–10 MHz sweep
also exercises passive fitting and the ngspice handoff. A fit is exported only
when its passivity and error checks pass; the report records rejection otherwise.
This narrow demonstration band does not establish fast-edge transient accuracy.
Review mesh and domain convergence against
[CMU-007](../../../docs/CMU-007-si-pi-analysis.md); generated output is ignored under
`sim/results/em/` and establishes no full-link acceptance.
