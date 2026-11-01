"""Atheria revision 03. Run in Blender with the existing Atheria lobby open.
Removes placeholder people and the raised gate grid; creates two Roblox-style
stone statues and genuine recessed inscriptions, plus the supplied cat motif.
No external files or add-ons. Does not save or render automatically.
"""
import bpy
import math
from mathutils import Matrix, Vector

scene = bpy.context.scene
active_camera_name = scene.camera.name if scene.camera else '01 Overview'
if not bpy.data.objects.get('Great sacred crystal'):
    raise RuntimeError('Open the generated Atheria lobby first.')

# Repeatable update: remove only the previous objects from this update.
for obj in list(bpy.data.objects):
    if obj.name.startswith('V03 '):
        bpy.data.objects.remove(obj, do_unlink=True)
for obj in list(bpy.data.objects):
    if obj.name.startswith(('Raised portcullis', 'Portcullis crossbar')):
        bpy.data.objects.remove(obj, do_unlink=True)
people = bpy.data.collections.get('10 / People and activity placeholders')
if people:
    for obj in list(people.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)

col = bpy.data.collections.get('13 / Memorials and engravings')
if col is None:
    col = bpy.data.collections.new('13 / Memorials and engravings')
    scene.collection.children.link(col)


def mat(name, color, metallic=0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = .72
    bs.inputs['Metallic'].default_value = metallic
    return m


stone = mat('Memorial stone', (.43, .49, .52))
figure = mat('Statue carved grey stone', (.25, .30, .33))
trim = mat('Memorial bronze trim', (.48, .30, .12), .45)
incised = mat('Dark engraved recesses', (.025, .035, .04))


def mesh_object(name, verts, faces, material, transform):
    data = bpy.data.meshes.new('V03 ' + name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new('V03 ' + name, data)
    col.objects.link(obj)
    obj.matrix_world = transform.copy()
    data.materials.append(material)
    return obj


def box(name, center, size, material, transform):
    x, y, z = center
    a, b, c = [v / 2 for v in size]
    verts = [(x+sx*a, y+sy*b, z+sz*c) for sx,sy,sz in [
        (-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
        (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),
             (1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return mesh_object(name, verts, faces, material, transform)


def beam(name, start, end, width, depth, transform):
    a, b = Vector(start), Vector(end)
    local = (Matrix.Translation((a+b)/2)
             @ (b-a).to_track_quat('Z','Y').to_matrix().to_4x4())
    return box(name, (0,0,0), (width,depth,(b-a).length),
               figure, transform @ local)


def head(name, center, transform):
    x,y,z = center
    n = 24
    verts = [(x+.54*math.cos(i*math.tau/n),
              y+.54*math.sin(i*math.tau/n), z+dz)
             for dz in [-.45,.45] for i in range(n)]
    faces = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh_object(name,verts,faces,figure,transform)


def convert_mesh(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    return bpy.context.object


def subtract(plate, cutter):
    # Material slot 1 transfers dark material to the freshly cut interior faces.
    if len(plate.data.materials) < 2:
        plate.data.materials.append(incised)
    cutter.data.materials.clear()
    cutter.data.materials.append(stone)
    cutter.data.materials.append(incised)
    for face in cutter.data.polygons:
        face.material_index = 1
    mod = plate.modifiers.new('Engrave actual surface', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    bpy.ops.object.select_all(action='DESELECT')
    plate.select_set(True)
    bpy.context.view_layer.objects.active = plate
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def engrave_text(plate, transform, text, z, size, max_width, front):
    data = bpy.data.curves.new('V03 text cutter', 'FONT')
    data.body = text
    data.align_x = 'CENTER'
    data.align_y = 'CENTER'
    data.size = size
    data.extrude = .10
    obj = bpy.data.objects.new('V03 text cutter', data)
    col.objects.link(obj)
    obj = convert_mesh(obj)
    vertices = obj.data.vertices
    xmin=min(v.co.x for v in vertices); xmax=max(v.co.x for v in vertices)
    zmin=min(v.co.z for v in vertices); zmax=max(v.co.z for v in vertices)
    scale=min(1,max_width/max(.001,xmax-xmin))
    for v in vertices:
        v.co.x *= scale
        v.co.y *= scale
        v.co.z = .12*(v.co.z-zmin)/max(.001,zmax-zmin)
    obj.matrix_world = (transform @ Matrix.Translation((0,front+.025,z))
                        @ Matrix.Rotation(math.pi/2,4,'X'))
    subtract(plate,obj)


def engraving_plate(name, transform, width, height, depth, lines):
    plate=box(name,(0,0,0),(width,depth,height),stone,transform)
    for text,z,size in lines:
        engrave_text(plate,transform,text,z,size,width*.91,-depth/2)
    plate['inscription']=' '.join(line[0] for line in lines)
    plate['engraving_method']='Applied Boolean difference; recessed 0.025 m'
    plate['atheria_kind']='MEMORIAL'
    return plate


def statue(name, title, x, y, angle, mirrored=False):
    transform=(Matrix.Translation((x,y,0))
               @ Matrix.Rotation(math.radians(angle),4,'Z'))
    before=set(col.objects)
    box(name+' footing',(0,0,.42),(3.6,2.7,.34),stone,transform)
    box(name+' pedestal',(0,0,1.06),(3.0,2.0,1.0),stone,transform)
    box(name+' cap',(0,0,1.67),(3.5,2.3,.22),stone,transform)
    box(name+' bronze lower molding',(0,0,.62),(3.15,2.15,.10),trim,transform)
    for side in [-1,1]:
        box(name+' block leg',(side*.43,0,2.53),(.76,.78,1.50),figure,transform)
    box(name+' Roblox torso',(0,0,4.03),(1.64,.82,1.50),figure,transform)
    head(name+' cylindrical head',(0,0,5.23),transform)
    side=-1 if mirrored else 1
    beam(name+' lowered arm',(-side*1.05,0,4.55),(-side*1.35,0,3.45),.62,.72,transform)
    beam(name+' raised upper arm',(side*1.03,0,4.5),(side*1.58,0,4.95),.62,.72,transform)
    beam(name+' raised forearm',(side*1.58,0,4.95),(side*1.97,0,5.70),.57,.66,transform)
    box(name+' open palm',(side*1.98,0,5.83),(.50,.30,.55),figure,transform)
    for i,length in enumerate([.34,.44,.48,.39]):
        box(name+' finger',(side*(1.81+i*.112),0,6.08+length/2),
            (.085,.23,length),figure,transform)
    beam(name+' thumb',(side*1.75,0,5.75),(side*1.53,0,6.00),.15,.25,transform)
    plaque_frame=transform @ Matrix.Translation((0,-1.045,1.08))
    plaque=engraving_plate(name+' engraved dedication',plaque_frame,2.75,.78,.16,
                           [(name,.17,.28),(title,-.17,.205)])
    root=bpy.data.objects.new('V03 '+name+' STATUE',None)
    col.objects.link(root)
    root['atheria_kind']='STATUE'
    root['dedication']=name+' '+title
    root.matrix_world=Matrix.Translation((x,y,0))
    inverse=root.matrix_world.inverted()
    for obj in list(set(col.objects)-before-{root}):
        world=obj.matrix_world.copy()
        obj.parent=root
        obj.matrix_parent_inverse=Matrix.Identity(4)
        obj.matrix_basis=inverse @ world
    return root


statue('Psychopomp','Lord of Lies',-33,14,90)
statue('7ote','Lord of Truth',35,-19,-90,mirrored=True)

# The side of the sanctuary arch: local +X faces out towards the festival route.
arch_frame=(Matrix.Translation((-3,-4,.3))
            @ Matrix.Rotation(math.radians(-43),4,'Z'))
cat_frame=(arch_frame @ Matrix.Translation((4.84,0,2.5))
           @ Matrix.Rotation(math.pi/2,4,'Z'))
cat=engraving_plate('Apples cat arch carving',cat_frame,1.30,2.0,.22,
                    [('Apples',-.31,.235),('Lord of Poop',-.69,.14)])
cat['reference']='User supplied cat drawing: pointed ears, oval eyes, muzzle and four whiskers'


def cat_stroke(points, smooth=False, closed=False, thickness=.024):
    data=bpy.data.curves.new('V03 cat line cutter','CURVE')
    data.dimensions='3D'
    data.bevel_depth=thickness
    data.bevel_resolution=3
    data.use_fill_caps=True
    spline=data.splines.new('BEZIER' if smooth else 'POLY')
    if smooth:
        spline.bezier_points.add(len(points)-1)
        for p,(x,z) in zip(spline.bezier_points,points):
            p.co=(x*.58,-.105,.40+z*.58)
            p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    else:
        spline.points.add(len(points)-1)
        for p,(x,z) in zip(spline.points,points):p.co=(x*.58,-.105,.40+z*.58,1)
    spline.use_cyclic_u=closed
    obj=bpy.data.objects.new('V03 cat line cutter',data)
    col.objects.link(obj)
    obj=convert_mesh(obj)
    obj.matrix_world=cat_frame.copy()
    subtract(cat,obj)


cat_stroke([(-.58,.12),(-.43,.65),(-.27,.42),(-.15,.52),(.15,.52),
            (.32,.40),(.53,.72),(.64,.15)])
cat_stroke([(-.15,-.10),(-.30,-.12),(-.46,-.30),(-.40,-.40),
            (-.22,-.40),(-.04,-.34),(0,-.28)],smooth=True)
cat_stroke([(0,-.28),(.15,-.39),(.36,-.41),(.47,-.32),(.38,-.14)],smooth=True)
for points in [[(-.62,-.12),(-1.0,-.03)],[(-.67,-.40),(-1.0,-.47)],
               [(.62,-.10),(1.0,.04)],[(.65,-.36),(1.0,-.36)]]:
    cat_stroke(points)
for cx,cz,tilt in [(-.25,.10,.20),(.28,.10,-.20)]:
    points=[]
    for i in range(24):
        a=i*math.tau/24
        u=.09*math.cos(a);v=.035*math.sin(a)
        points.append((cx+u*math.cos(tilt)-v*math.sin(tilt),
                       cz+u*math.sin(tilt)+v*math.cos(tilt)))
    cat_stroke(points,closed=True,thickness=.019)


def detail_camera(name, position, target, scale):
    data=bpy.data.cameras.new('V03 '+name)
    obj=bpy.data.objects.new('V03 '+name,data)
    col.objects.link(obj)
    obj.location=position
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO';data.ortho_scale=scale;data.clip_end=1000
    return obj


DETAIL_CAMERAS={
 'psychopomp':detail_camera('Psychopomp detail',(-23,12,5.8),(-33,14,3.1),10.5),
 'truth':detail_camera('7ote detail',(26,-15,5.5),(35,-19,3.1),10.5),
 'cat':detail_camera('Apples engraving detail',(3.83,-10.37,3.1),(.54,-7.30,2.8),3.1),
 'gate':detail_camera('Gate without overhead grid',(12,22,10),(12,32,7.6),22.5),
}
# Broad, restrained fill keeps the carved faces legible in the courtyard shade.
for name,pos,target in [('Psychopomp',(-26,12,8),(-33,14,3)),
                        ('7ote',(29,-16,8),(35,-19,3))]:
    data=bpy.data.lights.new('V03 '+name+' soft fill','AREA')
    data.energy=450;data.shape='DISK';data.size=6;data.color=(.85,.92,1)
    obj=bpy.data.objects.new('V03 '+name+' soft fill',data)
    col.objects.link(obj);obj.location=pos
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
scene['Revision']='03 — no placeholder people or overhead grid; Roblox memorials; Apples arch engraving'
scene.camera = bpy.data.objects.get(active_camera_name) or bpy.data.objects.get('01 Overview')
bpy.context.view_layer.update()
print('Atheria revision 03 applied. Save As, and choose a V03 detail camera to inspect the engravings.')
