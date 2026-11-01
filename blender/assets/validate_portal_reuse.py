"""Check portal instancing, cross-scene reuse, placement isolation and ground FX."""
import bpy
import os
import json
import importlib.util
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('reuse',HERE/'place_enemy_portals.py')
reuse=importlib.util.module_from_spec(spec);spec.loader.exec_module(reuse)
scene=bpy.context.scene
original=[o for o in scene.objects if o.get('Atheria portal placement')]
assert len(original)==3
assert len({o.instance_collection for o in original})==3
assert all(o.instance_type=='COLLECTION' and o.instance_collection.library for o in original)
assert all(child.modifiers[0].wrap_mode=='ABOVE_SURFACE' for o in original for child in o.children if child.type=='MESH')
assert all(reuse.asset(n).asset_data for n in (*reuse.NAMES,'Ground runes'))
ground=next(o for o in scene.objects if 'Grassland and terraced ridge foundation' in o.name)
reuse.MODE='LANES';reuse.main()
placed=[o for o in scene.objects if o.get('Atheria portal placement')]
assert len(placed)==3
animation=[];ground_checks=0
for obj in placed:
    assert obj.instance_collection==reuse.asset(obj['Design'])
    children=list(obj.children)
    arcs=[o for o in children if o.type=='MESH']
    assert len(arcs)==3 and all(o.modifiers[0].target==ground for o in arcs)
    graph=bpy.context.evaluated_depsgraph_get()
    for arc in arcs:
        evaluated=arc.evaluated_get(graph);mesh=evaluated.to_mesh()
        for vertex in list(mesh.vertices)[::15]:
            p=evaluated.matrix_world@vertex.co
            hit=ground.ray_cast(ground.matrix_world.inverted()@(p+Vector((0,0,30))),Vector((0,0,-1)))[1]
            floor=(ground.matrix_world@hit).z
            assert .015<p.z-floor<.11,(obj.name,p.z-floor)
            ground_checks+=1
        evaluated.to_mesh_clear()
    source=next(o for o in obj.instance_collection.all_objects if 'rotating energy' in o.name)
    scene.frame_set(1);graph=bpy.context.evaluated_depsgraph_get()
    first=source.evaluated_get(graph).rotation_euler[1]
    scene.frame_set(61);graph=bpy.context.evaluated_depsgraph_get()
    half=source.evaluated_get(graph).rotation_euler[1]
    assert abs(half-first-3.141592653589793)<.001,(obj.name,first,half)
    animation.append(obj['Design'])
scene.frame_set(1)

# Use the same design in separate map scenes, with independent transforms.
other=bpy.data.scenes.new('Portal cross-map test');bpy.context.window.scene=other
a=reuse.place(other,'A','Voidmaw',(4,7,0),.2,1)
b=reuse.place(other,'B','Voidmaw',(-9,3,0),1.1,1.75)
assert a.instance_collection is b.instance_collection is reuse.asset('Voidmaw')
assert next(o for o in a.children if o.type=='MESH').data is next(o for o in b.children if o.type=='MESH').data
before=b.location.copy();a.location.x+=8
assert b.location==before and b.scale.x==1.75
reuse.place(other,'A','Thornrift',(1,2,0),0,1.2)
assert len([o for o in other.objects if o.get('Atheria portal placement')])==2
assert len([o for o in scene.objects if o.get('Atheria portal placement')])==3
reuse.MODE='CURSOR';reuse.DESIGN='Stormscar';reuse.PLACEMENT_ID='Cursor spawn'
other.cursor.location=(8,-6,4);reuse.main()
cursor=next(o for o in other.objects if o.get('Atheria portal placement')=='Cursor spawn')
assert (cursor.location-Vector((8,-6,4))).length<.0001
marker=bpy.data.objects.new('Enemy marker',None);other.collection.objects.link(marker)
marker.location=(12,5,3);marker.rotation_euler.z=.7
for o in bpy.context.selected_objects:o.select_set(False)
marker.select_set(True);reuse.MODE='MARKERS';reuse.main()
marked=next(o for o in other.objects if o.get('Atheria portal placement')=='Enemy marker')
assert (marked.location-marker.location).length<.0001
assert abs(marked.rotation_euler.z-.7)<.0001
report=dict(asset_collections=4,vestergate_linked_placements=3,rerun_keeps_three=True,
    shared_core_and_ground_mesh_data=True,independent_position_rotation_scale=True,
    cross_scene_reuse=True,cursor_and_marker_modes=True,terrain_conforming_samples=ground_checks,
    animated_designs=animation,linked_library='Atheria_Portal_Library.blend',
    runtime_roblox_integration=False)
out=Path(os.environ.get('ATHERIA_REUSABLE_PORTALS_OUT','/workspace/atheria-blockout/reusable-enemy-portals'))
(out/'REUSE_VALIDATION.json').write_text(json.dumps(report,indent=2))
print('PORTAL_REUSE_VALIDATION',json.dumps(report),flush=True)
bpy.context.window.scene=scene
