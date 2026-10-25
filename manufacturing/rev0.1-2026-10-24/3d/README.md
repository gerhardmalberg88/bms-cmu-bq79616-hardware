# Mechanical exports

All files use mm, common lower-left board origin, and native KiCad component
positions. CMU-rev0.1-16S.step and .stl contain the 157 fitted components.
CMU-rev0.1-board.step contains only the board. DNP models are omitted.
The binary STL is below 10 MB and retains the native mesh without decimation.
Keep it as a normal Git file for GitHub's built-in STL viewer.

[Ray-traced PCB image](CMU-rev0.1-16S-raytraced.png): 2400 x 1600 pixels,
native KiCad high-quality angled top view with stackup colours and a neutral
grey background. It shows the 157 fitted components; DNP models are excluded.
Only an empty-background border is cropped to correct KiCad's output-size
quantisation; no resampling or geometry changes. See
[reproduction commands](../documentation/CMU-009-manufacturing.md#reproducing-the-pcb-image)
and [render verification](../verification/pcb-render.json).

Native STEP board body is 1.568 mm thick; surface copper/mask solids are not
included. The CAD stackup total is 1.708 mm including estimated masks; supplier
finished thickness/tolerance is still to be confirmed. Use those allowances
for enclosure fit. These models do not include mating cables or screw travel.
