"""Paste into Blender 4.3+ Text Editor and press Alt+P to build Vestergate revision 02.

Run from Blender's Text Editor, or:
  blender -b --python build_vestergate.py

Creates a separate scene and preserves existing scenes. No external assets needed.
Output: ATHERIA_VESTERGATE_OUT; toggle RENDER below to enable renders.
ATHERIA_VESTERGATE_SAMPLES=32, ATHERIA_VESTERGATE_VIEWS=overview,plan,...
This is a visual/layout blockout, not a Roblox runtime map or collision export.
"""
import bpy
import math
import random
import os
import json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

OUT = Path(os.environ.get('ATHERIA_VESTERGATE_OUT',
    bpy.path.abspath('//Vestergate_Blockout') if bpy.data.filepath
    else str(Path.home() / 'Vestergate_Blockout')))
OUT.mkdir(parents=True, exist_ok=True)
RENDER = False  # Set True to render all five camera views after building.
SAMPLES = int(os.environ.get('ATHERIA_VESTERGATE_SAMPLES', '32'))
rng = random.Random(2187)
scene = bpy.data.scenes.new('Vestergate / Three-lane woodland blockout')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
scene['Design stage'] = 'Blockout: terrain, routes, planting masses, defence terraces'
scene['Orientation'] = 'Gate at south (-Y); enemy trails enter from north (+Y)'
scene['Reference notes'] = 'docs/VESTERGATE_REFERENCE_NOTES.md'

groups = {}
for name in ['Terrain', 'Cliff terraces', 'Trails', 'Bridge', 'Kingdom gates',
             'Defence vantages', 'Crystal and spawn', 'Trees', 'Ground greenery',
             'Landmarks', 'Scale figures', 'Lighting', 'Cameras']:
    col = bpy.data.collections.new('Vestergate / ' + name)
    scene.collection.children.link(col)
    groups[name] = col
current = 'Terrain'
materials = {}

def material(name, color, roughness=.85, metallic=0, emission=0):
    mat = bpy.data.materials.new('Vestergate / ' + name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*color, 1)
        bsdf.inputs['Emission Strength'].default_value = emission
    materials[name] = mat
    return mat

for name, color in [
    ('grass', (.145,.30,.16)), ('grass light', (.23,.39,.17)),
    ('grass deep', (.085,.235,.16)), ('grass rim', (.28,.43,.19)),
    ('rock', (.29,.32,.285)), ('rock light', (.38,.40,.33)),
    ('rock shadow', (.21,.25,.235)), ('earth', (.31,.235,.13)),
    ('woodland trail', (.44,.325,.18)), ('gate road', (.51,.46,.34)),
    ('ridge trail', (.52,.395,.205)), ('cobble', (.61,.56,.43)),
    ('cobble dark', (.43,.415,.34)), ('timber', (.23,.12,.055)),
    ('timber light', (.38,.235,.105)), ('stone', (.40,.49,.49)),
    ('stone light', (.56,.62,.58)), ('stone dark', (.29,.375,.39)),
    ('iron', (.075,.115,.12)), ('gold', (.67,.45,.12)),
    ('blue cloth', (.055,.235,.34)), ('leaf dark', (.055,.23,.16)),
    ('leaf teal', (.07,.335,.235)), ('leaf green', (.135,.425,.225)),
    ('leaf light', (.25,.49,.23)), ('leaf gold', (.69,.56,.19)),
    ('leaf gold light', (.88,.71,.27)), ('fern', (.14,.38,.235)),
    ('flower blue', (.29,.39,.69)), ('flower pink', (.69,.25,.40)),
    ('placement stone', (.51,.55,.38)), ('scale figure', (.83,.81,.66)),
    ('lane green', (.30,.57,.38)), ('lane cream', (.80,.70,.39)),
    ('lane blue', (.25,.52,.65)), ('backdrop', (.085,.14,.15)),
]:
    material(name, color, metallic=.5 if name in ['iron','gold'] else 0)
material('crystal', (.075,.64,.88), roughness=.25, metallic=.25, emission=.65)
material('crystal pale', (.33,.88,1), roughness=.25, emission=.7)
material('crystal dark', (.035,.26,.45), roughness=.25, metallic=.2, emission=.25)
material('warm light', (1,.52,.12), roughness=.4, emission=3)
water = material('water', (.055,.27,.33), roughness=.22, metallic=.25)
material('dirt road', (.35,.25,.13), roughness=.96)
def dirt_color(nodes, links):
    geometry=nodes.new('ShaderNodeNewGeometry')
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.15
    noise.inputs['Detail'].default_value=2
    links.new(geometry.outputs['Position'],noise.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=.2
    ramp.color_ramp.elements[0].color=(.29,.195,.095,1)
    ramp.color_ramp.elements[1].position=.8
    ramp.color_ramp.elements[1].color=(.40,.29,.155,1)
    links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
    return ramp.outputs['Color']
dirt=materials['dirt road']
dirt.node_tree.links.new(dirt_color(dirt.node_tree.nodes,dirt.node_tree.links),
    dirt.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])

