"""DEFENDERS OF ATHERIA — Linked Courtyards, executable Blender blockout.

Tested with Blender 4.3.2. No add-ons, downloads or external textures required.

USAGE (terminal):
  blender --background --python atheria_linked_courtyards.py -- --output-dir ./atheria_output
  blender --background --python atheria_linked_courtyards.py -- --views overview entry plan --samples 48
  blender --background --python atheria_linked_courtyards.py -- --no-render

USAGE (Blender): Open this file in the Text Editor and choose Run Script.
It creates the scene, saves a .blend, and renders the overview by default.
IMPORTANT: This replaces the CURRENT scene. Run in a new Blender file.

Outputs: atheria_linked_courtyards.blend + requested PNG views + design notes.
Units: conceptual metres (not a final Roblox studs/export specification).
This is an editable, coloured architectural blockout, not a production asset kit.
All content is generated locally. Render paths can be changed with --output-dir.
"""

import argparse
import math
import os
import random
import sys
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector


def arguments():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', default=str(Path.home() / 'Atheria_Blockout_Revision05'))
    p.add_argument('--views', nargs='+', choices=['overview', 'entry', 'plan', 'sanctuary', 'psychopomp', 'truth', 'cat', 'gate', 'roads', 'junction', 'arrival', 'walls', 'corners', 'walljoin', 'bowangle'], default=['overview'])
    p.add_argument('--samples', type=int, default=48)
    p.add_argument('--resolution', type=int, default=1600, help='Image width; height is 75%% of width.')
    p.add_argument('--no-render', action='store_true')
    tail = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    return p.parse_args(tail)


ARGS = arguments()
OUT = Path(ARGS.output_dir).expanduser().resolve()
OUT.mkdir(parents=True, exist_ok=True)
RNG = random.Random(41)

# Clear scene objects, not unrelated files or assets on disk.
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
SCENE = bpy.context.scene
for col in list(bpy.data.collections):
    if col.name != 'Collection' and col.users == 0:
        bpy.data.collections.remove(col)

COL = None
XFORM = Matrix.Identity(4)
GROUP_COUNTS = {}


def grouped(kind):
    """Keep furniture and vegetation in independently editable assemblies."""
    def decorate(fn):
        @wraps(fn)
        def build(*args, **kwargs):
            before = set(COL.objects)
            anchor = XFORM @ Vector((args[0], args[1], 0))
            result = fn(*args, **kwargs)
            members = set(COL.objects) - before
            number = GROUP_COUNTS.get(kind, 0)
            GROUP_COUNTS[kind] = number + 1
            root = bpy.data.objects.new(f'{kind} | {number:02d}', None)
            COL.objects.link(root)
            root.empty_display_type = 'PLAIN_AXES'
            root.empty_display_size = .4
            root.matrix_world = Matrix.Translation(anchor)
            root['atheria_kind'] = kind
            inverse = root.matrix_world.inverted()
            for obj in members:
                world = obj.matrix_world.copy()
                obj.parent = root
                obj.matrix_parent_inverse = Matrix.Identity(4)
                obj.matrix_basis = inverse @ world
                obj['atheria_kind'] = kind
            return result
        return build
    return decorate


def collection(name):
    global COL
    COL = bpy.data.collections.new(name)
    SCENE.collection.children.link(COL)
    return COL


@contextmanager
def frame(x=0, y=0, z=0, angle=0):
    global XFORM
    previous = XFORM.copy()
    XFORM = XFORM @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(angle), 4, 'Z')
    try:
        yield
    finally:
        XFORM = previous


def material(name, rgb, roughness=.8, metal=0, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*rgb, 1)
    bs.inputs['Roughness'].default_value = roughness
    bs.inputs['Metallic'].default_value = metal
    if emission:
        bs.inputs['Emission Color'].default_value = (*rgb, 1)
        bs.inputs['Emission Strength'].default_value = emission
    return m


M = {}
for name, color in {
    'stone': (.34, .40, .46), 'stone_light': (.52, .59, .62),
    'stone_dark': (.19, .25, .30), 'plaster': (.78, .66, .46),
    'wood': (.19, .085, .041), 'wood_light': (.40, .22, .095),
    'roof_royal': (.055, .16, .28), 'roof_tavern': (.055, .28, .24),
    'roof_forge': (.30, .105, .065), 'iron': (.075, .10, .13),
    'grass': (.12, .27, .15), 'grass_light': (.28, .43, .14),
    'leaf': (.08, .25, .19), 'leaf_light': (.23, .39, .17),
    'bark': (.20, .11, .055), 'soil': (.13, .16, .14),
    'cliff': (.20, .27, .32), 'cliff_light': (.29, .34, .36),
    'canvas': (.41, .075, .30), 'canvas_light': (.78, .56, .27),
    'royal_blue': (.055, .15, .36), 'flower': (.55, .18, .40),
    'water': (.055, .28, .34), 'ink': (.055, .085, .10),
    'sign': (.83, .72, .49), 'skin': (.66, .43, .25),
}.items():
    M[name] = material(name, color)
M['gold'] = material('Old bronze and warm gold', (.67, .40, .10), .4, .55)
M['window'] = material('Occupied windows — warm amber', (1, .45, .10), .55, emission=1.3)
M['fire'] = material('Forge coals', (1, .14, .015), .7, emission=3)
M['violet'] = material('Sacred crystal — violet', (.34, .035, .85), .27, .12, .7)
M['violet_light'] = material('Sacred crystal — lavender', (.68, .23, 1), .25, .08, .9)
M['violet_dark'] = material('Sacred crystal — deep facets', (.16, .015, .45), .3, .12, .4)
M['rune'] = material('Protective inscriptions', (.53, .20, 1), .5, emission=1.8)
M['cyan'] = material('Workshop arcane prototype', (.07, .49, .62), .35, emission=.7)
PAVERS = [material('Paving variation %02d' % i, (.36+i*.014, .40+i*.014, .42+i*.012)) for i in range(6)]


