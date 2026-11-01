"""Render saved portal assets without rebuilding them; run inside Blender."""
import bpy
import os
from pathlib import Path

out=Path(os.environ.get('ATHERIA_PORTALS_OUT',bpy.path.abspath('//')))
out.mkdir(parents=True,exist_ok=True)
study=bpy.data.scenes['Atheria / Enemy portal design studies']
map_scene=next((s for s in bpy.data.scenes if any(o.get('Enemy route') for o in s.objects)),None)
views=[('designs',study,study.camera)]
if map_scene:
    for key,prefix in [('portal','Atheria enemy portals / 06 Enemy portal close-up'),
        ('overview','Vestergate / 01 Battlefield overview'),('plan','Vestergate / 02 Three-lane terrain plan')]:
        cam=next(o for o in map_scene.objects if o.type=='CAMERA' and o.name.startswith(prefix))
        views.append((key,map_scene,cam))
original_scene=bpy.context.scene
for key,scene,cam in views:
    if key not in os.environ.get('ATHERIA_PORTALS_VIEWS','designs,portal,overview,plan').split(','):continue
    old=(scene.camera,scene.render.resolution_x,scene.render.resolution_y,
        scene.render.resolution_percentage,scene.cycles.samples,scene.render.filepath,scene.frame_current)
    try:
        bpy.context.window.scene=scene;scene.camera=cam;scene.frame_set(1)
        scene.render.resolution_x=1600;scene.render.resolution_y=1200 if key in ['overview','plan'] else 1100
        scene.render.resolution_percentage=int(os.environ.get('ATHERIA_PORTALS_RESOLUTION_PERCENT','100'))
        scene.cycles.samples=int(os.environ.get('ATHERIA_PORTALS_SAMPLES','32'))
        scene.render.filepath=str(out/('enemy_portals_'+key+'.png'))
        bpy.ops.render.render(write_still=True,scene=scene.name)
        print('PORTAL_RENDERED',key,flush=True)
    finally:
        scene.camera,scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage,scene.cycles.samples,scene.render.filepath,frame=old
        scene.frame_set(frame)
bpy.context.window.scene=original_scene
