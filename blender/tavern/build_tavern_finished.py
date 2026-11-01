"""The Lantern Tavern: finished expanded interior with a blank leaderboard.
Creates a separate scene; preserves your existing lobby scene.
Run in Blender's Text Editor, or blender -b --python build_tavern_finished.py.
"""
import bpy, math, random, os
from pathlib import Path
from mathutils import Vector

OUT = Path(os.environ.get('ATHERIA_TAVERN_OUT', bpy.path.abspath('//Tavern_Finished') if bpy.data.filepath else str(Path.home()/'Atheria_Tavern_Finished')))
OUT.mkdir(parents=True, exist_ok=True)
RENDER = os.environ.get('ATHERIA_TAVERN_RENDER','1') != '0'
SAMPLES = 96
rng = random.Random(87)
scene = bpy.data.scenes.new('The Lantern Tavern / Finished Interior')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
collections = {}
for name in ['Architecture','Roof and ceiling','Furniture','Hearth','Leaderboard','Props','Lights','Cameras']:
    c=bpy.data.collections.new('Tavern / '+name);scene.collection.children.link(c);collections[name]=c
current='Architecture'
mats={}
def material(name,color,emission=0,metallic=0):
    m=bpy.data.materials.new('Tavern / '+name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=.72;p.inputs['Metallic'].default_value=metallic
    if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    mats[name]=m;return m
for n,c in [('timber',(.16,.075,.033)),('floor',(.32,.17,.08)),('table',(.27,.13,.053)),
    ('plaster',(.36,.29,.20)),('stone',(.25,.28,.27)),('stone light',(.40,.41,.36)),
    ('iron',(.055,.065,.069)),('bronze',(.40,.25,.075)),('wax',(.78,.64,.37)),
    ('bottle',(.065,.14,.095)),('label',(.65,.54,.35)),('mug',(.35,.36,.32)),
    ('red',(.36,.095,.06)),('cream',(.65,.55,.36)),('dark',(.027,.022,.019))]:material(n,c)
material('flame',(1,.30,.035),5);material('coals',(.85,.11,.015),2)
floors=[material('floor variation '+str(i),(.26+i*.021,.125+i*.014,.054+i*.008)) for i in range(6)]
def move(obj,name,mat):
    obj.name='Tavern / '+name
    for col in list(obj.users_collection):col.objects.unlink(obj)
    collections[current].objects.link(obj)
    obj.data.materials.append(mats[mat] if isinstance(mat,str) else mat)
    return obj
def box(name,pos,size,mat='timber',bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=move(bpy.context.object,name,mat)
    o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        m=o.modifiers.new('Soft blockout edges','BEVEL');m.width=bevel;m.segments=2
    return o
def cylinder(name,pos,radius,depth,mat='iron',vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=pos)
    return move(bpy.context.object,name,mat)
def beam(name,a,b,width=.2,mat='timber'):
    a,b=Vector(a),Vector(b);o=box(name,(a+b)/2,(width,width,(b-a).length),mat)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def torus(name,pos,radius,thickness,mat='iron'):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=thickness,major_segments=32,minor_segments=6,location=pos)
    return move(bpy.context.object,name,mat)
def point(name,pos,power=70,color=(1,.56,.24),radius=.4):
    data=bpy.data.lights.new(name,'POINT');data.energy=power;data.color=color;data.shadow_soft_size=radius
    o=bpy.data.objects.new(name,data);collections['Lights'].objects.link(o);o.location=pos;return o
def candle(x,y,z):
    cylinder('Candle',(x,y,z+.11),.045,.22,'wax',8)
    bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=.035,radius2=0,depth=.13,location=(x,y,z+.28));move(bpy.context.object,'Candle flame','flame')
def stool(x,y):
    box('Stool seat',(x,y,.62),(.55,.55,.12),'table')
    for dx in [-.19,.19]:
        for dy in [-.19,.19]:beam('Stool leg',(x+dx,y+dy,.05),(x+dx*.85,y+dy*.85,.6),.085)
def table(x,y,w,d):
    for i in range(max(3,int(w/.28))):
        n=max(3,int(w/.28));box('Tabletop plank',(x-w/2+(i+.5)*w/n,y,1.05),(w/n-.012,d,.13),'table')
    for dy in [-d*.32,d*.32]:
        box('Trestle',(x,y+dy,.52),(w*.65,.16,.95))
        box('Trestle foot',(x,y+dy,.12),(w*.86,.38,.16))
    beam('Table stretcher',(x,y-d*.32,.35),(x,y+d*.32,.35),.13)
