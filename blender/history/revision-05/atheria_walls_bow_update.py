"""Atheria revision 05. Run with the revision 04 lobby open in Blender 4.3+.
Rebuilds connected higher stone walls, including foundations, coping and corner
piers, and angles Psychopomp's bow to match the supplied diagonal reference.
No external files or add-ons. Inspect the result, then Save As. No auto-save.
"""
import bpy
import math
import bmesh
from mathutils import Matrix, Vector

scene=bpy.context.scene
if not bpy.data.objects.get('V04 Unified finished paving network'):
    raise RuntimeError('Open the revision 04 Atheria lobby first.')
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
old_camera=scene.camera.name if scene.camera else '01 Overview'
# Correct inward-wound original arch stones before finishing their wall joins.
for obj in scene.objects:
    if obj.type=='MESH' and 'voussoir' in obj.name:
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(obj.data);bm.free();obj.data.update()
for obj in list(bpy.data.objects):
    if obj.name.startswith('V05 '):bpy.data.objects.remove(obj,do_unlink=True)

old_wall_prefixes=('Bridge parapet','Western court divider','East court divider',
                   'North court divider','South court divider','Outer low parapet',
                   'Northern royal wall','South garden parapet')
for obj in list(bpy.data.objects):
    if obj.name.startswith(old_wall_prefixes):bpy.data.objects.remove(obj,do_unlink=True)

col=bpy.data.collections.get('15 / Connected finished walls')
if col is None:
    col=bpy.data.collections.new('15 / Connected finished walls');scene.collection.children.link(col)


def stone_material(name,c1,c2,mortar=None):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*c1,1);m.use_nodes=True
    nodes=m.node_tree.nodes;links=m.node_tree.links
    nodes.clear()
    output=nodes.new('ShaderNodeOutputMaterial');shader=nodes.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Roughness'].default_value=.84;links.new(shader.outputs['BSDF'],output.inputs['Surface'])
    uv=nodes.new('ShaderNodeTexCoord')
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=5
    noise.inputs['Detail'].default_value=2;links.new(uv.outputs['UV'],noise.inputs['Vector'])
    if mortar:
        brick=nodes.new('ShaderNodeTexBrick')
        brick.inputs['Color1'].default_value=(*c1,1);brick.inputs['Color2'].default_value=(*c2,1)
        brick.inputs['Mortar'].default_value=(*mortar,1)
        brick.inputs['Scale'].default_value=1;brick.inputs['Mortar Size'].default_value=.017
        brick.inputs['Mortar Smooth'].default_value=.01
        brick.inputs['Brick Width'].default_value=1.12;brick.inputs['Row Height'].default_value=.44
        brick.offset=.5;brick.offset_frequency=2;links.new(uv.outputs['UV'],brick.inputs['Vector'])
        links.new(brick.outputs['Color'],shader.inputs['Base Color'])
        joints=nodes.new('ShaderNodeBump');joints.invert=True
        joints.inputs['Strength'].default_value=.42;joints.inputs['Distance'].default_value=.055
        links.new(brick.outputs['Fac'],joints.inputs['Height'])
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.025
        links.new(joints.outputs['Normal'],bump.inputs['Normal'])
    else:
        mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(*c1,1);mix.inputs[2].default_value=(*c2,1)
        links.new(noise.outputs['Fac'],mix.inputs[0]);links.new(mix.outputs['Color'],shader.inputs['Base Color'])
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.018
    links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    return m


body_mat=stone_material('V05 coursed fortress stone',(.39,.45,.48),(.28,.34,.38),(.14,.19,.22))
base_mat=stone_material('V05 deep foundation stone',(.21,.27,.30),(.17,.22,.25),(.10,.14,.16))
cap_mat=stone_material('V05 dressed coping stone',(.57,.61,.61),(.46,.51,.52))


def mesh(name,verts,faces,material):
    data=bpy.data.meshes.new('V05 '+name);data.from_pydata(verts,[],faces);data.update()
    obj=bpy.data.objects.new('V05 '+name,data);col.objects.link(obj);data.materials.append(material)
    return obj


def signed_area(poly):return sum(a.x*b.y-b.x*a.y for a,b in zip(poly,poly[1:]+poly[:1]))/2


def prism(name,poly,bottom,top,material):
    poly=[Vector(p).to_2d() for p in poly]
    if signed_area(poly)<0:poly.reverse()
    n=len(poly);vs=[(p.x,p.y,z) for z in [bottom,top] for p in poly]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material)


