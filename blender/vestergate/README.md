# Vestergate — three-lane woodland blockout

**Latest cleaned map:** `vestergate_cleaned.blend`. The cliff terrain is joined to the foundation, floating/out-of-bounds scenery is removed, and the grey reference characters are deleted. See [CLEANUP.md](CLEANUP.md) and the self-contained `repair_vestergate_terrain.py` script. Re-export the cleaned map with fresh textures before importing it to Roblox.

Enemy portal models are now available in `vestergate_with_portals.blend`, which includes the revised map and a separate three-design comparison scene. See `PORTALS.md` and the self-contained `add_enemy_portals.py` script for placement, animation and copy/paste instructions.

Open `vestergate_blockout.blend` in Blender 4.3 or later. The active scene is a separate, editable exterior battlefield; the lobby and tavern have not been modified.

## Layout

- Kingdom gate and crenellated wall on the south side, with closed wooden gate leaves, two bastions, and blue kingdom standards.
- Player spawn immediately outside the gate; the defended cyan crystal stands farther forward in the same gate-side courtyard.
- Three separate dirt approaches: a shaded winding woodland trail on the left, an open gate road in the centre, and an elevated ridge trail with a timber bridge on the right. Cobbles have been removed; the crystal apron and gate-side approach also use dirt.
- Six plain grass-capped defence terraces with low ledges for jump access. Access ramps and grey centre discs have been removed. Labels D1–D6 appear only in the annotated review plan.
- Five positions have moved to the approximate centres of the user's red markings. The unmarked upper position D4 retains its horizontal location. The two crystal-side positions D7/D8 have been removed.
- Lantern brackets and hanging lamps point toward the closest road or courtyard axis.
- Layered rock escarpments, low woodland ground, a raised eastern ridge, a recessed stream crossing, broadleaf tree masses, selective golden trees, shrubs, grass, flowers, and trailing cliff vines.
- Three neutral human figures approximately 1.8 metres tall establish scale.

The coordinate system is metres, Z up. The gate is at negative Y; enemies approach from positive Y. The overall landscape is approximately 126 × 140 metres. Treat these as authoring dimensions; Roblox import scale and combat distances require playtesting.

| Plan label | Revised position | World X/Y, metres |
| --- | --- | --- |
| D1 | Woodland inside bend | -28 / 17 |
| D2 | Lower woodland shelf, nearer the road | -31.5 / 0 |
| D3 | Central overlook, nearer the gate road | -5.5 / 13 |
| D4 | Upper road shoulder, horizontal position retained | -12 / 39 |
| D5 | Ridge inside bend below the bridge | 25 / 12 |
| D6 | Lower shoulder between the ridge and gate road | 13 / -11 |

The dirt ribbons sample the actual terrain mesh across their width. Matching dirt shoulders beneath them and larger vegetation setbacks prevent green terrain triangles and overhanging plants appearing on the roads. Dirt colour uses a simple procedural noise shader with no external textures.

## Review views

The downloadable package keeps review images and the PDF beside this README; in the repository they are in `../../renders/vestergate/`. Views include the battlefield overview, annotated top-down route plan, gate-side arrival view, crystal/gate view, and ridge crossing view. The presentation PDF combines these views with a legend and blockout notes.

## Editing and rebuilding

Collections separate terrain, cliff terraces, trails, bridge, gates, defence vantages, crystal/spawn, trees, ground greenery, landmarks, figures, lights, and cameras.

Hide the Trees and Ground greenery collections to inspect the route layout. The Defence vantages collection contains only the six plain grass shelves.

`build_vestergate.py` is a self-contained Blender Python builder with no downloaded assets. It creates a separate scene and preserves existing scenes. Re-running it intentionally creates another independent scene rather than replacing one you may have edited.

For copy/paste use, open Blender's Scripting workspace, paste the full contents of `vestergate_blender_copy_paste.py` into a new Text Editor document, and press Alt+P. It builds and saves the same blockout with automatic rendering off. Set `RENDER = True` near the top to render all five camera views after building. The saved `.blend` and layout JSON files go into `Vestergate_Blockout` beside the current Blender file, or into `Vestergate_Blockout` in your home folder if the current file is unsaved. The script prints the actual output path in Blender's console.

```sh
ATHERIA_VESTERGATE_OUT=/path/to/output blender -b --python build_vestergate.py
```

Set `ATHERIA_VESTERGATE_RENDER=0` to build/save only. `ATHERIA_VESTERGATE_VIEWS=overview,plan,arrival,gate,ridge` chooses renders; `ATHERIA_VESTERGATE_SAMPLES=32` sets Cycles samples.

To rerender an existing file without rebuilding geometry:

```sh
ATHERIA_VESTERGATE_OUT=/path/to/renders blender -b vestergate_blockout.blend --python render_vestergate.py
```

## Validation and limits

`VESTERGATE_LAYOUT.json` records lane centre lines, widths and measured lengths, crystal/spawn positions, revised terrace positions and ledge heights, road-facing lamp directions, and trail-clearance checks. Route measurements describe the authored spline geometry; they are not a combat-balance claim. `VALIDATION.json` records actual mesh support and green-coverage checks across the road width, removal checks, lamp alignment, and authoring heights for jump access.

This is a visual and spatial blockout. Materials use simple colours and procedural dirt, with no production texture bake. Enemy navigation, build permissions, tower ranges, collision proxies, multiplayer spawning, and Roblox integration remain future work. Elevation does not imply a damage/range bonus. Jump heights must be checked against the imported scale and actual Roblox character settings; no live Roblox jump or collision validation has been performed.

Design basis: `REFERENCE_NOTES.md` in the downloadable package, or `../../docs/VESTERGATE_REFERENCE_NOTES.md` in the repository.
