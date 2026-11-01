# Export Vestergate with baked textures

Save the current map, paste the complete `export_vestergate_roblox.py` into a new Blender Text Editor document, and press Alt+P. The script writes `Vestergate_Roblox_Export` beside the saved file. The default texture resolution is 2048 × 2048 per section; change `TEXTURE_SIZE` near the top for a different size.

The exporter snapshots evaluated geometry, including the three linked portal collection instances and terrain-conforming rune meshes. It works on temporary copies and restores the active scene, selection, mode, frame and subframe afterward. Cameras and lights are not included; the three reference mannequins are excluded by default (`INCLUDE_SCALE_FIGURES = False`). It never saves over the source `.blend` file.

## Files

- `Vestergate.fbx`: the full static model, with a shared origin and at most 9,000 triangles per mesh piece.
- `VG##_Batch_##.fbx`: smaller imports of at most 100 mesh pieces, as an alternative to the full FBX.
- Five PNG maps for each section: `ColorMap`, `NormalMap`, `RoughnessMap`, `MetalnessMap`, and `EmissiveMask`.
- `AlphaMap` for transparent sections; its values are also embedded in the corresponding RGBA `ColorMap`.
- `TEXTURE_MANIFEST.json`: section/material assignments, mesh sources, triangle counts and export settings.
- `APPLY_TEXTURES.lua`: a Studio Command Bar helper with image-ID fields for each section.
- `ROBLOX_IMPORT.txt`: import steps.

Generated/Object coordinates and original UVs are frozen before the bake copies are joined, and the terrain's named road-clearance attribute is retained. This preserves the dirt noise, painted shoulders, grass colours and portal spiral masks. Smart UV atlases are baked into portable image files. Normal maps use OpenGL tangent space (+Y); FBX includes UVs, normals and tangents. Color maps are sRGB, and the other maps contain linear data.

To keep memory bounded, each bake image is saved and released before the next channel. Export materials reference the actual PNG files. The Blender shaders supported by this map are Principled BSDF, Emission, and Transparent/Emission mixes; unsupported custom shaders produce an explicit error rather than silently exporting an incorrect result.

## Roblox Studio

1. Keep all PNG files beside the FBX and import `Vestergate.fbx` through **Import 3D**. For smaller imports, use the batch files instead and preserve the same file origin. Import either the full model or the batches.
2. Upload the PNGs as images. Enter their **image asset IDs** in the matching rows of `APPLY_TEXTURES.lua`.
3. Select the imported model and run the helper in Studio's Command Bar. It assigns SurfaceAppearance maps, uses transparency for the portal energy, and applies the emissive masks when the Studio API supports them. The colour map already contains alpha, so the separate AlphaMap is a backup rather than an additional SurfaceAppearance slot.
4. The helper anchors the map, enables two-sided rendering for open surfaces, and disables collisions for portal visuals and ground greenery. Test collision and traversal on roads, terrain, ledges and the bridge, and adjust tree/prop collisions as needed.
5. Check scale against a Roblox character. The source map covers approximately 126 × 140 metres. Adjust `EXPORT_SCALE` or the import scale consistently for the whole map.

Blender sunlight, sky lighting and compositor bloom are not textures. Recreate them in Roblox. The portal pattern and geometry export in the chosen static pose (frame 1); Blender's looping object animation does not become a Roblox effect automatically. Emissive masks preserve the intended glow regions and strengths, with final brightness/bloom tuned in Studio.

The FBX materials intentionally have zero emission. FBX cannot preserve the shader math that multiplies each atlas's emissive mask, so linking the colour atlas to FBX emission can make the entire map appear to glow. The Studio helper first clears imported emission, then applies the actual uploaded mask. Judge final lighting in the Workspace; the import preview has its own lighting.

## Validation

The complete map was baked with 128-pixel test textures and exported in Blender 4.3.2, including all linked portal meshes. The FBX was reimported to verify mesh coverage, triangle limits, UVs and texture paths. Portal ColourMap alpha was checked against the separate AlphaMap. A representative terrain/road/linked-portal export also ran in Blender 5.0.1. The delivered script defaults to 2048-pixel textures. An actual Roblox Studio import and gameplay/collision check are still required.

Headless options: `VESTERGATE_EXPORT_OUT` sets the output folder and `VESTERGATE_EXPORT_SIZE` sets the texture size.