def barrel(x,y,z=.65,r=.45,h=1.25,horizontal=False):
    before=set(scene.objects)
    cylinder('Stave barrel',(x,y,z),r,h,'floor',12)
    for dz in [-h*.35,h*.35]:torus('Barrel hoop',(x,y,z+dz),r+.01,.035)
    for dz in [-h/2,h/2]:cylinder('Barrel end',(x,y,z+dz),r*.94,.04,'table',12)
    if horizontal:
        from mathutils import Matrix
        transform=Matrix.Translation((x,y,z))@Matrix.Rotation(math.pi/2,4,'Y')@Matrix.Translation((-x,-y,-z))
        for o in set(scene.objects)-before:o.matrix_world=transform@o.matrix_world
def bottle(x,y,z):
    cylinder('Bottle body',(x,y,z+.15),.085,.3,'bottle',10)
    cylinder('Bottle neck',(x,y,z+.35),.035,.12,'bottle',10)
    box('Bottle label',(x,y-.083,z+.16),(.105,.012,.12),'label',.004)
def mug(x,y,z):
    cylinder('Tankard',(x,y,z+.11),.09,.22,'mug',12)
    torus('Tankard lip',(x,y,z+.22),.09,.012,'iron')

# Expanded 18 x 16.5 metre concept interior; separate interior space.
box('Floor foundation',(0,0,-.14),(18.4,16.9,.28),'dark')
for row in range(46):
    x=-9+(row+.5)*18/46
    for j in range(4):
        y=-8.25+(j+.5)*16.5/4
        box('Worn floorboard',(x,y,0),(18/46-.014,16.5/4-.025,.10),rng.choice(floors),.008)
box('Rear wall',(0,8.35,2.55),(18.3,.22,5.1),'plaster')
left_wall=box('Left wall',(-9.1,0,2.55),(.22,16.8,5.1),'plaster')
right_wall=box('Right wall',(9.1,0,2.55),(.22,16.8,5.1),'plaster')
front=[]
for x in [-5.3,5.3]:front.append(box('Front wall beside entrance',(x,-8.35,2.55),(7.6,.22,5.1),'plaster'))
front.append(box('Entrance overhead',(0,-8.35,4.25),(3,.22,1.7),'plaster'))
for x in [-1.5,1.5]:box('Entrance jamb',(x,-8.26,1.65),(.22,.3,3.3))
box('Entrance lintel',(0,-8.26,3.4),(3.2,.35,.25))
for y in [-8.1,-3.6,3.6,8.1]:
    for x in [-8.9,8.9]:
        box('Wall post',(x,y,2.5),(.28,.28,5))
for x in [-5.4,5.4]:
    for y in [-3.6,3.6]:
        box('Interior post',(x,y,2.35),(.34,.34,4.7))
        for side in [-1,1]:beam('Diagonal knee brace',(x,y,3.6),(x+side*.85,y,4.7),.20)
for z in [.65,2.6,4.65]:
    for x in [-8.95,8.95]:box('Side wall rail',(x,0,z),(.16,16.5,.18))
    box('Rear wall rail',(0,8.20,z),(18,.18,.18))
current='Roof and ceiling'
for y in [-8.1,-3.6,0,3.6,8.1]:box('Ceiling crossbeam',(0,y,4.85),(18.2,.34,.38))
for x in [-5.4,0,5.4]:box('Long ceiling beam',(x,0,4.97),(.32,16.7,.30))
for i in range(45):box('Ceiling plank',(-9+(i+.5)*.4,0,5.15),(.39,16.7,.16),'floor',.008)
current='Furniture'
table(-.6,-1.2,2.25,4.8)
for x in [-2.5,1.3]:
    for y in [-2.5,-1,.5]:stool(x,y)
table(6.4,2.2,1.6,2.1)
for x in [5.05,7.75]:stool(x,2.2)
table(-2,5.4,2.2,1.6)
for y in [4.05,6.75]:stool(-2,y)
box('Bar counter body',(-6.55,2.7,.55),(1.3,6,1.1),'table')
box('Bar counter top',(-6.55,2.7,1.16),(1.45,6.15,.16),'floor')
for y in [1.2,4.9]:stool(-5.2,y)
for z in [1.5,2.15,2.8]:box('Back bar shelf',(-8.68,2.7,z),(.48,5.7,.13))

