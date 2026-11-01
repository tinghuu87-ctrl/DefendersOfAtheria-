"""Blender 4.3/5: connect Vestergate terrain, clean scenery, remove mannequins.
Run with the map open. Saves a separate cleaned file and copies linked libraries.
"""
import bpy
import bmesh
import os
import json
import shutil
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SAVE = True
OUT = Path(os.environ.get('VESTERGATE_CLEANUP_OUT',
    str(Path(bpy.data.filepath).parent/'Vestergate_Cleaned') if bpy.data.filepath
    else str(Path.home()/'Vestergate_Cleaned'))).resolve()
scene = next((s for s in [bpy.context.scene]+list(bpy.data.scenes)
    if any(o.get('Enemy route') for o in s.objects)), None)
assert scene is not None, 'Open the Vestergate map first.'
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.window.scene = scene
bpy.context.view_layer.update()
terrain = next(o for o in scene.objects if o.type=='MESH'
    and 'Grassland and terraced ridge foundation' in o.name)
report = dict(joined_cliffs=0, removed_characters=0, removed_trees=0,
    grounded_trees=0, removed_props=0, grounded_props=0,
    removed_plant_components=0, grounded_plant_components=0, sealed_defence_ledges=0,
    attached_vines=0)


def bvh(obj):
    return BVHTree.FromPolygons([obj.matrix_world@v.co for v in obj.data.vertices],
        [tuple(p.vertices) for p in obj.data.polygons])


def height(tree, x, y):
    hit = tree.ray_cast(Vector((x,y,1000)), Vector((0,0,-1)), 2000)[0]
    return None if hit is None else hit.z


def topology(mesh):
    bm = bmesh.new(); bm.from_mesh(mesh)
    bad = sum(not edge.is_manifold for edge in bm.edges)
    remaining = set(bm.verts); shells = 0
    while remaining:
        stack = [remaining.pop()]; shells += 1
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in remaining:
                    remaining.remove(other); stack.append(other)
    bm.free()
    return shells, bad