def mesh(name, verts, faces, mats, indices=None):
    data = bpy.data.meshes.new('Vestergate / ' + name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new('Vestergate / ' + name, data)
    groups[current].objects.link(obj)
    for mat in mats:
        data.materials.append(materials[mat] if isinstance(mat, str) else mat)
    if indices:
        for poly, index in zip(data.polygons, indices):
            poly.material_index = index
    return obj

def adopt(obj, name, mat):
    obj.name = 'Vestergate / ' + name
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    groups[current].objects.link(obj)
    if mat:
        obj.data.materials.append(materials[mat] if isinstance(mat, str) else mat)
    return obj

def box(name, pos, size, mat='timber', bevel=0):
    sx,sy,sz=size
    vv=[(x*sx/2,y*sy/2,z*sz/2) for x,y,z in
        [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),
         (1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    obj=mesh(name,vv,[(0,2,6,4),(1,5,7,3),(0,4,5,1),
        (2,3,7,6),(0,1,3,2),(4,6,7,5)],[mat])
    obj.location=pos
    if bevel:
        mod = obj.modifiers.new('Blockout edge softness', 'BEVEL')
        mod.width, mod.segments = bevel, 1
    return obj

def cylinder(name, pos, radius, depth, mat, vertices=16):
    n=vertices
    vv=[(radius*math.cos(i*math.tau/n),radius*math.sin(i*math.tau/n),z)
        for z in [-depth/2,depth/2] for i in range(n)]
    ff=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    ff += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    obj=mesh(name,vv,ff,[mat]);obj.location=pos;return obj

ICO_BASES={}
ICO_MESHES={}
def ico(name, pos, size, mat, subdivisions=1):
    if subdivisions not in ICO_BASES:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1)
        temp=bpy.context.object;ICO_BASES[subdivisions]=temp.data
        bpy.data.objects.remove(temp,do_unlink=True)
    key=(subdivisions,mat)
    if key not in ICO_MESHES:
        data=ICO_BASES[subdivisions].copy();data.name='Vestergate / shared '+mat+' ico'
        data.materials.append(materials[mat]);ICO_MESHES[key]=data
    obj=bpy.data.objects.new('Vestergate / '+name,ICO_MESHES[key])
    groups[current].objects.link(obj);obj.location=pos
    obj.scale = size
    obj.rotation_euler[2] = rng.random()*math.tau
    return obj

def beam(name, a, b, width, mat='timber', depth=None):
    a, b = Vector(a), Vector(b)
    obj = box(name, (a+b)/2, (width, depth or width, (b-a).length), mat)
    obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return obj

def ring(name, pos, radius, width, mat='gold', n=40):
    x,y,z=pos
    verts = [(x+math.cos(i*math.tau/n)*r, y+math.sin(i*math.tau/n)*r,z)
             for r in [radius-width, radius] for i in range(n)]
    return mesh(name, verts, [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)], [mat])

def smooth(v):
    v=max(0,min(1,v))
    return v*v*(3-2*v)

BRIDGE_CENTER = Vector((37,27))
BRIDGE_AXIS = Vector((-1,-1)).normalized()
BRIDGE_SIDE = Vector((1,-1)).normalized()

def ground(x,y):
    left = -1.2*smooth((-x-15)/8)*smooth((y+9)/14)
    ridge = 4*smooth((x-19)/7)*smooth((y+6)/23)*smooth((67-y)/10)
    edge = 5*smooth((abs(x)-46)/14)*( .7+.3*math.sin(y*.12)**2)
    back = 4*smooth((y-53)/19)*( .55+.45*math.sin(x*.08+.5)**2)
    q=Vector((x,y))-BRIDGE_CENTER
    along, across = q.dot(BRIDGE_AXIS),q.dot(BRIDGE_SIDE)
    cut=5.1*math.exp(-(along/2.3)**4)*smooth((13-abs(across))/3)
    return left+ridge+edge+back-cut

def bridge_zone(x,y,pad=0):
    q=Vector((x,y))-BRIDGE_CENTER
    return abs(q.dot(BRIDGE_AXIS))<5.9+pad and abs(q.dot(BRIDGE_SIDE))<3+pad

def trail_height(x,y):
    return 4.13 if bridge_zone(x,y) else terrain_height(x,y)+.065

# Rounded, irregular landscape slab. Coarse faceting is intentional at blockout stage.
N, R = 256, 65
verts=[(0,6,ground(0,6))]
for j in range(1,R+1):
    t=j/R
    for i in range(N):
        a=i*math.tau/N
        wobble=1+.014*math.sin(5*a)+.01*math.cos(9*a)
        x=63*math.copysign(abs(math.cos(a))**.5,math.cos(a))*t*wobble
        y=6+70*math.copysign(abs(math.sin(a))**.5,math.sin(a))*t*wobble
        verts.append((x,y,ground(x,y)))
faces=[]; ids=[]
for i in range(N):
    faces.append((0,1+i,1+(i+1)%N));ids.append(0)
for j in range(R-1):
    a=1+j*N;b=a+N
    for i in range(N):
        k=(i+1)%N;faces.append((a+i,b+i,b+k,a+k))
        ids.append(1 if rng.random()<.13 else 0)
outer=1+(R-1)*N
lower=len(verts)
for i in range(N):
    x,y,z=verts[outer+i];verts.append((x*.992,6+(y-6)*.992,-6.5))
for i in range(N):
    k=(i+1)%N;faces.append((outer+i,lower+i,lower+k,outer+k));ids.append(2+i%2)
faces.append(tuple(reversed(range(lower,lower+N))));ids.append(2)
terrain=mesh('Grassland and terraced ridge foundation',verts,faces,
    ['grass','grass light','rock','rock shadow'],ids)
for poly in terrain.data.polygons:
    if poly.material_index<2:poly.use_smooth=True
TERRAIN_BVH=BVHTree.FromPolygons([v.co.copy() for v in terrain.data.vertices],
    [tuple(p.vertices) for p in terrain.data.polygons])
def terrain_height(x,y):
    hit=TERRAIN_BVH.ray_cast(Vector((x,y,40)),Vector((0,0,-1)),80)
    return hit[0].z if hit[0] is not None else ground(x,y)

# Spline centre lines: distinct entries and no shared segment before the final apron.
LANES = [
    dict(id='left', label='Shaded woodland trail', material='dirt road', width=4.8,
         color='lane green', points=[(-40,57),(-44,42),(-35,29),(-39,16),
             (-25,6),(-20,-11),(-11,-23),(0,-31.8)]),
    dict(id='centre', label='Old gate road', material='dirt road', width=5.7,
         color='lane cream', points=[(0,65),(7,51),(4,38),(-1,26),
             (4,13),(0,0),(1,-17),(0,-31.8)]),
    dict(id='right', label='Sunlit ridge trail', material='dirt road', width=5.1,
         color='lane blue', points=[(45,55),(45,40),(44,34),(32,22),
             (35,12),(24,1),(22,-13),(11,-24),(0,-31.8)]),
]

def spline(points,steps=20):
    p=[Vector(v) for v in points];result=[]
    for i in range(len(p)-1):
        a,b,c,d=p[max(0,i-1)],p[i],p[i+1],p[min(len(p)-1,i+2)]
        for j in range(steps):
            t=j/steps
            result.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    result.append(p[-1]);return result

def distance_segment(p,a,b):
    delta=b-a
    t=max(0,min(1,(p-a).dot(delta)/delta.length_squared))
    return (p-(a+delta*t)).length

for lane in LANES:
    lane['samples']=spline(lane['points'])

LANE_SEGMENTS=[]
for lane in LANES:
    for a,b in zip(lane['samples'],lane['samples'][1:]):
        dx,dy=b.x-a.x,b.y-a.y
        LANE_SEGMENTS.append((a.x,a.y,dx,dy,1/(dx*dx+dy*dy),lane['width']/2))

def lane_distance(x,y):
    result=1e9
    for ax,ay,dx,dy,inverse,half_width in LANE_SEGMENTS:
        t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)*inverse))
        result=min(result,math.hypot(x-ax-dx*t,y-ay-dy*t)-half_width)
    return result

