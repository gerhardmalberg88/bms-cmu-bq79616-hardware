#!/usr/bin/env python3
"""Regenerate the marked tables in docs/*.md from the KiCad schematic.

Tables that restate the design must never be hand-typed, or they drift from it.
Each generated region is delimited:

    <!-- BEGIN GENERATED: <block-id> (do not edit by hand) -->
    ...
    <!-- END GENERATED -->

Usage:
    python tools/gen_doc_tables.py            rewrite every block in place
    python tools/gen_doc_tables.py --check    exit 1 if any block is stale

--check is the form for a pre-commit hook or CI: it regenerates into memory and
compares, so a schematic edit that has not been reflected in the documents
fails rather than sitting unnoticed.

Copyright (C) 2021-2026 Gerhard Malberg
SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import argparse
import collections
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DESIGN = os.path.join(ROOT, "design")
DOCS = os.path.join(ROOT, "docs")
SCHEMATIC = "battery_management_system_cell_monitoring_unit.kicad_sch"

KICAD_CLI_CANDIDATES = [
    r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe",
    r"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe",
    "kicad-cli",
]

BEGIN = "<!-- BEGIN GENERATED: %s (do not edit by hand) -->"
END = "<!-- END GENERATED -->"
BLOCK_RE = re.compile(
    r"<!-- BEGIN GENERATED: (?P<id>[a-z0-9-]+) \(do not edit by hand\) -->"
    r"(?P<body>.*?)"
    r"<!-- END GENERATED -->",
    re.S,
)


# --------------------------------------------------------------- netlist load

def find_kicad_cli():
    for candidate in KICAD_CLI_CANDIDATES:
        if os.path.isabs(candidate):
            if os.path.exists(candidate):
                return candidate
        elif shutil.which(candidate):
            return candidate
    raise SystemExit("kicad-cli not found; tried:\n  " + "\n  ".join(KICAD_CLI_CANDIDATES))


def export_netlist():
    """Export a fresh netlist to a temporary file and return its text."""
    cli = find_kicad_cli()
    fd, path = tempfile.mkstemp(suffix=".net")
    os.close(fd)
    try:
        result = subprocess.run(
            [cli, "sch", "export", "netlist", "--format", "kicadsexpr",
             "-o", path, os.path.join(DESIGN, SCHEMATIC)],
            capture_output=True, text=True)
        if result.returncode != 0:
            raise SystemExit("kicad-cli failed:\n" + (result.stderr or result.stdout))
        with io.open(path, encoding="utf-8") as handle:
            return handle.read()
    finally:
        os.unlink(path)


def parse(netlist):
    """Return (pin -> net, ref -> fields) from a kicadsexpr netlist."""
    pin_net = {}
    for block in re.split(r"\n\t\t\(net\n", netlist)[1:]:
        name = re.search(r'\(name "([^"]*)"\)', block)
        if not name:
            continue
        for node in re.findall(r"\(node\n(.*?)\n\t{3}\)", block, re.S):
            ref = re.search(r'\(ref "([^"]+)"\)', node)
            pin = re.search(r'\(pin "([^"]+)"\)', node)
            if ref and pin:
                pin_net[(ref.group(1), pin.group(1))] = name.group(1)

    comps = {}
    for match in re.finditer(r'\(comp\n\s*\(ref "([^"]+)"\)(.*?)\n\t\t\)\n',
                             netlist, re.S):
        blob = match.group(2)
        props = dict(re.findall(
            r'\(property\s*\(name "([^"]*)"\)\s*\(value "([^"]*)"\)', blob))

        def top(key):
            found = re.search(r'\n\t\t\t\(%s "([^"]*)"\)' % key, blob)
            return found.group(1) if found else ""

        comps[match.group(1)] = {
            "value": top("value"),
            "footprint": top("footprint"),
            "mpn": props.get("MPN", ""),
            "dk": props.get("digikey_pn", ""),
        }
    return pin_net, comps


def short(net):
    """Strip the sheet path from a net name."""
    return net.split("/")[-1]


def pins_of(pin_net, ref):
    """Yield (pin number, short net name) for one reference, in pin order."""
    rows = [(pin, short(net)) for (r, pin), net in pin_net.items() if r == ref]
    return sorted(rows, key=lambda row: int(row[0]) if row[0].isdigit() else 0)


def auto(net):
    """True if KiCad invented this net name rather than the designer."""
    return net.startswith("Net-(") or net.startswith("unconnected-")


def trace(pin_net, ref, pin):
    """Resolve a pin to a meaningful net, stepping through one series part.

    Every cell tap pin sits on its own short net between the connector and its
    fuse, which KiCad auto-names. Reporting that name says nothing useful, so
    step through the series part to the node carrying the real signal.

    Takes exactly one step, and only through a component that has exactly two
    pins. Following an auto-named net further, or guessing the far pin of a
    multi-pin part, wanders onto unrelated nodes.
    """
    net = pin_net.get((ref, pin))
    if net is None or net.startswith("unconnected-"):
        return None, None
    if not auto(net):
        return short(net), None

    members = [(r, p) for (r, p), n in pin_net.items() if n == net and r != ref]
    if len(members) != 1:
        return None, None
    other_ref, other_pin = members[0]

    if {p for (r, p) in pin_net if r == other_ref} != {"1", "2"}:
        return None, other_ref

    far_net = pin_net.get((other_ref, "2" if other_pin == "1" else "1"))
    if far_net is None or auto(far_net):
        return None, other_ref
    return short(far_net), other_ref


def readable(net, ref, pin):
    """Collapse KiCad's auto-generated net names to something meaningful."""
    if net.startswith("unconnected-"):
        return "_not connected_"
    if net.startswith("Net-("):
        return "local"
    return "`%s`" % net