def outline(points,width):
    points=[Vector(p) for p in points];left=[];right=[]
    for i,p in enumerate(points):
        incoming=(points[i]-points[i-1]).normalized() if i else (points[1]-p).normalized()
        outgoing=(points[i+1]-p).normalized() if i<len(points)-1 else incoming
        n0=Vector((-incoming.y,incoming.x));n1=Vector((-outgoing.y,outgoing.x))
        miter=(n0+n1).normalized();distance=(width/2)/max(.4,miter.dot(n1))
        # Ends overlap their shared nodes and the existing arch/tower masonry.
        q=p-incoming*.22 if i==0 else p+incoming*.22 if i==len(points)-1 else p
        left.append(q+miter*distance);right.append(q-miter*distance)
    return left+list(reversed(right))


left_pier=(-3-4.4*math.cos(math.radians(43)),-4+4.4*math.sin(math.radians(43)))
right_pier=(-3+4.4*math.cos(math.radians(43)),-4-4.4*math.sin(math.radians(43)))
runs=[
 ('Bridge west',[(-20.1,-39),(-20.1,-29)],2.0,.55),
 ('Bridge east',[(-13.9,-39),(-13.9,-33),(-11.5,-29)],2.0,.55),
 ('Front west',[(-37.5,-29),(-20.1,-29)],2.8,.80),
 ('Front east',[(-11.5,-29),(38,-29)],2.8,.80),
 ('Outer west',[(-37.5,-29),(-37.5,26),(-32.9,31)],3.2,.85),
 ('Outer east',[(38,-29),(38,26),(33.6,31.5)],3.2,.85),
 ('Royal west',[(-32.9,31),(.65,31)],5.0,.90),
 ('Royal east',[(23.7,32),(33.6,31.5)],5.0,.90),
 ('Workshop west',[(-37.5,-4),(-21.9,-4)],2.8,.80),
 ('Workshop east',[(-14.1,-4),(-9.4,-4),left_pier],2.8,.80),
 ('Sanctuary southwest',[left_pier,(-3,2.1),(-3,11.1)],2.8,.80),
 ('Sanctuary northwest',[(-3,18.9),(-3,31)],2.8,.80),
 ('Festival northwest',[right_pier,(3.4,-4),(11.1,-4)],2.8,.80),
 ('Festival northeast',[(18.9,-4),(38,-4)],2.8,.80),
 ('Spawn northeast',[(-3,-13.1),(-3,-10.1),right_pier],2.8,.80),
 ('Spawn southeast',[(-3,-29),(-3,-20.9)],2.8,.80),
]

layers=[[],[],[]]
for name,path,h,w in runs:
    layers[0].append(prism(name+' foundation',outline(path,w+.30),0,.40,base_mat))
    layers[1].append(prism(name+' masonry',outline(path,w),.32,h+.32,body_mat))
    layers[2].append(prism(name+' coping',outline(path,w+.22),h+.28,h+.52,cap_mat))

# Corner stones and buttresses support and conceal the physical joins.
arch_nodes=[(-21.9,-4),(-14.1,-4),(-3,11.1),(-3,18.9),(11.1,-4),(18.9,-4),
            (-3,-13.1),(-3,-20.9),left_pier,right_pier]
nodes={}
for name,path,h,w in runs:
    for p in path:
        key=(round(p[0],4),round(p[1],4));nodes[key]=max(h,nodes.get(key,0))
    for a,b in zip(path,path[1:]):
        a,b=Vector(a),Vector(b);length=(b-a).length
        for i in range(1,int(length/4)):
            p=a+(b-a)*(i/max(1,int(length/4)))
            key=(round(p.x,4),round(p.y,4));nodes[key]=max(h,nodes.get(key,0))


def square(x,y,size):return [(x-size/2,y-size/2),(x+size/2,y-size/2),(x+size/2,y+size/2),(x-size/2,y+size/2)]


for (x,y),h in nodes.items():
    if any((Vector((x,y))-Vector(p)).length<.75 for p in arch_nodes):continue
    if min((Vector((x,y))-Vector(p)).length for p in [(2.3,32),(21.7,32)])<3:continue
    layers[0].append(prism('Quoin foot',square(x,y,1.22),0,.40,base_mat))
    layers[1].append(prism('Quoin pier',square(x,y,1.02),.32,h+.40,body_mat))
    layers[2].append(prism('Quoin crown',square(x,y,1.25),h+.36,h+.62,cap_mat))


