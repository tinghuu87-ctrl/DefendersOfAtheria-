# Vestergate — three-lane woodland blockout

Open `vestergate_blockout.blend` in Blender 4.3 or later. The active scene is a separate, editable exterior battlefield; the lobby and tavern have not been modified.

## Layout

- Kingdom gate and crenellated wall on the south side, with closed wooden gate leaves, two bastions, and blue kingdom standards.
- Player spawn immediately outside the gate; the defended cyan crystal stands farther forward in the same gate-side courtyard.
- Three separate approaches: a shaded winding woodland trail on the left, an open cobbled gate road in the centre, and an elevated ridge trail with a timber bridge on the right.
- Eight grass-capped defence terraces, each with a broad access ramp and a marked 3.4-metre-diameter placeholder footprint. Terrace labels D1–D8 are shown in the annotated plan, not floating in the game environment.
- Layered rock escarpments, low woodland ground, a raised eastern ridge, a recessed stream crossing, broadleaf tree masses, selective golden trees, shrubs, grass, flowers, and trailing cliff vines.
- Three neutral human figures approximately 1.8 metres tall establish scale.

The coordinate system is metres, Z up. The gate is at negative Y; enemies approach from positive Y. The overall landscape is approximately 126 × 140 metres. Treat these as authoring dimensions; Roblox import scale and combat distances require playtesting.

| Plan label | Position |
| --- | --- |
| D1 | Overlooks the upper woodland bend |
| D2 | Lower woodland shelf |
| D3 | Central overlook between woodland and gate-road approaches |
| D4 | Upper gate-road shoulder |
| D5 | Raised shelf beside the ridge bridge |
| D6 | Lower shoulder between the ridge and gate road |
| D7 | West-side terrace near the crystal courtyard |
| D8 | East-side terrace near the crystal courtyard |

## Review views

The downloadable package keeps review images and the PDF beside this README; in the repository they are in `../../renders/vestergate/`. Views include the battlefield overview, annotated top-down route plan, gate-side arrival view, crystal/gate view, and ridge crossing view. The presentation PDF combines these views with a legend and blockout notes.

## Editing and rebuilding

Collections separate terrain, cliff terraces, trails, bridge, gates, defence vantages, crystal/spawn, trees, ground greenery, landmarks, figures, lights, and cameras.

Hide the Trees and Ground greenery collections to inspect the route layout. The Defence vantages collection contains the eight shelves, their access ramps, and the proposed placement footprints.

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

`VESTERGATE_LAYOUT.json` records lane centre lines, widths and measured lengths, crystal/spawn positions, terrace footprints, ramp endpoints/gradients, and trail-clearance checks. Route measurements describe the authored spline geometry; they are not a combat-balance claim.

This is a visual and spatial blockout. Materials are simple colour assignments, with no production texture bake. Enemy navigation, build permissions, tower ranges, collision proxies, multiplayer spawning, and Roblox integration remain future work. Elevation does not imply a damage/range bonus. The marked discs are proposed placement footprints rather than implemented build interactions. Live Roblox validation has not been performed.

Design basis: `REFERENCE_NOTES.md` in the downloadable package, or `../../docs/VESTERGATE_REFERENCE_NOTES.md` in the repository.
