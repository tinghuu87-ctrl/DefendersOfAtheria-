"""Build the shared portal library and migrate Vestergate to linked placements.
Run with the existing vestergate_with_portals.blend open in Blender 4.3+.
"""
import bpy
import os
import importlib.util
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
OUT=Path(os.environ.get('ATHERIA_REUSABLE_PORTALS_OUT','/workspace/atheria-blockout/reusable-enemy-portals'))
OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('portal_reuse',HERE/'place_enemy_portals.py')
reuse=importlib.util.module_from_spec(spec);spec.loader.exec_module(reuse)
map_scene=next(s for s in bpy.data.scenes if any(o.get('Enemy route') for o in s.objects))
study=bpy.data.scenes['Atheria / Enemy portal design studies']
reuse.make_assets_from_models()
assets=[reuse.asset(n) for n in (*reuse.NAMES,'Ground runes')]
assert all(assets) and all(c.library is None for c in assets),'Rebuild from the original local portal models. Edit existing linked masters in the library file itself.'

def scene(name):
    s=bpy.data.scenes.new(name);s.world=study.world;s.render.engine='CYCLES'
    s.cycles.samples=32;s.cycles.use_denoising=False;s.cycles.transparent_max_bounces=16
    s.unit_settings.system='METRIC';s.frame_end=120
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
    s.render.resolution_x=1600;s.render.resolution_y=1100
    floor=next(o for o in study.objects if o.get('Portal presentation')).copy();s.collection.objects.link(floor)
    light=next(o for o in study.objects if o.type=='LIGHT' and 'softbox' in o.name).copy();s.collection.objects.link(light)
    cam=study.camera.copy();cam.data=study.camera.data.copy();s.collection.objects.link(cam);s.camera=cam
    s.use_nodes=True;nodes,links=s.node_tree.nodes,s.node_tree.links
    render=next(n for n in nodes if n.type=='R_LAYERS');render.scene=s
    composite=next(n for n in nodes if n.type=='COMPOSITE')
    glow=nodes.new('CompositorNodeGlare');glow.name='Atheria Portal Glow'
    glow.glare_type='FOG_GLOW';glow.threshold=2;glow.size=8;glow.mix=-.60
    links.new(render.outputs['Image'],glow.inputs[0]);links.new(glow.outputs[0],composite.inputs[0])
    return s

preview=scene('01 Atheria / Portal library preview')
for i,name in enumerate(reuse.NAMES):
    for design in [name,'Ground runes']:
        obj=bpy.data.objects.new(name+' / '+design,None);preview.collection.objects.link(obj)
        obj.instance_type='COLLECTION';obj.instance_collection=reuse.asset(design);obj.location=((i-1)*10,0,0)
masters=[]
for name in reuse.NAMES:
    master=scene('Portal master / '+name)
    master.collection.children.link(reuse.asset(name));master.collection.children.link(reuse.asset('Ground runes'))
    master.camera.location=(7,13,8)
    master.camera.rotation_euler=(Vector((0,0,2.6))-master.camera.location).to_track_quat('-Z','Y').to_euler()
    master.camera.data.ortho_scale=13
    masters.append(master)
library=HERE/'Atheria_Portal_Library.blend'
bpy.data.libraries.write(str(library),set(assets+[preview]+masters),fake_user=True,compress=True)
catalog='# Atheria reusable asset catalog\nVERSION 1\n'+reuse.CATALOG+':Atheria/Enemy Portals:Enemy Portals\n'
(HERE/'blender_assets.cats.txt').write_text(catalog)
print('PORTAL_LIBRARY_SAVED',library,flush=True)

# Replace local master data with linked references from the saved library.
for s in [preview]+masters:bpy.data.scenes.remove(s)
for col in assets:bpy.data.collections.remove(col)
with bpy.data.libraries.load(str(library),link=True) as (available,loaded):
    loaded.collections=['Atheria Portal / '+n for n in (*reuse.NAMES,'Ground runes')]
bpy.context.window.scene=map_scene
reuse.MODE='LANES';reuse.main()
# Use the same assets in the comparison scene without duplicate model geometry.
for root in [o for o in study.objects if o.get('Design') and o.get('Atheria enemy portal asset')]:
    for obj in reversed(reuse.descendants(root)):bpy.data.objects.remove(obj,do_unlink=True)
bpy.context.window.scene=study
for i,name in enumerate(reuse.NAMES):reuse.place(study,'Study '+name,name,((i-1)*10,0,0),0,1)
bpy.context.window.scene=map_scene;map_scene.frame_set(1);study.frame_set(1)
linked=next(l for l in bpy.data.libraries if Path(bpy.path.abspath(l.filepath)).resolve()==library.resolve())
linked.filepath='//../assets/Atheria_Portal_Library.blend'
repo_native=HERE.parent/'vestergate/vestergate_with_portals.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(repo_native),relative_remap=False)
linked.filepath='//Atheria_Portal_Library.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'vestergate_with_portals.blend'),relative_remap=False)
print('PORTAL_REUSE_READY',OUT,flush=True)