current='Hearth'
box('Hearth stone slab',(1.5,4.8,.16),(3.2,1.6,.28),'stone')
box('Hearth dark back',(1.5,5.35,1.25),(2.6,.14,2.1),'dark')
for x in [.15,2.85]:box('Stone hearth pier',(x,4.95,1.15),(.45,1,2.1),'stone light')
box('Stone hearth lintel',(1.5,4.95,2.25),(3.15,1.1,.35),'stone light')
verts=[(1.5+sx*w,yy,zz) for w,zz,front_y in [(1.5,2.4,4.35),(.6,4.8,4.95)] for sx,yy in [(-1,front_y),(1,front_y),(1,5.45),(-1,5.45)]]
data=bpy.data.meshes.new('Hearth hood');data.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
hood=bpy.data.objects.new('Tavern / Tapered stone chimney',data);collections[current].objects.link(hood);data.materials.append(mats['stone'])
box('Coal bed',(1.5,4.8,.37),(1.9,.65,.11),'coals')
for i in range(4):beam('Hearth log',(.8+i*.3,4.5,.48),(1.25+i*.3,5.1,.48),.16)
for i in range(5):
    bpy.ops.mesh.primitive_cone_add(vertices=6,radius1=.11,radius2=0,depth=.55+rng.random()*.3,location=(.85+i*.3,4.85,.8));move(bpy.context.object,'Hearth flame','flame')
point('Hearth warm pool',(1.5,4.2,1.2),180,(1,.35,.10),.65)

# Relocate the hearth assembly to the new rear wall, preserving its size.
from mathutils import Matrix
for obj in list(collections['Hearth'].objects):
    obj.matrix_world=Matrix.Translation((.75,2.8,0)) @ obj.matrix_world
for obj in collections['Lights'].objects:
    if obj.name.startswith('Hearth warm pool'):obj.location += Vector((.75,2.8,0))

current='Leaderboard'
box('Leaderboard carved backing',(8.84,-3.1,2.45),(.22,4.8,3.0),'timber')
box('Leaderboard dark face',(8.71,-3.1,2.45),(.045,4.46,2.68),'dark',.012)
for y in [-5.48,-.72]:box('Leaderboard vertical frame',(8.65,y,2.45),(.16,.13,3.12),'bronze')
for z in [.92,3.98]:box('Leaderboard horizontal frame',(8.65,-3.1,z),(.16,4.9,.13),'bronze')
# Board intentionally left blank for future rankings.
# A three-metre-deep viewing area is left unfurnished in front of the board.
point('Leaderboard soft light',(6.7,-3.1,3.4),90,(1,.75,.42),.8)

current='Props'
barrel(-6.75,-5.55,1.2,.8,1.8,True)
for y in [-6.13,-4.97]:
    for x in [-7.4,-6.1]:box('Cask cradle',(x,y,.5),(.15,.15,1))
    beam('Cask support',(-7.4,y,.55),(-6.1,y,.55),.18)
for x,y in [(7.5,6.6),(6.45,7.3)]:barrel(x,y)
for x,y,z in [(-.6,-1.6,1.12),(-1,.5,1.12),(6.4,2.2,1.12),(-2,5.4,1.12),(-6.55,1.7,1.25)]:
    bottle(x-.24,y,z);mug(x+.3,y+.17,z);candle(x,y-.27,z)
for z in [1.57,2.22,2.87]:
    for y in [.5,1.6,3.2,4.9]:bottle(-8.65,y,z)
for x,y,r in [(-.6,-1.2,1.15),(-2.4,4.4,.8),(6.2,2.1,.65)]:
    torus('Iron candle chandelier',(x,y,3.75),r,.055)
    for a in [0,2*math.pi/3,4*math.pi/3]:
        beam('Chandelier chain',(x+r*math.cos(a),y+r*math.sin(a),3.75),(x,y,4.65),.023,'iron')
    for i in range(8):
        a=i*math.pi/4;candle(x+r*math.cos(a),y+r*math.sin(a),3.78)
    point('Chandelier pool',(x,y,3.5),145,(1,.65,.34),.8)
for x,y in [(-8.75,-1.2),(8.75,-6.1),(-5.4,3.6),(8.75,7.0)]:
    beam('Wall torch bracket',(x,y,2.3),(x*.97,y,2.8),.09,'iron')
    candle(x*.97,y,2.8);point('Wall flame',(x*.94,y,2.95),60,(1,.47,.16),.4)