def nearest_road_point(x,y):
    best=None;distance=1e9
    for ax,ay,dx,dy,inverse,half_width in LANE_SEGMENTS:
        t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)*inverse))
        q=Vector((ax+dx*t,ay+dy*t));d=(q-Vector((x,y))).length_squared
        if d<distance:distance=d;best=q
    if y<-29:
        for q in [Vector((0,-35.2)),Vector((0,-42))]:
            d=(q-Vector((x,y))).length_squared
            if d<distance:distance=d;best=q
    return best

# Paint matching dirt beneath the road ribbons and along their narrow shoulders.
# This also prevents any residual terrain triangle from appearing green on a trail.
clearance=terrain.data.attributes.new('Road clearance','FLOAT','POINT')
for vertex,value in zip(terrain.data.vertices,clearance.data):
    value.value=lane_distance(vertex.co.x,vertex.co.y)
for index in range(2):
    original=terrain.data.materials[index]
    mat=original.copy();mat.name='Vestergate / Terrain '+original.name.rsplit(' / ',1)[-1]
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    bsdf=nodes.get('Principled BSDF');base=tuple(bsdf.inputs['Base Color'].default_value)
    attribute=nodes.new('ShaderNodeAttribute');attribute.attribute_name='Road clearance'
    threshold=nodes.new('ShaderNodeMath');threshold.operation='LESS_THAN'
    threshold.inputs[1].default_value=.30
    links.new(attribute.outputs['Fac'],threshold.inputs[0])
    mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=base
    links.new(threshold.outputs[0],mix.inputs[0])
    links.new(dirt_color(nodes,links),mix.inputs[2])
    links.new(mix.outputs[0],bsdf.inputs['Base Color'])
    terrain.data.materials[index]=mat

current='Trails'
for lane in LANES:
    samples=lane['samples'];vv=[];ff=[];columns=13
    for i,p in enumerate(samples):
        tangent=(samples[min(i+1,len(samples)-1)]-samples[max(0,i-1)]).normalized()
        normal=Vector((-tangent.y,tangent.x))
        width=lane['width']*(1+.035*math.sin(i*.22))
        for column in range(columns):
            sign=-1+2*column/(columns-1)
            xy=p+normal*width*.5*sign
            # Tiny layer offsets prevent coplanar flicker where the final lanes meet.
            layer={'left':0,'centre':.008,'right':.016}[lane['id']]
            vv.append((xy.x,xy.y,trail_height(xy.x,xy.y)+layer))
        if i:
            a=columns*(i-1)
            # The bridge supplies its own surface, with no dirt hovering over planks.
            midpoint=(samples[i]+samples[i-1])/2
            if not (lane['id']=='right' and bridge_zone(*midpoint)):
                for column in range(columns-1):
                    b=a+column;ff.append((b,b+columns,b+columns+1,b+1))
    # A shallow solid soil bed meets the terrain instead of floating like a decal.
    count=len(vv)
    vv += [(x,y,z-.28) for x,y,z in vv]
    solids=list(ff)
    boundary={}
    for a,b,c,d in ff:
        solids.append((d+count,c+count,b+count,a+count))
        for u,v in [(a,b),(b,c),(c,d),(d,a)]:
            key=tuple(sorted((u,v)))
            if key in boundary:boundary.pop(key)
            else:boundary[key]=(u,v)
    for a,b in boundary.values():solids.append((a,a+count,b+count,b))
    obj=mesh(lane['label']+' / walkable surface',vv,solids,[lane['material']])
    obj['Lane']=lane['id'];obj['Width metres']=lane['width']
    obj['Enemy route']=True

