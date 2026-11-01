"""Check actual Blender mesh support along the authored routes and on the terraces.

Run in background Blender with vestergate_blockout.blend open. This checks the
blockout's geometry, not Roblox collision fidelity or enemy navigation.
"""
import bpy
import json
import os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

scene=bpy.context.scene
out=Path(os.environ.get('ATHERIA_VESTERGATE_OUT',bpy.path.abspath('//')))
layout=json.loads((out/'VESTERGATE_LAYOUT.json').read_text())
vertices=[];faces=[]
support=[]
for obj in scene.objects:
    if obj.type!='MESH':continue
    name=obj.name.removeprefix('Vestergate / ')
    if (name.startswith(('Grassland','Scenic forest escarpment','D1 /','D2 /','D3 /',
        'D4 /','D5 /','D6 /','D7 /','D8 /','Ridge bridge deck plank',
        'Gate-road worn cobble','Crystal apron','Gate staging paving','Player spawn paving'))
        or ' / walkable surface' in name):
        support.append(obj)
        offset=len(vertices)
        vertices.extend([obj.matrix_world@v.co for v in obj.data.vertices])
        faces.extend([tuple(offset+i for i in p.vertices) for p in obj.data.polygons])
bvh=BVHTree.FromPolygons(vertices,faces,all_triangles=False)
def floor(x,y):
    hit=bvh.ray_cast(Vector((x,y,35)),Vector((0,0,-1)),70)
    return hit[0].z if hit[0] is not None else None

issues=[];samples=0;max_raise=0;max_drop=0
for lane in layout['lanes']:
    points=lane['centreline']
    for i,p in enumerate(points):
        a=Vector(points[max(0,i-1)][:2]);b=Vector(points[min(len(points)-1,i+1)][:2])
        tangent=(b-a).normalized();side=Vector((-tangent.y,tangent.x))
        for offset in [-.34*lane['width'],0,.34*lane['width']]:
            q=Vector(p[:2])+side*offset
            heights=[floor(q.x+dx,q.y+dy) for dx,dy in [(0,0),(.12,0),(-.12,0),(0,.12),(0,-.12)]]
            heights=[h for h in heights if h is not None]
            samples+=1
            if not heights:
                issues.append(dict(lane=lane['id'],sample=i,offset=offset,reason='no supporting mesh'))
                continue
            difference=max(heights)-p[2]
            max_raise=max(max_raise,difference);max_drop=max(max_drop,-difference)
            # Lateral points on a sloped route may differ naturally from its centre.
            if difference>.75 or difference<-.65:
                issues.append(dict(lane=lane['id'],sample=i,offset=round(offset,3),
                    floor_difference=round(difference,3),xy=[round(q.x,3),round(q.y,3)]))
for pad in layout['defence_terraces']:
    h=floor(pad['x'],pad['y'])
    assert h is not None and abs(h-pad['z']-.083)<.08,pad['id']
report=dict(kind='Blender actual-mesh support and layout checks',
    support_mesh_count=len(support),route_support_samples=samples,
    max_sample_raise_metres=round(max_raise,4),max_sample_drop_metres=round(max_drop,4),
    route_support_issues=issues,terrace_checks=layout['checks'],
    defence_footprint_count=len(layout['defence_terraces']),
    lane_lengths_metres=layout['lane_lengths_metres'],
    native_scene=scene.name,mesh_object_count=sum(o.type=='MESH' for o in scene.objects),
    no_runtime_or_roblox_collision_validation=True)
(out/'VALIDATION.json').write_text(json.dumps(report,indent=2))
print('VESTERGATE_VALIDATION',json.dumps(report),flush=True)
assert not issues,'Review route support issues in VALIDATION.json'
