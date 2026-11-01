#!/usr/bin/env bash
# SPDX-License-Identifier: CERN-OHL-P-2.0
# Combine completed PCB cases inside the pinned EM numerical-tools environment.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$(cd "$HERE/../../.." && pwd)"
OUT="$PROJECT/sim/results/em/board-path"
ENGINE="${PCB_EM_ENGINE:-podman}"
mkdir -p "$OUT"
USER_FLAGS=(--user "$(id -u):$(id -g)")
if [[ "$ENGINE" == podman ]]; then USER_FLAGS+=(--userns=keep-id); fi
exec "$ENGINE" run --rm --init --network=none "${USER_FLAGS[@]}" \
  --env HOME=/tmp/pcb-em-home --env MPLCONFIGDIR=/tmp/pcb-em-matplotlib \
  --env OMP_NUM_THREADS=1 --env OPENBLAS_NUM_THREADS=1 \
  --volume "$PROJECT:/project:ro" --volume "$OUT:/work:rw" --entrypoint '' \
  localhost/pcb-em-tools:0.1 pcb-python /project/sim/em/transformer-coupling/model.py \
  --project /project --output /work "$@"
