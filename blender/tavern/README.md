# The Lantern Tavern — interior blockout

Open `atheria_tavern_blockout.blend` in Blender 4.3 or later. The active camera looks into the common room from the entrance. Other cameras show the hearth, dollhouse cutaway and floor plan.

`build_tavern.py` is a complete procedural builder. Run it in Blender's Text Editor or with `blender --background --python build_tavern.py`. It creates a separate scene, preserving other scenes in the open file. Its output goes to `Tavern_Blockout/` beside the open .blend, or `Atheria_Tavern_Blockout/` in your home directory when starting without a saved file. Set `RENDER=False` near the top to build without rendering. `ATHERIA_TAVERN_OUT` can override the output directory for batch rendering.

## Design

- Concept room: 12 × 11 metres, 5.1 metre ceiling, 3 metre entrance opening. Final Roblox scale/camera comfort still needs testing.
- Heavy posts, diagonal braces, crossbeams and an enclosed plank ceiling.
- Long communal table, six adjacent stools, two smaller seating areas.
- A rear-right stone hearth with tapered chimney and fire indication.
- Three candle chandeliers, wall lights, table candles and cool entry fill.
- Large horizontal cask in the foreground, barrel storage, mugs and bottles.
- A compact left-side bar/backbar is an added layout proposal; the reference image did not establish its exact position.
- Clear entrance apron and right-hand aisle leading toward the hearth.

This is a colored architectural blockout with illustrative lighting. Flames, chains, stored bundles and table props are simplified geometry. The room has no NPC placeholders, upstairs level, kitchen or gameplay UI. The interior is not connected to the Roblox lobby yet; doorway traversal and collision/export setup are later work.

The build checks 12 body-height rays across the entrance and main route, including lateral clearance offsets. It does not certify every possible character interaction or replace an in-Studio movement test.

Cutaway/plan renders temporarily hide parts of the shell for inspection. The saved scene retains the full room and ceiling. Presentation views are in `../../renders/tavern/` from this folder (see the root README links).

## Expanded revision

The latest larger interior is `atheria_tavern_expanded.blend`; see `README_EXPANDED.md` and `build_tavern_expanded.py`. It includes leaderboard space.

## Finished render

The material and lighting pass is available in `atheria_tavern_finished.blend`. See `README_FINISHED.md` for the render views and rebuild instructions. The expanded layout and blank leaderboard are preserved.