def select(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active = obj


def boolean(obj, other, operation):
    select(obj)
    modifier = obj.modifiers.new('Connect map terrain', 'BOOLEAN')
    modifier.operation = operation; modifier.solver = 'EXACT'; modifier.object = other
    modifier.material_mode = 'TRANSFER'
    bpy.ops.object.modifier_apply(modifier=modifier.name)


cliffs = [o for o in scene.objects if o.type=='MESH' and 'Scenic forest escarpment' in o.name]
temporary = []
if cliffs:
    # The original foundation is closed; the scenic cliff meshes have open bottoms.
    # Make closed, deeply embedded operands and clip them to the actual map edge.
    vertices = [terrain.matrix_world@v.co for v in terrain.data.vertices]
    top = [p for p in terrain.data.polygons if p.material_index<2]
    edge_counts = {}
    for polygon in top:
        for a,b in polygon.edge_keys:
            key = tuple(sorted((a,b))); edge_counts[key] = edge_counts.get(key,0)+1
    adjacency = {}
    for (a,b),count in edge_counts.items():
        if count==1:
            adjacency.setdefault(a,[]).append(b); adjacency.setdefault(b,[]).append(a)
    assert adjacency and all(len(v)==2 for v in adjacency.values()), 'Cannot identify the map boundary.'
    start = next(iter(adjacency)); ring = [start]; previous = None; current = start
    while True:
        following = next(v for v in adjacency[current] if v!=previous)
        if following==start: break
        ring.append(following); previous,current = current,following
    assert len(ring)==len(adjacency), 'The map boundary contains unexpected holes.'
    centre = sum((vertices[i] for i in ring),Vector())/len(ring)
    bottom = min(vertices[i].z for p in top for i in p.vertices)-.75
    high = max(v.z for v in vertices)+50
    points = []
    for z in [bottom-1,high]:
        for i in ring:
            p = vertices[i].copy(); d = Vector((centre.x-p.x,centre.y-p.y,0))
            if d.length: p += d.normalized()*.02
            points.append((p.x,p.y,z))
    n = len(ring)
    faces = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    data = bpy.data.meshes.new('Cleanup boundary'); data.from_pydata(points,[],faces); data.update()
    data.materials.append(terrain.data.materials[2])
    prism = bpy.data.objects.new('Cleanup boundary',data); scene.collection.objects.link(prism); temporary.append(prism)
    work = terrain.copy(); work.data = terrain.data.copy()
    scene.collection.objects.link(work); temporary.append(work)
    try:
        for cliff in cliffs:
            operand = cliff.copy(); operand.data = cliff.data.copy()
            scene.collection.objects.link(operand); temporary.append(operand)
            inverse = operand.matrix_world.inverted()
            base = min(v.co.z for v in operand.data.vertices)
            for vertex in operand.data.vertices:
                if abs(vertex.co.z-base)<.0001:
                    p = operand.matrix_world@vertex.co; p.z = bottom
                    vertex.co = inverse@p
            bm = bmesh.new(); bm.from_mesh(operand.data)
            edges = [edge for edge in bm.edges if edge.is_boundary]
            if edges: bmesh.ops.holes_fill(bm,edges=edges,sides=0)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            bm.to_mesh(operand.data); bm.free(); operand.data.update()
            boolean(operand,prism,'INTERSECT')
            assert operand.data.polygons, 'A cliff has no intersection with the map.'
            boolean(work,operand,'UNION')
            report['joined_cliffs'] += 1
            print('CLIFF_CONNECTED',cliff.name,flush=True)
        assert topology(work.data)==(1,0), 'Terrain union did not produce one closed solid.'
        assert 'Road clearance' in work.data.attributes, 'Road paint attribute was lost.'
        terrain.data = work.data
        for cliff in cliffs: bpy.data.objects.remove(cliff,do_unlink=True)
    finally:
        for obj in reversed(temporary):
            data = obj.data; bpy.data.objects.remove(obj,do_unlink=True)
            if data.users==0: bpy.data.meshes.remove(data)

# Keep the six build ledges separately editable, with closed bases embedded in
# the foundation. Their tops and horizontal positions remain the same.
pad_bottom = min((terrain.matrix_world@v.co).z for v in terrain.data.vertices)+.25
for obj in list(scene.objects):
    if obj.type!='MESH' or not any('Defence vantages' in c.name for c in obj.users_collection): continue
    if obj.data.users>1: obj.data = obj.data.copy()
    base = min(v.co.z for v in obj.data.vertices); inverse = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        if abs(vertex.co.z-base)<.0001:
            p = obj.matrix_world@vertex.co; p.z = pad_bottom; vertex.co = inverse@p
    bm = bmesh.new(); bm.from_mesh(obj.data)
    edges = [edge for edge in bm.edges if edge.is_boundary]
    if edges: bmesh.ops.holes_fill(bm,edges=edges,sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    assert topology(obj.data)==(1,0), 'A defence ledge could not be sealed.'
    report['sealed_defence_ledges'] += 1

ground = bvh(terrain)
# Identify figures by their own objects/collection, not their shared sign material.
for obj in list(scene.objects):
    if ('1.8m figure' in obj.name or any('Scale figures' in c.name for c in obj.users_collection)):
        bpy.data.objects.remove(obj,do_unlink=True); report['removed_characters'] += 1


def tree_root(obj):
    z = min(v.co.z for v in obj.data.vertices)
    return obj.matrix_world@Vector((0,0,z))


trees = [o for o in scene.objects if o.type=='MESH' and '/ Tree / branching trunk' in o.name]
bundles = {o:[o] for o in trees}
roots = {o:tree_root(o) for o in trees}
for col in scene.collection.children:
    if '/ Trees' not in col.name: continue
    current = None
    for obj in list(col.objects):
        if obj in bundles: current = obj
        elif current is not None: bundles[current].append(obj)
for trunk, objects in bundles.items():
    root = roots[trunk]; z = height(ground,root.x,root.y)
    if z is None:
        for obj in objects: bpy.data.objects.remove(obj,do_unlink=True)
        report['removed_trees'] += 1
    else:
        dz = z-(root.z+.12)
        for obj in objects:
            matrix = obj.matrix_world.copy(); matrix.translation.z += dz; obj.matrix_world = matrix
        trunk['Grounded root'] = [root.x,root.y,z]
        report['grounded_trees'] += 1

# Grass blades and broad-leaf plants contain many disconnected little components.
for obj in list(scene.objects):
    if obj.type!='MESH' or not any('Ground greenery' in c.name for c in obj.users_collection): continue
    if 'Grass tufts' in obj.name or 'Broad-leaf ground plant' in obj.name:
        obj.data = obj.data.copy() if obj.data.users>1 else obj.data
        bm = bmesh.new(); bm.from_mesh(obj.data)
        remaining = set(bm.verts); delete = []; inverse = obj.matrix_world.inverted()
        while remaining:
            component = [remaining.pop()]; stack = component.copy()
            while stack:
                v = stack.pop()
                for edge in v.link_edges:
                    other = edge.other_vert(v)
                    if other in remaining:
                        remaining.remove(other); component.append(other); stack.append(other)
            world = [obj.matrix_world@v.co for v in component]
            low = min(v.z for v in world)
            base = [p for p in world if abs(p.z-low)<.0001]
            root = sum(base,Vector())/len(base); z = height(ground,root.x,root.y)
            if z is None:
                delete.extend(component); report['removed_plant_components'] += 1
            else:
                dz = z+(.025 if 'Grass tufts' in obj.name else 0)-low
                for vertex,p in zip(component,world):
                    p.z += dz; vertex.co = inverse@p
                report['grounded_plant_components'] += 1
        if delete: bmesh.ops.delete(bm,geom=delete,context='VERTS')
        bm.to_mesh(obj.data); bm.free(); obj.data.update()
        if not obj.data.polygons: bpy.data.objects.remove(obj,do_unlink=True)
        continue
    p = obj.matrix_world.translation.copy(); z = height(ground,p.x,p.y)
    if z is None:
        bpy.data.objects.remove(obj,do_unlink=True); report['removed_props'] += 1
    elif 'Trailing cliff vine' in obj.name:
        near,normal,_,distance = ground.find_nearest(p)
        if near is None or distance>1.0:
            bpy.data.objects.remove(obj,do_unlink=True); report['removed_props'] += 1
        else:
            matrix = obj.matrix_world.copy(); matrix.translation = near+normal*.06; obj.matrix_world = matrix
            report['attached_vines'] += 1
    else:
        offset = .12 if 'Ground rock' in obj.name else .35
        if 'Low shrub' in obj.name: offset = obj.matrix_world.to_scale().x*.35
        if 'Wildflower patch' in obj.name:
            offset = p.z-min((obj.matrix_world@v.co).z for v in obj.data.vertices)-.02
        matrix = obj.matrix_world.copy(); matrix.translation.z = z+offset; obj.matrix_world = matrix
        report['grounded_props'] += 1

bpy.context.view_layer.update()
report['terrain_shells'],report['terrain_nonmanifold_edges'] = topology(terrain.data)
assert (report['terrain_shells'],report['terrain_nonmanifold_edges'])==(1,0)
scene['Vestergate terrain cleanup'] = True
select(terrain)
if SAVE:
    OUT.mkdir(parents=True,exist_ok=True)
    libraries = []
    for library in bpy.data.libraries:
        original = Path(bpy.path.abspath(library.filepath)).resolve()
        assert original.is_file(), 'Missing portal library: '+str(original)
        target = OUT/'Libraries'/original.name; target.parent.mkdir(exist_ok=True)
        if original!=target: shutil.copy2(original,target)
        catalog = original.parent/'blender_assets.cats.txt'
        if catalog.is_file() and catalog.resolve()!=(target.parent/catalog.name).resolve():
            shutil.copy2(catalog,target.parent/catalog.name)
        library.filepath = str(target); libraries.append((library,target))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'vestergate_cleaned.blend'))
    for library,target in libraries: library.filepath = bpy.path.relpath(str(target))
    scene.render.filepath = '//vestergate_cleaned_overview.png'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'vestergate_cleaned.blend'))
    (OUT/'CLEANUP_REPORT.json').write_text(json.dumps(report,indent=2))
print('VESTERGATE_CLEANUP_COMPLETE',json.dumps(report),str(OUT),flush=True)