# Grassy rock-capped terraces: one solid rock mass plus an exposed flat upper shelf.
TERRACES=[]
def terrace(name,x,y,rx,ry,height,phase=0,mat='grass rim'):
    z=ground(x,y);n=12;vv=[]
    shape=[1+.10*math.sin(i*2.8+phase)+.045*math.cos(i*4.4+phase) for i in range(n)]
    for scale,zz in [(1.08,z-.15),(1.04,z+height*.30),(1,z+height-.26),(1.015,z+height)]:
        for i in range(n):
            a=i*math.tau/n
            vv.append((x+math.cos(a)*rx*shape[i]*scale,
                       y+math.sin(a)*ry*shape[i]*scale,zz))
    ff=[];ids=[]
    for layer in range(3):
        for i in range(n):
            k=(i+1)%n
            ff.append((layer*n+i,layer*n+k,(layer+1)*n+k,(layer+1)*n+i))
            ids.append(3 if layer==2 else (i+layer)%3)
    ff.append(tuple(range(3*n,4*n)));ids.append(3)
    o=mesh(name,vv,ff,['rock','rock light','rock shadow',mat],ids)
    o['Terrain top metres']=z+height
    TERRACES.append((x,y,rx,ry,z+height))
    return z+height

current='Cliff terraces'
for i,(x,y,rx,ry,h) in enumerate([
    (-58,47,8,11,7),(-54,19,6,9,8),(-53,-8,6,10,5),
    (-27,65,12,6,7),(-12,71,9,4,5),(18,69,9,5,6),
    (58,48,7,10,8),(56,15,5,12,8),(53,-9,6,9,5),
]):
    terrace('Scenic forest escarpment %02d'%i,x,y,rx,ry,h,i*.7)

# Five relocated positions follow the user's red marks; the unmarked D4 is retained.
# Short grass ledges are intended for jump access, without ramps or centre discs.
PAD_SPECS=[
    ('D1','Woodland bend',-28,17,3.7,3.9,1.55),
    ('D2','Lower woodland shelf',-31.5,0,4.1,4.0,1.45),
    ('D3','Central overlook',-5.5,13,4.8,5.0,1.60),
    ('D4','Upper road shoulder',-12,39,4.6,4.8,1.65),
    ('D5','Ridge bend overlook',25,12,3.6,3.8,.80),
    ('D6','Lower ridge shoulder',13,-11,4.0,4.3,1.45),
]
PADS=[]
current='Defence vantages'
for index,(pid,name,x,y,rx,ry,height) in enumerate(PAD_SPECS):
    z=terrace(pid+' / '+name,x,y,rx,ry,height,index*.2)
    PADS.append(dict(id=pid,name=name,x=x,y=y,z=z,rx=rx,ry=ry,
        access='jump',ledge_height=height))

# Right lane bridge: a visible crossing over a small recessed stream cut.
current='Bridge'
angle=math.atan2(BRIDGE_AXIS.y,BRIDGE_AXIS.x)
for i in range(27):
    along=-5.85+(i+.5)*11.7/27
    p=BRIDGE_CENTER+BRIDGE_AXIS*along
    ob=box('Ridge bridge deck plank',(p.x,p.y,4.12),(5.8,.41,.22),
        'timber light' if i%4 else 'timber',.025)
    ob.rotation_euler[2]=angle-math.pi/2
for side in [-1,1]:
    for along in [-5.6,-2.8,0,2.8,5.6]:
        p=BRIDGE_CENTER+BRIDGE_AXIS*along+BRIDGE_SIDE*3*side
        box('Bridge railing post',(p.x,p.y,4.8),(.28,.28,1.6),'timber',.025)
    for z in [4.7,5.35]:
        a=BRIDGE_CENTER-BRIDGE_AXIS*5.85+BRIDGE_SIDE*3*side
        b=BRIDGE_CENTER+BRIDGE_AXIS*5.85+BRIDGE_SIDE*3*side
        beam('Bridge handrail',(*a,z),(*b,z),.19,'timber light')
    a=BRIDGE_CENTER-BRIDGE_AXIS*6+BRIDGE_SIDE*2.3*side
    b=BRIDGE_CENTER+BRIDGE_AXIS*6+BRIDGE_SIDE*2.3*side
    beam('Bridge structural bearer',(*a,3.75),(*b,3.75),.36)
for along in [-4.5,4.5]:
    for side in [-1,1]:
        p=BRIDGE_CENTER+BRIDGE_AXIS*along+BRIDGE_SIDE*2.35*side
        beam('Bridge pier',(p.x,p.y,ground(*p)-.1),(p.x,p.y,3.8),.45)
vv=[]
for t in range(26):
    p=BRIDGE_CENTER+BRIDGE_SIDE*(-11+t*22/25)
    for sign in [-1,1]:
        q=p+BRIDGE_AXIS*.8*sign;vv.append((q.x,q.y,-.38))
