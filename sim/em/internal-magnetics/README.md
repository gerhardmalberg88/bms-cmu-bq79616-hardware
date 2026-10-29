# Approximate internal magnetic models

Cases [t501.yaml](t501.yaml), [t502.yaml](t502.yaml), and [l601.yaml](l601.yaml)
provide editable linear magnetostatic models. T501/T502 include separate
transformer and integrated common-mode-choke winding/core sets. A small-signal
Driven variant is [t501-driven.yaml](t501-driven.yaml).

**Internal geometry, turn counts and material properties are inferred placeholders.**
Supplier package CAD is not internal winding evidence. The open cylindrical cores
and individual gapped sheet turns expose parameters for study; they do not claim
manufacturer topology. Fields exclude leads and PCB copper. Saturation, hysteresis
and nonlinear behavior are outside this initial Palace implementation.

The saved BOM identifies T501/T502 as SM91502AL and L601 as 220 µH. These internal
templates are **uncalibrated demonstrators**: for example, the initial four-turn
L601 geometry yields roughly 0.14–0.15 µH, far below its nominal component value.
Replace the winding/core assumptions with supplier or measured information before
using these fields to describe the physical parts. Matching nominal inductance
by parameter fitting alone would still not establish the actual internal fields.

Follow the shared [EM workflow](../../../../pcb-em-lab/README.md#em-workflow)
and [validation status](../../../../pcb-em-lab/docs/validation.md). CPU static
and driven pipelines, matrix checks and winding-field normalization passed.
The internal geometry remains uncalibrated; component field accuracy is unestablished.

```bash
# From the sibling workflow checkout:
./pcb-em run ../bms-cmu-bq79616-hardware/sim/em/internal-magnetics/l601.yaml --backend cpu
```

Sweep core permeability, core size, winding spacing and domain size separately
from mesh refinement. Report signed winding inductance/coupling and inspect
field superposition using declared winding signs. Terminal inductance agreement
alone cannot validate internal fields. Relate reviewed terminal results to
[CMU-007](../../../docs/CMU-007-si-pi-analysis.md) and component assumptions in
[CMU-008](../../../docs/CMU-008-interface-control.md) where applicable.

Completed studies cover L601 material/mesh/domain variation and transformer/choke
permeability for the shared T501/T502 internal template. The choke sweep retained
identical mesh bytes and varied only its linear permeability:

```bash
./pcb-em sweep ../bms-cmu-bq79616-hardware/sim/em/internal-magnetics/t501.yaml \
  --backend cpu --parameter magnetics.cores.1.mu_r --values 250 500 1000
```

Its positive-winding self-inductance is approximately 21.151/21.277/21.341 nH.
T501/T502 currently use identical internal-model parameters; this is shared
template sensitivity, not validation of the physical components.
