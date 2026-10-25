#!/usr/bin/env bash
# Run the cell-tap-mis-mate simulation and compare against the committed baseline.
#
# Copyright (C) 2021-2026 Gerhard Malberg
# SPDX-License-Identifier: CERN-OHL-P-2.0
set -euo pipefail

NAME="cell-tap-mis-mate"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM_ROOT="$(cd "$HERE/../.." && pwd)"
NETLIST="$HERE/$NAME.cir"
OUT="$SIM_ROOT/results/$NAME"

# --- the netlist may not be written yet -------------------------------------
if [[ ! -f "$NETLIST" ]]; then
  echo "$NAME: no netlist yet."
  echo "  expected: $NETLIST"
  echo "  This simulation is a skeleton. See notes.md for what it must model"
  echo "  and the pass criteria it has to meet."
  exit 2
fi

# --- locate ngspice ---------------------------------------------------------
find_ngspice() {
  if command -v ngspice >/dev/null 2>&1; then command -v ngspice; return; fi
  for c in     "/c/Program Files/ngspice/bin/ngspice.exe"     "/c/Spice64/bin/ngspice.exe"     "/usr/local/bin/ngspice"; do
    [[ -x "$c" ]] && { echo "$c"; return; }
  done
  return 1
}

if ! NGSPICE="$(find_ngspice)"; then
  echo "$NAME: ngspice not found." >&2
  echo "  Install ngspice 39 or newer and put it on PATH." >&2
  echo "  KiCad bundles ngspice as a library for its own GUI simulator, but" >&2
  echo "  that cannot be driven from the command line - a standalone build is" >&2
  echo "  needed to run this script." >&2
  exit 3
fi

# --- fetch any vendor models this simulation depends on ---------------------
# models.txt, if present, holds one "<filename> <url>" per line. Vendor models
# are never committed; see ../../lib/README.md.
if [[ -f "$HERE/models.txt" ]]; then
  mkdir -p "$SIM_ROOT/lib/vendor"
  while read -r fname url; do
    [[ -z "${fname:-}" || "$fname" == \#* ]] && continue
    dest="$SIM_ROOT/lib/vendor/$fname"
    if [[ ! -f "$dest" ]]; then
      echo "$NAME: fetching $fname"
      curl -fsSL "$url" -o "$dest"
    fi
  done < "$HERE/models.txt"
fi

# --- run --------------------------------------------------------------------
mkdir -p "$OUT"
echo "$NAME: running $(basename "$NGSPICE")"
"$NGSPICE" -b -o "$OUT/$NAME.log" -r "$OUT/$NAME.raw" "$NETLIST"

# --- compare against the baseline -------------------------------------------
if [[ -f "$HERE/check.py" ]]; then
  python "$HERE/check.py" --raw "$OUT/$NAME.raw" --expected "$HERE/expected"
else
  echo "$NAME: ran, but no check.py - result not verified against a baseline." >&2
  echo "  A simulation nobody checks is decoration. See notes.md." >&2
  exit 4
fi
