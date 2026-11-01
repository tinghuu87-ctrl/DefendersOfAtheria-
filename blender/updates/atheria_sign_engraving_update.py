"""Atheria revision 07: remove the welcome sign and relocate Apples.
Run with the revision 05 or 06 town open. No external files required.
The new position is the sanctuary-facing wall beside the bench and planter.
"""
import bpy
import math
from mathutils import Matrix, Vector

scene = bpy.context.scene
cat = bpy.data.objects.get('V03 Apples cat arch carving')
if cat is None or not bpy.data.objects.get('V05 Joined masonry wall network'):
    raise RuntimeError('Open your revision 05 or 06 Atheria town first.')
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# Store the original location once, so the update can be run repeatedly.
key = 'v07_original_arch_matrix'
if key not in cat:
    cat[key] = [value for row in cat.matrix_world for value in row]
values = list(cat[key])
original_matrix = Matrix([values[i:i + 4] for i in range(0, 16, 4)])

# The welcome sign has separate backing, face and lettering objects.
def center(obj):
    return sum((obj.matrix_world @ Vector(p) for p in obj.bound_box), Vector()) / 8

signs = [obj for obj in scene.objects
         if obj.name.startswith('Carved sign: WELCOME TO ATHERIA')]
anchors = [center(obj) for obj in signs] or [Vector((-17, -29, 3))]
for obj in list(scene.objects):
    title = obj.name.upper()
    if ('WELCOME TO ATHERIA' in title or
        (obj.type == 'MESH' and obj.name.startswith('Sign face')
         and any((center(obj) - anchor).length < 0.5 for anchor in anchors))):
        bpy.data.objects.remove(obj, do_unlink=True)

collection_name = '17 / Relocated Apples engraving'
collection = bpy.data.collections.get(collection_name)
if collection:
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    collection = bpy.data.collections.new(collection_name)
    scene.collection.children.link(collection)

# A plain stone replaces the old engraved panel on the arch.
vertices = [(x * 0.65, y * 0.11, z)
            for x, y, z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                            (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),
         (1,2,6,5),(2,3,7,6),(3,0,4,7)]
mesh = bpy.data.meshes.new('V07 Plain replacement arch stone')
mesh.from_pydata(vertices, [], faces)
mesh.update()
stone = bpy.data.objects.new('V07 Plain replacement arch stone', mesh)
collection.objects.link(stone)
stone.matrix_world = original_matrix
mesh.materials.append(cat.data.materials[0])
bevel = stone.modifiers.new('Soft stone edges', 'BEVEL')
bevel.width = 0.015
bevel.segments = 2

# Move the original Boolean-engraved mesh intact, including cat and title.
# Wall centerline X=-3; its sanctuary-facing surface is X=-2.60.
# Local -Y is the engraved front, rotated to face east into the courtyard.
cat.matrix_world = (Matrix.Translation((-2.52, 4.5, 1.72))
                    @ Matrix.Rotation(math.pi / 2, 4, 'Z'))
cat['location_note'] = 'Sanctuary divider wall beside the bench and planter'
cat['inscription'] = 'Apples Lord of Poop'

def camera(name, position, target, scale):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector(target) - Vector(position)).to_track_quat('-Z', 'Y').to_euler()
    data.type = 'ORTHO'
    data.ortho_scale = scale
    data.clip_end = 1000
    obj.location += obj.rotation_euler.to_quaternion() @ Vector((0, 0, 100))
    return obj

detail = camera('V07 Apples wall detail', (7, 4.5, 2.5), (-2.52, 4.5, 1.72), 3.8)
camera('V07 Apples wall context', (12, -5, 10), (-3, 6, 1.8), 21)
old_detail = bpy.data.objects.get('V03 Apples engraving detail')
if old_detail:
    old_detail.matrix_world = detail.matrix_world.copy()
    old_detail.data.type = 'ORTHO'
    old_detail.data.ortho_scale = 3.8
scene.camera = detail
scene['Revision'] = '07 — welcome sign removed; Apples engraving moved beside sanctuary bench'
bpy.context.view_layer.update()
print('Atheria updated. Press F12 to inspect the relocated engraving, then save your file.')
