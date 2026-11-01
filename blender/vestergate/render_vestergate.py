"""Render an existing Vestergate blockout without rebuilding its geometry.

blender -b vestergate_blockout.blend --python render_vestergate.py
Uses the same ATHERIA_VESTERGATE_OUT / SAMPLES / VIEWS options as the builder.
"""
import bpy
import os
from pathlib import Path

scene = bpy.context.scene
assert scene.name.startswith('Vestergate /'), 'Open vestergate_blockout.blend first.'
out = Path(os.environ.get('ATHERIA_VESTERGATE_OUT', bpy.path.abspath('//')))
out.mkdir(parents=True, exist_ok=True)
views = dict(overview='01 Battlefield overview', plan='02 Three-lane terrain plan',
    arrival='03 Outside the kingdom gate', gate='04 Crystal and kingdom walls',
    ridge='05 Ridge crossing and defence terraces')
original = (scene.camera, scene.render.filepath, scene.cycles.samples)
try:
    scene.cycles.samples=int(os.environ.get('ATHERIA_VESTERGATE_SAMPLES','32'))
    for key in os.environ.get('ATHERIA_VESTERGATE_VIEWS',','.join(views)).split(','):
        scene.camera=next(o for o in scene.objects if o.type=='CAMERA' and o.name.startswith('Vestergate / '+views[key]))
        scene.render.filepath=str(out/('vestergate_'+key+'.png'))
        bpy.ops.render.render(write_still=True)
        print('VESTERGATE_RENDERED',key,flush=True)
finally:
    scene.camera,scene.render.filepath,scene.cycles.samples=original
