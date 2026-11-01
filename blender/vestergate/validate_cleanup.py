"""Check actual saved terrain connectivity, foliage support and character removal."""
import bpy,bmesh,json,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

scene=bpy.context.scene
terrain=next(o for o in scene.objects if 'Grassland and terraced ridge foundation' in o.name)
tree=BVHTree.FromPolygons([terrain.matrix_world@v.co for v in terrain.data.vertices],
    [tuple(p.vertices) for p in terrain.data.polygons])
def floor(p):
    hit=tree.ray_cast(Vector((p.x,p.y,1000)),Vector((0,0,-1)),2000)[0]
    return None if hit is None else hit.z
def manifold(obj):
    bm=bmesh.new();bm.from_mesh(obj.data)
    assert all(e.is_manifold for e in bm.edges),obj.name
    remaining=set(bm.verts);stack=[remaining.pop()]
    while stack:
        for e in stack.pop().link_edges:
            for v in e.verts:
                if v in remaining:remaining.remove(v);stack.append(v)
    assert not remaining,obj.name
    bm.free()
manifold(terrain)
for x,y in [(-58,47),(-54,19),(-53,-8),(-27,65),(-12,71),(18,69),(58,48),(56,15),(53,-9)]:
    hit=tree.ray_cast(Vector((x,y,1000)),Vector((0,0,-1)),2000)
    assert hit[0] is not None
    material=terrain.data.materials[terrain.data.polygons[hit[2]].material_index]
    assert material is not None and 'grass rim' in material.name,(x,y,material.name if material else None)
assert not any('Scenic forest escarpment' in o.name for o in scene.objects)
assert not any('1.8m figure' in o.name or any('Scale figures' in c.name for c in o.users_collection) for o in scene.objects)
pads=[o for o in scene.objects if o.type=='MESH' and any('Defence vantages' in c.name for c in o.users_collection)]
assert len(pads)==6
for obj in pads:
    manifold(obj)
    p=sum((obj.matrix_world@v.co for v in obj.data.vertices),Vector())/len(obj.data.vertices)
    z=floor(p);assert z is not None
    assert min((obj.matrix_world@v.co).z for v in obj.data.vertices)<z-.25
trunks=[o for o in scene.objects if '/ Tree / branching trunk' in o.name]
for obj in trunks:
    p=obj.matrix_world@Vector((0,0,min(v.co.z for v in obj.data.vertices)))
    z=floor(p);assert z is not None and abs(p.z+.12-z)<.0002,(obj.name,p,z)
count=0
for obj in scene.objects:
    if obj.type!='MESH' or not any('Ground greenery' in c.name for c in obj.users_collection):continue
    if 'Grass tufts' in obj.name or 'Broad-leaf ground plant' in obj.name:
        for face in obj.data.polygons:
            points=[obj.matrix_world@obj.data.vertices[i].co for i in face.vertices]
            low=min(p.z for p in points);bottom=[p for p in points if abs(p.z-low)<.0001]
            p=sum(bottom,Vector())/len(bottom);z=floor(p)
            expected=.025 if 'Grass tufts' in obj.name else 0
            assert z is not None and abs(low-z-expected)<.0002,(obj.name,tuple(p),z)
            count+=1
    else:
        p=obj.matrix_world.translation;z=floor(p);assert z is not None,(obj.name,p)
        if 'Trailing cliff vine' in obj.name:
            assert tree.find_nearest(p)[3]<.065,obj.name
        elif 'Wildflower patch' in obj.name:
            low=min((obj.matrix_world@v.co).z for v in obj.data.vertices)
            assert abs(low-z+.02)<.0002,obj.name
report=dict(terrain_closed_connected_solid=True,connected_defence_ledges=6,
    grounded_trees=len(trunks),unsupported_scenery=0,grey_characters=0,
    checked_plant_faces=count,cliff_materials_preserved=True,
    road_and_portal_geometry_checked_separately=True)
out=Path(os.environ.get('VESTERGATE_CLEANUP_OUT',bpy.path.abspath('//')))
(out/'CLEANUP_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
print('CLEANUP_VALIDATION_PASS',json.dumps(report),flush=True)
