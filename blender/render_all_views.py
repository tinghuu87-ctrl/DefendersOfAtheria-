"""Open atheria_linked_courtyards_v06.blend, then run this in Blender.
Renders all six town cameras beside the .blend file, in Town_Renders.
"""
import bpy
from pathlib import Path

WIDTH = 1600
SAMPLES = 128
VIEWS = {
    'overview': 'V06 Town overview',
    'tavern': 'V06 Tavern courtyard',
    'forge': 'V06 Forge courtyard',
    'sanctuary': 'V06 Sanctuary and quest hall',
    'market': 'V06 Festival court',
    'street': 'V06 Arrival street',
}
if not bpy.data.filepath:
    raise RuntimeError('Open or save the revision 06 Blender scene first.')
scene = bpy.context.scene
missing = [name for name in VIEWS.values() if not scene.objects.get(name)]
if missing:
    raise RuntimeError('Required town cameras are missing: ' + ', '.join(missing))
output = Path(bpy.data.filepath).parent / 'Town_Renders'
output.mkdir(parents=True, exist_ok=True)
scene.render.engine = 'CYCLES'
scene.cycles.samples = SAMPLES
try:
    import _cycles
    scene.cycles.use_denoising = bool(getattr(_cycles, 'with_openimagedenoise', False))
except ImportError:
    scene.cycles.use_denoising = False
scene.render.resolution_x = WIDTH
scene.render.resolution_y = WIDTH * 3 // 4
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
previous_camera = scene.camera
previous_path = scene.render.filepath
try:
    for key, name in VIEWS.items():
        scene.camera = scene.objects[name]
        scene.render.filepath = str(output / ('atheria_town_' + key + '.png'))
        bpy.ops.render.render(write_still=True)
finally:
    scene.camera = previous_camera
    scene.render.filepath = previous_path
print('Town renders saved to:', output)
