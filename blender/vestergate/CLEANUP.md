# Vestergate terrain and scenery cleanup

The latest map is `vestergate_cleaned.blend`. Its nine scenic cliff sections are clipped to the actual map footprint and joined to the foundation as one closed, connected mesh. The six grass defence ledges remain separate, with closed bases embedded in the ground and their original top heights and positions retained.

The cleanup removes all three grey reference characters (18 body pieces), three trees rooted outside the map, unsupported props and grass components. Remaining trees and plants are grounded on the actual repaired terrain surface. Vines are attached to nearby cliff faces, and the small flower heads meet the ground. Sign lettering is preserved even though it uses the same grey material as the old figures.

## Repair an existing file

With the map open, paste all of `repair_vestergate_terrain.py` into a new Blender Text Editor document and press Alt+P. No external scripts or add-ons are required. It saves `Vestergate_Cleaned/vestergate_cleaned.blend` beside the current file and copies the linked portal library into a `Libraries` folder. The original file on disk is preserved.

**Run the repair before exporting.** Re-run `export_vestergate_roblox.py` on the cleaned map and use its newly generated FBX and textures together. The terrain geometry and atlas layouts have changed, so use the new texture assignment manifest as well.

The portable download contains the cleaned Blender file, its linked portal library, the repair and export scripts, two inspection renders and the validation reports. Keep `Libraries` beside the downloaded `.blend`. The repository file links to `../assets/Atheria_Portal_Library.blend` instead.

## Checks

The repaired foundation has one connected shell and no non-manifold edges. All six ledges are closed solids with embedded bases. Independent saved-file checks verify that the 69 remaining trees and 9,247 plant faces have terrain support, and that no grey reference characters remain. The existing 3,101 road checks, lamp orientation checks and all three portal placement/animation checks pass. The repair script was also exercised in Blender 5.0.1.

`CLEANUP_REPORT.json` records the changes; `CLEANUP_VALIDATION.json`, `VALIDATION.json` and `PORTAL_VALIDATION.json` record the checks. The screenshots show the cleaned layout and an eye-level view of the connected cliffs. The earlier full-map render set documents the previous revision.

The source builder is retained as the earlier blockout generator. If rebuilding from it, run the repair script afterward. Roblox import scale, navigation and collision still need in-game checks.
