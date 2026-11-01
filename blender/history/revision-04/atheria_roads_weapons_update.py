"""Atheria revision 04. Run with revision 03 lobby open in Blender 4.3+.
Replaces segmented roads with a single finished paving network and continuous
kerbs; simplifies statue arms; adds a raised bow and sword; removes prototype sign.
No add-ons or external assets. Inspect, then Save As. No automatic save/render.
"""
import bpy
import math
import bmesh
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon

scene=bpy.context.scene
if not bpy.data.objects.get('V03 Psychopomp Roblox torso'):
    raise RuntimeError('Open the revision 03 Atheria lobby first.')
if bpy.context.object and bpy.context.object.mode!='OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
old_camera=scene.camera.name if scene.camera else '01 Overview'
for o in list(bpy.data.objects):
    if o.name.startswith('V04 '):bpy.data.objects.remove(o,do_unlink=True)

col=bpy.data.collections.get('14 / Finished roads and statue weapons')
if col is None:
    col=bpy.data.collections.new('14 / Finished roads and statue weapons')
    scene.collection.children.link(col)


def material(name,color,metal=0,rough=.8):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal
    p.inputs['Roughness'].default_value=rough
    return m


stone=bpy.data.materials['Statue carved grey stone']
steel=material('V04 sword faceted steel',(.38,.49,.55),.65,.32)
gold=material('V04 weapon bronze',(.53,.31,.09),.55,.4)
grip=material('V04 wrapped grips',(.12,.075,.045),0,.85)
string_mat=material('V04 bowstring',(.60,.51,.35),.1,.65)
kerb_mat=material('V04 dressed kerbstone',(.47,.46,.40))
road_mat=material('V04 continuous running bond paving',(.36,.39,.39),0,.88)
nodes=road_mat.node_tree.nodes;links=road_mat.node_tree.links
for n in list(nodes):
    if n.type not in {'BSDF_PRINCIPLED','OUTPUT_MATERIAL'}:nodes.remove(n)
shader=nodes.get('Principled BSDF')
pos=nodes.new('ShaderNodeNewGeometry')
brick=nodes.new('ShaderNodeTexBrick')
brick.inputs['Color1'].default_value=(.43,.44,.41,1)
brick.inputs['Color2'].default_value=(.29,.34,.35,1)
brick.inputs['Mortar'].default_value=(.095,.115,.12,1)
brick.inputs['Scale'].default_value=1
brick.inputs['Mortar Size'].default_value=.012
brick.inputs['Mortar Smooth'].default_value=.008
brick.inputs['Brick Width'].default_value=.58
brick.inputs['Row Height'].default_value=.34
brick.offset=.5;brick.offset_frequency=2
links.new(pos.outputs['Position'],brick.inputs['Vector'])
links.new(brick.outputs['Color'],shader.inputs['Base Color'])
bump=nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value=.32
bump.inputs['Distance'].default_value=.035
bump.invert=True
links.new(brick.outputs['Fac'],bump.inputs['Height'])
links.new(bump.outputs['Normal'],shader.inputs['Normal'])


def mesh(name,verts,faces,mat):
    data=bpy.data.meshes.new('V04 '+name);data.from_pydata(verts,[],faces);data.update()
    o=bpy.data.objects.new('V04 '+name,data);col.objects.link(o);data.materials.append(mat)
    return o