mesh('Stream in ridge cutting',vv,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(25)],['water'])

# Gate, continuous wall, closed wooden leaves and flanking crenellated towers.
current='Kingdom gates'
for side in [-1,1]:
    box('Kingdom curtain wall',(side*33,-49,6.35),(42,3.4,12.7),'stone',.12)
    box('Curtain wall coping',(side*33,-49,12.8),(42.5,3.8,.5),'stone light',.07)
    for x in range(15,54,4):
        box('Wall crenellation',(side*x,-49,13.65),(1.7,3.55,1.4),'stone light',.07)
    for x in [23,37,51]:
        box('Wall buttress',(side*x,-46.9,5.6),(1.7,2.4,11.2),'stone dark',.06)
        box('Buttress foot',(side*x,-46.5,.7),(2.5,3.1,1.4),'stone light',.05)
    # Horizontal courses communicate scale without finishing every stone block.
    for z in [2.5,5,7.5,10]:
        box('Wall masonry course',(side*33,-47.27,z),(41,.045,.065),'stone dark')
    for i in range(30):
        x=side*rng.uniform(14,52);z=rng.uniform(1,11.7)
        box('Large dressed stone',(x,-47.22,z),(rng.uniform(1.4,2.8),.13,.65),
            'stone light' if i%3 else 'stone dark',.025)
    tower=cylinder('Gate flanking bastion',(side*10.2,-48.4,8),4.6,16,'stone',16)
    for z in [.6,6,12,15.8]:
        cylinder('Bastion stone belt',(side*10.2,-48.4,z),4.78,.32,'stone light',16)
    for i in range(12):
        a=i*math.tau/12
        ob=box('Bastion battlement',(side*10.2+4.25*math.cos(a),-48.4+4.25*math.sin(a),16.8),
            (1.35,1.35,1.6),'stone light',.06)
        ob.rotation_euler[2]=a
    for z in [5,10]:
        box('Bastion arrow slit',(side*10.2,-43.77,z),(.23,.08,1.35),'iron')
    beam('Kingdom banner mast',(side*10.2,-48.4,15.9),(side*10.2,-48.4,21),.13,'gold')
    mesh('Blue kingdom standard',[(side*10.2,-48.4,20.6),(side*10.2+3,-48.25,20.2),
        (side*10.2+2.7,-48.1,18.5),(side*10.2,-48.4,18.8)],[(0,1,2,3)],['blue cloth'])
for side in [-1,1]:
    box('Gate jamb',(side*6.6,-48.3,3.25),(1.4,3.6,6.5),'stone light',.09)
# Arch stones span the actual opening; the door's upper edge follows the inner arch.
for i in range(19):
    a=i*math.pi/19;b=(i+1)*math.pi/19
    vv=[(r*math.cos(t),y,6+r*math.sin(t))
        for y in [-46.5,-50.1] for r,t in [(6,a),(7.25,a),(7.25,b),(6,b)]]
    mesh('Gate arch voussoir %02d'%i,vv,[(0,1,2,3),(4,7,6,5),(0,4,5,1),
        (1,5,6,2),(2,6,7,3),(3,7,4,0)],['stone light' if i%3 else 'stone'])
box('Gate parapet',(0,-49,13.6),(15.6,3.7,1.1),'stone',.06)
for x in [-6,-3,0,3,6]:box('Gate crown crenellation',(x,-49,14.65),(1.4,3.5,1.25),'stone light',.06)
for i in range(16):
    x=-5.85+(i+.5)*11.7/16;top=6+math.sqrt(max(0,5.95**2-x*x))
    box('Closed gate wooden plank',(x,-47.4,top/2),(.70,.48,top),'timber light' if i%3 else 'timber',.025)
for side in [-1,1]:
    for z in [2,5,7.5]:box('Gate iron strap',(side*3,-47.10,z),(5.7,.13,.24),'iron',.025)
    beam('Gate diagonal brace',(side*5.7,-47.03,1.2),(side*.5,-47.03,7.7),.17,'iron',.11)
    cylinder('Gate handle boss',(side*.5,-46.96,3.7),.18,.18,'gold',12).rotation_euler[0]=math.pi/2
crest=box('Kingdom crystal crest',(0,-46.26,13.65),(1.1,.18,1.1),'gold',.04)
crest.rotation_euler[1]=math.pi/4

# Defended objective and player staging space directly outside the closed gate.
current='Crystal and spawn'
CX,CY=0,-35.2
cylinder('Crystal apron',(CX,CY,.08),8.0,.20,'dirt road',48)
for radius,z,depth,mat in [(3.1,.16,.32,'stone dark'),(2.75,.42,.24,'stone light'),
                          (2.3,.65,.22,'stone'),(1.45,.86,.22,'gold')]:
    cylinder('Crystal stepped plinth',(CX,CY,z),radius,depth,mat,12)
ring('Crystal energy ring',(CX,CY,.79),2.02,.08,'crystal pale')
def crystal(name,x,y,z,radius,height):
    vv=[(x,y,z-height*.46)]
    vv += [(x+radius*math.cos(i*math.tau/6),y+radius*math.sin(i*math.tau/6),z-height*.06) for i in range(6)]
    vv.append((x+.12*radius,y,z+height*.54))
    faces=[(0,1+(i+1)%6,1+i) for i in range(6)]+[(7,1+i,1+(i+1)%6) for i in range(6)]
    return mesh(name,vv,faces,['crystal','crystal pale','crystal dark'],[i%3 for i in range(12)])
