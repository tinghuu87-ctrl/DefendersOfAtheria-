# The Lantern Tavern — expanded blockout

Open `atheria_tavern_expanded.blend` in Blender 4.3 or later. The opening view faces the common room from the entrance. The original 12 × 11 metre blockout remains available separately.

The new concept room is **18 × 16.5 metres**, retaining the 5.1 metre ceiling height and roughly human-scale furniture. Its floor area is 2.25 times the original room. This enlarged room is a separate interior concept; an entrance transition and final Roblox scale remain future work.

## Changes

- Expanded timber shell and ceiling bays.
- Communal table and stools kept at comfortable sizes, with more open circulation.
- Longer bar and additional backbar shelf space.
- Smaller seating bays spread into the larger room.
- Hearth repositioned against the new rear wall.
- A 4.8 metre-wide framed leaderboard blockout on the right-hand entrance-side wall, with an entirely blank face and a large clear viewing area.
- Direct clear routes from the entrance to the hearth and from the main aisle to the leaderboard.
- Additional warm lighting for the leaderboard.

The leaderboard face is intentionally blank. No lettering, row dividers, player data, ranking metric, or functional UI is connected.

## Builder

Run `build_tavern_expanded.py` in Blender's Text Editor. It creates a new scene and preserves other scenes in the open file. Set `RENDER=False` to skip rendering. Default output is `Tavern_Expanded/` beside the current .blend, or `Atheria_Tavern_Expanded/` in your home folder when starting without a saved file. `ATHERIA_TAVERN_OUT` overrides the output directory for batch runs.

The builder performs 15 body-height ray probes along the entrance/hearth route and leaderboard branch. These check the planned circulation, not all possible movement or every character size. The room still needs an in-Studio character/camera test when imported.

Five rendered views show the entrance, hearth, cutaway, floor plan and leaderboard. Cutaway/plan renders temporarily hide the ceiling and part of the shell; the saved scene keeps the complete shell.