for x in [-5.4,5.4]:
    for j in range(6):
        yy=-3.5+j*.14;zz=4.35-abs(j-2.5)*.05
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.11,location=(x,yy,zz));move(bpy.context.object,'Hanging stored bundle','cream' if j%2 else 'red')

# Cool, subdued entrance fill and warm local fire/candle lighting.
world=bpy.data.worlds.new('Tavern ambient');world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.22,.28,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.18;scene.world=world
data=bpy.data.lights.new('Doorway daylight','AREA');data.energy=240;data.shape='DISK';data.size=5;data.color=(.65,.79,1)
o=bpy.data.objects.new('Doorway daylight',data);collections['Lights'].objects.link(o);o.location=(0,-7.9,3)
o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
def camera(name,pos,target,lens=24,ortho=None):
    data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);collections['Cameras'].objects.link(o)
    o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    data.lens=lens;data.clip_end=300
    if ortho:data.type='ORTHO';data.ortho_scale=ortho
    return o
cameras={
 'arrival':camera('01 Entering the Lantern Tavern',(0,-7.6,1.9),(0,2,2.25),21),
 'hearth':camera('02 Hearth and social bays',(3.8,1.2,1.9),(2.2,7.1,2),24),
 'cutaway':camera('03 Dollhouse cutaway',(-24,-30,24),(0,0,1.7),ortho=29),
 'leaderboard':camera('05 Leaderboard viewing area',(6.5,-3.1,2.45),(8.75,-3.1,2.45),ortho=6.6),
 'plan':camera('04 Floor plan',(0,0,38),(0,0,0),ortho=24),
}
scene.render.engine='CYCLES';scene.cycles.samples=SAMPLES;scene.cycles.max_bounces=5
scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.045
try:
    import _cycles
    scene.cycles.use_denoising=bool(getattr(_cycles,'with_openimagedenoise',False))