crystal('Defend this crystal',CX,CY,3.35,1.05,4.65)
for i in range(3):
    a=i*math.tau/3+.4
    crystal('Orbiting crystal shard',CX+1.65*math.cos(a),CY+1.65*math.sin(a),2.45,.24,1.05)
cylinder('Player spawn paving',(0,-43.05,.075),2.25,.15,'stone light',24)
ring('Player spawn inset',(0,-43.05,.16),1.95,.075,'gold')
box('Gate staging paving',(0,-42,.025),(11,10,.05),'dirt road')
SPAWN=(0,-43.05,.16)

def is_clear(x,y,margin=0):
    if y<-42 or lane_distance(x,y)<margin:return False
    if (Vector((x,y))-Vector((CX,CY))).length<7+margin:return False
    for pad in PADS:
        if ((x-pad['x'])/(pad['rx']+margin+1))**2+((y-pad['y'])/(pad['ry']+margin+1))**2<1:
            return False
    return True

# Broad planting masses are deliberately kept away from the lane surfaces.
current='Trees'
print('VESTERGATE_GEOMETRY terrain, three trails, accessible shelves, bridge, gate and crystal ready',flush=True)
TREE_POSITIONS=[]
def surface(x,y):
    z=ground(x,y)
    for a,b,rx,ry,top in TERRACES:
        if ((x-a)/(rx*.85))**2+((y-b)/(ry*.85))**2<1:
            z=max(z,top)
    return z

def tree(x,y,height=9,golden=False):
    z=surface(x,y);radius=.36+height*.025
    trunk=beam('Tree / branching trunk',(x,y,z-.12),(x+.45,y-.1,z+height*.79),radius*2,'timber')
    for dx,dy in [(-1.5,.6),(1.6,.3),(.3,-1.6)]:
        beam('Tree / spreading branch',(x+.2,y,z+height*.45),
            (x+dx,y+dy,z+height*.79),radius*.8,'timber')
    leaves=['leaf gold','leaf gold light'] if golden else ['leaf dark','leaf teal','leaf green','leaf light']
    for i,(dx,dy,zz,s) in enumerate([(-1.8,.4,.77,1),(1.6,.5,.79,1),(.2,-1.6,.77,.92),(0,.1,.91,1.05)]):
        ico('Golden tree crown' if golden else 'Broadleaf tree crown',
            (x+dx,y+dy,z+height*zz),(height*.32*s,height*.29*s,height*.18*s),
            leaves[i%len(leaves)],2)
    TREE_POSITIONS.append((x,y,height,z))

attempts=0
while len(TREE_POSITIONS)<70 and attempts<5000:
    attempts+=1
    x=rng.uniform(-57,57);y=rng.uniform(-31,69)
    if not is_clear(x,y,5.4):continue
    if any((Vector((x,y))-Vector(p[:2])).length<6 for p in TREE_POSITIONS):continue
    tree(x,y,rng.uniform(7.8,11.7),golden=(x>12 and rng.random()<.17))
for x,y in [(17,46),(33,4),(-17,55)]:
    if is_clear(x,y,4):tree(x,y,8.8,True)

current='Ground greenery'
# Combined grass meshes stay easy to hide/edit and avoid thousands of tiny objects.
gv=[];gf=[];gi=[]
for i in range(2200):
    x=rng.uniform(-59,59);y=rng.uniform(-39,70)
    if not is_clear(x,y,.90):continue
    z=surface(x,y)+.025
    for j in range(5):
        a=rng.random()*math.tau;h=rng.uniform(.25,.65);w=rng.uniform(.09,.19)
        dx,dy=math.cos(a),math.sin(a);k=len(gv)
        gv += [(x-dy*w,y+dx*w,z),(x+dy*w,y-dx*w,z),
               (x+dx*h*.55,y+dy*h*.55,z+h)]
        gf.append((k,k+1,k+2));gi.append(rng.randrange(3))
mesh('Grass tufts / clustered edge planting',gv,gf,['grass light','grass rim','fern'],gi)
for i in range(120):
    x=rng.uniform(-58,58);y=rng.uniform(-38,69)
    if not is_clear(x,y,1.65):continue
    z=surface(x,y);r=rng.uniform(.5,1.25)
    ico('Low shrub',(x,y,z+r*.35),(r,r*.85,r*.65),rng.choice(['leaf teal','leaf green','fern']),1)
for i in range(110):
    x=rng.uniform(-58,58);y=rng.uniform(-40,68)
    if not is_clear(x,y,1.4):continue
    z=surface(x,y);r=rng.uniform(.3,1.05)
    ico('Ground rock',(x,y,z+.12),(r,r*.76,r*.65),rng.choice(['rock','rock light']),1)
# Long leaves, flowers and a few hanging vines communicate the reference's greenery.
for i in range(80):
    x=rng.uniform(-54,54);y=rng.uniform(-36,63)
    if not is_clear(x,y,1.65):continue
    z=surface(x,y);vv=[];ff=[]
    for j in range(7):
        a=j*math.tau/7+rng.random()*.3;length=rng.uniform(.65,1.4)
        d=Vector((math.cos(a),math.sin(a)));side=Vector((-d.y,d.x));p=Vector((x,y))
        points=[(*p,z),(*(p+d*length*.5+side*.17),z+.48),
                (*(p+d*length),z+.2),(*(p+d*length*.5-side*.17),z+.48)]
        k=len(vv);vv+=points;ff += [(k,k+1,k+2),(k,k+2,k+3)]
    mesh('Broad-leaf ground plant',vv,ff,['fern'])
