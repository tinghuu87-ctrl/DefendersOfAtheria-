"""Run in the original editable Atheria town .blend, then re-export."""
import bpy
from mathutils import Vector

scene = bpy.context.scene
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

def center(obj):
    return sum((obj.matrix_world @ Vector(p) for p in obj.bound_box), Vector()) / 8

backings = [o for o in scene.objects
            if o.name.startswith('Carved sign: FESTIVAL COURT')]
anchors = [center(o) for o in backings] or [Vector((23, -6, 2.3))]
targets = []
for obj in list(scene.objects):
    named = (obj.name.startswith('Carved sign: FESTIVAL COURT')
             or obj.name.startswith('Sign text: FESTIVAL COURT'))
    face = (obj.type == 'MESH' and obj.name.startswith('Sign face')
            and any((center(obj) - p).length < 0.5 for p in anchors))
    if named or face:
        targets.append(obj)

removed = [o.name for o in targets]
for obj in targets:
    bpy.data.objects.remove(obj, do_unlink=True)
scene['Festival Court sign'] = 'Removed backing, pale face and lettering'
print('Removed:', removed if removed else 'Sign already removed.')
print('Save this updated source and re-export with the latest Atheria exporter.')