def fuse(parts,name):
    result=parts[0]
    for other in parts[1:]:
        modifier=result.modifiers.new('Join wall edges','BOOLEAN')
        modifier.operation='UNION';modifier.solver='EXACT';modifier.object=other
        bpy.context.view_layer.objects.active=result
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(other,do_unlink=True)
    result.name='V05 '+name
    uv=result.data.uv_layers.new(name='Stone courses in metres')
    result.data.update()
    for face in result.data.polygons:
        normal=face.normal
        tangent=Vector((-normal.y,normal.x,0)).normalized() if abs(normal.z)<.6 else None
        for loop_index in face.loop_indices:
            p=result.data.vertices[result.data.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv=(p.dot(tangent),p.z) if tangent is not None else (p.x,p.y)
    result['atheria_kind']='CONNECTED_WALL'
    return result


wall_objects=[fuse(parts,name) for parts,name in zip(layers,
    ['Continuous wall foundations','Joined masonry wall network','Continuous coping and corner caps'])]

# Leave a fitted recess around the existing engraved panel. Its original arch
# pier remains intact behind it, while the higher walls and coping clear it.
cat=bpy.data.objects.get('V03 Apples cat arch carving')
if cat:
    vs=[(sx*.70,sy*.20,sz*1.06) for sx,sy,sz in
        [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    niche=mesh('temporary engraving recess',vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),
                 (1,2,6,5),(2,3,7,6),(3,0,4,7)],body_mat)
    niche.matrix_world=cat.matrix_world.copy()
    for obj in wall_objects[1:]:
        modifier=obj.modifiers.new('Clear the Apples engraving','BOOLEAN')
        modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=niche
        bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(niche,do_unlink=True)
for obj in wall_objects:
    bevel=obj.modifiers.new('Dressed stone edges','BEVEL');bevel.width=.025;bevel.segments=2

# Riser stays at the block arm's grip. The bow's top leans back toward the head,
# and its lower tip points outward, following the user's marked diagonal.
torso=bpy.data.objects['V03 Psychopomp Roblox torso']
frame=torso.matrix_world.copy()
operation=(frame @ Matrix.Translation((2,-.55,5.85))
           @ Matrix.Rotation(math.radians(-55),4,'Y')
           @ Matrix.Translation((-2,.10,-5.85)) @ frame.inverted())
for name in ['V04 Psychopomp raised longbow','V04 Psychopomp bowstring','V04 Psychopomp bow grip']:
    obj=bpy.data.objects.get(name)
    if obj and not obj.get('v05_bow_pose'):
        if name.endswith('bow grip'):
            for v in obj.data.vertices:v.co.y*=.50/.22
        obj.matrix_world=operation @ obj.matrix_world
        obj['v05_bow_pose']='Diagonal -55 degrees, grip retained, reference image 4'
bpy.data.objects['V03 Psychopomp STATUE']['bow_reference_angle_degrees']=-55


def camera(name,pos,target,scale=None,lens=32):
    data=bpy.data.cameras.new('V05 '+name);obj=bpy.data.objects.new('V05 '+name,data)
    col.objects.link(obj);obj.location=pos
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.clip_end=1000;data.lens=lens
    if scale:data.type='ORTHO';data.ortho_scale=scale
    return obj


WALL_CAMERAS={
 'walls':camera('Connected walls overview',(83,-112,119),(0,1,2),112),
 'corners':camera('Connected front wall corner',(-47,-39,13),(-34,-24,2),22),
 'walljoin':camera('Wall and arch joins',(-10,-14,10),(-5,-3,2.3),24),
 'bowangle':camera('Bow reference angle',(-41,10,7),(-33,14,5.2),7.5),
}
scene['Revision']='05 — connected higher finished stone walls and diagonal reference bow pose'
scene['wall_runs']=str(runs)
scene['wall_heights']='Courtyard/front 2.8 m; outer 3.2 m; bridge 2.0 m; royal 5.0 m, plus coping'
scene.camera=bpy.data.objects.get(old_camera) or bpy.data.objects.get('01 Overview')
bpy.context.view_layer.update()
print('Atheria revision 05 applied:',len(runs),'joined wall runs; diagonal bow pose')