for i in range(170):
    x=rng.uniform(-51,51);y=rng.uniform(-35,62)
    if not is_clear(x,y,.9):continue
    z=surface(x,y)
    for j in range(3):
        dx,dy=rng.uniform(-.35,.35),rng.uniform(-.35,.35)
        ico('Wildflower patch',(x+dx,y+dy,z+.35),(.14,.14,.17),
            'flower blue' if i%3 else 'flower pink',1)
for x,y,rx,ry,z in TERRACES[:9]:
    for i in range(6):
        a=-math.pi*.35+i*.26
        px=x+math.cos(a)*rx;py=y+math.sin(a)*ry
        for j in range(5):
            zz=z-.3-j*.43
            ico('Trailing cliff vine',(px+.1*math.sin(j),py,zz),(.23,.12,.25),'leaf teal',1)

current='Landmarks'
LAMPS=[]
def lantern(x,y,z):
    target=nearest_road_point(x,y);direction=(target-Vector((x,y))).normalized()
    reach=Vector((x,y))+direction*.65;hang=Vector((x,y))+direction*.60
    post=beam('Lantern post',(x,y,z),(x,y,z+2.7),.17)
    post['Road target']=[*target];post['Facing direction']=[*direction]
    beam('Lantern bracket',(x,y,z+2.7),(*reach,z+2.7),.15)
    pane=box('Lantern glowing pane',(*hang,z+2.23),(.27,.27,.42),'warm light')
    post['Lantern pane']=pane.name
    for zz in [z+1.96,z+2.5]:box('Lantern iron cap',(*hang,zz),(.42,.42,.09),'iron')
    LAMPS.append(dict(position=[x,y,z],road_target=[*target],facing=[*direction]))
for x,y in [(-30,10),(-30,35),(-5,-20),(7,26),(28,15),(28,-6),(-5,-40),(5,-40)]:
    if lane_distance(x,y)>.25:lantern(x,y,ground(x,y))

def sign(x,y,label,mat):
    z=ground(x,y)
    for dx in [-1.3,1.3]:beam('Trail entry marker',(x+dx,y,z),(x+dx,y,z+3),.17)
    box('Trail marker board',(x,y,z+2.6),(3.4,.18,.65),'timber')
    # The sign faces south, towards the defending gate.
    data=bpy.data.curves.new('Trail sign lettering','FONT');data.body=label
    data.align_x='CENTER';data.align_y='CENTER';data.size=.32;data.extrude=.002
    ob=bpy.data.objects.new('Vestergate / '+label+' sign',data);groups[current].objects.link(ob)
    ob.location=(x,y-.103,z+2.6);ob.rotation_euler=(math.pi/2,0,0)
    data.materials.append(materials['scale figure'])
    for dx in [-1.3,1.3]:
        mesh('Trail-colored pennant',[(x+dx,y,z+2.1),(x+dx+.6,y,z+1.8),
            (x+dx,y,z+1.3)],[(0,1,2)],[mat])
for lane in LANES:
    x,y=lane['points'][0]
    # Offset the sign to the side, leaving the route itself open.
    sign(x-4.7,y+1,{'left':'WOODLAND','centre':'GATE ROAD','right':'RIDGE'}[lane['id']],lane['color'])

current='Scale figures'
def figure(x,y,z):
    for dx in [-.13,.13]:
        beam('1.8m figure leg',(x+dx,y,z+.08),(x+dx,y,z+.83),.15,'scale figure')
    box('1.8m figure torso',(x,y,z+1.14),(.47,.25,.63),'scale figure',.06)
    ico('1.8m figure head',(x,y,z+1.63),(.18,.18,.2),'scale figure',2)
    for dx in [-.34,.34]:
        beam('1.8m figure arm',(x+dx*.8,y,z+1.38),(x+dx,y,z+.91),.12,'scale figure')
figure(*SPAWN)
figure(PADS[2]['x'],PADS[2]['y'],PADS[2]['z']+.02)
figure(37,27,4.25)

current='Lighting'
world=bpy.data.worlds.new('Vestergate / Cool woodland daylight');scene.world=world
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.38,.57,.66,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
light=bpy.data.lights.new('Vestergate / Afternoon sun','SUN');light.energy=2.4
light.angle=math.radians(18);light.color=(1,.87,.66)
ob=bpy.data.objects.new(light.name,light);groups[current].objects.link(ob)
ob.rotation_euler=(math.radians(28),math.radians(-25),math.radians(-35))
light=bpy.data.lights.new('Vestergate / Sky softbox','AREA');light.energy=5500
light.shape='DISK';light.size=65;light.color=(.58,.80,1)
ob=bpy.data.objects.new(light.name,light);groups[current].objects.link(ob);ob.location=(-20,-5,55)
light=bpy.data.lights.new('Vestergate / Crystal glow','POINT');light.energy=100
light.color=(.11,.72,1);light.shadow_soft_size=2
ob=bpy.data.objects.new(light.name,light);groups[current].objects.link(ob);ob.location=(0,CY,3.5)

