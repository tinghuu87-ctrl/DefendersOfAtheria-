# Enemy portals — violet vortex designs

**Reusable workflow:** the map now uses linked collection assets from `../assets/Atheria_Portal_Library.blend`. Use `../assets/place_enemy_portals.py` to place these designs in more maps, with independent position, rotation and scale. See `../assets/README.md`. The original generator below remains useful for rebuilding the initial designs.

Open `vestergate_with_portals.blend` in Blender 4.3+. It includes the revised dirt-road map with three enemy entrance models, plus a separate `Atheria / Enemy portal design studies` scene showing all three designs together.

| Lane | Design | Frame |
| --- | --- | --- |
| Woodland | Thornrift | Seven broken obsidian segments with asymmetric outward talons |
| Gate road | Voidmaw | Ten reinforced segments with magenta rune cuts |
| Ridge | Stormscar | Five fractured segments with longer angular talons |

Each model has a recessed dark centre, a procedural spiral face, layered soft violet wisps, brighter irregular spiral ribbons, broken ground rune arcs, gold sparks, and a local violet light. The energy layers rotate on a seamless 120-frame Blender loop; frames 1–120 show one cycle.

The 6.8-metre aperture models face down the actual road's entrance tangent. `EnemySpawn` and `FirstWaypoint` empties sit on the lane-facing side, 0.12 metres above the terrain. No frame piece crosses the checked central body opening. Portal objects carry `CanCollide = False` metadata to describe their intended use as visual effects; this metadata does not configure Roblox automatically.

## Copy and paste

With the Vestergate map open, paste the complete `add_enemy_portals.py` into Blender's Text Editor and press Alt+P. It finds the three tagged lane meshes and places the portals automatically. It also works from an empty Blender file, creating only the design-study scene. Re-running it replaces its own portal objects rather than duplicating them. Existing terrain, roads, foliage, defence ledges and lamp positions are preserved.

The generator supports legacy animation actions and newer action slots/channel bags. It also supports Blender 5 compositor node groups and glare sockets. Verified in Blender 4.3.2 and 5.0.1, including rebuilding after the original `Action.fcurves` exception and checking the repeated 120-frame animation. If an older pasted script raises that exception, replace its complete contents with the updated generator and run it again with the map open.

The script requires no external textures or add-ons. It saves a separate file in `Vestergate_Portals` beside the current Blender file, or in your home folder when the current file is unsaved. `ATHERIA_PORTALS_OUT` overrides this location. Automatic rendering is off; set `RENDER = True` or use `ATHERIA_PORTALS_RENDER=1` to enable it.

`render_enemy_portals.py` rerenders a saved scene without rebuilding. Options are `ATHERIA_PORTALS_SAMPLES`, `ATHERIA_PORTALS_RESOLUTION_PERCENT`, and `ATHERIA_PORTALS_VIEWS=designs,portal,overview,plan`.

`PORTAL_LAYOUT.json` records the model positions and lane-facing directions. `PORTAL_VALIDATION.json` records placement, marker ground heights, frame-opening probes, and the 120-frame idle loop checks. The comparison sheet, map close-up, overview, and top-down plan are in `renders/vestergate-portals/` in the repository, or beside this README in the download package.

These are Blender visual assets. Enemy spawning, Roblox animation/VFX, and collision settings still require game-side implementation. Shader glow, transparency, procedural patterns and Blender object animation do not transfer directly to Roblox as a working portal effect.
