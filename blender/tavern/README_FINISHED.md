# The Lantern Tavern — finished interior render

Open **atheria_tavern_finished.blend** in Blender 4.3 or later. The entrance camera is active. All materials are procedural, so no external texture files are required.

The expanded **18 × 16.5 metre** common room retains its 5.1 metre ceiling, communal table, bar, smaller seating bays, rear hearth, and clear circulation. The framed leaderboard and the open space in front of it remain completely blank: no text, rows or rankings.

## Finishing pass

- Directional timber and floor grain, warm plaster, coursed hearth masonry, aged iron and bronze.
- Curved candle and hearth flames, charred logs, and linked chandelier chains.
- Wooden barrel staves, tankard handles and ale, earthenware plates, and bread.
- A subdued woven aisle rug and two narrow diamond-leaded window panels.
- Layered candle/hearth lighting, softer warm room fill, and cool entrance/window light.

## Views

The repository’s `renders/tavern-finished/` folder contains entrance, hearth, cutaway, and blank-leaderboard PNG views plus a multipage PDF. In the downloadable ZIP these views sit beside the Blender file. The cutaway temporarily hides the ceiling and the front/left shell. The saved Blender scene retains the full shell.

Delivered PNG views are 1200 × 900, rendered in Cycles with 16–64 samples and cleaned with Open Image Denoise 1.4.3 using albedo and normal guides. This environment's Blender build has no built-in denoiser. The editable scene defaults to 1400 × 1050 at 96 samples. On a Blender build with denoising support, enable Render Properties → Sampling → Render → Denoise for clean rerenders.

## Rebuild and rerender

`build_tavern_finished.py` is a complete standalone generator. Run it in Blender's Text Editor to create a separate scene; existing scenes are preserved. It includes the finishing source. By default it saves the scene and renders four views into `Tavern_Finished/` beside the current file (or `Atheria_Tavern_Finished/` in the home directory when starting unsaved).

For command-line use, `ATHERIA_TAVERN_OUT` overrides the output directory and `ATHERIA_TAVERN_RENDER=0` skips rendering. `finish_tavern.py` applies just the material/detail pass to the active expanded tavern. `render_tavern_finished.py` rerenders the four cameras in an existing finished scene.

## Validation and scope

The finished scene passed 15 body-height ray probes along the entrance/hearth route and the leaderboard branch. The board has no text objects or row dividers, and the saved scene retains its roof and shell. A fresh generator run also passed its circulation checks. See `VALIDATION_FINISHED.json`.

This deliverable finishes the Blender interior and presentation renders. Roblox import, collision setup, and a doorway transition are separate integration work.