def box(name,center,size,mat,transform):
    x,y,z=center;a,b,c=[v/2 for v in size]
    vs=[(x+sx*a,y+sy*b,z+sz*c) for sx,sy,sz in
        [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    o=mesh(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    o.matrix_world=transform.copy();return o


def beam(name,a,b,width,depth,mat,transform):
    a,b=Vector(a),Vector(b)
    local=Matrix.Translation((a+b)/2)@(b-a).to_track_quat('Z','Y').to_matrix().to_4x4()
    return box(name,(0,0,0),(width,depth,(b-a).length),mat,transform@local)


def curve(name,points,radius,mat,transform,closed=False):
    data=bpy.data.curves.new('V04 '+name,'CURVE');data.dimensions='3D'
    data.resolution_u=16;data.bevel_depth=radius;data.bevel_resolution=3;data.use_fill_caps=True
    s=data.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for p,co in zip(s.bezier_points,points):
        p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    s.use_cyclic_u=closed
    o=bpy.data.objects.new('V04 '+name,data);col.objects.link(o);o.matrix_world=transform.copy()
    data.materials.append(mat);return o


# Simple, single-piece Roblox arms. No fingers, thumbs, palms or forearm joints.
for name,side in [('Psychopomp',1),('7ote',-1)]:
    torso=bpy.data.objects['V03 '+name+' Roblox torso']
    transform=torso.matrix_world.copy()
    root=bpy.data.objects['V03 '+name+' STATUE']
    prefixes=['V03 '+name+' '+part for part in
              ['lowered arm','raised upper arm','raised forearm','open palm','finger','thumb']]
    for o in list(bpy.data.objects):
        if any(o.name.startswith(p) for p in prefixes):bpy.data.objects.remove(o,do_unlink=True)
    before=set(col.objects)
    beam(name+' regular lowered Roblox arm',(-side*1.05,0,4.55),(-side*1.35,0,3.3),.70,.80,stone,transform)
    beam(name+' regular raised Roblox arm',(side*1.05,0,4.55),(side*2.0,0,5.85),.70,.80,stone,transform)
    if name=='7ote':
        x=-2.0
        beam('7ote sword grip',(x,-.05,5.53),(x,-.05,6.24),.17,.17,grip,transform)
        box('7ote sword pommel',(x,-.05,5.49),(.26,.25,.24),gold,transform)
        box('7ote sword crossguard',(x,-.05,6.26),(.98,.20,.18),gold,transform)
        vs=[]
        for zz,ww in [(6.34,.20),(8.10,.16)]:
            vs.extend([(x-ww,-.05,zz),(x,-.12,zz),(x+ww,-.05,zz),(x,.02,zz)])
        vs.append((x,-.05,8.65))
        faces=[(3,2,1,0)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
        faces += [(i+4,(i+1)%4+4,8) for i in range(4)]
        blade=mesh('7ote raised sword blade',vs,faces,steel);blade.matrix_world=transform.copy()
    else:
        curve('Psychopomp raised longbow',[(1.35,-.10,4.35),(1.75,-.10,4.70),
              (1.98,-.10,5.30),(2,-.10,5.85),(1.98,-.10,6.40),
              (1.75,-.10,7.0),(1.35,-.10,7.35)],.085,gold,transform)
        beam('Psychopomp bowstring',(1.35,-.10,4.35),(1.35,-.10,7.35),.025,.025,string_mat,transform)
        beam('Psychopomp bow grip',(2,-.10,5.60),(2,-.10,6.10),.22,.22,grip,transform)
    for o in set(col.objects)-before:
        world=o.matrix_world.copy();o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4)
        o.matrix_basis=root.matrix_world.inverted()@world
        o['atheria_kind']='STATUE_WEAPON_OR_ARM'

# Remove the prototype sign, its inset face and its lettering, retaining towers.
sign=bpy.data.objects.get('Carved sign: DEFENCE PROTOTYPES')
if sign:
    def center(o):return sum((o.matrix_world@Vector(v) for v in o.bound_box),Vector())/8
    anchor=center(sign)
    for o in list(bpy.data.objects):
        if (o.name.startswith('Sign face') and (center(o)-anchor).length<.5) or o==sign:
            bpy.data.objects.remove(o,do_unlink=True)
for o in list(bpy.data.objects):
    if o.name.startswith(('Sign text: DEFENCE PROTOTYPES','Carved sign: DEFENSE PROTOTYPES',
                          'Sign text: DEFENSE PROTOTYPES')):bpy.data.objects.remove(o,do_unlink=True)

# Remove the original independent slab roads, gold strips and floating ring sheet.
old_roads=('Primary crystal approach','Western loop','Eastern loop','Quest approach',
           'Gate approach','Continuous sanctuary promenade')
for o in list(bpy.data.objects):
    if o.name.startswith(old_roads):bpy.data.objects.remove(o,do_unlink=True)


def area(poly):return sum(a.x*b.y-b.x*a.y for a,b in zip(poly,poly[1:]+poly[:1]))/2


def prism(name,poly,bottom=.14,top=.34,mat=None):
    poly=[Vector(p).to_2d() for p in poly]
    if area(poly)<0:poly.reverse()
    n=len(poly)
    vs=[(p.x,p.y,z) for z in [bottom,top] for p in poly]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,mat or road_mat)


def rounded_line(points):
    points=[Vector(p) for p in points];out=[points[0]]
    for a,p,b in zip(points,points[1:],points[2:]):
        d=min(3.5,(a-p).length*.38,(b-p).length*.38)
        u=p+(a-p).normalized()*d;v=p+(b-p).normalized()*d
        out.append(u)
        for i in range(1,13):
            t=i/12;out.append((1-t)**2*u+2*(1-t)*t*p+t*t*v)
    out.append(points[-1]);return out


def strip(points,width):
    ps=rounded_line(points);left=[];right=[]
    for i,p in enumerate(ps):
        tangent=(ps[min(i+1,len(ps)-1)]-ps[max(i-1,0)]).normalized()
        normal=Vector((-tangent.y,tangent.x))
        left.append(p+normal*width/2);right.append(p-normal*width/2)
    return left+list(reversed(right))


def disk(cx,cy,r,n=96):
    return [Vector((cx+r*math.cos(i*math.tau/n),cy+r*math.sin(i*math.tau/n))) for i in range(n)]


specs=[
 ('arrival',[(-17,-39.5),(-17,-31),(-13.5,-27.5),(-13.5,-23),(-17,-19)],3.0),
 ('hero',[(-17,-19),(-3,-4),(6,6)],4.0),
 ('west',[(-17,-19),(-18,-4),(-18,12),(-3,15),(2.5,15)],3.5),
 ('east',[(17,6),(18,1),(15,-4),(9,-10),(8,-17),(-3,-17),(-15,-17)],3.5),
 ('quest',[(21,13),(22.1,13)],3.4),
 ('battle',[(12,22),(12,31.25)],5.0),
]
pieces=[prism('temporary '+name,strip(ps,w)) for name,ps,w in specs]
pieces.append(prism('temporary spawn apron',disk(-17,-19,3)))
# Solid annulus: the same paved surface continues around the sacred monument.
ring_vs=[];ring_fs=[];n=128
for zz in [.14,.34]:
    for radius in [7.5,10.5]:
        ring_vs += [(11+radius*math.cos(i*math.tau/n),13+radius*math.sin(i*math.tau/n),zz) for i in range(n)]
for i in range(n):
    j=(i+1)%n
    ring_fs += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
pieces.append(mesh('temporary sanctuary ring',ring_vs,ring_fs,road_mat))

road=pieces[0]
for other in pieces[1:]:
    mod=road.modifiers.new('Fuse connected road volumes','BOOLEAN')
    mod.operation='UNION';mod.solver='EXACT';mod.object=other
    bpy.context.view_layer.objects.active=road
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(other,do_unlink=True)

# Extract the union's top perimeter, including courtyard islands and crystal hole.
edge_counts={};directions={}
for face in road.data.polygons:
    if face.normal.z>.9 and all(abs(road.data.vertices[i].co.z-.34)<.0001 for i in face.vertices):
        ids=list(face.vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):
            key=tuple(sorted((a,b)));edge_counts[key]=edge_counts.get(key,0)+1;directions[key]=(a,b)
edges=[directions[e] for e,count in edge_counts.items() if count==1]
next_vertex={a:b for a,b in edges}
assert len(next_vertex)==len(edges),'Road boundary is not a set of closed contours'
loops=[]
while next_vertex:
    start=next(iter(next_vertex));i=start;loop=[]
    while True:
        loop.append(road.data.vertices[i].co.to_2d());i=next_vertex.pop(i)
        if i==start:break
    loops.append(loop)


def soften(poly):
    result=[]
    for i,p in enumerate(poly):
        a,b=poly[i-1],poly[(i+1)%len(poly)]
        va,vb=a-p,b-p
        if va.length<.00001 or vb.length<.00001:continue
        if va.normalized().dot(vb.normalized())<-.998:
            result.append(p);continue
        trim=min(.65,va.length*.24,vb.length*.24)
        u=p+va.normalized()*trim;v=p+vb.normalized()*trim
        for k in range(7):
            t=k/6;result.append((1-t)**2*u+2*(1-t)*t*p+t*t*v)
    return result


loops=[soften(loop) for loop in loops]
loops3=[[Vector((p.x,p.y,.34)) for p in loop] for loop in loops]
raw_triangles=tessellate_polygon(loops3)
flat3=[p for loop in loops3 for p in loop]
# Blender builds expose either flattened indices or coordinate vectors here.
triangles=[[flat3[i] for i in tri] if isinstance(tri[0],int) else tri for tri in raw_triangles]
flat=[p for loop in loops for p in loop]
lookup={(round(p.x,6),round(p.y,6)):i for i,p in enumerate(flat)}
count=len(flat)
verts=[(p.x,p.y,z) for z in [.14,.34] for p in flat]
faces=[]
for tri in triangles:
    ids=tuple(lookup[(round(p.x,6),round(p.y,6))] for p in tri)
    a,b,c=[Vector(verts[i]) for i in ids]
    if (b-a).cross(c-a).z<0:ids=tuple(reversed(ids))
    faces.extend([tuple(i+count for i in ids),tuple(reversed(ids))])
offset=0
for loop in loops:
    for i in range(len(loop)):
        a=offset+i;b=offset+(i+1)%len(loop)
        faces.append((a,b,b+count,a+count))
    offset+=len(loop)
finished=mesh('Unified finished paving network',verts,faces,road_mat)
bm=bmesh.new();bm.from_mesh(finished.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
assert all(e.is_manifold for e in bm.edges),'Road mesh has open or non-manifold seams'
bm.to_mesh(finished.data);bm.free();finished.data.update()
finished['atheria_kind']='FINISHED_ROAD'
finished['road_specs']=str(specs)
finished['contour_count']=len(loops)
finished['construction']='One fused watertight road with softened junction contours and shared world-space paving'
bpy.data.objects.remove(road,do_unlink=True)
# Validate triangulation area: holes must stay empty and all islands stay connected.
expected=abs(sum(area(loop) for loop in loops))
actual=sum((b-a).cross(c-a).length/2 for a,b,c in triangles)
assert abs(actual-expected)<.02,('Paving tessellation mismatch',actual,expected)

# Continuous dressed stone kerbs follow the final smoothed road perimeter.
for index,loop in enumerate(loops):
    inner=[];outer=[]
    for i,p in enumerate(loop):
        tangent=(loop[(i+1)%len(loop)]-loop[i-1]).normalized()
        normal=Vector((tangent.y,-tangent.x))
        inner.append(p+normal*.012);outer.append(p+normal*.16)
    n=len(loop);vs=[]
    for z in [.17,.40]:
        vs += [(p.x,p.y,z) for p in inner+outer]
    fs=[]
    for i in range(n):
        j=(i+1)%n
        fs += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
               (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
    kerb=mesh('Continuous kerb %02d'%index,vs,fs,kerb_mat)
    bevel=kerb.modifiers.new('Small dressed stone edge','BEVEL');bevel.width=.018;bevel.segments=2

# Set the arrival medallion into the paving rather than above it.
for o in scene.objects:
    target=.346 if o.name.startswith('Arrival compass ray') else (
        .344 if o.name.startswith('Spawn inner medallion') else
        .342 if o.name.startswith('Spawn stone medallion') else None)
    if target is not None:
        top=max((o.matrix_world@Vector(v)).z for v in o.bound_box)
        world=o.matrix_world.copy();world.translation.z+=target-top;o.matrix_world=world

# The new arrival lane needs the old spawn lamp moved into its edge pocket.
for root in scene.objects:
    if root.type=='EMPTY' and root.get('atheria_kind')=='LAMP':
        if (root.matrix_world.translation-Vector((-12,-27,0))).length<.1:
            world=root.matrix_world.copy();world.translation+=Vector((1.5,-1,0));root.matrix_world=world
for light in scene.objects:
    if light.type=='LIGHT' and light.name.startswith('Lantern light pool'):
        if (light.matrix_world.translation-Vector((-12,-26.6,3.4))).length<.1:
            light.location+=Vector((1.5,-1,0))

# Existing detail cameras now frame the raised weapons completely.
for name,pos,target,scale in [
    ('V03 Psychopomp detail',(-23,12,6.5),(-33,14,3.8),11.5),
    ('V03 7ote detail',(26,-15,6.8),(35,-19,4.3),13.5)]:
    cam=bpy.data.objects.get(name)
    if cam:
        cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.data.ortho_scale=scale


def camera(name,pos,target,scale=None,lens=30):
    data=bpy.data.cameras.new('V04 '+name);o=bpy.data.objects.new('V04 '+name,data);col.objects.link(o)
    o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    data.clip_end=1000;data.lens=lens
    if scale:data.type='ORTHO';data.ortho_scale=scale
    return o


ROAD_CAMERAS={
 'roads':camera('Roads plan',(0,-2,140),(0,-2,0),112),
 'junction':camera('Smooth junction detail',(-7,-12,15),(1,-3,.3),24),
 'arrival':camera('Arrival paving detail',(-15,-29,3.8),(-15,-19,.8),lens=27),
}
scene.camera=bpy.data.objects.get(old_camera) or bpy.data.objects.get('01 Overview')
scene['Revision']='04 — raised sword and bow; regular Roblox arms; unified finished roads; prototype sign removed'
bpy.context.view_layer.update()
print('Atheria revision 04 complete:',len(finished.data.vertices),'road vertices;',len(loops),'smooth boundary loops')