except ImportError:scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=min(5,os.cpu_count() or 4)
scene.render.resolution_x=1100;scene.render.resolution_y=825;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.camera=cameras['arrival']
scene['Design']='Timber common room; communal table; side seating; hearth focal point; expanded social space; dedicated leaderboard wall and viewing area.'
scene['Scope']='Finished Blender interior concept. Doorway connection and Roblox import are separate tasks.'
scene['Concept room size']='18 x 16.5 metres; 5.1 metre ceiling; 3 metre entrance opening.'
FINISH_SOURCE = '"""Finish the expanded Lantern Tavern in Blender 4.3+. Leaderboard stays blank.\nRun with the expanded tavern scene active. Save after inspecting the result.\n"""\nimport bpy, bmesh, math, random\nfrom mathutils import Vector\ns=bpy.context.scene\nassert any(\'Leaderboard dark face\' in o.name for o in s.objects),\'Open the expanded tavern scene first.\'\nrng=random.Random(901)\nname=\'Tavern / Finished details\'\nold=next((c for c in s.collection.children if c.get(\'atheria_tavern_finish\') or c.name==name),None)\nif old:\n    for o in list(old.objects):bpy.data.objects.remove(o,do_unlink=True)\n    bpy.data.collections.remove(old)\ncol=bpy.data.collections.new(name);s.collection.children.link(col);col[\'atheria_tavern_finish\']=True\n\ndef shader(mat,light,dark,stretch=(1,1,1),scale=6,rough=.7,metal=0):\n    mat.diffuse_color=(*light,1);mat.use_nodes=True\n    n=mat.node_tree.nodes;n.clear();l=mat.node_tree.links\n    out=n.new(\'ShaderNodeOutputMaterial\');p=n.new(\'ShaderNodeBsdfPrincipled\')\n    p.inputs[\'Roughness\'].default_value=rough;p.inputs[\'Metallic\'].default_value=metal\n    l.new(p.outputs[0],out.inputs[\'Surface\'])\n    uv=n.new(\'ShaderNodeTexCoord\');mult=n.new(\'ShaderNodeVectorMath\');mult.operation=\'MULTIPLY\';mult.inputs[1].default_value=stretch\n    l.new(uv.outputs[\'Generated\'],mult.inputs[0])\n    noise=n.new(\'ShaderNodeTexNoise\');noise.inputs[\'Scale\'].default_value=scale;noise.inputs[\'Detail\'].default_value=3\n    l.new(mult.outputs[0],noise.inputs[\'Vector\'])\n    ramp=n.new(\'ShaderNodeValToRGB\');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=(*dark,1)\n    ramp.color_ramp.elements[1].position=.85;ramp.color_ramp.elements[1].color=(*light,1)\n    l.new(noise.outputs[\'Fac\'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs[\'Base Color\'])\n    bump=n.new(\'ShaderNodeBump\');bump.inputs[\'Strength\'].default_value=.2;bump.inputs[\'Distance\'].default_value=.014\n    l.new(noise.outputs[\'Fac\'],bump.inputs[\'Height\']);l.new(bump.outputs[0],p.inputs[\'Normal\'])\n    return mat,p\n\ndef material(name,light,dark,**kw):\n    m=bpy.data.materials.get(\'TF / \'+name) or bpy.data.materials.new(\'TF / \'+name)\n    return shader(m,light,dark,**kw)[0]\n\nused={m for o in s.objects if o.type in {\'MESH\',\'CURVE\',\'FONT\'} for m in o.data.materials if m}\nfor m in used:\n    label=m.name.split(\' / \')[-1].split(\'.\')[0]\n    if label==\'timber\':shader(m,(.21,.105,.048),(.065,.028,.013),stretch=(11,11,.45),rough=.77)\n    elif label in [\'floor\',\'table\'] or label.startswith(\'floor variation\'):\n        if label.startswith(\'floor variation\'):\n            index=int(label.rsplit(\' \',1)[1]);base=(.32+index*.018,.17+index*.012,.078+index*.006)\n        else:base=(.38,.205,.092) if label==\'floor\' else (.32,.16,.063)\n        shader(m,base,tuple(v*.52 for v in base),stretch=(12,.5,6),scale=5,rough=.64)\n    elif label==\'plaster\':shader(m,(.48,.405,.295),(.32,.27,.19),scale=24,rough=.92)\n    elif label in [\'stone\',\'stone light\']:\n        light=(.36,.38,.34) if label==\'stone\' else (.53,.52,.44)\n        m,p=shader(m,light,tuple(v*.7 for v in light),scale=18,rough=.86)\n        n=m.node_tree.nodes;l=m.node_tree.links\n        uv=n.new(\'ShaderNodeTexCoord\');mapping=n.new(\'ShaderNodeVectorMath\');mapping.operation=\'MULTIPLY\';mapping.inputs[1].default_value=(1,1,1)\n        # Object coordinates keep masonry courses at a consistent physical size.\n        sep=n.new(\'ShaderNodeSeparateXYZ\');l.new(uv.outputs[\'Object\'],sep.inputs[0])\n        combine=n.new(\'ShaderNodeCombineXYZ\');l.new(sep.outputs[\'X\'],combine.inputs[\'X\']);l.new(sep.outputs[\'Z\'],combine.inputs[\'Y\'])\n        brick=n.new(\'ShaderNodeTexBrick\');brick.inputs[\'Scale\'].default_value=1.5\n        brick.inputs[\'Brick Width\'].default_value=.8;brick.inputs[\'Row Height\'].default_value=.28\n        brick.inputs[\'Mortar Size\'].default_value=.012;brick.inputs[\'Mortar Smooth\'].default_value=.006\n        brick.inputs[\'Color1\'].default_value=(*light,1);brick.inputs[\'Color2\'].default_value=(*tuple(v*.75 for v in light),1)\n        brick.inputs[\'Mortar\'].default_value=(.12,.125,.11,1)\n        l.new(combine.outputs[0],brick.inputs[\'Vector\']);l.new(brick.outputs[\'Color\'],p.inputs[\'Base Color\'])\n    elif label==\'iron\':shader(m,(.105,.12,.13),(.025,.033,.04),scale=9,rough=.34,metal=.8)\n    elif label==\'bronze\':shader(m,(.52,.33,.11),(.22,.12,.035),scale=8,rough=.38,metal=.65)\n    elif label==\'mug\':shader(m,(.47,.48,.44),(.20,.22,.21),scale=9,rough=.3,metal=.72)\n    elif label==\'bottle\':\n        _,p=shader(m,(.075,.20,.105),(.018,.052,.03),scale=4,rough=.2)\n        p.inputs[\'Coat Weight\'].default_value=.35\n    elif label==\'dark\':shader(m,(.045,.055,.047),(.018,.023,.021),scale=15,rough=.9)\n    elif label==\'coals\':\n        _,p=shader(m,(.15,.035,.012),(.025,.008,.004),scale=22)\n        p.inputs[\'Emission Color\'].default_value=(.65,.07,.006,1);p.inputs[\'Emission Strength\'].default_value=.8\n\nwood=material(\'Barrel staves\',(.34,.18,.075),(.12,.055,.022),stretch=(10,10,.4),rough=.73)\nchar=material(\'Charred timber\',(.085,.043,.02),(.018,.012,.008),stretch=(10,10,.4),rough=.94)\nceramic=material(\'Glazed earthenware\',(.54,.32,.16),(.29,.15,.065),scale=5,rough=.3)\nbread=material(\'Rustic bread\',(.58,.35,.12),(.28,.12,.025),scale=18,rough=.9)\nliquid=material(\'Dark ale\',(.055,.025,.008),(.025,.009,.003),scale=12,rough=.16)\nrope=material(\'Rope\',(.29,.20,.10),(.13,.09,.046),scale=24,rough=.95)\nrugmat=material(\'Wine wool\',(.23,.05,.038),(.085,.02,.018),scale=95,rough=.98)\ntrim=material(\'Woven rug border\',(.39,.28,.13),(.21,.14,.065),scale=80,rough=.95)\nmetal=next(m for m in used if m.name.split(\' / \')[-1].split(\'.\')[0]==\'iron\')\ngold=next(m for m in used if m.name.split(\' / \')[-1].split(\'.\')[0]==\'bronze\')\nflame=bpy.data.materials.get(\'TF / Golden flame\') or bpy.data.materials.new(\'TF / Golden flame\');flame.use_nodes=True\np=flame.node_tree.nodes.get(\'Principled BSDF\');p.inputs[\'Base Color\'].default_value=(1,.45,.06,1)\np.inputs[\'Emission Color\'].default_value=(1,.5,.09,1);p.inputs[\'Emission Strength\'].default_value=4\n\ndef mesh(name,verts,faces,mat):\n    data=bpy.data.meshes.new(\'TF / \'+name);data.from_pydata(verts,[],faces);data.update()\n    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()\n    o=bpy.data.objects.new(\'TF / \'+name,data);col.objects.link(o);data.materials.append(mat);return o\n\ndef box(name,pos,size,mat):\n    p=Vector(pos);h=Vector(size)/2\n    vs=[p+Vector((x*h.x,y*h.y,z*h.z)) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]\n    return mesh(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)\n\ndef curve(name,points,mat,width=.01):\n    data=bpy.data.curves.new(\'TF / \'+name,\'CURVE\');data.dimensions=\'3D\';data.bevel_depth=width;data.bevel_resolution=2\n    sp=data.splines.new(\'POLY\');sp.points.add(len(points)-1)\n    for p,v in zip(sp.points,points):p.co=(*v,1)\n    o=bpy.data.objects.new(\'TF / \'+name,data);col.objects.link(o);data.materials.append(mat);return o\n\ndef disc(name,pos,r,depth,mat):\n    x,y,z=pos;n=24;vs=[(x+r*math.cos(i*math.tau/n),y+r*math.sin(i*math.tau/n),z+dz) for dz in [-depth/2,depth/2] for i in range(n)]\n    return mesh(name,vs,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)\n\n# Curved flames replace the pointed blockout cones.\nfor o in list(s.objects):\n    if o.type!=\'MESH\':continue\n    label=o.name.split(\' / \')[-1].split(\'.\')[0]\n    if label in [\'Candle flame\',\'Hearth flame\']:\n        zs=[v.co.z for v in o.data.vertices];height=max(zs)-min(zs)\n        radius=max(Vector((v.co.x,v.co.y)).length for v in o.data.vertices)\n        verts=[];faces=[];sides=12;levels=7\n        for j in range(levels):\n            t=j/(levels-1);r=radius*max(.015,math.sin(math.pi*(.12+.88*t)))**.8\n            for i in range(sides):\n                a=i*math.tau/sides;verts.append((r*math.cos(a)+radius*.65*t*t,r*math.sin(a),min(zs)+height*t))\n        faces=[tuple(reversed(range(sides))),tuple(range((levels-1)*sides,levels*sides))]\n        faces += [(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i) for j in range(levels-1) for i in range(sides)]\n        new=mesh(\'Temporary flame\',verts,faces,flame);o.data=new.data;bpy.data.objects.remove(new,do_unlink=True)\n        for face in o.data.polygons:face.use_smooth=True\n    elif label==\'Hearth log\':\n        zs=[v.co.z for v in o.data.vertices];h=max(zs)-min(zs);n=12\n        vs=[(.105*math.cos(i*math.tau/n),.105*math.sin(i*math.tau/n),z) for z in [-h/2,h/2] for i in range(n)]\n        new=mesh(\'Temporary log\',vs,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],char)\n        o.data=new.data;bpy.data.objects.remove(new,do_unlink=True)\n    elif label==\'Stave barrel\':\n        o.data.materials.clear();o.data.materials.append(wood)\n        zs=[v.co.z for v in o.data.vertices];r=max(Vector((v.co.x,v.co.y)).length for v in o.data.vertices)\n        for i in range(12):\n            a=i*math.tau/12;pts=[o.matrix_world@Vector((r*math.cos(a),r*math.sin(a),z)) for z in [min(zs)*.94,max(zs)*.94]]\n            curve(\'Barrel stave seam\',pts,char,.005)\n    elif label==\'Tankard\':\n        ps=[o.matrix_world@Vector(v) for v in o.bound_box];center=sum(ps,Vector())/8;top=max(p.z for p in ps)\n        disc(\'Ale in tankard\',(center.x,center.y,top+.003),.074,.008,liquid)\n        curve(\'Tankard handle\',[(center.x+.09+.065*math.sin(i*math.pi/20),center.y,center.z+.085*math.cos(i*math.pi/20)) for i in range(21)],metal,.014)\n    elif label==\'Chandelier chain\':\n        zs=[v.co.z for v in o.data.vertices];lo,hi=min(zs),max(zs);count=max(5,int((hi-lo)/.10));verts=[];faces=[]\n        for j in range(count):\n            for i in range(12):\n                a=i*math.tau/12\n                radial=Vector((math.cos(j*math.pi/2),math.sin(j*math.pi/2),0))\n                for k in range(4):\n                    b=k*math.tau/4\n                    local=radial*((.035+.008*math.cos(b))*math.sin(a))+Vector((0,0,lo+(j+.5)*(hi-lo)/count+(.059+.008*math.cos(b))*math.cos(a)))\n                    local+=Vector((-radial.y,radial.x,0))*(.008*math.sin(b));verts.append(o.matrix_world@local)\n            base=j*48\n            for i in range(12):\n                for k in range(4):faces.append((base+i*4+k,base+((i+1)%12)*4+k,base+((i+1)%12)*4+(k+1)%4,base+i*4+(k+1)%4))\n        mesh(\'Linked iron chain\',verts,faces,metal);o.hide_render=True\n\n# Small useful objects enrich tables without obstructing the floor routes.\nfor x,y in [(-.55,-2.65),(0,-.3),(6.35,2.75),(-2,5.85)]:\n    disc(\'Earthenware plate\',(x,y,1.14),.22,.035,ceramic)\n    for dx,dy in [(-.07,0),(.05,.04)]:\n        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.095,location=(x+dx,y+dy,1.22))\n        o=bpy.context.object;o.name=\'TF / Bread roll\';o.scale=(1.2,.8,.65)\n        for c in list(o.users_collection):c.objects.unlink(o)\n        col.objects.link(o);o.data.materials.append(bread)\nbox(\'Woven aisle rug\',(3.8,.3,.062),(1.5,10.8,.015),rugmat)\nfor x in [3.08,4.52]:box(\'Rug border\',(x,.3,.072),(.045,10.75,.006),trim)\nfor y in [-5.06,5.66]:box(\'Rug border\',(3.8,y,.072),(1.47,.045,.006),trim)\n\n# Narrow lattice windows with cool daylight, between the structural posts.\nwindow=material(\'Blue leaded glass\',(.11,.23,.29),(.035,.09,.12),scale=8,rough=.3)\np=window.node_tree.nodes.get(\'Principled BSDF\');p.inputs[\'Emission Color\'].default_value=(.14,.29,.40,1);p.inputs[\'Emission Strength\'].default_value=.35\nfor x,y in [(-8.96,-1.8),(8.96,4.9)]:\n    box(\'Leaded window glass\',(x,y,2.65),(.045,1,1.65),window)\n    for yy in [y-.55,y+.55]:box(\'Window jamb\',(x*.997,yy,2.65),(.12,.11,1.85),wood)\n    for zz in [1.78,3.52]:box(\'Window rail\',(x*.997,y,zz),(.12,1.2,.12),wood)\n    for slope in [-1,1]:\n        for intercept in [-1,-.5,0,.5,1]:\n            points=[]\n            for u in [-.48,.48]:\n                v=slope*u+intercept\n                if -.79<=v<=.79:points.append((u,v))\n            for v in [-.79,.79]:\n                u=(v-intercept)/slope\n                if -.48<=u<=.48:points.append((u,v))\n            if len(points)>=2:curve(\'Diamond glazing lead\',[(x*.996,y+u,2.65+v) for u,v in points[:2]],metal,.014)\n    data=bpy.data.lights.new(\'TF Window fill\',\'AREA\');data.energy=65;data.size=1.2;data.color=(.58,.75,1)\n    o=bpy.data.objects.new(\'TF Window fill\',data);col.objects.link(o);o.location=(x*.94,y,2.65)\n    o.rotation_euler=(Vector((0,y,1.9))-o.location).to_track_quat(\'-Z\',\'Y\').to_euler()\n\nfor o in s.objects:\n    if o.type!=\'LIGHT\':continue\n    if o.name.startswith(\'Chandelier pool\'):o.data.color=(1,.78,.48)\n    elif o.name.startswith(\'Wall flame\'):o.data.color=(1,.6,.3)\n    elif o.name.startswith(\'Hearth warm pool\'):o.data.color=(1,.48,.19)\ns.world.node_tree.nodes[\'Background\'].inputs[1].default_value=.23\n# Readable soft fill, still subordinate to the hearth and candles.\ndata=bpy.data.lights.new(\'TF Warm room bounce\',\'AREA\');data.energy=180;data.size=7;data.color=(1,.82,.61)\no=bpy.data.objects.new(\'TF Warm room bounce\',data);col.objects.link(o);o.location=(0,-1,4.25)\n\n# Keep the leaderboard entirely blank.\nfor o in list(s.objects):\n    if any(\'leaderboard\' in c.name.lower() for c in o.users_collection) and o.type==\'FONT\':bpy.data.objects.remove(o,do_unlink=True)\n    elif o.name.startswith(\'Tavern / Leaderboard row divider\'):bpy.data.objects.remove(o,do_unlink=True)\ns.cycles.samples=96;s.cycles.adaptive_threshold=.035\ns.render.resolution_x=1400;s.render.resolution_y=1050\ns[\'Tavern finish\']=\'Aged timber, plaster, masonry, iron chains, tableware, lattice windows, layered warm/cool light.\'\ns[\'Leaderboard\']=\'Blank framed face; clear viewing area retained.\'\nbpy.context.view_layer.update()\nprint(\'TAVERN_FINISH_APPLIED\',len(col.objects),\'detail objects\',flush=True)\n'
exec(compile(FINISH_SOURCE,'finish_tavern.py','exec'), {'__name__':'__main__'})
try:
    text=bpy.data.texts.new('build_tavern_finished.py');text.write(Path(__file__).read_text())
