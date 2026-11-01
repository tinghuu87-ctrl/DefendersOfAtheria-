"""Run in Blender with the expanded tavern scene active."""
import bpy

scene = bpy.context.scene
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

removed = []
for obj in list(scene.objects):
    in_board = any('leaderboard' in col.name.lower() for col in obj.users_collection)
    lettering = in_board and obj.type == 'FONT'
    divider = obj.name.startswith('Tavern / Leaderboard row divider')
    if lettering or divider:
        removed.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)

scene['Leaderboard'] = 'Blank framed board; reserved for future rankings'
print('Leaderboard cleared:', len(removed), 'lettering/divider objects removed.')
print('Save your Blender file to keep the change.')
