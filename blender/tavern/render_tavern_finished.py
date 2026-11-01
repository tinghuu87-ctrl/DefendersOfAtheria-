"""Render four views of the active finished tavern; restore the scene afterward."""
import bpy
from pathlib import Path
scene = bpy.context.scene
assert scene.get('Tavern finish'), 'Open a finished Lantern Tavern scene first.'
out = Path(bpy.path.abspath('//Tavern_Finished_Renders'))
out.mkdir(parents=True, exist_ok=True)
views = [('arrival','01 Entering the Lantern Tavern'),
         ('hearth','02 Hearth and social bays'),
         ('cutaway','03 Dollhouse cutaway'),
         ('leaderboard','05 Leaderboard viewing area')]
original_camera, original_path = scene.camera, scene.render.filepath
original_denoising = scene.cycles.use_denoising
visibility = {o:o.hide_render for o in scene.objects}
try:
    import _cycles
    scene.cycles.use_denoising = bool(getattr(_cycles,'with_openimagedenoise',False))
except ImportError:
    scene.cycles.use_denoising = False
try:
    for key, camera_name in views:
        if key == 'cutaway':
            for o in scene.objects:
                if any(c.name.startswith('Tavern / Roof and ceiling') for c in o.users_collection) or o.name.startswith(('Tavern / Front wall beside entrance','Tavern / Entrance overhead','Tavern / Left wall')):
                    o.hide_render = True
        scene.camera = next(o for o in scene.objects if o.type=='CAMERA' and o.name.startswith(camera_name))
        scene.render.filepath = str(out / ('tavern_'+key+'.png'))
        bpy.ops.render.render(write_still=True)
        for o, hidden in visibility.items():
            o.hide_render = hidden
finally:
    scene.camera, scene.render.filepath = original_camera, original_path
    scene.cycles.use_denoising = original_denoising
    for o, hidden in visibility.items():
        o.hide_render = hidden
print('Tavern views saved to', out)