def mesh(name, verts, faces, mat, bevel=0):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    COL.objects.link(obj)
    obj.matrix_world = XFORM.copy()
    mats = mat if isinstance(mat, list) else [mat]
    for m in mats:
        data.materials.append(M[m] if isinstance(m, str) else m)
    if bevel:
        mod = obj.modifiers.new('Soft blockout edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 1
    return obj


def box(name, pos, size, mat='stone', bevel=.04):
    x, y, z = pos
    a, b, c = [v/2 for v in size]
    vs = [(x+sx*a, y+sy*b, z+sz*c) for sx, sy, sz in
          [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    return mesh(name, vs, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], mat, bevel)


def cylinder(name, pos, radius, depth, mat='stone', n=12, top_radius=None):
    x, y, z = pos
    rt = radius if top_radius is None else top_radius
    vs = [(x+r*math.cos(i*math.tau/n), y+r*math.sin(i*math.tau/n), z+dz)
          for r, dz in [(radius,-depth/2),(rt,depth/2)] for i in range(n)]
    fs = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name, vs, fs, mat)


def beam(name, a, b, width, mat='wood', depth=None):
    a, b = Vector(a), Vector(b)
    length = (b-a).length
    # Mesh is made in local coordinates before the context transform is applied.
    obj = box(name, (0,0,0), (width, depth or width, length), mat)
    local = Matrix.Translation((a+b)/2) @ (b-a).to_track_quat('Z','Y').to_matrix().to_4x4()
    obj.matrix_world = XFORM @ local
    return obj


def ico(name, pos, radius, mat='leaf', subdivisions=1, scale=(1,1,1)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=radius)
    obj = bpy.context.object
    obj.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    COL.objects.link(obj)
    # Compose explicitly: matrix_world can be stale immediately after setting
    # location/scale on a newly created object in Blender's dependency graph.
    obj.matrix_world = XFORM @ Matrix.Translation(pos) @ Matrix.Diagonal((*scale,1))
    obj.data.materials.append(M[mat])
    return obj


def text(name, body, pos, size=.45, mat='sign', rot=(90,0,0), align='CENTER'):
    data = bpy.data.curves.new(name, 'FONT')
    data.body = body
    data.align_x = align
    data.align_y = 'CENTER'
    data.size = size
    data.extrude = .008
    obj = bpy.data.objects.new(name, data)
    COL.objects.link(obj)
    rotation=Euler(tuple(math.radians(v) for v in rot),'XYZ').to_matrix().to_4x4()
    obj.matrix_world = XFORM @ Matrix.Translation(pos) @ rotation
    data.materials.append(M[mat])
    return obj


def arch(name, x, y, width=7, spring=4.7, depth=1.5, z=.3, angle=0, ornament=True):
    """Open masonry arch, never a solid wall masquerading as a doorway."""
    with frame(x,y,z,angle):
        r = width/2
        thickness = .8
        for side in [-1,1]:
            box(name+' pier', (side*(r+thickness/2),0,spring/2), (thickness,depth,spring), 'stone_light', .10)
            box(name+' foot', (side*(r+thickness/2),0,.25), (thickness+.4,depth+.4,.5), 'stone_dark')
            box(name+' capital', (side*(r+.4),0,spring), (1.1,depth+.3,.35), 'gold' if ornament else 'stone')
        for i in range(11):
            a, b = i*math.pi/11+.003, (i+1)*math.pi/11-.003
            vs = [(rr*math.cos(t), yy, spring+rr*math.sin(t))
                  for yy in [-depth/2,depth/2] for rr,t in [(r,a),(r,b),(r+thickness,b),(r+thickness,a)]]
            mesh(name+' voussoir', vs, [(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)], 'stone_light', .035)
        box(name+' keystone', (0,0,spring+r+.15), (.75,depth+.2,.9), 'gold' if ornament else 'stone_light')


def wall(name, a, b, height=2.0, thickness=.65):
    a, b = Vector((*a,0)), Vector((*b,0))
    d = b-a
    with frame((a.x+b.x)/2,(a.y+b.y)/2,0,math.degrees(math.atan2(d.y,d.x))):
        box(name, (0,0,height/2+.25), (d.length,thickness,height), 'stone', .08)
        box(name+' coping', (0,0,height+.3), (d.length+.1,thickness+.25,.25), 'stone_light')
        for i in range(int(d.length/3)+1):
            x=-d.length/2 + i*d.length/max(1,int(d.length/3))
            box(name+' upright', (x,0,height/2+.3), (.6,thickness+.25,height+.4), 'stone_dark')


PATH_LAYER = 0


def path(name, points, width=3.5):
    global PATH_LAYER
    # Laid stone strips deliberately connect every functional destination.
    for a,b in zip(points,points[1:]):
        delta=Vector(b)-Vector(a)
        PATH_LAYER += 1
        with frame((a[0]+b[0])/2,(a[1]+b[1])/2,.27+PATH_LAYER*.0008,math.degrees(math.atan2(delta.y,delta.x))):
            box(name,(0,0,0),(delta.length+.3,width,.09),'stone_light',.10)
            for side in [-1,1]:
                box(name+' edge inlay',(0,side*(width/2-.12),.052),(delta.length,.055,.012),'gold',0)


def paved_court(name, center, size):
    x,y=center; w,d=size
    box(name+' foundation',(x,y,.10),(w,d,.27),'stone_dark',.20)
    # Batch the many broad paving stones into one mesh per court.
    vs=[]; fs=[]; mids=[]
    nx,ny=int(w/1.85),int(d/1.85)
    for j in range(ny):
        for i in range(nx):
            a=x-w/2+(i+.5)*w/nx; b=y-d/2+(j+.5)*d/ny
            hw,hd=w/nx/2-.035,d/ny/2-.035
            k=len(vs); zz=.245+RNG.uniform(-.012,.012)
            vs.extend([(a-hw,b-hd,zz),(a+hw,b-hd,zz),(a+hw,b+hd,zz),(a-hw,b+hd,zz)])
            fs.append((k,k+1,k+2,k+3)); mids.append(RNG.randrange(len(PAVERS)))
    obj=mesh(name+' broad paving',vs,fs,PAVERS)
    for p,mi in zip(obj.data.polygons,mids):p.material_index=mi


def promenade(cx,cy,inner=7.5,outer=10.5):
    vs=[];fs=[]
    for i in range(64):
        a=i*math.tau/64
        for r in [inner,outer]:vs.append((cx+r*math.cos(a),cy+r*math.sin(a),.34))
    for i in range(64):
        j=(i+1)%64
        fs.append((2*i,2*i+1,2*j+1,2*j))
    ob=mesh('Continuous sanctuary promenade',vs,fs,PAVERS)
    for p in ob.data.polygons:p.material_index=p.index%len(PAVERS)


def point_light(name,pos,color,power=100,radius=1):
    data=bpy.data.lights.new(name,'POINT');data.energy=power;data.color=color;data.shadow_soft_size=radius
    obj=bpy.data.objects.new(name,data);COL.objects.link(obj)
    obj.matrix_world=XFORM@Matrix.Translation(pos)
    return obj


@grouped('LAMP')
def lantern(x,y,z=0, tall=True):
    with frame(x,y,z + (.26 if tall else 0)):
        h=3.6 if tall else .5
        if tall:
            cylinder('Lantern foot',(0,0,.25),.32,.5,'stone_dark')
            beam('Lantern post',(0,0,.25),(0,0,h),.15,'wood')
            beam('Lantern bracket',(0,0,h),(0,.48,h),.12,'iron')
        box('Amber lantern',(0,.4,h-.4),(.42,.42,.65),'window')
        box('Lantern cap',(0,.4,h),(.58,.58,.15),'iron')
        for xx in [-.23,.23]:
            beam('Lantern frame',(xx,.17,h-.75),(xx,.17,h-.08),.045,'iron')


def sign(body,x,y,z=2.8,width=5.0,angle=0):
    with frame(x,y,0,angle):
        box('Carved sign: '+body,(0,0,z),(width,.18,.85),'wood')
        box('Sign face',(0,-.11,z),(width-.15,.035,.66),'sign',.02)
        text('Sign text: '+body,body,(0,-.14,z),min(.40,width/(len(body)*.65)),'ink')


def banner(x,y,z=5,angle=0,width=1.5,height=3):
    with frame(x,y,0,angle):
        beam('Banner crossbar',(-width*.65,0,z),(width*.65,0,z),.12,'gold')
        vs=[(-width/2,-.08,z),(width/2,-.08,z),(width/2,-.10,z-height+.5),(0,-.2,z-height),(-width/2,-.1,z-height+.5)]
        mesh('Atheria blue swallowtail',vs,[(0,1,2,3,4)],'royal_blue')
        # Diamond crest ties ordinary buildings to the protected crystals.
        mesh('Crystal crest',[(-.33,-.23,z-height*.46),(0,-.23,z-height*.46+.5),(.33,-.23,z-height*.46),(0,-.23,z-height*.46-.5)],[(0,1,2,3)],'gold')


def front_window(x,y,z,width=1,height=1.5):
    box('Window dark surround',(x,y,z),(width+.20,.18,height+.22),'wood')
    box('Warm occupied window',(x,y-.11,z),(width,.06,height),'window')
    box('Window vertical mullion',(x,y-.16,z),(.07,.10,height),'wood')
    box('Window horizontal mullion',(x,y-.16,z),(width,.10,.08),'wood')


def roof(name,w,d,z,rise,mat):
    # Two broad roof slopes, thick fascia and a strongly readable front gable.
    vs=[(-w/2,-d/2,z),(-w/2,d/2,z),(0,d/2,z+rise),(0,-d/2,z+rise),
        (w/2,-d/2,z),(w/2,d/2,z)]
    mesh(name,vs,[(3,2,1,0),(4,5,2,3)],mat)
    for yy in [-d/2,d/2]:
        for xx in [-w/2,w/2]:
            beam('Roof edge fascia',(xx,yy,z),(0,yy,z+rise),.27,'wood')
    beam('Roof ridge',(0,-d/2-.25,z+rise),(0,d/2+.25,z+rise),.30,'wood')
    for k in range(1,5):
        t=k/5
        for side in [-1,1]:
            xx=side*w/2*(1-t)
            beam('Broad roof course',(xx,-d/2,z+rise*t+.025),(xx,d/2,z+rise*t+.025),.055,'stone_dark')


def building(name,x,y,w,d,h,roof_mat='roof_royal',angle=0,door=True):
    with frame(x,y,.3,angle):
        box(name+' stone foundation',(0,0,.5),(w+.6,d+.6,1),'stone_dark',.12)
        box(name+' plaster mass',(0,0,h/2+.8),(w,d,h-1),'plaster',.08)
        for zz in [1.1,h*.52,h-.1]:
            box(name+' horizontal timber',(0,-d/2-.07,zz),(w+.2,.22,.30),'wood')
            box(name+' rear timber',(0,d/2+.07,zz),(w+.2,.22,.30),'wood')
            for side in [-1,1]:box(name+' side timber',(side*w/2,0,zz),(.25,d,.30),'wood')
        for xx in [-w/2,-w/4,0,w/4,w/2]:
            box(name+' facade upright',(xx,-d/2-.08,h/2),(.30,.24,h),'wood')
        for xx in [-w/2,w/2]:
            for yy in [-d/2,d/2]:box(name+' corner',(xx,yy,h/2),(.38,.38,h),'wood')
        # Side elevations stay legible from overview and neighbouring courts.
        for side in [-1,1]:
            for yy in [-d*.28,d*.28]:
                box(name+' side upright',(side*(w/2+.05),yy,h/2),(.25,.27,h),'wood')
                with frame(side*(w/2+.1),yy,0,side*90):
                    front_window(0,0,h*.73,1.1,1.5)
        gable=[(-w/2,-d/2,h),(w/2,-d/2,h),(0,-d/2,h+3.9)]
        mesh(name+' front gable',gable,[(0,1,2)],'plaster')
        mesh(name+' rear gable',[(a,d/2,c) for a,b,c in gable],[(2,1,0)],'plaster')
        roof(name+' chunky pitched roof',w+1.5,d+1.6,h,4.4,roof_mat)
        beam('Gable king post',(0,-d/2-.06,h),(0,-d/2-.06,h+3.9),.24,'wood')
        for side in [-1,1]:
            beam('Diagonal timber',(side*(w/2-.4),-d/2-.15,h*.53),(side*.5,-d/2-.15,h-.35),.22,'wood')
            front_window(side*w*.30,-d/2-.15,h*.73,1.3,1.7)
        if door:
            box(name+' doorway shadow',(0,-d/2-.12,1.7),(2.4,.20,3.1),'wood')
            for xx in [-.8,-.4,0,.4,.8]:box('Door plank',(xx,-d/2-.25,1.65),(.35,.08,2.8),'wood_light')
            arch(name+' door surround',0,-d/2-.3,2.2,2.05,.4,z=.1,ornament=False)
            cylinder('Entry step',(0,-d/2-.45,.13),1.8,.25,'stone_light',n=8)
        lantern(-w*.43,-d/2-.4,2.3,False)
        lantern(w*.43,-d/2-.4,2.3,False)


@grouped('BENCH')
def bench(x,y,angle=0):
    with frame(x,y,.26,angle):
        for xx in [-1,1]:
            box('Bench leg',(xx,0,.35),(.18,.65,.7),'iron')
            box('Bench back support',(xx,.27,.8),(.15,.15,1.5),'iron')
        for yy in [-.22,0,.22]:box('Bench seat slat',(0,yy,.75),(2.5,.17,.12),'wood_light')
        for zz in [1.12,1.42]:box('Bench back slat',(0,.29,zz),(2.5,.13,.22),'wood_light')


def barrel(x,y,z=.3):
    cylinder('Barrel',(x,y,z+.57),.46,1.14,'wood_light',n=10)
    for dz in [.16,.85]:cylinder('Barrel iron band',(x,y,z+dz),.48,.10,'iron',n=10)


@grouped('TABLE')
def table(x,y,umbrella=False):
    cylinder('Tavern table foot',(x,y,.65),.15,.8,'wood')
    cylinder('Round table',(x,y,1.13),1.1,.16,'wood_light')
    for a in [0,math.pi]:
        xx=x+1.6*math.cos(a); yy=y+1.6*math.sin(a)
        cylinder('Stool',(xx,yy,.78),.4,.15,'wood_light')
        beam('Stool leg',(xx,yy,.3),(xx,yy,.75),.18,'wood')
    if umbrella:
        beam('Parasol pole',(x,y,.3),(x,y,3.7),.10,'wood')
        cylinder('Cream canopy',(x,y,3.4),2,.8,'canvas_light',n=8,top_radius=.08)


@grouped('TREE')
def pine(x,y,h=7):
    cylinder('Pine trunk',(x,y,h*.23),.22,h*.46,'bark',n=7)
    for i in range(3):
        cylinder('Pine tier',(x,y,h*(.40+i*.17)),h*(.25-i*.05),h*.46,
                 'leaf' if i%2==0 else 'leaf_light',n=7,top_radius=.03)


@grouped('TREE')
def broadleaf(x,y,h=6):
    beam('Bent tree trunk',(x,y,.2),(x+.3,y,h*.72),.42,'bark')
    for dx,dy,dz,rr in [(0,0,.78,.34),(-.20,.05,.70,.25),(.20,-.02,.72,.25)]:
        ico('Rounded tree canopy',(x+dx*h,y+dy*h,h*dz),h*rr,'leaf_light' if dx>0 else 'leaf',2,scale=(1,1,.85))


@grouped('PLANTER')
def planter(x,y,w=3,d=1.2):
    box('Planted stone bed',(x,y,.48),(w,d,.7),'stone_dark',.10)
    box('Garden soil',(x,y,.85),(w-.2,d-.2,.08),'soil')
    for i in range(max(2,int(w))):
        xx=x+RNG.uniform(-w*.38,w*.38); yy=y+RNG.uniform(-d*.3,d*.3)
        ico('Shrub',(xx,yy,1.1),.55,'grass_light',1,scale=(1,.7,.75))
        if i%2==0:ico('Flower',(xx,yy,1.5),.18,'flower')


def person(name,x,y,angle=0,guard=False,pose='idle'):
    with frame(x,y,.30,angle):
        cloth='royal_blue' if guard else RNG.choice(['canvas','wood_light','roof_tavern'])
        cylinder(name+' tunic',(0,0,.95),.28,.65,cloth,n=8,top_radius=.36)
        ico(name+' head',(0,0,1.63),.22,'skin',2)
        for side in [-1,1]:
            foot_y=.12*side if pose=='walk' else 0
            beam(name+' leg',(side*.15,0,.75),(side*.17,foot_y,.18),.15,'iron')
            box(name+' boot',(side*.17,foot_y-.07,.10),(.21,.34,.2),'wood')
            end=(side*.45,-.18,1.05) if pose!='work' else (side*.38,-.5,1.45)
            beam(name+' arm',(side*.32,0,1.25),end,.15,cloth)
            ico(name+' hand',end,.10,'skin')
        if guard:
            cylinder(name+' helmet',(0,0,1.79),.245,.20,'iron',n=8,top_radius=.12)
            beam(name+' spear',(.48,0,.15),(.48,0,2.8),.055,'wood')
            cylinder(name+' spear tip',(.48,0,2.9),.1,.35,'gold',n=4,top_radius=0)


NOTES = '''DEFENDERS OF ATHERIA / LINKED COURTYARDS / DESIGN INTENT

ESTABLISHED LORE: Heroes defend Atheria. Sacred crystals seal an ancient evil.
Monster hordes seek to destroy the crystals and release that evil.
The lobby is a proposed fortified sanctuary and preparation settlement.
The named services and districts are design proposals, not new fixed lore.

1 WHY INTERESTING: An immediately visible crystal, short preparation routes,
   discoverable districts, framed reveals through arches, and contrasting scales.
2 STRUCTURES: Shared chunky stone/timber construction; distinct building masses,
   roofs, chimneys, royal spire, open workshop props and seasonal canvas.
3 DISTINCT PLACES: Cool violet sanctuary; amber forge; teal welcoming tavern;
   plum/gold festival. Identity is architectural as well as colour-coded.
4 LIFE: Tables, benches, supplies, bunting, gardens and occupied windows.
   Placeholder people were removed in revision 03; ambient animation is future work.
5 ATTENTION: Crystal is the identity landmark; battle gate is the action landmark.
   Arches, paving, bronze inlays, elevated gate and restrained signs guide players.
6 TEXTURES: Broad paving joints, masonry courses, simplified roof courses, visible
   timber framing and planted edges. Material colours stand in for painterly art.
7 IMPLEMENTATION: Modular editable meshes in functional collections, five open
   connectors, a diagonal shortcut and full peripheral loop. Scenes use no add-ons.

COURT GRAPH: Spawn -> Workshop -> Sanctuary -> Festival -> Spawn is the loop.
Spawn -> Sanctuary is the short primary route through the diagonal hero arch.
Workshop and quest hall are services; Battle Gate is the main departure.
Archways are actual openings. Buildings have visible facade entrances but their
interiors are deliberately solid blockout masses. No gameplay, rigging, animation,
navigation mesh, collision export or Roblox scripts are included.

READINESS: Evaluate scale, camera, routes and spawn sightline in Roblox Studio
before production modelling. Units here are metres, not final Roblox stud scale.
All geometry/materials are original procedural placeholders. A static render can
suggest activity; it does not implement moving crowds, flickering lights or audio.

CAMERAS: overview = spatial concept; entry = arriving player; plan = topology;
sanctuary = court-level perspective. Revision 03 contains two static Roblox-style memorial statues.
Render uses Cycles CPU for portable headless use. All generation is deterministic.
'''


# ---------------------------------------------------------------------------
# 01 TERRAIN — inhabited plateau with a clear edge, not an empty flat plane.
# ---------------------------------------------------------------------------
collection('01 / Terrain and landscape')
outline=[(-41,-29),(-38,27),(-27,37),(27,38),(42,25),(41,-28),(29,-36),(-23,-36)]
vs=[]
for scale,zz in [(0.75,-12),(.94,-8),(1.02,-3),(1,0)]:
    vs.extend([(x*scale,y*scale,zz+RNG.uniform(-.3,.3) if zz else zz) for x,y in outline])
fs=[tuple(reversed(range(24,32))),tuple(range(8))]
for ring in range(3):
    for i in range(8):
        a=ring*8+i; b=ring*8+(i+1)%8
        fs += [(b+8,b,a),(a+8,b+8,a)]
rock=mesh('Faceted sanctuary plateau',vs,fs,['grass','cliff','cliff_light'])
for p in rock.data.polygons:p.material_index=0 if p.index==0 else 1+(p.index%3==0)
for i in range(30):
    a=RNG.uniform(0,math.tau)
    x=math.cos(a)*39; y=math.sin(a)*32
    if y < -29 and abs(x+16)<8:continue
    ico('Cliff shoulder',(x,y,-7),RNG.uniform(2,4),'cliff_light',1,scale=(1,1,1.7))

# ---------------------------------------------------------------------------
# 02 COURTS AND ROUTES — all connectors remain unobstructed.
# ---------------------------------------------------------------------------
collection('02 / Courts and circulation')
paved_court('Spawn Court',(-19,-17),(32,24))
paved_court('Workshop Court',(-21,13),(30,32))
paved_court('Sanctuary Court',(17,14),(40,34))
paved_court('Festival Court',(18,-17),(36,24))
path('Primary crystal approach',[(-17,-19),(-3,-4),(5,4)],4.0)
promenade(11,13)
path('Western loop',[(-17,-19),(-18,-4),(-18,12),(-3,15),(1,15)],3.5)
path('Eastern loop',[(19,6),(15,-4),(9,-10),(8,-17),(-3,-17),(-15,-17)],3.5)
path('Quest approach',[(21,13),(24,13)],3.4)
path('Gate approach',[(12,23),(12,33)],5.0)
# Arrival bridge and a tiny set of steps over the plateau edge.
box('Arrival bridge masonry',(-17,-34,-.15),(6,12,.65),'stone_dark',.1)
for yy in [-38,-35,-32]:
    for xx in [-20, -14]:
        cylinder('Bridge pillar',(xx,yy,-4.2),.75,8,'stone_dark',n=8)
for xx in [-20.1,-13.9]:wall('Bridge parapet',(xx,-39),(xx,-29),1,.45)
cylinder('Spawn stone medallion',(-17,-19,.33),2.3,.12,'gold',n=16)
cylinder('Spawn inner medallion',(-17,-19,.40),2.05,.05,'stone_light',n=16)
for a in range(0,360,45):
    with frame(-17,-19,.44,a):
        mesh('Arrival compass ray',[(0,1.3,0),(-.16,.5,0),(.16,.5,0)],[(0,1,2)],'gold')

# ---------------------------------------------------------------------------
# 03 ARCHES — five connectors; low dividers preserve orientation and camera.
# ---------------------------------------------------------------------------
collection('03 / Walls arches and gate')
wall('Western court divider',(-37,-4),(-23,-4),2)
wall('Western court divider',(-13,-4),(-9,-4),2)
wall('East court divider',(4,-4),(10,-4),2)
wall('East court divider',(20,-4),(38,-4),2)
wall('North court divider',(-3,2),(-3,10),2.1)
wall('North court divider',(-3,20),(-3,30),2.1)
wall('South court divider',(-3,-29),(-3,-22),1.5)
wall('South court divider',(-3,-12),(-3,-10),1.5)
arch('Workshop approach',-18,-4,7,4,1.1,ornament=False)
arch('Workshop to sanctuary',-3,15,7,4,1.1,angle=90,ornament=False)
arch('Festival approach',15,-4,7,4,1.1,ornament=False)
arch('Garden lane',-3,-17,7,3.8,1.1,angle=90,ornament=False)
arch('Hero crystal reveal',-3,-4,8,4.4,1.5,angle=-43)
with frame(-3,-4,0,-43):
    banner(-5,-.2,6.4,0,1.1,2.7)
    banner(5,-.2,6.4,0,1.1,2.7)
    sign('SANCTUARY',0,-.9,8.3,5.4)
for x in [-37.5,38]:
    wall('Outer low parapet',(x,-27),(x,29),1.8)
wall('Northern royal wall',(-37,31),(-.5,31),5)
wall('Northern royal wall',(24.5,32),(38,32),5)
wall('South garden parapet',(-36,-29),(-22,-29),1.2)
wall('South garden parapet',(-12,-29),(37,-29),1.2)
arch('Battle Gate',12,32,12,7.5,3,z=.3)
for x in [2.3,21.7]:
    cylinder('Gate tower',(x,32,6.0),2.5,11.5,'stone',n=10)
    cylinder('Tower crown',(x,32,11.9),2.8,.7,'stone_light',n=10)
    cylinder('Gate slate spire',(x,32,14.4),2.9,4.4,'roof_royal',n=10,top_radius=.05)
    for i in range(8):
        a=i*math.tau/8
        box('Tower merlon',(x+2.4*math.cos(a),32+2.4*math.sin(a),12.6),(.7,.7,1.1),'stone_light')
    banner(x,29.45,10,0,1.7,4.2)
sign('BATTLE GATE',12,30.2,12.9,8)
# Closed arched double doors, fitted inside the existing stone opening.
for side in [-1, 1]:
    xs = [side * (5.90 * i / 16) for i in range(17)]
    xs.sort()
    if side < 0: xs[-1] = -.045
    else: xs[0] = .045
    profile = [(xs[0], .27), (xs[-1], .27)]
    profile += [(x, 7.8 + math.sqrt(36-x*x) - .12) for x in reversed(xs)]
    verts = [(12+x, yy, zz) for yy in [31.70,32.30] for x,zz in profile]
    n = len(profile)
    faces = [tuple(range(n)), tuple(reversed(range(n,2*n)))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    door = mesh('Closed gate left' if side<0 else 'Closed gate right',verts,faces,'wood_light',.035)
    door['atheria_kind'] = 'GATE'
    for dx in [side*.35, side*2.3, side*4.3, side*5.5]:
        height=7.8+math.sqrt(36-dx*dx)-.20
        box('Gate vertical ironwork',(12+dx,31.63,(height+.30)/2),(.10,.12,height-.30),'iron')
    for zz in [1.4,4.1,6.7]:
        box('Gate strap',(12+side*3,31.58,zz),(5.6,.18,.28),'iron')
    cylinder('Gate handle plate',(12+side*.65,31.45,3.6),.20,.15,'gold',n=8)
box('Gate centre lock',(12,31.46,3.6),(.65,.25,.8),'gold')
box('Gate threshold',(12,31.8,.28),(11.8,1.0,.08),'stone_dark')
box('Road beyond battle gate',(12,36,.18),(11,8,.2),'stone_dark')

# ---------------------------------------------------------------------------
# 04 SANCTUARY — sacred monument; routes go around, not through its base.
# ---------------------------------------------------------------------------
collection('04 / Sacred crystal sanctuary')
with frame(11,13,0):
    for radius,z,depth in [(7,.39,.3),(6.2,.65,.3),(5.3,.93,.3),(3.1,1.30,.45),(2.65,1.7,.4)]:
        cylinder('Sanctuary concentric step',(0,0,z),radius,depth,'stone_light',n=16)
    cylinder('Bronze plinth',(0,0,2.08),2.4,.45,'gold',n=8)
    crystal_mats=['violet','violet_light','violet_dark']
    def crystal(name,cx,cy,base,height,radius):
        n=6;vv=[(cx,cy,base)]
        for rr,zz,off in [(radius*.8,height*.18,0),(radius,height*.54,0),(radius*.57,height*.83,.10)]:
            vv.extend([(cx+rr*math.cos(i*math.tau/n+off),cy+rr*math.sin(i*math.tau/n+off),base+zz) for i in range(n)])
        vv.append((cx-.15*radius,cy,base+height))
        ff=[]
        for i in range(n):
            j=(i+1)%n
            ff.extend([(0,1+j,1+i),(1+i,1+j,7+j),(1+i,7+j,7+i),
                       (7+i,7+j,13+j,13+i),(13+i,13+j,19)])
        ob=mesh(name,vv,ff,crystal_mats)
        for face in ob.data.polygons:face.material_index=(face.index*7)%3
    crystal('Great sacred crystal',0,0,2.1,10.8,2.15)
    for i in range(6):
        a=i*math.tau/6
        ax,ay=math.cos(a),math.sin(a)
        beam('Bronze crystal cradle',(ax*2.4,ay*2.4,1.9),(ax*2.9,ay*2.9,4.2),.28,'gold')
        beam('Bronze cradle tip',(ax*2.9,ay*2.9,4.2),(ax*2.0,ay*2.0,5.1),.22,'gold')
        crystal('Outer ward crystal',ax*5.6,ay*5.6,.9,1.7,.40)
    for i in range(16):
        a=i*math.tau/16
        with frame(4.0*math.cos(a),4.0*math.sin(a),1.12,math.degrees(a)):
            mesh('Ward rune',[(-.16,0,0),(0,.32,0),(.16,0,0),(0,-.32,0)],[(0,1,2,3)],'rune')
    point_light('Crystal spill',(0,0,6.3),(.48,.16,1),650,3)
    for x,y in [(-11.5,-4.7),(20,-7.5),(-9,8),(7,15)]:planter(x,y,2.7,1.2)
    for x,y,a in [(-9,11,90),(12,13,0),(16,-9,-120),(-11,-6.5,145)]:bench(x,y,a)
    sign('THE SACRED SEAL',0,-6.5,1.25,5.5)

# ---------------------------------------------------------------------------
# 05 WORKSHOP — functional silhouettes: chimney, forge, defence prototypes.
# ---------------------------------------------------------------------------
collection('05 / Forge and defence workshop')
building('Forge',-24,23,17,9,7.5,'roof_forge',door=False)
with frame(-24,23,.3):
    box('Open forge recess',(0,-4.64,2.1),(6,.12,3.4),'iron')
    arch('Forge hearth surround',0,-4.8,4.4,1.9,.6,z=.1,ornament=False)
    box('Glowing forge coals',(0,-4.9,.8),(3.7,1,.3),'fire')
    box('Forge hood',(0,-2.8,6.0),(5,3,2),'stone_dark')
    box('Large forge chimney',(-5,1,8.5),(2,2,13),'stone_dark',.12)
    for zz in [5,9,13.5]:box('Chimney collar',(-5,1,zz),(2.35,2.35,.4),'stone_light')
    sign('FORGE & WORKSHOP',0,-5.2,6.3,11)
    point_light('Warm forge interior',(0,-5.2,2.5),(1,.24,.045),400,2)
    for xx in [-6,6]:barrel(xx,-5.7)
    # Static smoke masses are explicitly blockout placeholders for future VFX.
    for k in range(3):ico('Smoke volume placeholder',(-5+.3*k,1,15+k*.7),.65+k*.18,'stone_light',1)
box('Anvil block',(-23,12,.9),(1.4,1.2,1.2),'wood')
box('Anvil foot',(-23,12,1.65),(1.4,.8,.25),'iron')
box('Anvil body',(-23,12,2),(1,.65,.5),'iron')
box('Anvil face',(-23,12,2.3),(1.7,.85,.18),'iron')
beam('Anvil horn',(-23.5,12,2.25),(-24.2,12,2.15),.35,'iron')
for xx in [-32,-29]:
    box('Supply crate',(xx,10,.9),(1.8,1.8,1.2),'wood_light')
    for yy in [9.1,10.9]:beam('Crate diagonal',(xx-.8,yy,.4),(xx+.8,yy,1.45),.12,'wood')
# Display towers help this read as tower defence, even without text.
for x,y in [(-29,3),(-11,7)]:
    cylinder('Prototype display plinth',(x,y,.5),2,.5,'stone_dark',n=8)
with frame(-29,3,.7):
    box('Bolt tower timber base',(0,0,1.3),(2.4,2.4,2.6),'wood')
    box('Bolt tower deck',(0,0,2.8),(3.1,3.1,.35),'wood_light')
    cylinder('Bolt swivel',(0,0,3.2),.65,.6,'iron')
    beam('Ballista stock',(0,-1.7,3.6),(0,1.3,3.6),.30,'wood')
    beam('Ballista left limb',(-1.8,.5,3.7),(0,-.25,3.6),.20,'wood_light')
    beam('Ballista right limb',(1.8,.5,3.7),(0,-.25,3.6),.20,'wood_light')
    beam('Ballista bowstring',(-1.8,.5,3.7),(0,1.2,3.6),.035,'iron')
    beam('Ballista bowstring',(1.8,.5,3.7),(0,1.2,3.6),.035,'iron')
with frame(-11,7,.7):
    cylinder('Arcane prototype base',(0,0,1.3),1.3,2.6,'stone',n=6,top_radius=.8)
    cylinder('Arcane bronze crown',(0,0,2.8),1.4,.4,'gold',n=6)
    ico('Arcane prototype orb',(0,0,3.7),.75,'cyan',2)
    for a in range(0,360,120):
        rad=math.radians(a)
        beam('Prototype claw',(1.1*math.cos(rad),1.1*math.sin(rad),2.9),
             (1.0*math.cos(rad),1.0*math.sin(rad),4.3),.14,'gold')
sign('DEFENCE PROTOTYPES',-21,1.2,1.1,7.8)

# ---------------------------------------------------------------------------
# 06 QUEST HALL — royal roof, spire and map instead of generic shop signage.
# ---------------------------------------------------------------------------
collection('06 / Quest hall and war map')
building('Quest Hall',29,16,12,12,9,'roof_royal',angle=-90)
with frame(29,16,.3,-90):
    for xx in [-4.5,4.5]:banner(xx,-6.3,7,0,1.2,3.2)
    sign('QUEST HALL',0,-6.45,4.9,6.5)
    box('Royal bell turret',(0,1,12.2),(2.4,2.4,3.3),'wood')
    cylinder('Quest hall spire',(0,1,16),2.1,4.5,'roof_royal',n=4,top_radius=0)
    beam('Spire finial',(0,1,18.2),(0,1,19.4),.12,'gold')
    front_window(0,-.3,12.8,1.2,1.4)
with frame(21,22,0,-75):
    box('War map stand',(0,0,1.5),(3.5,.3,2.4),'wood')
    box('War map parchment',(0,-.18,1.7),(3.1,.05,1.8),'sign')
    beam('Map left leg',(-1.3,0,.3),(-1.3,0,2.7),.15,'wood')
    beam('Map right leg',(1.3,0,.3),(1.3,0,2.7),.15,'wood')
    for xx,zz in [(-1,1.1),(-.3,1.5),(.5,1.7),(1,2.2)]:
        ico('Map campaign marker',(xx,-.25,zz),.11,'canvas')
    text('Map caption','DEFEND ATHERIA',(0,-.25,2.33),.21,'ink')

# ---------------------------------------------------------------------------
# 07 SPAWN AND TAVERN — warm human scale, seating and a protected garden.
# ---------------------------------------------------------------------------
collection('07 / Tavern and welcome court')
building('Tavern',-29,-18,13,12,7.3,'roof_tavern',angle=90)
with frame(-29,-18,.3,90):
    sign('THE LANTERN TAVERN',0,-6.25,4.7,10)
    box('Tavern awning',(0,-7.3,3.7),(10,2.8,.22),'roof_tavern')
    for xx in [-4.6,4.6]:beam('Awning post',(xx,-8.3,0),(xx,-8.3,3.8),.22,'wood')
    box('Tavern chimney',(-4,2,8),(1.3,1.3,6),'stone_dark')
for x,y in [(-18,-25),(-23.5,-8)]:table(x,y,umbrella=(y==-25))
for x,y in [(-19,-11),(-25,-26)]:barrel(x,y)
planter(-8,-26.8,3,1.4)
broadleaf(-29,-7.5,4.8)
bench(-10,-25,180)
sign('WELCOME TO ATHERIA',-17,-29,3,8)
# Orientation board is modest and near spawn, not a floating screen.
with frame(-9,-20,0,20):
    for xx in [-1.5,1.5]:beam('Wayfinding posts',(xx,0,.3),(xx,0,3.2),.15,'wood')
    box('Orientation board',(0,0,2.4),(3.8,.22,1.4),'wood')
    text('Orientation labels','SANCTUARY  /  BATTLE GATE\nWORKSHOP  /  TAVERN',(0,-.14,2.4),.21,'sign')

# ---------------------------------------------------------------------------
# 08 FESTIVAL COURT — distinct canvas silhouette and a changeable side space.
# ---------------------------------------------------------------------------
collection('08 / Festival garden and market')
def stall(x,y,angle=0,variant=0):
    with frame(x,y,.3,angle):
        for xx in [-2.3,2.3]:
            for yy in [-1.5,1.5]:beam('Festival tent post',(xx,yy,0),(xx,yy,3.2),.14,'wood')
        box('Market counter',(0,-1.1,1.0),(4.8,.8,1.5),'wood_light')
        vs=[(-2.8,-2,3.2),(2.8,-2,3.2),(2.8,2,3.2),(-2.8,2,3.2),(0,0,5.2)]
        ob=mesh('Plum and gold canopy',vs,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],['canvas','canvas_light'])
        for p in ob.data.polygons:p.material_index=(p.index+variant)%2
        for xx in [-1.5,0,1.5]:ico('Market goods',(xx,-1.1,2),.35,'canvas_light')
        cylinder('Canopy finial',(0,0,5.4),.12,.5,'gold',n=6,top_radius=0)
stall(27,-22,-30)
stall(31,-11,-100,1)
stall(13,-26,0,1)
with frame(17,-16,0):
    cylinder('Garden fountain step',(0,0,.45),2.5,.4,'stone_light',n=12)
    cylinder('Fountain basin',(0,0,.85),2.05,.5,'stone_dark',n=12)
    cylinder('Fountain water surface',(0,0,1.12),1.8,.04,'water',n=16)
    cylinder('Fountain central pedestal',(0,0,1.6),.45,1.1,'stone_light',n=8)
    cylinder('Fountain upper bowl',(0,0,2.1),.9,.3,'gold',n=12)
for a,b in [((5,-25),(31,-25)),((31,-25),(33,-7)),((5,-25),(5,-10))]:
    for xx,yy in [a,b]:beam('Bunting pole',(xx,yy,.3),(xx,yy,6),.12,'wood')
    last=None
    for i in range(15):
        t=i/14; xx=a[0]*(1-t)+b[0]*t; yy=a[1]*(1-t)+b[1]*t; zz=6-1.0*math.sin(math.pi*t)
        if last:beam('Bunting rope',last,(xx,yy,zz),.028,'wood')
        last=(xx,yy,zz)
        if 0<i<14:
            mesh('Festival pennant',[(xx-.3,yy,zz),(xx+.3,yy,zz),(xx,yy,zz-.65)],[(0,1,2)],'canvas' if i%2 else 'canvas_light')
bench(7,-23,135)
bench(24,-8.5,-45)
planter(4,-27,4,1.4)
sign('FESTIVAL COURT',23,-6,2.3,7)

# ---------------------------------------------------------------------------
# 09 LIVED-IN EDGES — selective detail; paths and hero views stay clear.
# ---------------------------------------------------------------------------
collection('09 / Vegetation lights and furnishings')
for x,y,h in [(-34,0,6),(-25,34.8,7),(-12,34.8,6.5),(30,35.0,6),(34,27.5,6.5)]:pine(x,y,h)
for x,y,h in [(-9,25,4.8),(34,-26,4.5),(32,1,5)]:broadleaf(x,y,h)
for x,y,w in [(-28,-1,4),(-8,21,3),(5,27,4),(29,26,3),(26,-1,4),(-33,7,3)]:planter(x,y,w,1.4)
LAMP_POSITIONS=[(-12,-27),(-24,-5.8),(-25.5,3),(-8,2.5),(-9,19),(4.5,24),
                (18,25.5),(21,1),(34,6),(5,-11),(24,-26.5),(34,-16)]
for x,y in LAMP_POSITIONS:lantern(x,y)
for x,y in LAMP_POSITIONS[::3]:point_light('Lantern light pool',(x,y+.4,3.4),(1,.57,.21),80,1.2)
# Deliberate small planted pockets replace random wall/roof intersections.
for cx,cy in [(-34,9),(-29,34.5),(-17,35),(35,25),(34,-24),(-8,27)]:
    for i in range(4):
        x=cx+RNG.uniform(-.55,.55);y=cy+RNG.uniform(-.35,.35)
        ico('Boundary planting',(x,y,.35),RNG.uniform(.20,.38),'grass_light',1,scale=(1,1,.55))

# Ground captions are an optional design overlay, hidden in beauty renders.
overlay=collection('11 / OPTIONAL planning labels (hidden)')
for body,x,y in [('SPAWN COURT',-17,-16),('WORKSHOP COURT',-21,16),('SANCTUARY COURT',11,3),('FESTIVAL COURT',18,-11)]:
    text('Planning caption',body,(x,y,.39),.72,'gold',rot=(0,0,0))
overlay.hide_render=True
overlay.hide_viewport=True

# ---------------------------------------------------------------------------
# 12 CAMERAS, LIGHT AND OUTPUT
# ---------------------------------------------------------------------------
collection('12 / Cameras and lighting')
world=bpy.data.worlds.new('Atheria cool daylight')
SCENE.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.26,.39,.56,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.45

def area(name,pos,energy,size,color,target):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color
    ob=bpy.data.objects.new(name,data);COL.objects.link(ob);ob.location=pos
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()

sun_data=bpy.data.lights.new('Warm late afternoon sun','SUN')
sun_data.energy=2.3;sun_data.angle=math.radians(18);sun_data.color=(1,.84,.65)
sun=bpy.data.objects.new('Warm late afternoon sun',sun_data);COL.objects.link(sun)
sun.rotation_euler=(math.radians(26),math.radians(-25),math.radians(-32))
area('Large soft sky fill',(-30,-15,55),2300,45,(.63,.78,1),(0,0,0))
area('Warm front bounce',(10,-45,30),1600,35,(1,.74,.44),(0,0,3))

def camera(name,pos,target,ortho=None,lens=25):
    data=bpy.data.cameras.new(name);obj=bpy.data.objects.new(name,data);COL.objects.link(obj)
    obj.location=pos;obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.clip_end=1000;data.clip_start=.08
    if ortho:data.type='ORTHO';data.ortho_scale=ortho
    else:data.lens=lens
    return obj

CAMS={
    'overview':camera('01 Overview',(83,-112,119),(0,1,2),ortho=112),
    'entry':camera('02 Arrival crystal reveal',(-16,-22,2.4),(3,3,5.4),lens=24),
    'plan':camera('03 Top plan',(0,1,150),(0,1,0),ortho=112),
    'sanctuary':camera('04 Sanctuary life',(1,-.5,3.6),(13,15,6.3),lens=21),
}

# Self-contained revision 03 additions, also supplied as an in-place patch.
REVISION_03_UPDATE = '"""Atheria revision 03. Run in Blender with the existing Atheria lobby open.\nRemoves placeholder people and the raised gate grid; creates two Roblox-style\nstone statues and genuine recessed inscriptions, plus the supplied cat motif.\nNo external files or add-ons. Does not save or render automatically.\n"""\nimport bpy\nimport math\nfrom mathutils import Matrix, Vector\n\nscene = bpy.context.scene\nactive_camera_name = scene.camera.name if scene.camera else \'01 Overview\'\nif not bpy.data.objects.get(\'Great sacred crystal\'):\n    raise RuntimeError(\'Open the generated Atheria lobby first.\')\n\n# Repeatable update: remove only the previous objects from this update.\nfor obj in list(bpy.data.objects):\n    if obj.name.startswith(\'V03 \'):\n        bpy.data.objects.remove(obj, do_unlink=True)\nfor obj in list(bpy.data.objects):\n    if obj.name.startswith((\'Raised portcullis\', \'Portcullis crossbar\')):\n        bpy.data.objects.remove(obj, do_unlink=True)\npeople = bpy.data.collections.get(\'10 / People and activity placeholders\')\nif people:\n    for obj in list(people.all_objects):\n        bpy.data.objects.remove(obj, do_unlink=True)\n\ncol = bpy.data.collections.get(\'13 / Memorials and engravings\')\nif col is None:\n    col = bpy.data.collections.new(\'13 / Memorials and engravings\')\n    scene.collection.children.link(col)\n\n\ndef mat(name, color, metallic=0):\n    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)\n    m.diffuse_color = (*color, 1)\n    m.use_nodes = True\n    bs = m.node_tree.nodes.get(\'Principled BSDF\')\n    bs.inputs[\'Base Color\'].default_value = (*color, 1)\n    bs.inputs[\'Roughness\'].default_value = .72\n    bs.inputs[\'Metallic\'].default_value = metallic\n    return m\n\n\nstone = mat(\'Memorial stone\', (.43, .49, .52))\nfigure = mat(\'Statue carved grey stone\', (.25, .30, .33))\ntrim = mat(\'Memorial bronze trim\', (.48, .30, .12), .45)\nincised = mat(\'Dark engraved recesses\', (.025, .035, .04))\n\n\ndef mesh_object(name, verts, faces, material, transform):\n    data = bpy.data.meshes.new(\'V03 \' + name)\n    data.from_pydata(verts, [], faces)\n    data.update()\n    obj = bpy.data.objects.new(\'V03 \' + name, data)\n    col.objects.link(obj)\n    obj.matrix_world = transform.copy()\n    data.materials.append(material)\n    return obj\n\n\ndef box(name, center, size, material, transform):\n    x, y, z = center\n    a, b, c = [v / 2 for v in size]\n    verts = [(x+sx*a, y+sy*b, z+sz*c) for sx,sy,sz in [\n        (-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),\n        (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]\n    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),\n             (1,2,6,5),(2,3,7,6),(3,0,4,7)]\n    return mesh_object(name, verts, faces, material, transform)\n\n\ndef beam(name, start, end, width, depth, transform):\n    a, b = Vector(start), Vector(end)\n    local = (Matrix.Translation((a+b)/2)\n             @ (b-a).to_track_quat(\'Z\',\'Y\').to_matrix().to_4x4())\n    return box(name, (0,0,0), (width,depth,(b-a).length),\n               figure, transform @ local)\n\n\ndef head(name, center, transform):\n    x,y,z = center\n    n = 24\n    verts = [(x+.54*math.cos(i*math.tau/n),\n              y+.54*math.sin(i*math.tau/n), z+dz)\n             for dz in [-.45,.45] for i in range(n)]\n    faces = [tuple(reversed(range(n))),tuple(range(n,2*n))]\n    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]\n    return mesh_object(name,verts,faces,figure,transform)\n\n\ndef convert_mesh(obj):\n    bpy.ops.object.select_all(action=\'DESELECT\')\n    obj.select_set(True)\n    bpy.context.view_layer.objects.active = obj\n    bpy.ops.object.convert(target=\'MESH\')\n    return bpy.context.object\n\n\ndef subtract(plate, cutter):\n    # Material slot 1 transfers dark material to the freshly cut interior faces.\n    if len(plate.data.materials) < 2:\n        plate.data.materials.append(incised)\n    cutter.data.materials.clear()\n    cutter.data.materials.append(stone)\n    cutter.data.materials.append(incised)\n    for face in cutter.data.polygons:\n        face.material_index = 1\n    mod = plate.modifiers.new(\'Engrave actual surface\', \'BOOLEAN\')\n    mod.operation = \'DIFFERENCE\'\n    mod.solver = \'EXACT\'\n    mod.object = cutter\n    bpy.ops.object.select_all(action=\'DESELECT\')\n    plate.select_set(True)\n    bpy.context.view_layer.objects.active = plate\n    bpy.ops.object.modifier_apply(modifier=mod.name)\n    bpy.data.objects.remove(cutter, do_unlink=True)\n\n\ndef engrave_text(plate, transform, text, z, size, max_width, front):\n    data = bpy.data.curves.new(\'V03 text cutter\', \'FONT\')\n    data.body = text\n    data.align_x = \'CENTER\'\n    data.align_y = \'CENTER\'\n    data.size = size\n    data.extrude = .10\n    obj = bpy.data.objects.new(\'V03 text cutter\', data)\n    col.objects.link(obj)\n    obj = convert_mesh(obj)\n    vertices = obj.data.vertices\n    xmin=min(v.co.x for v in vertices); xmax=max(v.co.x for v in vertices)\n    zmin=min(v.co.z for v in vertices); zmax=max(v.co.z for v in vertices)\n    scale=min(1,max_width/max(.001,xmax-xmin))\n    for v in vertices:\n        v.co.x *= scale\n        v.co.y *= scale\n        v.co.z = .12*(v.co.z-zmin)/max(.001,zmax-zmin)\n    obj.matrix_world = (transform @ Matrix.Translation((0,front+.025,z))\n                        @ Matrix.Rotation(math.pi/2,4,\'X\'))\n    subtract(plate,obj)\n\n\ndef engraving_plate(name, transform, width, height, depth, lines):\n    plate=box(name,(0,0,0),(width,depth,height),stone,transform)\n    for text,z,size in lines:\n        engrave_text(plate,transform,text,z,size,width*.91,-depth/2)\n    plate[\'inscription\']=\' \'.join(line[0] for line in lines)\n    plate[\'engraving_method\']=\'Applied Boolean difference; recessed 0.025 m\'\n    plate[\'atheria_kind\']=\'MEMORIAL\'\n    return plate\n\n\ndef statue(name, title, x, y, angle, mirrored=False):\n    transform=(Matrix.Translation((x,y,0))\n               @ Matrix.Rotation(math.radians(angle),4,\'Z\'))\n    before=set(col.objects)\n    box(name+\' footing\',(0,0,.42),(3.6,2.7,.34),stone,transform)\n    box(name+\' pedestal\',(0,0,1.06),(3.0,2.0,1.0),stone,transform)\n    box(name+\' cap\',(0,0,1.67),(3.5,2.3,.22),stone,transform)\n    box(name+\' bronze lower molding\',(0,0,.62),(3.15,2.15,.10),trim,transform)\n    for side in [-1,1]:\n        box(name+\' block leg\',(side*.43,0,2.53),(.76,.78,1.50),figure,transform)\n    box(name+\' Roblox torso\',(0,0,4.03),(1.64,.82,1.50),figure,transform)\n    head(name+\' cylindrical head\',(0,0,5.23),transform)\n    side=-1 if mirrored else 1\n    beam(name+\' lowered arm\',(-side*1.05,0,4.55),(-side*1.35,0,3.45),.62,.72,transform)\n    beam(name+\' raised upper arm\',(side*1.03,0,4.5),(side*1.58,0,4.95),.62,.72,transform)\n    beam(name+\' raised forearm\',(side*1.58,0,4.95),(side*1.97,0,5.70),.57,.66,transform)\n    box(name+\' open palm\',(side*1.98,0,5.83),(.50,.30,.55),figure,transform)\n    for i,length in enumerate([.34,.44,.48,.39]):\n        box(name+\' finger\',(side*(1.81+i*.112),0,6.08+length/2),\n            (.085,.23,length),figure,transform)\n    beam(name+\' thumb\',(side*1.75,0,5.75),(side*1.53,0,6.00),.15,.25,transform)\n    plaque_frame=transform @ Matrix.Translation((0,-1.045,1.08))\n    plaque=engraving_plate(name+\' engraved dedication\',plaque_frame,2.75,.78,.16,\n                           [(name,.17,.28),(title,-.17,.205)])\n    root=bpy.data.objects.new(\'V03 \'+name+\' STATUE\',None)\n    col.objects.link(root)\n    root[\'atheria_kind\']=\'STATUE\'\n    root[\'dedication\']=name+\' \'+title\n    root.matrix_world=Matrix.Translation((x,y,0))\n    inverse=root.matrix_world.inverted()\n    for obj in list(set(col.objects)-before-{root}):\n        world=obj.matrix_world.copy()\n        obj.parent=root\n        obj.matrix_parent_inverse=Matrix.Identity(4)\n        obj.matrix_basis=inverse @ world\n    return root\n\n\nstatue(\'Psychopomp\',\'Lord of Lies\',-33,14,90)\nstatue(\'7ote\',\'Lord of Truth\',35,-19,-90,mirrored=True)\n\n# The side of the sanctuary arch: local +X faces out towards the festival route.\narch_frame=(Matrix.Translation((-3,-4,.3))\n            @ Matrix.Rotation(math.radians(-43),4,\'Z\'))\ncat_frame=(arch_frame @ Matrix.Translation((4.84,0,2.5))\n           @ Matrix.Rotation(math.pi/2,4,\'Z\'))\ncat=engraving_plate(\'Apples cat arch carving\',cat_frame,1.30,2.0,.22,\n                    [(\'Apples\',-.31,.235),(\'Lord of Poop\',-.69,.14)])\ncat[\'reference\']=\'User supplied cat drawing: pointed ears, oval eyes, muzzle and four whiskers\'\n\n\ndef cat_stroke(points, smooth=False, closed=False, thickness=.024):\n    data=bpy.data.curves.new(\'V03 cat line cutter\',\'CURVE\')\n    data.dimensions=\'3D\'\n    data.bevel_depth=thickness\n    data.bevel_resolution=3\n    data.use_fill_caps=True\n    spline=data.splines.new(\'BEZIER\' if smooth else \'POLY\')\n    if smooth:\n        spline.bezier_points.add(len(points)-1)\n        for p,(x,z) in zip(spline.bezier_points,points):\n            p.co=(x*.58,-.105,.40+z*.58)\n            p.handle_left_type=\'AUTO\';p.handle_right_type=\'AUTO\'\n    else:\n        spline.points.add(len(points)-1)\n        for p,(x,z) in zip(spline.points,points):p.co=(x*.58,-.105,.40+z*.58,1)\n    spline.use_cyclic_u=closed\n    obj=bpy.data.objects.new(\'V03 cat line cutter\',data)\n    col.objects.link(obj)\n    obj=convert_mesh(obj)\n    obj.matrix_world=cat_frame.copy()\n    subtract(cat,obj)\n\n\ncat_stroke([(-.58,.12),(-.43,.65),(-.27,.42),(-.15,.52),(.15,.52),\n            (.32,.40),(.53,.72),(.64,.15)])\ncat_stroke([(-.15,-.10),(-.30,-.12),(-.46,-.30),(-.40,-.40),\n            (-.22,-.40),(-.04,-.34),(0,-.28)],smooth=True)\ncat_stroke([(0,-.28),(.15,-.39),(.36,-.41),(.47,-.32),(.38,-.14)],smooth=True)\nfor points in [[(-.62,-.12),(-1.0,-.03)],[(-.67,-.40),(-1.0,-.47)],\n               [(.62,-.10),(1.0,.04)],[(.65,-.36),(1.0,-.36)]]:\n    cat_stroke(points)\nfor cx,cz,tilt in [(-.25,.10,.20),(.28,.10,-.20)]:\n    points=[]\n    for i in range(24):\n        a=i*math.tau/24\n        u=.09*math.cos(a);v=.035*math.sin(a)\n        points.append((cx+u*math.cos(tilt)-v*math.sin(tilt),\n                       cz+u*math.sin(tilt)+v*math.cos(tilt)))\n    cat_stroke(points,closed=True,thickness=.019)\n\n\ndef detail_camera(name, position, target, scale):\n    data=bpy.data.cameras.new(\'V03 \'+name)\n    obj=bpy.data.objects.new(\'V03 \'+name,data)\n    col.objects.link(obj)\n    obj.location=position\n    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat(\'-Z\',\'Y\').to_euler()\n    data.type=\'ORTHO\';data.ortho_scale=scale;data.clip_end=1000\n    return obj\n\n\nDETAIL_CAMERAS={\n \'psychopomp\':detail_camera(\'Psychopomp detail\',(-23,12,5.8),(-33,14,3.1),10.5),\n \'truth\':detail_camera(\'7ote detail\',(26,-15,5.5),(35,-19,3.1),10.5),\n \'cat\':detail_camera(\'Apples engraving detail\',(3.83,-10.37,3.1),(.54,-7.30,2.8),3.1),\n \'gate\':detail_camera(\'Gate without overhead grid\',(12,22,10),(12,32,7.6),22.5),\n}\n# Broad, restrained fill keeps the carved faces legible in the courtyard shade.\nfor name,pos,target in [(\'Psychopomp\',(-26,12,8),(-33,14,3)),\n                        (\'7ote\',(29,-16,8),(35,-19,3))]:\n    data=bpy.data.lights.new(\'V03 \'+name+\' soft fill\',\'AREA\')\n    data.energy=450;data.shape=\'DISK\';data.size=6;data.color=(.85,.92,1)\n    obj=bpy.data.objects.new(\'V03 \'+name+\' soft fill\',data)\n    col.objects.link(obj);obj.location=pos\n    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat(\'-Z\',\'Y\').to_euler()\nscene[\'Revision\']=\'03 — no placeholder people or overhead grid; Roblox memorials; Apples arch engraving\'\nscene.camera = bpy.data.objects.get(active_camera_name) or bpy.data.objects.get(\'01 Overview\')\nbpy.context.view_layer.update()\nprint(\'Atheria revision 03 applied. Save As, and choose a V03 detail camera to inspect the engravings.\')\n'
exec(compile(REVISION_03_UPDATE, 'atheria_memorials_update.py', 'exec'), globals())
CAMS.update(DETAIL_CAMERAS)


# Revision 04 is embedded to keep this generator self-contained.
REVISION_04_UPDATE = '"""Atheria revision 04. Run with revision 03 lobby open in Blender 4.3+.\nReplaces segmented roads with a single finished paving network and continuous\nkerbs; simplifies statue arms; adds a raised bow and sword; removes prototype sign.\nNo add-ons or external assets. Inspect, then Save As. No automatic save/render.\n"""\nimport bpy\nimport math\nimport bmesh\nfrom mathutils import Matrix, Vector\nfrom mathutils.geometry import tessellate_polygon\n\nscene=bpy.context.scene\nif not bpy.data.objects.get(\'V03 Psychopomp Roblox torso\'):\n    raise RuntimeError(\'Open the revision 03 Atheria lobby first.\')\nif bpy.context.object and bpy.context.object.mode!=\'OBJECT\':\n    bpy.ops.object.mode_set(mode=\'OBJECT\')\nold_camera=scene.camera.name if scene.camera else \'01 Overview\'\nfor o in list(bpy.data.objects):\n    if o.name.startswith(\'V04 \'):bpy.data.objects.remove(o,do_unlink=True)\n\ncol=bpy.data.collections.get(\'14 / Finished roads and statue weapons\')\nif col is None:\n    col=bpy.data.collections.new(\'14 / Finished roads and statue weapons\')\n    scene.collection.children.link(col)\n\n\ndef material(name,color,metal=0,rough=.8):\n    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)\n    m.diffuse_color=(*color,1);m.use_nodes=True\n    p=m.node_tree.nodes.get(\'Principled BSDF\')\n    p.inputs[\'Base Color\'].default_value=(*color,1)\n    p.inputs[\'Metallic\'].default_value=metal\n    p.inputs[\'Roughness\'].default_value=rough\n    return m\n\n\nstone=bpy.data.materials[\'Statue carved grey stone\']\nsteel=material(\'V04 sword faceted steel\',(.38,.49,.55),.65,.32)\ngold=material(\'V04 weapon bronze\',(.53,.31,.09),.55,.4)\ngrip=material(\'V04 wrapped grips\',(.12,.075,.045),0,.85)\nstring_mat=material(\'V04 bowstring\',(.60,.51,.35),.1,.65)\nkerb_mat=material(\'V04 dressed kerbstone\',(.47,.46,.40))\nroad_mat=material(\'V04 continuous running bond paving\',(.36,.39,.39),0,.88)\nnodes=road_mat.node_tree.nodes;links=road_mat.node_tree.links\nfor n in list(nodes):\n    if n.type not in {\'BSDF_PRINCIPLED\',\'OUTPUT_MATERIAL\'}:nodes.remove(n)\nshader=nodes.get(\'Principled BSDF\')\npos=nodes.new(\'ShaderNodeNewGeometry\')\nbrick=nodes.new(\'ShaderNodeTexBrick\')\nbrick.inputs[\'Color1\'].default_value=(.43,.44,.41,1)\nbrick.inputs[\'Color2\'].default_value=(.29,.34,.35,1)\nbrick.inputs[\'Mortar\'].default_value=(.095,.115,.12,1)\nbrick.inputs[\'Scale\'].default_value=1\nbrick.inputs[\'Mortar Size\'].default_value=.012\nbrick.inputs[\'Mortar Smooth\'].default_value=.008\nbrick.inputs[\'Brick Width\'].default_value=.58\nbrick.inputs[\'Row Height\'].default_value=.34\nbrick.offset=.5;brick.offset_frequency=2\nlinks.new(pos.outputs[\'Position\'],brick.inputs[\'Vector\'])\nlinks.new(brick.outputs[\'Color\'],shader.inputs[\'Base Color\'])\nbump=nodes.new(\'ShaderNodeBump\')\nbump.inputs[\'Strength\'].default_value=.32\nbump.inputs[\'Distance\'].default_value=.035\nbump.invert=True\nlinks.new(brick.outputs[\'Fac\'],bump.inputs[\'Height\'])\nlinks.new(bump.outputs[\'Normal\'],shader.inputs[\'Normal\'])\n\n\ndef mesh(name,verts,faces,mat):\n    data=bpy.data.meshes.new(\'V04 \'+name);data.from_pydata(verts,[],faces);data.update()\n    o=bpy.data.objects.new(\'V04 \'+name,data);col.objects.link(o);data.materials.append(mat)\n    return o\n\n\ndef box(name,center,size,mat,transform):\n    x,y,z=center;a,b,c=[v/2 for v in size]\n    vs=[(x+sx*a,y+sy*b,z+sz*c) for sx,sy,sz in\n        [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]\n    o=mesh(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)\n    o.matrix_world=transform.copy();return o\n\n\ndef beam(name,a,b,width,depth,mat,transform):\n    a,b=Vector(a),Vector(b)\n    local=Matrix.Translation((a+b)/2)@(b-a).to_track_quat(\'Z\',\'Y\').to_matrix().to_4x4()\n    return box(name,(0,0,0),(width,depth,(b-a).length),mat,transform@local)\n\n\ndef curve(name,points,radius,mat,transform,closed=False):\n    data=bpy.data.curves.new(\'V04 \'+name,\'CURVE\');data.dimensions=\'3D\'\n    data.resolution_u=16;data.bevel_depth=radius;data.bevel_resolution=3;data.use_fill_caps=True\n    s=data.splines.new(\'BEZIER\');s.bezier_points.add(len(points)-1)\n    for p,co in zip(s.bezier_points,points):\n        p.co=co;p.handle_left_type=\'AUTO\';p.handle_right_type=\'AUTO\'\n    s.use_cyclic_u=closed\n    o=bpy.data.objects.new(\'V04 \'+name,data);col.objects.link(o);o.matrix_world=transform.copy()\n    data.materials.append(mat);return o\n\n\n# Simple, single-piece Roblox arms. No fingers, thumbs, palms or forearm joints.\nfor name,side in [(\'Psychopomp\',1),(\'7ote\',-1)]:\n    torso=bpy.data.objects[\'V03 \'+name+\' Roblox torso\']\n    transform=torso.matrix_world.copy()\n    root=bpy.data.objects[\'V03 \'+name+\' STATUE\']\n    prefixes=[\'V03 \'+name+\' \'+part for part in\n              [\'lowered arm\',\'raised upper arm\',\'raised forearm\',\'open palm\',\'finger\',\'thumb\']]\n    for o in list(bpy.data.objects):\n        if any(o.name.startswith(p) for p in prefixes):bpy.data.objects.remove(o,do_unlink=True)\n    before=set(col.objects)\n    beam(name+\' regular lowered Roblox arm\',(-side*1.05,0,4.55),(-side*1.35,0,3.3),.70,.80,stone,transform)\n    beam(name+\' regular raised Roblox arm\',(side*1.05,0,4.55),(side*2.0,0,5.85),.70,.80,stone,transform)\n    if name==\'7ote\':\n        x=-2.0\n        beam(\'7ote sword grip\',(x,-.05,5.53),(x,-.05,6.24),.17,.17,grip,transform)\n        box(\'7ote sword pommel\',(x,-.05,5.49),(.26,.25,.24),gold,transform)\n        box(\'7ote sword crossguard\',(x,-.05,6.26),(.98,.20,.18),gold,transform)\n        vs=[]\n        for zz,ww in [(6.34,.20),(8.10,.16)]:\n            vs.extend([(x-ww,-.05,zz),(x,-.12,zz),(x+ww,-.05,zz),(x,.02,zz)])\n        vs.append((x,-.05,8.65))\n        faces=[(3,2,1,0)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]\n        faces += [(i+4,(i+1)%4+4,8) for i in range(4)]\n        blade=mesh(\'7ote raised sword blade\',vs,faces,steel);blade.matrix_world=transform.copy()\n    else:\n        curve(\'Psychopomp raised longbow\',[(1.35,-.10,4.35),(1.75,-.10,4.70),\n              (1.98,-.10,5.30),(2,-.10,5.85),(1.98,-.10,6.40),\n              (1.75,-.10,7.0),(1.35,-.10,7.35)],.085,gold,transform)\n        beam(\'Psychopomp bowstring\',(1.35,-.10,4.35),(1.35,-.10,7.35),.025,.025,string_mat,transform)\n        beam(\'Psychopomp bow grip\',(2,-.10,5.60),(2,-.10,6.10),.22,.22,grip,transform)\n    for o in set(col.objects)-before:\n        world=o.matrix_world.copy();o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4)\n        o.matrix_basis=root.matrix_world.inverted()@world\n        o[\'atheria_kind\']=\'STATUE_WEAPON_OR_ARM\'\n\n# Remove the prototype sign, its inset face and its lettering, retaining towers.\nsign=bpy.data.objects.get(\'Carved sign: DEFENCE PROTOTYPES\')\nif sign:\n    def center(o):return sum((o.matrix_world@Vector(v) for v in o.bound_box),Vector())/8\n    anchor=center(sign)\n    for o in list(bpy.data.objects):\n        if (o.name.startswith(\'Sign face\') and (center(o)-anchor).length<.5) or o==sign:\n            bpy.data.objects.remove(o,do_unlink=True)\nfor o in list(bpy.data.objects):\n    if o.name.startswith((\'Sign text: DEFENCE PROTOTYPES\',\'Carved sign: DEFENSE PROTOTYPES\',\n                          \'Sign text: DEFENSE PROTOTYPES\')):bpy.data.objects.remove(o,do_unlink=True)\n\n# Remove the original independent slab roads, gold strips and floating ring sheet.\nold_roads=(\'Primary crystal approach\',\'Western loop\',\'Eastern loop\',\'Quest approach\',\n           \'Gate approach\',\'Continuous sanctuary promenade\')\nfor o in list(bpy.data.objects):\n    if o.name.startswith(old_roads):bpy.data.objects.remove(o,do_unlink=True)\n\n\ndef area(poly):return sum(a.x*b.y-b.x*a.y for a,b in zip(poly,poly[1:]+poly[:1]))/2\n\n\ndef prism(name,poly,bottom=.14,top=.34,mat=None):\n    poly=[Vector(p).to_2d() for p in poly]\n    if area(poly)<0:poly.reverse()\n    n=len(poly)\n    vs=[(p.x,p.y,z) for z in [bottom,top] for p in poly]\n    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]\n    fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]\n    return mesh(name,vs,fs,mat or road_mat)\n\n\ndef rounded_line(points):\n    points=[Vector(p) for p in points];out=[points[0]]\n    for a,p,b in zip(points,points[1:],points[2:]):\n        d=min(3.5,(a-p).length*.38,(b-p).length*.38)\n        u=p+(a-p).normalized()*d;v=p+(b-p).normalized()*d\n        out.append(u)\n        for i in range(1,13):\n            t=i/12;out.append((1-t)**2*u+2*(1-t)*t*p+t*t*v)\n    out.append(points[-1]);return out\n\n\ndef strip(points,width):\n    ps=rounded_line(points);left=[];right=[]\n    for i,p in enumerate(ps):\n        tangent=(ps[min(i+1,len(ps)-1)]-ps[max(i-1,0)]).normalized()\n        normal=Vector((-tangent.y,tangent.x))\n        left.append(p+normal*width/2);right.append(p-normal*width/2)\n    return left+list(reversed(right))\n\n\ndef disk(cx,cy,r,n=96):\n    return [Vector((cx+r*math.cos(i*math.tau/n),cy+r*math.sin(i*math.tau/n))) for i in range(n)]\n\n\nspecs=[\n (\'arrival\',[(-17,-39.5),(-17,-31),(-13.5,-27.5),(-13.5,-23),(-17,-19)],3.0),\n (\'hero\',[(-17,-19),(-3,-4),(6,6)],4.0),\n (\'west\',[(-17,-19),(-18,-4),(-18,12),(-3,15),(2.5,15)],3.5),\n (\'east\',[(17,6),(18,1),(15,-4),(9,-10),(8,-17),(-3,-17),(-15,-17)],3.5),\n (\'quest\',[(21,13),(22.1,13)],3.4),\n (\'battle\',[(12,22),(12,31.25)],5.0),\n]\npieces=[prism(\'temporary \'+name,strip(ps,w)) for name,ps,w in specs]\npieces.append(prism(\'temporary spawn apron\',disk(-17,-19,3)))\n# Solid annulus: the same paved surface continues around the sacred monument.\nring_vs=[];ring_fs=[];n=128\nfor zz in [.14,.34]:\n    for radius in [7.5,10.5]:\n        ring_vs += [(11+radius*math.cos(i*math.tau/n),13+radius*math.sin(i*math.tau/n),zz) for i in range(n)]\nfor i in range(n):\n    j=(i+1)%n\n    ring_fs += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),\n                (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]\npieces.append(mesh(\'temporary sanctuary ring\',ring_vs,ring_fs,road_mat))\n\nroad=pieces[0]\nfor other in pieces[1:]:\n    mod=road.modifiers.new(\'Fuse connected road volumes\',\'BOOLEAN\')\n    mod.operation=\'UNION\';mod.solver=\'EXACT\';mod.object=other\n    bpy.context.view_layer.objects.active=road\n    bpy.ops.object.modifier_apply(modifier=mod.name)\n    bpy.data.objects.remove(other,do_unlink=True)\n\n# Extract the union\'s top perimeter, including courtyard islands and crystal hole.\nedge_counts={};directions={}\nfor face in road.data.polygons:\n    if face.normal.z>.9 and all(abs(road.data.vertices[i].co.z-.34)<.0001 for i in face.vertices):\n        ids=list(face.vertices)\n        for a,b in zip(ids,ids[1:]+ids[:1]):\n            key=tuple(sorted((a,b)));edge_counts[key]=edge_counts.get(key,0)+1;directions[key]=(a,b)\nedges=[directions[e] for e,count in edge_counts.items() if count==1]\nnext_vertex={a:b for a,b in edges}\nassert len(next_vertex)==len(edges),\'Road boundary is not a set of closed contours\'\nloops=[]\nwhile next_vertex:\n    start=next(iter(next_vertex));i=start;loop=[]\n    while True:\n        loop.append(road.data.vertices[i].co.to_2d());i=next_vertex.pop(i)\n        if i==start:break\n    loops.append(loop)\n\n\ndef soften(poly):\n    result=[]\n    for i,p in enumerate(poly):\n        a,b=poly[i-1],poly[(i+1)%len(poly)]\n        va,vb=a-p,b-p\n        if va.length<.00001 or vb.length<.00001:continue\n        if va.normalized().dot(vb.normalized())<-.998:\n            result.append(p);continue\n        trim=min(.65,va.length*.24,vb.length*.24)\n        u=p+va.normalized()*trim;v=p+vb.normalized()*trim\n        for k in range(7):\n            t=k/6;result.append((1-t)**2*u+2*(1-t)*t*p+t*t*v)\n    return result\n\n\nloops=[soften(loop) for loop in loops]\nloops3=[[Vector((p.x,p.y,.34)) for p in loop] for loop in loops]\nraw_triangles=tessellate_polygon(loops3)\nflat3=[p for loop in loops3 for p in loop]\n# Blender builds expose either flattened indices or coordinate vectors here.\ntriangles=[[flat3[i] for i in tri] if isinstance(tri[0],int) else tri for tri in raw_triangles]\nflat=[p for loop in loops for p in loop]\nlookup={(round(p.x,6),round(p.y,6)):i for i,p in enumerate(flat)}\ncount=len(flat)\nverts=[(p.x,p.y,z) for z in [.14,.34] for p in flat]\nfaces=[]\nfor tri in triangles:\n    ids=tuple(lookup[(round(p.x,6),round(p.y,6))] for p in tri)\n    a,b,c=[Vector(verts[i]) for i in ids]\n    if (b-a).cross(c-a).z<0:ids=tuple(reversed(ids))\n    faces.extend([tuple(i+count for i in ids),tuple(reversed(ids))])\noffset=0\nfor loop in loops:\n    for i in range(len(loop)):\n        a=offset+i;b=offset+(i+1)%len(loop)\n        faces.append((a,b,b+count,a+count))\n    offset+=len(loop)\nfinished=mesh(\'Unified finished paving network\',verts,faces,road_mat)\nbm=bmesh.new();bm.from_mesh(finished.data)\nbmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)\nbmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)\nbmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))\nassert all(e.is_manifold for e in bm.edges),\'Road mesh has open or non-manifold seams\'\nbm.to_mesh(finished.data);bm.free();finished.data.update()\nfinished[\'atheria_kind\']=\'FINISHED_ROAD\'\nfinished[\'road_specs\']=str(specs)\nfinished[\'contour_count\']=len(loops)\nfinished[\'construction\']=\'One fused watertight road with softened junction contours and shared world-space paving\'\nbpy.data.objects.remove(road,do_unlink=True)\n# Validate triangulation area: holes must stay empty and all islands stay connected.\nexpected=abs(sum(area(loop) for loop in loops))\nactual=sum((b-a).cross(c-a).length/2 for a,b,c in triangles)\nassert abs(actual-expected)<.02,(\'Paving tessellation mismatch\',actual,expected)\n\n# Continuous dressed stone kerbs follow the final smoothed road perimeter.\nfor index,loop in enumerate(loops):\n    inner=[];outer=[]\n    for i,p in enumerate(loop):\n        tangent=(loop[(i+1)%len(loop)]-loop[i-1]).normalized()\n        normal=Vector((tangent.y,-tangent.x))\n        inner.append(p+normal*.012);outer.append(p+normal*.16)\n    n=len(loop);vs=[]\n    for z in [.17,.40]:\n        vs += [(p.x,p.y,z) for p in inner+outer]\n    fs=[]\n    for i in range(n):\n        j=(i+1)%n\n        fs += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),\n               (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]\n    kerb=mesh(\'Continuous kerb %02d\'%index,vs,fs,kerb_mat)\n    bevel=kerb.modifiers.new(\'Small dressed stone edge\',\'BEVEL\');bevel.width=.018;bevel.segments=2\n\n# Set the arrival medallion into the paving rather than above it.\nfor o in scene.objects:\n    target=.346 if o.name.startswith(\'Arrival compass ray\') else (\n        .344 if o.name.startswith(\'Spawn inner medallion\') else\n        .342 if o.name.startswith(\'Spawn stone medallion\') else None)\n    if target is not None:\n        top=max((o.matrix_world@Vector(v)).z for v in o.bound_box)\n        world=o.matrix_world.copy();world.translation.z+=target-top;o.matrix_world=world\n\n# The new arrival lane needs the old spawn lamp moved into its edge pocket.\nfor root in scene.objects:\n    if root.type==\'EMPTY\' and root.get(\'atheria_kind\')==\'LAMP\':\n        if (root.matrix_world.translation-Vector((-12,-27,0))).length<.1:\n            world=root.matrix_world.copy();world.translation+=Vector((1.5,-1,0));root.matrix_world=world\nfor light in scene.objects:\n    if light.type==\'LIGHT\' and light.name.startswith(\'Lantern light pool\'):\n        if (light.matrix_world.translation-Vector((-12,-26.6,3.4))).length<.1:\n            light.location+=Vector((1.5,-1,0))\n\n# Existing detail cameras now frame the raised weapons completely.\nfor name,pos,target,scale in [\n    (\'V03 Psychopomp detail\',(-23,12,6.5),(-33,14,3.8),11.5),\n    (\'V03 7ote detail\',(26,-15,6.8),(35,-19,4.3),13.5)]:\n    cam=bpy.data.objects.get(name)\n    if cam:\n        cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat(\'-Z\',\'Y\').to_euler()\n        cam.data.ortho_scale=scale\n\n\ndef camera(name,pos,target,scale=None,lens=30):\n    data=bpy.data.cameras.new(\'V04 \'+name);o=bpy.data.objects.new(\'V04 \'+name,data);col.objects.link(o)\n    o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat(\'-Z\',\'Y\').to_euler()\n    data.clip_end=1000;data.lens=lens\n    if scale:data.type=\'ORTHO\';data.ortho_scale=scale\n    return o\n\n\nROAD_CAMERAS={\n \'roads\':camera(\'Roads plan\',(0,-2,140),(0,-2,0),112),\n \'junction\':camera(\'Smooth junction detail\',(-7,-12,15),(1,-3,.3),24),\n \'arrival\':camera(\'Arrival paving detail\',(-15,-29,3.8),(-15,-19,.8),lens=27),\n}\nscene.camera=bpy.data.objects.get(old_camera) or bpy.data.objects.get(\'01 Overview\')\nscene[\'Revision\']=\'04 — raised sword and bow; regular Roblox arms; unified finished roads; prototype sign removed\'\nbpy.context.view_layer.update()\nprint(\'Atheria revision 04 complete:\',len(finished.data.vertices),\'road vertices;\',len(loops),\'smooth boundary loops\')\n'
exec(compile(REVISION_04_UPDATE, 'atheria_roads_weapons_update.py', 'exec'), globals())
CAMS.update(ROAD_CAMERAS)


# Self-contained revision 05 wall and bow update.
REVISION_05_UPDATE = '"""Atheria revision 05. Run with the revision 04 lobby open in Blender 4.3+.\nRebuilds connected higher stone walls, including foundations, coping and corner\npiers, and angles Psychopomp\'s bow to match the supplied diagonal reference.\nNo external files or add-ons. Inspect the result, then Save As. No auto-save.\n"""\nimport bpy\nimport math\nimport bmesh\nfrom mathutils import Matrix, Vector\n\nscene=bpy.context.scene\nif not bpy.data.objects.get(\'V04 Unified finished paving network\'):\n    raise RuntimeError(\'Open the revision 04 Atheria lobby first.\')\nif bpy.context.object and bpy.context.object.mode!=\'OBJECT\':bpy.ops.object.mode_set(mode=\'OBJECT\')\nold_camera=scene.camera.name if scene.camera else \'01 Overview\'\n# Correct inward-wound original arch stones before finishing their wall joins.\nfor obj in scene.objects:\n    if obj.type==\'MESH\' and \'voussoir\' in obj.name:\n        bm=bmesh.new();bm.from_mesh(obj.data)\n        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))\n        bm.to_mesh(obj.data);bm.free();obj.data.update()\nfor obj in list(bpy.data.objects):\n    if obj.name.startswith(\'V05 \'):bpy.data.objects.remove(obj,do_unlink=True)\n\nold_wall_prefixes=(\'Bridge parapet\',\'Western court divider\',\'East court divider\',\n                   \'North court divider\',\'South court divider\',\'Outer low parapet\',\n                   \'Northern royal wall\',\'South garden parapet\')\nfor obj in list(bpy.data.objects):\n    if obj.name.startswith(old_wall_prefixes):bpy.data.objects.remove(obj,do_unlink=True)\n\ncol=bpy.data.collections.get(\'15 / Connected finished walls\')\nif col is None:\n    col=bpy.data.collections.new(\'15 / Connected finished walls\');scene.collection.children.link(col)\n\n\ndef stone_material(name,c1,c2,mortar=None):\n    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)\n    m.diffuse_color=(*c1,1);m.use_nodes=True\n    nodes=m.node_tree.nodes;links=m.node_tree.links\n    nodes.clear()\n    output=nodes.new(\'ShaderNodeOutputMaterial\');shader=nodes.new(\'ShaderNodeBsdfPrincipled\')\n    shader.inputs[\'Roughness\'].default_value=.84;links.new(shader.outputs[\'BSDF\'],output.inputs[\'Surface\'])\n    uv=nodes.new(\'ShaderNodeTexCoord\')\n    noise=nodes.new(\'ShaderNodeTexNoise\');noise.inputs[\'Scale\'].default_value=5\n    noise.inputs[\'Detail\'].default_value=2;links.new(uv.outputs[\'UV\'],noise.inputs[\'Vector\'])\n    if mortar:\n        brick=nodes.new(\'ShaderNodeTexBrick\')\n        brick.inputs[\'Color1\'].default_value=(*c1,1);brick.inputs[\'Color2\'].default_value=(*c2,1)\n        brick.inputs[\'Mortar\'].default_value=(*mortar,1)\n        brick.inputs[\'Scale\'].default_value=1;brick.inputs[\'Mortar Size\'].default_value=.017\n        brick.inputs[\'Mortar Smooth\'].default_value=.01\n        brick.inputs[\'Brick Width\'].default_value=1.12;brick.inputs[\'Row Height\'].default_value=.44\n        brick.offset=.5;brick.offset_frequency=2;links.new(uv.outputs[\'UV\'],brick.inputs[\'Vector\'])\n        links.new(brick.outputs[\'Color\'],shader.inputs[\'Base Color\'])\n        joints=nodes.new(\'ShaderNodeBump\');joints.invert=True\n        joints.inputs[\'Strength\'].default_value=.42;joints.inputs[\'Distance\'].default_value=.055\n        links.new(brick.outputs[\'Fac\'],joints.inputs[\'Height\'])\n        bump=nodes.new(\'ShaderNodeBump\');bump.inputs[\'Strength\'].default_value=.15;bump.inputs[\'Distance\'].default_value=.025\n        links.new(joints.outputs[\'Normal\'],bump.inputs[\'Normal\'])\n    else:\n        mix=nodes.new(\'ShaderNodeMixRGB\');mix.inputs[1].default_value=(*c1,1);mix.inputs[2].default_value=(*c2,1)\n        links.new(noise.outputs[\'Fac\'],mix.inputs[0]);links.new(mix.outputs[\'Color\'],shader.inputs[\'Base Color\'])\n        bump=nodes.new(\'ShaderNodeBump\');bump.inputs[\'Strength\'].default_value=.16;bump.inputs[\'Distance\'].default_value=.018\n    links.new(noise.outputs[\'Fac\'],bump.inputs[\'Height\']);links.new(bump.outputs[\'Normal\'],shader.inputs[\'Normal\'])\n    return m\n\n\nbody_mat=stone_material(\'V05 coursed fortress stone\',(.39,.45,.48),(.28,.34,.38),(.14,.19,.22))\nbase_mat=stone_material(\'V05 deep foundation stone\',(.21,.27,.30),(.17,.22,.25),(.10,.14,.16))\ncap_mat=stone_material(\'V05 dressed coping stone\',(.57,.61,.61),(.46,.51,.52))\n\n\ndef mesh(name,verts,faces,material):\n    data=bpy.data.meshes.new(\'V05 \'+name);data.from_pydata(verts,[],faces);data.update()\n    obj=bpy.data.objects.new(\'V05 \'+name,data);col.objects.link(obj);data.materials.append(material)\n    return obj\n\n\ndef signed_area(poly):return sum(a.x*b.y-b.x*a.y for a,b in zip(poly,poly[1:]+poly[:1]))/2\n\n\ndef prism(name,poly,bottom,top,material):\n    poly=[Vector(p).to_2d() for p in poly]\n    if signed_area(poly)<0:poly.reverse()\n    n=len(poly);vs=[(p.x,p.y,z) for z in [bottom,top] for p in poly]\n    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]\n    fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]\n    return mesh(name,vs,fs,material)\n\n\ndef outline(points,width):\n    points=[Vector(p) for p in points];left=[];right=[]\n    for i,p in enumerate(points):\n        incoming=(points[i]-points[i-1]).normalized() if i else (points[1]-p).normalized()\n        outgoing=(points[i+1]-p).normalized() if i<len(points)-1 else incoming\n        n0=Vector((-incoming.y,incoming.x));n1=Vector((-outgoing.y,outgoing.x))\n        miter=(n0+n1).normalized();distance=(width/2)/max(.4,miter.dot(n1))\n        # Ends overlap their shared nodes and the existing arch/tower masonry.\n        q=p-incoming*.22 if i==0 else p+incoming*.22 if i==len(points)-1 else p\n        left.append(q+miter*distance);right.append(q-miter*distance)\n    return left+list(reversed(right))\n\n\nleft_pier=(-3-4.4*math.cos(math.radians(43)),-4+4.4*math.sin(math.radians(43)))\nright_pier=(-3+4.4*math.cos(math.radians(43)),-4-4.4*math.sin(math.radians(43)))\nruns=[\n (\'Bridge west\',[(-20.1,-39),(-20.1,-29)],2.0,.55),\n (\'Bridge east\',[(-13.9,-39),(-13.9,-33),(-11.5,-29)],2.0,.55),\n (\'Front west\',[(-37.5,-29),(-20.1,-29)],2.8,.80),\n (\'Front east\',[(-11.5,-29),(38,-29)],2.8,.80),\n (\'Outer west\',[(-37.5,-29),(-37.5,26),(-32.9,31)],3.2,.85),\n (\'Outer east\',[(38,-29),(38,26),(33.6,31.5)],3.2,.85),\n (\'Royal west\',[(-32.9,31),(.65,31)],5.0,.90),\n (\'Royal east\',[(23.7,32),(33.6,31.5)],5.0,.90),\n (\'Workshop west\',[(-37.5,-4),(-21.9,-4)],2.8,.80),\n (\'Workshop east\',[(-14.1,-4),(-9.4,-4),left_pier],2.8,.80),\n (\'Sanctuary southwest\',[left_pier,(-3,2.1),(-3,11.1)],2.8,.80),\n (\'Sanctuary northwest\',[(-3,18.9),(-3,31)],2.8,.80),\n (\'Festival northwest\',[right_pier,(3.4,-4),(11.1,-4)],2.8,.80),\n (\'Festival northeast\',[(18.9,-4),(38,-4)],2.8,.80),\n (\'Spawn northeast\',[(-3,-13.1),(-3,-10.1),right_pier],2.8,.80),\n (\'Spawn southeast\',[(-3,-29),(-3,-20.9)],2.8,.80),\n]\n\nlayers=[[],[],[]]\nfor name,path,h,w in runs:\n    layers[0].append(prism(name+\' foundation\',outline(path,w+.30),0,.40,base_mat))\n    layers[1].append(prism(name+\' masonry\',outline(path,w),.32,h+.32,body_mat))\n    layers[2].append(prism(name+\' coping\',outline(path,w+.22),h+.28,h+.52,cap_mat))\n\n# Corner stones and buttresses support and conceal the physical joins.\narch_nodes=[(-21.9,-4),(-14.1,-4),(-3,11.1),(-3,18.9),(11.1,-4),(18.9,-4),\n            (-3,-13.1),(-3,-20.9),left_pier,right_pier]\nnodes={}\nfor name,path,h,w in runs:\n    for p in path:\n        key=(round(p[0],4),round(p[1],4));nodes[key]=max(h,nodes.get(key,0))\n    for a,b in zip(path,path[1:]):\n        a,b=Vector(a),Vector(b);length=(b-a).length\n        for i in range(1,int(length/4)):\n            p=a+(b-a)*(i/max(1,int(length/4)))\n            key=(round(p.x,4),round(p.y,4));nodes[key]=max(h,nodes.get(key,0))\n\n\ndef square(x,y,size):return [(x-size/2,y-size/2),(x+size/2,y-size/2),(x+size/2,y+size/2),(x-size/2,y+size/2)]\n\n\nfor (x,y),h in nodes.items():\n    if any((Vector((x,y))-Vector(p)).length<.75 for p in arch_nodes):continue\n    if min((Vector((x,y))-Vector(p)).length for p in [(2.3,32),(21.7,32)])<3:continue\n    layers[0].append(prism(\'Quoin foot\',square(x,y,1.22),0,.40,base_mat))\n    layers[1].append(prism(\'Quoin pier\',square(x,y,1.02),.32,h+.40,body_mat))\n    layers[2].append(prism(\'Quoin crown\',square(x,y,1.25),h+.36,h+.62,cap_mat))\n\n\ndef fuse(parts,name):\n    result=parts[0]\n    for other in parts[1:]:\n        modifier=result.modifiers.new(\'Join wall edges\',\'BOOLEAN\')\n        modifier.operation=\'UNION\';modifier.solver=\'EXACT\';modifier.object=other\n        bpy.context.view_layer.objects.active=result\n        bpy.ops.object.modifier_apply(modifier=modifier.name)\n        bpy.data.objects.remove(other,do_unlink=True)\n    result.name=\'V05 \'+name\n    uv=result.data.uv_layers.new(name=\'Stone courses in metres\')\n    result.data.update()\n    for face in result.data.polygons:\n        normal=face.normal\n        tangent=Vector((-normal.y,normal.x,0)).normalized() if abs(normal.z)<.6 else None\n        for loop_index in face.loop_indices:\n            p=result.data.vertices[result.data.loops[loop_index].vertex_index].co\n            uv.data[loop_index].uv=(p.dot(tangent),p.z) if tangent is not None else (p.x,p.y)\n    result[\'atheria_kind\']=\'CONNECTED_WALL\'\n    return result\n\n\nwall_objects=[fuse(parts,name) for parts,name in zip(layers,\n    [\'Continuous wall foundations\',\'Joined masonry wall network\',\'Continuous coping and corner caps\'])]\n\n# Leave a fitted recess around the existing engraved panel. Its original arch\n# pier remains intact behind it, while the higher walls and coping clear it.\ncat=bpy.data.objects.get(\'V03 Apples cat arch carving\')\nif cat:\n    vs=[(sx*.70,sy*.20,sz*1.06) for sx,sy,sz in\n        [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]\n    niche=mesh(\'temporary engraving recess\',vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),\n                 (1,2,6,5),(2,3,7,6),(3,0,4,7)],body_mat)\n    niche.matrix_world=cat.matrix_world.copy()\n    for obj in wall_objects[1:]:\n        modifier=obj.modifiers.new(\'Clear the Apples engraving\',\'BOOLEAN\')\n        modifier.operation=\'DIFFERENCE\';modifier.solver=\'EXACT\';modifier.object=niche\n        bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=modifier.name)\n    bpy.data.objects.remove(niche,do_unlink=True)\nfor obj in wall_objects:\n    bevel=obj.modifiers.new(\'Dressed stone edges\',\'BEVEL\');bevel.width=.025;bevel.segments=2\n\n# Riser stays at the block arm\'s grip. The bow\'s top leans back toward the head,\n# and its lower tip points outward, following the user\'s marked diagonal.\ntorso=bpy.data.objects[\'V03 Psychopomp Roblox torso\']\nframe=torso.matrix_world.copy()\noperation=(frame @ Matrix.Translation((2,-.55,5.85))\n           @ Matrix.Rotation(math.radians(-55),4,\'Y\')\n           @ Matrix.Translation((-2,.10,-5.85)) @ frame.inverted())\nfor name in [\'V04 Psychopomp raised longbow\',\'V04 Psychopomp bowstring\',\'V04 Psychopomp bow grip\']:\n    obj=bpy.data.objects.get(name)\n    if obj and not obj.get(\'v05_bow_pose\'):\n        if name.endswith(\'bow grip\'):\n            for v in obj.data.vertices:v.co.y*=.50/.22\n        obj.matrix_world=operation @ obj.matrix_world\n        obj[\'v05_bow_pose\']=\'Diagonal -55 degrees, grip retained, reference image 4\'\nbpy.data.objects[\'V03 Psychopomp STATUE\'][\'bow_reference_angle_degrees\']=-55\n\n\ndef camera(name,pos,target,scale=None,lens=32):\n    data=bpy.data.cameras.new(\'V05 \'+name);obj=bpy.data.objects.new(\'V05 \'+name,data)\n    col.objects.link(obj);obj.location=pos\n    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat(\'-Z\',\'Y\').to_euler()\n    data.clip_end=1000;data.lens=lens\n    if scale:data.type=\'ORTHO\';data.ortho_scale=scale\n    return obj\n\n\nWALL_CAMERAS={\n \'walls\':camera(\'Connected walls overview\',(83,-112,119),(0,1,2),112),\n \'corners\':camera(\'Connected front wall corner\',(-47,-39,13),(-34,-24,2),22),\n \'walljoin\':camera(\'Wall and arch joins\',(-10,-14,10),(-5,-3,2.3),24),\n \'bowangle\':camera(\'Bow reference angle\',(-41,10,7),(-33,14,5.2),7.5),\n}\nscene[\'Revision\']=\'05 — connected higher finished stone walls and diagonal reference bow pose\'\nscene[\'wall_runs\']=str(runs)\nscene[\'wall_heights\']=\'Courtyard/front 2.8 m; outer 3.2 m; bridge 2.0 m; royal 5.0 m, plus coping\'\nscene.camera=bpy.data.objects.get(old_camera) or bpy.data.objects.get(\'01 Overview\')\nbpy.context.view_layer.update()\nprint(\'Atheria revision 05 applied:\',len(runs),\'joined wall runs; diagonal bow pose\')\n'
exec(compile(REVISION_05_UPDATE, 'atheria_walls_bow_update.py', 'exec'), globals())
CAMS.update(WALL_CAMERAS)

SCENE.render.engine='CYCLES'
SCENE.cycles.device='CPU'
SCENE.cycles.samples=max(1,ARGS.samples)
# Some headless Linux builds omit OpenImageDenoise. Keep the script portable.
try:
    import _cycles
    SCENE.cycles.use_denoising=bool(getattr(_cycles, 'with_openimagedenoise', False))
except ImportError:
    SCENE.cycles.use_denoising=False
SCENE.cycles.max_bounces=6
SCENE.cycles.diffuse_bounces=3
SCENE.cycles.glossy_bounces=3
SCENE.render.threads_mode='FIXED';SCENE.render.threads=min(5,os.cpu_count() or 4)
SCENE.render.resolution_x=max(320,ARGS.resolution)
SCENE.render.resolution_y=int(SCENE.render.resolution_x*.75)
SCENE.render.resolution_percentage=100
SCENE.render.image_settings.file_format='PNG'
SCENE.render.film_transparent=False
SCENE.view_settings.view_transform='AgX'
SCENE.view_settings.look='AgX - Medium High Contrast'
SCENE.render.image_settings.color_mode='RGB'
SCENE.camera=CAMS['overview']
SCENE.unit_settings.system='METRIC'
SCENE['Design intent']='Linked courtyards: full peripheral loop + diagonal crystal reveal.'
SCENE['Source script']='atheria_linked_courtyards_v05.py'
SCENE['Revision']='05 — connected higher walls; finished masonry; diagonal reference bow pose'
SCENE['Scale note']='Conceptual metres; rescale deliberately for Roblox avatars and camera.'
readme=bpy.data.texts.new('READ ME — Atheria design intent');readme.write(NOTES)
try:
    script=Path(__file__)
    if script.exists():
        embedded=bpy.data.texts.new('atheria_linked_courtyards.py');embedded.write(script.read_text())
except NameError:
    pass
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.clip_end=1000
            ar.spaces.active.region_3d.view_distance=105
            ar.spaces.active.region_3d.view_location=(0,0,0)
            ar.spaces.active.shading.color_type='MATERIAL'
            ar.spaces.active.region_3d.view_perspective='CAMERA'

(OUT/'DESIGN_NOTES.txt').write_text(NOTES,encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'atheria_linked_courtyards_v05.blend'))
print('ATHERIA: built',len(SCENE.objects),'objects; saved scene to',OUT,flush=True)
if not ARGS.no_render:
    for view in ARGS.views:
        SCENE.camera=CAMS[view]
        SCENE.render.filepath=str(OUT/('atheria_'+view+'.png'))
        bpy.ops.render.render(write_still=True)
        print('ATHERIA: rendered',view,flush=True)
SCENE.camera=CAMS['overview']
print('ATHERIA: complete.',flush=True)
