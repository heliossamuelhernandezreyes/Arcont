# Arcont selected CC0 runtime assets
This folder contains only assets promoted from `assets/cc0_staging` for active Godot runtime use.
Source warehouse is ignored by Godot. Promotion requires source/license audit and metric/runtime tests.
- Weapons: Quaternius Ultimate Gun Pack — CC0.
- Street clutter: loafbrr LampPost/TrashCan/Bench — CC0.
- Factory cone/box: Kenney Factory Kit — CC0; `Textures/colormap.png` retained as a required glTF dependency.
Status: PROVISIONAL / not final Arcont art.

Validation target for this pass: all five weapon visuals, selected street clutter and factory props must import cleanly, satisfy metric/runtime contracts, boot, and export through Android CI before promotion beyond this branch.
