"""Validate revision 02 Blender roads, green coverage, vantages and lamp direction.
These are authoring checks, not Roblox collision or live character-jump tests.
"""
import bpy
import json
import os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

scene=bpy.context.scene
out=Path(os.environ.get('ATHERIA_VESTERGATE_OUT',bpy.path.abspath('//')))
layout=json.loads((out/'VESTERGATE_LAYOUT.json').read_text())
terrain=next(o for o in scene.objects if o.name.startswith('Vestergate / Grassland'))
terrain.data.calc_loop_triangles()
triangles=[tuple(t.vertices) for t in terrain.data.loop_triangles]
terrain_bvh=BVHTree.FromPolygons([v.co.copy() for v in terrain.data.vertices],triangles,all_triangles=True)
attribute=terrain.data.attributes['Road clearance']

def make_bvh(objects):
    vertices=[];faces=[]
    for obj in objects:
        start=len(vertices)
        vertices.extend([obj.matrix_world@v.co for v in obj.data.vertices])
        faces.extend([tuple(start+i for i in p.vertices) for p in obj.data.polygons])
    return BVHTree.FromPolygons(vertices,faces)

def cast(bvh,x,y):
    return bvh.ray_cast(Vector((x,y,40)),Vector((0,0,-1)),80)

roads=[];green=[];terraces=[]
for obj in scene.objects:
    if obj.type!='MESH':continue
    name=obj.name.removeprefix('Vestergate / ')
    if ' / walkable surface' in name or name.startswith(('Ridge bridge deck plank','Crystal apron','Gate staging paving')):
        roads.append(obj)
    if any('Defence vantages' in c.name for c in obj.users_collection):terraces.append(obj)
    if (any('Ground greenery' in c.name for c in obj.users_collection)
        and any(any(tag in m.name for tag in ['leaf','grass','fern']) for m in obj.data.materials if m)):
        green.append(obj)

road_bvh=make_bvh(roads);green_bvh=make_bvh(green);pad_bvh=make_bvh(terraces)
issues=[];green_issues=[];samples=0;max_raise=0;max_drop=0
for lane in layout['lanes']:
    points=lane['centreline']
    for i,p in enumerate(points):
        a=Vector(points[max(0,i-1)][:2]);b=Vector(points[min(len(points)-1,i+1)][:2])
        tangent=(b-a).normalized();side=Vector((-tangent.y,tangent.x))
        for offset in [-.44,-.30,-.15,0,.15,.30,.44]:
            q=Vector(p[:2])+side*(offset*lane['width']);samples+=1
            hits=[cast(road_bvh,q.x+dx,q.y+dy)[0] for dx,dy in [(0,0),(.06,0),(-.06,0),(0,.06),(0,-.06)]]
            heights=[h.z for h in hits if h is not None]
            if not heights:
                issues.append(dict(lane=lane['id'],sample=i,offset=offset,reason='missing road or bridge mesh'))
                continue
            road_z=max(heights);difference=road_z-p[2]
            max_raise=max(max_raise,difference);max_drop=max(max_drop,-difference)
            if abs(difference)>.75:
                issues.append(dict(lane=lane['id'],sample=i,offset=offset,height_difference=round(difference,4)))
            hit,normal,index,distance=cast(terrain_bvh,q.x,q.y)
            if hit is not None and hit.z>road_z+.003:
                ids=triangles[index]
                value=barycentric_transform(hit,*[terrain.data.vertices[j].co for j in ids],
                    *[Vector((attribute.data[j].value,0,0)) for j in ids]).x
                if value>.30:
                    green_issues.append(dict(lane=lane['id'],sample=i,offset=offset,kind='unpainted terrain above road',clearance=value))
            foliage=cast(green_bvh,q.x,q.y)[0]
            if foliage is not None and foliage.z>road_z+.035:
                green_issues.append(dict(lane=lane['id'],sample=i,offset=offset,kind='vegetation over road'))
            shelf=cast(pad_bvh,q.x,q.y)[0]
            if shelf is not None and shelf.z>road_z+.15:
                issues.append(dict(lane=lane['id'],sample=i,offset=offset,kind='defence shelf overlaps road'))

assert len(layout['defence_terraces'])==6
jump_checks=[]
for pad in layout['defence_terraces']:
    hit=cast(pad_bvh,pad['x'],pad['y'])[0]
    assert hit is not None and abs(hit.z-pad['z'])<.025,pad['id']
    nearest=min((p for l in layout['lanes'] for p in l['centreline']),
        key=lambda p:(p[0]-pad['x'])**2+(p[1]-pad['y'])**2)
    rise=pad['z']-nearest[2]
    jump_checks.append(dict(id=pad['id'],rise_from_nearest_road_metres=round(rise,3)))

for obj in scene.objects:
    assert not any(tag in obj.name for tag in ['accessible grass ramp','flat defence footprint','footprint edge','Gate-road worn cobble'])
    assert not obj.name.startswith(('Vestergate / D7 /','Vestergate / D8 /'))
for obj in roads:
    if ' / walkable surface' in obj.name:
        assert all('dirt road' in m.name for m in obj.data.materials)
lamp_checks=[]
for post in scene.objects:
    if 'Lantern pane' not in post:continue
    pane=scene.objects[post['Lantern pane']]
    position=Vector((post.location.x,post.location.y))
    actual=(Vector((pane.location.x,pane.location.y))-position).normalized()
    expected=(Vector(post['Road target'])-position).normalized()
    dot=actual.dot(expected)
    assert dot>.9999,(post.name,dot)
    lamp_checks.append(dict(post=post.name,road_facing_dot=round(dot,6)))
assert len(lamp_checks)==len(layout['lamps']) and len(lamp_checks)>0

report=dict(kind='Revision 02 Blender geometry, road coverage, removals and lamp checks',
    route_support_samples=samples,route_support_issues=issues,green_road_issues=green_issues,
    max_sample_raise_metres=round(max_raise,4),max_sample_drop_metres=round(max_drop,4),
    terrace_checks=layout['checks'],jump_access_authoring_checks=jump_checks,
    defence_terrace_count=len(terraces),lamp_checks=lamp_checks,
    removed_geometry_verified=['cobbles','ramps','vantage centre discs','D7','D8'],
    lane_lengths_metres=layout['lane_lengths_metres'],native_scene=scene.name,
    mesh_object_count=sum(o.type=='MESH' for o in scene.objects),
    live_roblox_collision_and_jump_validation=False)
(out/'VALIDATION.json').write_text(json.dumps(report,indent=2))
print('VESTERGATE_VALIDATION',json.dumps(report),flush=True)
assert not issues,'Route support issues: see VALIDATION.json'
assert not green_issues,'Green on road: see VALIDATION.json'
assert all(p['rise_from_nearest_road_metres']<1.95 for p in jump_checks),'Jump approach height: see VALIDATION.json'
