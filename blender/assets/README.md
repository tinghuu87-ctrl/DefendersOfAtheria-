# Reusable enemy portal library

These three designs are the default enemy entrances for future Atheria battle maps. Reuse them with map-specific placements and sizes.

`Atheria_Portal_Library.blend` contains four marked collection assets: **Thornrift**, **Voidmaw**, **Stormscar**, and **Ground runes**. The portal cores share their geometry, materials, lights and 120-frame idle animations between placements. The lightweight rune meshes also share mesh data, with a separate terrain-conforming modifier at each placement.

Vestergate now uses three linked portal instances, including independent, grounded `EnemySpawn` and `FirstWaypoint` markers. The six grass vantages, dirt roads and road-facing lamps remain part of the map. Other campaign battle maps have not yet been modelled; the same library is ready for their enemy entrances.

## Use in another map

1. Keep `Atheria_Portal_Library.blend` beside the map's `.blend` file, or set `LIBRARY_PATH` in `place_enemy_portals.py` to its location.
2. Paste the full placement script into Blender 4.3+'s Text Editor and press Alt+P.
3. Set `DESIGN`, `SCALE`, and `FACING_DEGREES` near the top as needed.

`MODE = 'AUTO'` uses tagged lane entrances if present, otherwise selected empty markers, otherwise the 3D cursor. Explicit modes are `LANES`, `MARKERS`, and `CURSOR`. The portal's forward direction is local **+Y**. Marker mode takes the selected empties' facing directions; cursor mode uses the requested Z rotation. Set `GROUND_OBJECT_NAME` for other terrain meshes, or mark the terrain mesh with the `Portal ground` custom property.

In cursor mode, change `PLACEMENT_ID` to add another portal. Reusing the same ID updates that placement. Re-running lane mode updates the existing entrance placements. Operations affect the active scene only.

The script can also convert the original portal-model file into shared local assets when the original designs are already loaded; no external library is needed for that conversion. For new files, `LINK_LIBRARY = True` loads linked masters from the library so changes to that library can propagate to each map when its linked data is reloaded. `LINK_LIBRARY = False` appends editable local masters instead.

## Asset Browser and master edits

Add this folder under **Edit → Preferences → File Paths → Asset Libraries**. In the Asset Browser, choose the **Atheria / Enemy Portals** catalog. The portal cores and ground runes are separate assets; the placement script combines them and fits the runes to terrain automatically.

Open the library file itself and select a `Portal master / …` scene to edit a master. Save the library and reload the linked library in dependent map files, or reopen those files. Editing a shared master updates all placements that reference it; each placement retains its own position, rotation and scale.

## Files and validation

The portable download keeps `vestergate_with_portals.blend` and the library in the same folder. Keep them together. In the repository the map links to `../assets/Atheria_Portal_Library.blend`.

`build_portal_library.py` rebuilds the library from the original portal designs. `validate_portal_reuse.py` checks reloads, repeated placement, shared data, independent transforms, multiple scenes, marker/cursor modes, ground projection and animation. `REUSE_VALIDATION.json` contains the latest results. Existing design renders show the same portal shapes and shaders.

This is a Blender authoring library. Roblox enemy spawning and VFX remain game-side work. Collection instances must be realised or handled by an exporter when preparing geometry for Roblox; Blender links and shader effects do not become working Roblox portal scripts automatically.