current='Cameras'
CAMERAS={}
def camera(key,name,pos,target,lens=42,ortho=None):
    data=bpy.data.cameras.new(name);data.lens=lens;data.clip_end=700;data.clip_start=.1
    if ortho:data.type='ORTHO';data.ortho_scale=ortho
    obj=bpy.data.objects.new('Vestergate / '+name,data);groups[current].objects.link(obj)
    obj.location=pos;obj.rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler()
    CAMERAS[key]=obj;return obj
camera('overview','01 Battlefield overview',(108,133,119),(0,3,1),ortho=185)
camera('plan','02 Three-lane terrain plan',(0,6,170),(0,6,0),ortho=200)
camera('arrival','03 Outside the kingdom gate',(4,-43.5,2.15),(0,18,3.0),lens=19)
camera('gate','04 Crystal and kingdom walls',(35,-7,19),(0,-44,6.4),lens=32)
camera('ridge','05 Ridge crossing and defence terraces',(53,38,34),(29,23,4),lens=36)
scene.camera=CAMERAS['overview']
scene.render.engine='CYCLES';scene.cycles.samples=SAMPLES
scene.cycles.use_denoising=False
scene.cycles.max_bounces=5;scene.cycles.diffuse_bounces=2;scene.cycles.glossy_bounces=2
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=1600;scene.render.resolution_y=1200
scene.render.resolution_percentage=int(os.environ.get('ATHERIA_VESTERGATE_RESOLUTION_PERCENT','100'))
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=.2

# A useful saved material-preview viewport, rather than an empty or wireframe scene.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.clip_end=700
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.region_3d.view_distance=165
            area.spaces.active.region_3d.view_location=(0,3,1)
            area.spaces.active.region_3d.view_rotation=CAMERAS['overview'].rotation_euler.to_quaternion()
            area.spaces.active.overlay.show_extras=False
bpy.ops.object.select_all(action='DESELECT')

# Geometric checks: no terrace body can intersect a lane's usable width.
checks=[]
for pad in PADS:
    clear=float('inf')
    for lane in LANES:
        for p in lane['samples']:
            q=Vector((p.x-pad['x'],p.y-pad['y']))
            if q.length<.001:clear=-100;continue
            u=q.normalized()
            edge=1/math.sqrt((u.x/pad['rx'])**2+(u.y/pad['ry'])**2)
            clear=min(clear,q.length-edge*1.15-lane['width']/2)
    checks.append(dict(id=pad['id'],minimum_lane_clearance_metres=round(clear,3),
        access='jump',ledge_height_metres=pad['ledge_height']))
    assert clear>.05, 'Defence terrace overlaps a trail: '+pad['id']+' '+str(clear)
lengths={}
for lane in LANES:
    pp=[Vector((p.x,p.y,trail_height(*p))) for p in lane['samples']]
    lengths[lane['id']]=round(sum((a-b).length for a,b in zip(pp,pp[1:])),2)
manifest=dict(stage='Blender visual blockout; not connected to Roblox',
    coordinate_system='metres, Z up, gates south (-Y)',
    crystal=[0,CY,.8],player_spawn=list(SPAWN),
    lane_lengths_metres=lengths,
    lanes=[dict(id=l['id'],name=l['label'],width=l['width'],
        centreline=[[round(p.x,4),round(p.y,4),round(trail_height(*p),4)] for p in l['samples']]) for l in LANES],
    defence_terraces=PADS,tree_count=len(TREE_POSITIONS),lamps=LAMPS,
    roads='Dirt surfaces conformed to actual terrain, with matching dirt shoulders',
    removed_vantages=['D7','D8'],revision=2,
    scale_figure_height_metres=1.83,checks=checks,
    live_roblox_validation=False)
(OUT/'VESTERGATE_LAYOUT.json').write_text(json.dumps(manifest,indent=2))
projections={}
bpy.context.view_layer.update()
for key,cam in CAMERAS.items():
    projections[key]={}
    anchors={'crystal':(0,CY,4),'spawn':SPAWN,'gate':(0,-47,13)}
    anchors.update({p['id']:(p['x'],p['y'],p['z']+.25) for p in PADS})
    anchors.update({l['id']:tuple([*l['samples'][22],trail_height(*l['samples'][22])+.3]) for l in LANES})
    for name,pos in anchors.items():
        p=world_to_camera_view(scene,cam,Vector(pos))
        projections[key][name]=[round(p.x,6),round(1-p.y,6),round(p.z,4)]
(OUT/'CAMERA_ANNOTATIONS.json').write_text(json.dumps(projections,indent=2))
scene['Blockout validation']='6 jump-access grass terraces; three dirt routes; see VESTERGATE_LAYOUT.json'
scene.render.filepath=str(OUT/'vestergate_overview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'vestergate_blockout.blend'))
print('VESTERGATE_SAVED',str(OUT),json.dumps(lengths),flush=True)
if RENDER:
    wanted=os.environ.get('ATHERIA_VESTERGATE_VIEWS','overview,plan,arrival,gate,ridge').split(',')
    for key in wanted:
        assert key in CAMERAS,key
        scene.camera=CAMERAS[key]
        scene.render.filepath=str(OUT/('vestergate_'+key+'.png'))
        bpy.ops.render.render(write_still=True)
        print('VESTERGATE_RENDERED',key,flush=True)
    scene.camera=CAMERAS['overview']
    scene.render.filepath=str(OUT/'vestergate_overview.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'vestergate_blockout.blend'))
print('VESTERGATE_COMPLETE',flush=True)