# ------------------------------------------------------------ block builders

def tap_connector_pinouts(pin_net, comps):
    refs = [r for r in ("J401", "J402", "J403") if comps.get(r, {}).get("on_board", False) and any(k[0] == r for k in pin_net)]
    if not refs:
        return "\n_No tap connectors found in the netlist._\n"
    npins = max(len(pins_of(pin_net, r)) for r in refs)

    header = ["Pin"]
    for r in refs:
        header += ["%s signal" % r, "fuse"]
    out = ["", "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]

    maps = {}
    for i in range(1, npins + 1):
        cells = ["%d" % i]
        for r in refs:
            net, via = trace(pin_net, r, str(i))
            cells += ["`%s`" % net if net else "—", via or "—"]
            maps.setdefault(r, {})[i] = net
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    out.append("Current PCB connector(s) only. Signal is the node reached through "
               "the listed fuse. J402/J403 and their alternative fuse banks are "
               "schematic-only options excluded from this PCB and purchasing list.")

    distinct = {r: sorted(v for v in m.values() if v) for r, m in maps.items()}
    if len({tuple(sorted(m.items(), key=lambda kv: kv[0])) for m in maps.values()}) > 1:
        out.append("")
        out.append("> **These three connectors are NOT pin-compatible with each "
                   "other.** They carry the same %d signals but on different "
                   "pins, because J401 is a 2x10 dual-row part and J402/J403 are "
                   "1x20 single-row. A harness built for one will not work on "
                   "another. Build the wire schedule from this table, per "
                   "connector."
                   % len(set(distinct[refs[0]])))
    out.append("")
    return "\n".join(out)


def daisy_chain_pinouts(pin_net, comps):
    out = ["", "| Connector | Pin | Signal |", "|---|---|---|"]
    for ref in ("J501", "J502"):
        rows = pins_of(pin_net, ref)
        if not rows:
            continue
        for pin, net in rows:
            out.append("| %s | %s | %s |" % (ref, pin, readable(net, ref, pin)))
    out.append("")
    return "\n".join(out)


def ntc_pinouts(pin_net, comps):
    rows = pins_of(pin_net, "J201")
    if not rows:
        return "\n_J201 not found in the netlist._\n"
    out = ["", "| Pin | Signal | Via |", "|---|---|---|"]
    for pin, net in rows:
        if auto(net):
            resolved, via = trace(pin_net, "J201", pin)
            out.append("| %s | %s | %s |"
                       % (pin, "`%s`" % resolved if resolved else "local",
                          via or "-"))
        else:
            out.append("| %s | `%s` | - |" % (pin, short(net)))
    out.append("")
    return "\n".join(out)


def dissipation_table(pin_net, comps):
    groups = collections.defaultdict(list)
    for ref, fields in comps.items():
        if not fields.get("on_board", False) or fields.get("dnp", True):
            continue
        groups[(fields["value"], fields["mpn"])].append(ref)
    interesting = [(v, m, refs) for (v, m), refs in groups.items()
                   if len(refs) >= 8 or v.endswith("2W")]
    interesting.sort(key=lambda row: -len(row[2]))
    out = ["", "| Value | MPN | Qty | Refs |", "|---|---|---|---|"]
    for value, mpn, refs in interesting[:8]:
        srefs = sorted(refs, key=lambda r: (re.match(r"[A-Z]+", r).group(),
                                            int(re.search(r"\d+", r).group())))
        shown = "%s..%s" % (srefs[0], srefs[-1]) if len(srefs) > 3 else ", ".join(srefs)
        out.append("| %s | %s | %d | %s |" % (value, mpn or "-", len(refs), shown))
    out.append("")
    out.append("_Fitted PCB population by value, reconciled with the schematic. DNP and schematic-only alternatives are excluded. Dissipation figures are "
               "hand-derived in the prose below._")
    out.append("")
    return "\n".join(out)


BUILDERS = {
    "tap-connector-pinouts": tap_connector_pinouts,
    "daisy-chain-pinouts": daisy_chain_pinouts,
    "ntc-pinouts": ntc_pinouts,
    "dissipation-table": dissipation_table,
}


# ------------------------------------------------------------------- driver

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if any generated block is stale")
    args = parser.parse_args()

    pin_net, comps = parse(export_netlist())
    # The netlist also contains unbuilt alternatives. PCB population flags are
    # authoritative for the current physical assembly, including DNP links.
    import pcbnew
    board = pcbnew.LoadBoard(os.path.join(DESIGN, "battery_management_system_cell_monitoring_unit.kicad_pcb"))
    present = {f.GetReference(): f for f in board.GetFootprints()}
    for ref, fields in comps.items():
        footprint = present.get(ref)
        fields["on_board"] = footprint is not None and not footprint.IsExcludedFromBOM()
        fields["dnp"] = footprint.IsDNP() if footprint is not None else True

    stale, written, unknown = [], [], []
    for name in sorted(os.listdir(DOCS)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(DOCS, name)
        with io.open(path, encoding="utf-8", newline="") as handle:
            raw = handle.read()
        crlf = "\r\n" in raw
        text = raw.replace("\r\n", "\n")

        def replace(match):
            block_id = match.group("id")
            builder = BUILDERS.get(block_id)
            if builder is None:
                unknown.append((name, block_id))
                return match.group(0)
            body = builder(pin_net, comps)
            if body != match.group("body"):
                stale.append((name, block_id))
            return BEGIN % block_id + body + END

        new = BLOCK_RE.sub(replace, text)
        if new != text and not args.check:
            with io.open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(new.replace("\n", "\r\n") if crlf else new)
            written.append(name)

    for name, block_id in unknown:
        print("  unknown block id %r in %s" % (block_id, name))

    if args.check:
        if stale:
            print("STALE generated blocks (run without --check to fix):")
            for name, block_id in stale:
                print("  %s : %s" % (name, block_id))
            return 1
        print("all generated blocks up to date")
        return 1 if unknown else 0

    if written:
        print("rewrote generated blocks in: %s" % ", ".join(written))
    else:
        print("all generated blocks already up to date")
    return 1 if unknown else 0


if __name__ == "__main__":
    sys.exit(main())