except (NameError,OSError):pass
bpy.context.view_layer.update()
# Check the entrance and main circulation at body height, with lateral offsets.
routes=[[(0,-8.7),(0,-5),(3.8,-4.8),(3.8,5.7),(2.25,6.3)],
        [(3.8,-3.1),(7.1,-3.1)]]
route_checks=[]
for route in routes:route_checks.extend(zip(route,route[1:]))
dg=bpy.context.evaluated_depsgraph_get();checks=0
for a,b in route_checks:
    a,b=Vector((*a,1.3)),Vector((*b,1.3));direction=(b-a).normalized();side=Vector((-direction.y,direction.x,0))
    for offset in [-.28,0,.28]:
        hit,loc,normal,index,obj,matrix=scene.ray_cast(dg,a+side*offset,direction,distance=(b-a).length)
        assert not hit,('Main aisle obstruction',obj.name if obj else None)
        checks+=1
print('TAVERN_CLEARANCE_PASSED',checks,'route probes',flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'atheria_tavern_finished.blend'))
if RENDER:
    for key in ['arrival','hearth','cutaway','leaderboard']:
        hidden=list(collections['Roof and ceiling'].objects)+front+[left_wall] if key in ['cutaway','plan'] else []
        if key=='plan':hidden+=list(collections['Props'].objects)
        for obj in hidden:obj.hide_render=True
        scene.camera=cameras[key];scene.render.filepath=str(OUT/('tavern_'+key+'.png'))
        bpy.ops.render.render(write_still=True)
        for obj in hidden:obj.hide_render=False
        print('TAVERN_RENDERED',key,flush=True)
scene.camera=cameras['arrival']
print('Finished tavern complete:',OUT,flush=True)
