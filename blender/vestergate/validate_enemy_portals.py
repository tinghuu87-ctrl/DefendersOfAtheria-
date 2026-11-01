"""Validate placed portal directions, clear apertures, markers and idle loops."""
import bpy
import json
import os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

out=Path(os.environ.get('ATHERIA_PORTALS_OUT',bpy.path.abspath('//')))
map_scene=next((s for s in bpy.data.scenes if any(o.get('Enemy route') for o in s.objects)),None)
study=bpy.data.scenes['Atheria / Enemy portal design studies']
studies=[o for o in study.objects if o.get('Design')]
assert len(studies)==3
report=dict(blender_version=bpy.app.version_string,design_count=3,standalone_or_map='map' if map_scene else 'standalone',portals=[])
if map_scene:
    bpy.context.window.scene=map_scene;map_scene.frame_set(1);bpy.context.view_layer.update()
    roots=[o for o in map_scene.objects if o.get('Design') and o.get('Lane')]
    assert len(roots)==3
    terrain=next(o for o in map_scene.objects if 'Grassland and terraced ridge foundation' in o.name)
    bvh=BVHTree.FromPolygons([terrain.matrix_world@v.co for v in terrain.data.vertices],
        [tuple(p.vertices) for p in terrain.data.polygons])
    for root in roots:
        lane=root['Lane'];road=next(o for o in map_scene.objects if o.get('Enemy route') and o.get('Lane')==lane)
        columns=road.data.polygons[0].vertices[1]
        a=sum((road.matrix_world@v.co for v in road.data.vertices[:columns]),Vector())/columns
        b=sum((road.matrix_world@v.co for v in road.data.vertices[columns:2*columns]),Vector())/columns
        expected=Vector((b.x-a.x,b.y-a.y,0)).normalized()
        actual=(root.matrix_world.to_3x3()@Vector((0,1,0))).normalized()
        assert actual.dot(expected)>.9999
        assert (Vector(root.location[:2])-Vector(a[:2])).length<.001
        marker_checks=[]
        for suffix in ['EnemySpawn','FirstWaypoint']:
            marker=next(o for o in root.children if o.name.endswith(' / '+suffix) or o.get('Portal marker')==suffix)
            p=marker.matrix_world.translation
            hit=bvh.ray_cast(p+Vector((0,0,30)),Vector((0,0,-1)),60)[0]
            assert hit is not None and abs(p.z-hit.z-.12)<.01
            assert (p-root.location).dot(actual)>0
            marker_checks.append(suffix)
        verts=[];faces=[]
        shared=root.instance_type=='COLLECTION' and root.instance_collection is not None
        frame_objects=root.instance_collection.all_objects if shared else root.children
        for obj in frame_objects:
            if obj.type=='MESH' and any(t in obj.name for t in ['broken rim','obsidian talon']):
                start=len(verts);matrix=obj.matrix_world if shared else root.matrix_world.inverted()@obj.matrix_world
                verts.extend([matrix@v.co for v in obj.data.vertices])
                faces.extend([tuple(start+i for i in f.vertices) for f in obj.data.polygons])
        frame=BVHTree.FromPolygons(verts,faces)
        probes=0
        for x in [-.65,0,.65]:
            for z in [.1,.6,1.2,1.8,2.5,3.2]:
                assert frame.ray_cast(Vector((x,2,z)),Vector((0,-1,0)),4)[0] is None
                probes+=1
        energy=next(o for o in frame_objects if 'rotating energy' in o.name)
        map_scene.frame_set(1);first=energy.evaluated_get(bpy.context.evaluated_depsgraph_get()).rotation_euler[1]
        map_scene.frame_set(61);half=energy.evaluated_get(bpy.context.evaluated_depsgraph_get()).rotation_euler[1]
        assert abs(half-first-3.141592653589793)<.0001
        map_scene.frame_set(181);repeat=energy.evaluated_get(bpy.context.evaluated_depsgraph_get()).rotation_euler[1]
        assert abs(repeat-half)<.0001,'Portal animation must repeat every 120 frames'
        map_scene.frame_set(1)
        report['portals'].append(dict(lane=lane,design=root['Design'],road_facing_dot=round(actual.dot(expected),6),
            clear_body_probes=probes,grounded_markers=marker_checks,animation_loop_frames=120))
for scene in [study]+([map_scene] if map_scene else []):
    for obj in scene.objects:
        if obj.get('Atheria enemy portal asset') or obj.get('Atheria portal placement'):
            assert obj.get('CanCollide')==False
    tree=scene.compositing_node_group if hasattr(scene,'compositing_node_group') else scene.node_tree
    for n in tree.nodes:
        if n.type=='R_LAYERS':assert n.scene==scene
report['roblox_spawning_and_vfx_integration']=False
(out/'PORTAL_VALIDATION.json').write_text(json.dumps(report,indent=2))
print('PORTAL_VALIDATION',json.dumps(report),flush=True)
