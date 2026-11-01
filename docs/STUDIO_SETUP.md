# Roblox Studio setup

Save a copy of your place before applying installers. Run `.lua` files by copying their complete contents into **Studio's Command Bar with Play stopped**, then save the place. They are authoring installers, not ordinary runtime scripts to paste into Workspace.

## Base lobby

1. Open `blender/atheria_lobby.blend` and run `blender/export_roblox.py` in Blender's Scripting workspace.
2. Import its FBX and textures through Studio's 3D Importer. Check scale and placement against your avatar. If a color map is missing, upload its PNG and assign it through `SurfaceAppearance.ColorMap`; the export's JSON manifest maps mesh names to textures.
3. Select the imported town Model and run `roblox/collision/fix_atheria_collision.lua`. Reimporting creates new MeshParts, so reapply collision settings after later imports. Complex meshes can still require dedicated collision geometry if precise convex decomposition fills an opening.
4. Optionally run `roblox/environment/atheria_sharp_wall_material.lua` to replace low-density wall atlases with repeating stone-gray masonry. Select the town Model or the individual wall MeshParts.

## Environment and decoration

- `roblox/environment/atheria_daytime_sky.lua`: blue daytime sky, atmosphere and clouds.
- `roblox/environment/atheria_lobby_music.lua`: loop audio `76612846505659` at volume `0.25`. Grant this experience audio access in Creator Dashboard if required. Install only in the lobby place.
- `roblox/decor/quest_hall_apples.lua`: add the second Apples plaque to the rear of Quest Hall after the service circles are installed. The original Blender wall engraving remains.

## Service circles

1. Select the complete imported town Model with its original exported section names.
2. Run `roblox/interactions/install_atheria_circles.lua`. Its placement calibration expects the Forge, Quest Hall and Tavern section names and the original town layout.
3. Run `roblox/interactions/raise_atheria_circles.lua` to keep the original locations and sizes while lifting the Quest Hall/Tavern effects above entrance steps.

`clear_atheria_circles.lua` is an alternative earlier clearance adjustment that moves/shrinks pads. The later chosen direction was to retain original placement and raise effects. The raise script also restores saved original positions after the clearance adjustment.

## Battle Gate atlas

1. Run `roblox/ui/install_battle_gate_ui.lua`. The current installer includes an independent walk-in detector and keeps movement available. It creates the runtime LocalScripts in StarterPlayerScripts.
2. Upload `art/atlas/atheria_simple_atlas.png` to Roblox as an image asset.
3. Paste its image asset ID into `ATLAS_IMAGE_ID` in `roblox/ui/simplify_atheria_atlas.lua`, then run that complete script. This installs the simpler overhead atlas, Atheria destination names, finer trails and circular marker styling.
4. Save, start a **fresh Play session**, and enter the Battle Gate circle. The atlas should open when you enter and close when you leave. Its X button and M also close it.

For installations made from earlier chat scripts, `repair_gate_ui_and_collision.lua` repairs the UI initialization and installs the independent walk-in detector while reapplying collision fidelity to the selected import. `enable_walk_in_battle_gate.lua` is the earlier migration and normally isn't needed with the current installer.

The supplied LocalScripts were syntax-checked outside Studio. Layout, asset availability, input, streaming and imported collisions need verification in your own Studio place.

## Concept destinations

Vespergate; Brassveil Ward; Crownshard Court; Orison Bastion; Auralith Sanctum; Thornwake Crossing; Velmorrow Hollow; Gravemantle Roost.

All are previews. Normal, Intermediate and Expert are selectable; no battle destinations or teleport IDs are configured.
