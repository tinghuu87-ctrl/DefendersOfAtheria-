"""The Lantern Tavern: expanded interior with leaderboard area.
Creates a separate scene; preserves your existing lobby scene.
Run in Blender's Text Editor, or blender -b --python build_tavern_expanded.py.
"""
import bpy, math, random, os
from pathlib import Path
from mathutils import Vector

OUT = Path(os.environ.get('ATHERIA_TAVERN_OUT', bpy.path.abspath('//Tavern_Expanded') if bpy.data.filepath else str(Path.home()/'Atheria_Tavern_Expanded')))
OUT.mkdir(parents=True, exist_ok=True)
RENDER = True
SAMPLES = 32
rng = random.Random(87)
scene = bpy.data.scenes.new('The Lantern Tavern / Expanded Interior')
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
scene['Scope']='Separate Blender interior blockout. Doorway connection and Roblox import are future tasks.'
scene['Concept room size']='18 x 16.5 metres; 5.1 metre ceiling; 3 metre entrance opening.'
try:
    text=bpy.data.texts.new('build_tavern_expanded.py');text.write(Path(__file__).read_text())
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
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'atheria_tavern_expanded.blend'))
if RENDER:
    for key in ['arrival','hearth','cutaway','plan','leaderboard']:
        hidden=list(collections['Roof and ceiling'].objects)+front+[left_wall] if key in ['cutaway','plan'] else []
        if key=='plan':hidden+=list(collections['Props'].objects)
        for obj in hidden:obj.hide_render=True
        scene.camera=cameras[key];scene.render.filepath=str(OUT/('tavern_'+key+'.png'))
        bpy.ops.render.render(write_still=True)
        for obj in hidden:obj.hide_render=False
        print('TAVERN_RENDERED',key,flush=True)
scene.camera=cameras['arrival']
print('Tavern blockout complete:',OUT,flush=True)
