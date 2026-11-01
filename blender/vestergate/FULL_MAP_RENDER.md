# Vestergate map render pass

`vestergate_render_ready.blend` contains the revised map with seven render cameras, procedural daylight lighting and restrained portal/crystal bloom. It links to the reusable portal library in `../assets/Atheria_Portal_Library.blend`. The portable download instead keeps that library in `Libraries` beside the map file.

## Render views

The 1920 × 1440 render set covers the complete battlefield, an overhead layout, arrival outside the gate, the crystal courtyard, the woodland lane, the central gate road and the ridge bridge. The overhead annotation is a separate image; labels are not baked into the map geometry. `../../renders/vestergate-finished/vestergate_full_map_views.pdf` collects the views, and `vestergate_render_sheet.png` shows them together.

The preset caps the hero view at 96 samples, the overhead plan at 32, and the closer views at 48, with adaptive sampling and denoising. The packaged renders were produced with Blender 4.3.2 and denoised using Intel Open Image Denoise 1.4.3. `RENDER_MANIFEST.json` records the actual preset and output views. Blender 5.0.1 was also checked with the render script, including a small rendered view.

## Reproduce

Open the map, paste the complete `render_complete_map.py` into Blender's Text Editor and press Alt+P. The script renders automatically, writes a separate output folder, saves a new native file, and copies linked asset libraries with relative file paths. Set `RENDER = False` to prepare without rendering. Running it from `vestergate_render_ready.blend` reuses that file's folder and updates the named render cameras.

```sh
ATHERIA_MAP_OUT=/path/to/output blender -b vestergate_with_portals.blend --python render_complete_map.py
```

Options: `ATHERIA_MAP_RENDER`, `ATHERIA_MAP_SAMPLES`, `ATHERIA_MAP_PERCENT`, `ATHERIA_MAP_DENOISE`, and `ATHERIA_MAP_VIEWS=overview,plan,arrival,gate,woodland,centre,ridge`.

The script supports legacy compositor trees and Blender 5 compositor node groups, glare sockets, and the renamed sky controls. It does not read removed `Action.fcurves` properties. Portal animations remain shared assets. Builds without native denoising fall back to rendering without it.

`present_complete_map.py` assembles the review PDF, annotated plan and contact sheet from completed render PNGs and `VESTERGATE_LAYOUT.json`, using ordinary Python with Pillow.

## Preserved layout

This pass changes the render setup: the three dirt roads, foliage setbacks, six grass ledges, road-facing lamps, closed gate, objective and spawn remain in their authored positions. The original road and portal geometry checks pass on the render-ready file. The underlying map remains a Blender layout study; Roblox gameplay, collisions, navigation and VFX require game-side work.
