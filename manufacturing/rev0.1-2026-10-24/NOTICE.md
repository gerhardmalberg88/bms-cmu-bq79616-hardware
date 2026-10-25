# Copyright, licensing and third-party notices

Copyright (C) 2021-2026 Gerhard Malberg.

SPDX-License-Identifier: CERN-OHL-P-2.0

The project's original hardware design, documentation, tools, simulation
scaffolding and generated manufacturing outputs are made available under
**CERN-OHL-P-2.0**. The unmodified license text is supplied in `LICENSE` and
`LICENSES/CERN-OHL-P-2.0.txt`. This notice supplements the README; it does not
change the project's license choice or third-party rights.

## Imported and generated CAD

- Original custom symbols, footprints and models are imported from
  [Gerhard Malberg's kicad-libraries](https://github.com/gerhardmalberg88/kicad-libraries)
  under CERN-OHL-P-2.0. The project library manifest records their content
  identifiers. The 2026-10-24 publication review records the matching upstream
  provenance rows and SHA-256 hashes in `docs/generated/library-provenance.csv`.
  All 33 imported footprint/model files and all five symbol blocks match the
  corresponding shared-library content (21 footprints, 12 original STEP models,
  five symbols). The register records author, license, modification notes and
  `cleared_original` redistribution status. This is a consistency check against
  recorded provenance, not an independent determination of authorship. Neither
  local repository has an initial commit; content hashes identify these copies.
  A content hash is not evidence of a published upstream commit.
- Standard symbols, footprints and referenced 3D models come from the
  **KiCad library contributors**. Their terms are **CC-BY-SA-4.0 with the KiCad
  library exception**, retained in `LICENSES/CC-BY-SA-4.0.txt` and
  `LICENSES/KICAD-LIBRARY-EXCEPTION.txt`. Standard library files are installed
  with KiCad; embedded design data, generated assembly STEP/STL and PNGs may contain
  their geometry. The exception permits choosing a different license for
  designs and files generated from those designs; it does not relicense a
  separately redistributed KiCad library collection. See the
  [KiCad library license](https://www.kicad.org/libraries/license/).
- STEP/STL and the ray-traced PNG are generated assembly visualizations. No third-party library
  collection, vendor SPICE model, datasheet or software dependency is added
  to the manufacturing archives. Installed export dependencies retain their
  own licenses and are not distributed with this project.

The existing `LICENSES/THIRD-PARTY-NOASSERTION.txt` explains the handling of
unverified assets; it is not a license grant. The current imported-asset
register records `cleared_original`. Future unverified/restricted content must
remain excluded until its provenance and redistribution permission are resolved.

## Modification and release record

2026-10-24: prepared the revision 0.1, 16S prototype manufacturing package;
aligned population and publication documentation; added STL/package navigation
and included these notices and license texts in standalone archives. These
documentation/export-packaging changes do not alter the saved design, circuit,
layout, revision or design issue date. Source hashes identify the design. On the same date, redundant documentation
was consolidated into the analyses and release record, EM/thermal placeholder
pages and a native KiCad ray-traced PNG were added, and the README presentation
was updated. Manufacturing artwork, quantities, placement, schematic PDF and
STEP/STL geometry were preserved.

Retain applicable notices when sharing source or manufacturing packages. The
disclaimer in `LICENSE` applies. Manufacturer and product names identify parts
and do not imply endorsement. Publication of this prototype does not establish
thermal, SI, safety, aerospace or system qualification.
