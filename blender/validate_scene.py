"""Read-only geometric checks for the generated Atheria blockout."""
import bpy
import json
from mathutils import Vector

scene=bpy.context.scene
depsgraph=bpy.context.evaluated_depsgraph_get()
checks=[]
connectors=[
    ('Spawn to workshop',(-18,-8),(-18,0)),
    ('Workshop to sanctuary',(-7,15),(1,15)),
    ('Sanctuary to festival',(15,0),(15,-8)),
    ('Festival to spawn',(1,-17),(-7,-17)),
    ('Diagonal sanctuary shortcut',(-6,-7),(0,-1)),
]
for label,a,b in connectors:
    av,bv=Vector((*a,1.3)),Vector((*b,1.3))
    direction=(bv-av).normalized()
    lateral=Vector((-direction.y,direction.x,0))
    for offset in [-1,0,1]:
        start=av+lateral*offset;end=bv+lateral*offset
        hit,loc,normal,index,obj,matrix=scene.ray_cast(depsgraph,start,direction,distance=(end-start).length)
        checks.append({'check':label,'lateral_offset_m':offset,'clear':not hit,'obstacle':obj.name if hit else None})

# Camera must actually see the sacred crystal, not just point in its direction.
start=scene.objects['02 Arrival crystal reveal'].matrix_world.translation
target=Vector((11,13,8.8))
hit,loc,normal,index,obj,matrix=scene.ray_cast(depsgraph,start,(target-start).normalized(),distance=100)
checks.append({'check':'Arrival camera line of sight to crystal',
               'clear':bool(hit and obj.name.startswith('Great sacred crystal')),
               'first_visible_object':obj.name if hit else None})
result={'objects':len(scene.objects),'cameras':len([o for o in scene.objects if o.type=='CAMERA']),
        'checks':checks,'all_passed':all(c['clear'] for c in checks)}
print('ATHERIA_VALIDATION',json.dumps(result,indent=2))
assert result['all_passed'], 'One or more route or landmark sightline checks failed'
