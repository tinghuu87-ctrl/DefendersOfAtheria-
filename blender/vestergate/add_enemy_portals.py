"""Enemy portal models for Blender 4.3+. Paste into Text Editor and press Alt+P.
Adds three portals to the open Vestergate map and creates a comparison scene.
Also works in an empty file, creating the three-design comparison on its own.
No external textures or add-ons. Enemy spawning is not implemented by this script.
"""
import bpy
import math
import random
import os
import json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

RENDER = os.environ.get('ATHERIA_PORTALS_RENDER', '0') == '1'
OUT = Path(os.environ.get('ATHERIA_PORTALS_OUT',
    bpy.path.abspath('//Vestergate_Portals') if bpy.data.filepath
    else str(Path.home() / 'Vestergate_Portals')))
OUT.mkdir(parents=True, exist_ok=True)
PREFIX = 'Atheria enemy portals / '
original_scene = bpy.context.scene
map_scene = next((s for s in [original_scene]+list(reversed(list(bpy.data.scenes)))
    if any(o.get('Enemy route') for o in s.objects)), None)
# Replace only this installer's own objects when run again.
for obj in list(bpy.data.objects):
    if obj.get('Atheria enemy portal asset'):
        bpy.data.objects.remove(obj, do_unlink=True)
for col in list(bpy.data.collections):
    if col.get('Atheria enemy portal collection'):
        bpy.data.collections.remove(col)
study = bpy.data.scenes.get('Atheria / Enemy portal design studies')
if study is None:
    study = bpy.data.scenes.new('Atheria / Enemy portal design studies')
for obj in list(study.objects):
    if obj.get('Portal presentation'):
        bpy.data.objects.remove(obj, do_unlink=True)

def collection(scene, name):
    col = bpy.data.collections.new(PREFIX+name)
    col['Atheria enemy portal collection'] = True
    scene.collection.children.link(col)
    return col

def mark(obj):
    obj['Atheria enemy portal asset'] = True
    obj['CanCollide'] = False
    obj['CanTouch'] = False
    return obj

def material(name, color, emission=0, metal=0):
    mat = bpy.data.materials.get(PREFIX+name) or bpy.data.materials.new(PREFIX+name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = .46
    p.inputs['Metallic'].default_value = metal
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = emission
    return mat

obsidian = material('Fractured obsidian', (.075,.052,.11), metal=.4)
iron = material('Dark iron', (.065,.045,.09), metal=.7)
bronze = material('Tarnished gold', (.23,.12,.035), metal=.7)
violet = material('Violet edge', (.37,.008,1), 7)
pink = material('Magenta edge', (.72,.015,.85), 9)
pale = material('Hot lavender', (.65,.17,1), 13)
gold = material('Golden sparks', (1,.48,.075), 8)

def mesh(col, parent, name, verts, faces, mat, uv=False):
    data = bpy.data.meshes.new(PREFIX+name)
    data.from_pydata(verts, [], faces)
    data.materials.append(mat)
    data.update()
    if uv:
        layer = data.uv_layers.new(name='Portal UV')
        for poly in data.polygons:
            for loop in poly.loop_indices:
                i = data.loops[loop].vertex_index
                layer.data[loop].uv = ((i % 2), (i//2)/max(1,len(verts)//2-1))
    obj = mark(bpy.data.objects.new(PREFIX+name, data))
    col.objects.link(obj)
    obj.parent = parent
    if mat.name.startswith(PREFIX) and any(t in mat.name for t in ['wisps','strands','cores','void','edge','sparks','lavender']):
        obj.visible_diffuse = False
        obj.visible_glossy = False
        obj.visible_shadow = False
    return obj

def empty(col, parent, name, position=(0,0,0)):
    obj = mark(bpy.data.objects.new(PREFIX+name, None))
    col.objects.link(obj)
    obj.parent = parent
    obj.location = position
    obj.empty_display_type = 'PLAIN_AXES'
    obj.empty_display_size = .35
    return obj

def beam(col, parent, name, a, b, width, mat):
    a,b = Vector(a),Vector(b)
    axis = (b-a).normalized()
    side = axis.cross(Vector((0,1,0)))
    if side.length<.01: side = axis.cross(Vector((1,0,0)))
    side.normalize();up=axis.cross(side).normalized()
    verts=[tuple(p+side*s*width+up*t*width) for p in [a,b]
        for s,t in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    return mesh(col,parent,name,verts,[(0,3,2,1),(4,5,6,7),
        (0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)

def ribbon_material(name, color, strength):
    mat = bpy.data.materials.get(PREFIX+name) or bpy.data.materials.new(PREFIX+name)
    mat.use_nodes=True
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    nodes.clear()
    uv=nodes.new('ShaderNodeTexCoord');separate=nodes.new('ShaderNodeSeparateXYZ')
    links.new(uv.outputs['UV'],separate.inputs[0])
    mul=nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=math.pi
    links.new(separate.outputs['X'],mul.inputs[0])
    sine=nodes.new('ShaderNodeMath');sine.operation='SINE';links.new(mul.outputs[0],sine.inputs[0])
    power=nodes.new('ShaderNodeMath');power.operation='POWER';power.inputs[1].default_value=.65
    links.new(sine.outputs[0],power.inputs[0])
    scale=nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(2,9,1)
    links.new(uv.outputs['UV'],scale.inputs[0])
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.5;noise.inputs['Detail'].default_value=3
    links.new(scale.outputs[0],noise.inputs['Vector'])
    breakup=nodes.new('ShaderNodeValToRGB')
    breakup.color_ramp.elements[0].position=.26;breakup.color_ramp.elements[0].color=(.04,.04,.04,1)
    breakup.color_ramp.elements[1].position=.66;breakup.color_ramp.elements[1].color=(1,1,1,1)
    links.new(noise.outputs['Fac'],breakup.inputs[0])
    mask=nodes.new('ShaderNodeMath');mask.operation='MULTIPLY'
    links.new(power.outputs[0],mask.inputs[0]);links.new(breakup.outputs[0],mask.inputs[1])
    transparent=nodes.new('ShaderNodeBsdfTransparent')
    emission=nodes.new('ShaderNodeEmission');emission.inputs[0].default_value=(*color,1)
    emission.inputs[1].default_value=strength
    mix=nodes.new('ShaderNodeMixShader');links.new(mask.outputs[0],mix.inputs[0])
    links.new(transparent.outputs[0],mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2])
    output=nodes.new('ShaderNodeOutputMaterial');links.new(mix.outputs[0],output.inputs['Surface'])
    return mat

soft = ribbon_material('Soft violet wisps', (.13,.002,.55), 1.8)
strand = ribbon_material('Electric purple strands', (.25,.004,.85), 4.5)
hot = ribbon_material('Bright spiral cores', (.65,.06,1), 7)

def vortex_material():
    mat=bpy.data.materials.get(PREFIX+'Swirling void') or bpy.data.materials.new(PREFIX+'Swirling void')
    mat.use_nodes=True;nodes,links=mat.node_tree.nodes,mat.node_tree.links;nodes.clear()
    def op(kind,a,b=None):
        n=nodes.new('ShaderNodeMath');n.operation=kind
        for i,v in enumerate([a,b]):
            if v is None:continue
            if isinstance(v,(int,float)):n.inputs[i].default_value=v
            else:links.new(v,n.inputs[i])
        return n.outputs[0]
    uv=nodes.new('ShaderNodeTexCoord');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(uv.outputs['UV'],sep.inputs[0])
    x=op('SUBTRACT',sep.outputs['X'],.5);z=op('SUBTRACT',sep.outputs['Y'],.5)
    radius=op('MULTIPLY',op('SQRT',op('ADD',op('MULTIPLY',x,x),op('MULTIPLY',z,z))),2)
    angle=op('ARCTAN2',z,x)
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=8;noise.inputs['Detail'].default_value=4
    links.new(uv.outputs['UV'],noise.inputs['Vector'])
    phase=op('ADD',op('ADD',op('MULTIPLY',angle,5),op('MULTIPLY',radius,19)),op('MULTIPLY',noise.outputs['Fac'],2.6))
    wave=op('POWER',op('MAXIMUM',op('SINE',phase),0),3)
    centre=op('MINIMUM',op('MAXIMUM',op('MULTIPLY',op('SUBTRACT',radius,.19),1.8),0),1)
    mask=op('MULTIPLY',centre,op('ADD',.06,op('MULTIPLY',wave,.94)))
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.004,.0001,.012,1)
    ramp.color_ramp.elements[1].color=(.62,.04,1,1)
    mid=ramp.color_ramp.elements.new(.42);mid.color=(.10,.001,.32,1)
    links.new(mask,ramp.inputs[0])
    emission=nodes.new('ShaderNodeEmission');emission.inputs[1].default_value=2.5
    links.new(ramp.outputs['Color'],emission.inputs[0])
    out=nodes.new('ShaderNodeOutputMaterial');links.new(emission.outputs[0],out.inputs['Surface'])
    return mat

void=vortex_material()
terrain=None
if map_scene:
    terrain=next((o for o in map_scene.objects if o.type=='MESH' and 'Grassland and terraced ridge foundation' in o.name),None)
terrain_bvh=None
if terrain:
    terrain_bvh=BVHTree.FromPolygons([terrain.matrix_world@v.co for v in terrain.data.vertices],
        [tuple(p.vertices) for p in terrain.data.polygons])
def floor(x,y):
    hit=terrain_bvh.ray_cast(Vector((x,y,80)),Vector((0,0,-1)),160) if terrain_bvh else (None,)
    return hit[0].z if hit[0] is not None else 0

def animation_curves(obj):
    """Read the object's own slot on Blender 4.4+/5; keep 4.3 support."""
    data=obj.animation_data
    if data is None or data.action is None:return
    action=data.action;slot=getattr(data,'action_slot',None)
    if slot is not None:
        for layer in action.layers:
            for strip in layer.strips:
                if strip.type!='KEYFRAME':continue
                bag=strip.channelbag(slot)
                if bag is not None:yield from bag.fcurves
    else:
        yield from getattr(action,'fcurves',())

def portal_glow(scene):
    """Preserve the existing compositor and support Blender 5 node groups."""
    if hasattr(scene,'compositing_node_group'):
        tree=scene.compositing_node_group
        if tree is None:
            tree=bpy.data.node_groups.new(PREFIX+scene.name+' compositor','CompositorNodeTree')
            scene.compositing_node_group=tree
        if not any(s.item_type=='SOCKET' and s.in_out=='OUTPUT' and s.name=='Image'
                   for s in tree.interface.items_tree):
            tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
        output=next((n for n in tree.nodes if n.type=='GROUP_OUTPUT' and n.is_active_output),None)
        output=output or tree.nodes.new('NodeGroupOutput')
    else:
        scene.use_nodes=True;tree=scene.node_tree
        output=next((n for n in tree.nodes if n.type=='COMPOSITE'),None) or tree.nodes.new('CompositorNodeComposite')
    nodes,links=tree.nodes,tree.links
    for node in nodes:
        if node.type=='R_LAYERS':node.scene=scene
    if nodes.get('Atheria Portal Glow'):return
    socket=output.inputs['Image']
    previous=socket.links[0].from_socket if socket.is_linked else None
    if previous is None:
        layer=nodes.new('CompositorNodeRLayers');layer.scene=scene;previous=layer.outputs['Image']
    glow=nodes.new('CompositorNodeGlare');glow.name='Atheria Portal Glow'
    if glow.inputs.get('Type') is not None:
        glow.inputs['Type'].default_value='Fog Glow'
        glow.inputs['Quality'].default_value='Medium'
    else:
        glow.glare_type='FOG_GLOW';glow.quality='MEDIUM'
    if glow.inputs.get('Threshold') is not None:
        glow.inputs['Threshold'].default_value=2
        glow.inputs['Size'].default_value=.25;glow.inputs['Strength'].default_value=.4
    else:
        glow.threshold=2;glow.size=8;glow.mix=-.60
    links.new(previous,glow.inputs['Image']);links.new(glow.outputs['Image'],socket)

def portal(col, name, position, forward, variant):
    rand=random.Random(370+variant);r=3.4;centre=r-.60
    root=empty(col,None,name,position);f=Vector(forward).normalized();side=Vector((f.y,-f.x))
    root.rotation_euler[2]=math.atan2(-f.x,f.y)
    root['Design']=name;root['Aperture diameter metres']=2*r;root['Preview animation']='Frames 1–120'
    energy=empty(col,root,name+' / rotating energy',(0,0,centre))
    # A concave, UV-mapped void surface gives the spiral a recessed dark centre.
    verts=[(0,-.85,0)];n=128;rings=20
    for j in range(1,rings+1):
        radius=r*j/rings
        for i in range(n):
            a=i*math.tau/n;verts.append((radius*math.cos(a),-.85*(1-j/rings)**2,radius*math.sin(a)))
    faces=[(0,1+(i+1)%n,1+i) for i in range(n)]
    for j in range(rings-1):
        a=1+j*n;b=a+n
        faces += [(a+i,a+(i+1)%n,b+(i+1)%n,b+i) for i in range(n)]
    disc=mesh(col,energy,name+' / recessed vortex',verts,faces,void)
    uv=disc.data.uv_layers.new(name='Portal UV')
    for loop in disc.data.loops:
        x,y,z=verts[loop.vertex_index];uv.data[loop.index].uv=(x/(2*r)+.5,z/(2*r)+.5)
    # Soft broad wisps, bright spiral ribbons and thin hot cores are actual mesh.
    for layer,count,mat,width in [(0,11,soft,.27),(1,[4,5,3][variant],strand,.14),(2,5,hot,.035)]:
        for arm in range(count):
            vv=[];steps=112;phase=arm*math.tau/count+variant*.37+rand.uniform(-.32,.32)
            turns=rand.uniform(.66,1.1);start=rand.uniform(0,.09);end=rand.uniform(.69,.94) if layer==2 else 1
            for i in range(steps):
                t=start+(end-start)*i/(steps-1)
                radius=r*(.99-.83*t)+.035*r*math.sin(t*31+phase)
                angle=phase+t*math.tau*turns+.27*math.sin(t*11+phase*2)+.065*math.sin(t*43+phase)
                w=width*(.15+.95*max(0,math.sin(math.pi*t))**.8)*(.8+.25*math.sin(t*23+phase))
                for sign in [-1,1]:
                    rr=radius+sign*w
                    vv.append((rr*math.cos(angle),.035+layer*.028-.66*(1-radius/r)**2,
                        rr*math.sin(angle)))
            mesh(col,energy,name+' / spiral ribbon',vv,
                [(i*2,i*2+1,i*2+3,i*2+2) for i in range(steps-1)],mat,uv=True)
    # Broken obsidian rim. Variant-specific outward talons keep the designs distinct.
    pieces=[7,10,5][variant]
    for i in range(pieces):
        angle=i*math.tau/pieces+.16*math.sin(i*2+variant)
        span=[.42,.34,.52][variant];vv=[];steps=6
        for depth in [-.30,.10]:
            for radius in [r+.10,r+.43]:
                for j in range(steps):
                    a=angle+(j/(steps-1)-.5)*span
                    vv.append((radius*math.cos(a),depth,centre+radius*math.sin(a)))
        ff=[]
        for j in range(steps-1):
            ff += [(j,j+1,j+1+steps,j+steps),
                   (j+2*steps,j+3*steps,j+1+3*steps,j+1+2*steps),
                   (j,j+2*steps,j+1+2*steps,j+1),
                   (j+steps,j+1+steps,j+1+3*steps,j+3*steps)]
        ff += [(0,steps,3*steps,2*steps),(steps-1,3*steps-1,4*steps-1,2*steps-1)]
        mesh(col,root,name+' / broken rim',vv,ff,obsidian if i%3 else iron)
        if i%2==variant%2:
            a=angle+.10;tip_r=r+[1.15,.85,1.45][variant]
            base=Vector(((r+.25)*math.cos(a),-.12,centre+(r+.25)*math.sin(a)))
            tip=Vector((tip_r*math.cos(a+.15),-.25,centre+tip_r*math.sin(a+.15)))
            tangent=Vector((-math.sin(a)*.34,0,math.cos(a)*.34))
            mesh(col,root,name+' / obsidian talon',[tuple(base-tangent),tuple(base+tangent),
                tuple(base+Vector((0,.5,0))),tuple(tip)],[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],obsidian)
        a=angle;beam(col,root,name+' / glowing rim incision',
            ((r+.31)*math.cos(a-.10),.112,centre+(r+.31)*math.sin(a-.10)),
            ((r+.31)*math.cos(a+.10),.112,centre+(r+.31)*math.sin(a+.10)),.018,pink if variant==1 else violet)
    # Broken rune arcs lie on the ground without adding a physical floor obstruction.
    for k in range(3):
        vv=[];steps=42
        for i in range(steps):
            a=k*math.tau/3+i/(steps-1)*1.55+.2*variant
            for rr in [r+.38,r+.47]:
                x,y=rr*math.cos(a),rr*math.sin(a)
                wx=position[0]+side.x*x+f.x*y;wy=position[1]+side.y*x+f.y*y
                z=(floor(wx,wy)-position[2] if col.name.startswith(PREFIX+'Map') else 0)+.045
                vv.append((x,y,z))
        mesh(col,root,name+' / ground rune arc',vv,
            [(2*i,2*i+1,2*i+3,2*i+2) for i in range(steps-1)],violet if k%2 else pink)
    for i in range(22):
        a=rand.uniform(0,math.tau);rr=rand.uniform(r*.85,r+1.0)
        p=Vector((rr*math.cos(a),rand.uniform(.20,.9),centre+rr*math.sin(a)))
        if p.z<.12:continue
        d=Vector((-math.sin(a),.1,math.cos(a)))*rand.uniform(.12,.38)
        beam(col,root,name+' / drifting spark',p,p+d,.014,gold if i%3 else pale)
    light=bpy.data.lights.new(PREFIX+name+' / violet spill','POINT')
    light.energy=500;light.color=(.48,.025,1);light.shadow_soft_size=1.8
    obj=mark(bpy.data.objects.new(light.name,light));col.objects.link(obj);obj.parent=root;obj.location=(0,1.0,centre)
    for label,distance in [('EnemySpawn',.9),('FirstWaypoint',3.2)]:
        z=floor(position[0]+f.x*distance,position[1]+f.y*distance)-position[2] if col.name.startswith(PREFIX+'Map') else 0
        empty(col,root,name+' / '+label,(0,distance,z+.12))
    energy.rotation_euler[1]=variant*.31;energy.keyframe_insert('rotation_euler',index=1,frame=1)
    energy.rotation_euler[1]+=math.tau;energy.keyframe_insert('rotation_euler',index=1,frame=121)
    for curve in animation_curves(energy):
        for key in curve.keyframe_points:key.interpolation='LINEAR'
        if not any(m.type=='CYCLES' for m in curve.modifiers):curve.modifiers.new('CYCLES')
    energy.rotation_euler[1]=variant*.31
    return root

names=['Thornrift','Voidmaw','Stormscar'];roots=[];manifest=[]
if map_scene:
    col=collection(map_scene,'Map lane entrances')
    for index,lane in enumerate(['left','centre','right']):
        road=next(o for o in map_scene.objects if o.get('Enemy route') and o.get('Lane')==lane)
        columns=road.data.polygons[0].vertices[1]
        first=sum((road.matrix_world@v.co for v in road.data.vertices[:columns]),Vector())/columns
        second=sum((road.matrix_world@v.co for v in road.data.vertices[columns:2*columns]),Vector())/columns
        direction=Vector((second.x-first.x,second.y-first.y)).normalized()
        position=(first.x,first.y,floor(first.x,first.y))
        root=portal(col,names[index],position,direction,index);root['Lane']=lane;roots.append(root)
        manifest.append(dict(lane=lane,design=names[index],position=list(position),forward=list(direction),aperture_diameter=6.8))

col=collection(study,'Three design studies')
for i,name in enumerate(names):portal(col,name+' study',((i-1)*10,0,0),(0,1),i)
bpy.context.window.scene=study
study.unit_settings.system='METRIC';study.frame_end=120
study.cycles.samples=64;study.render.resolution_x=1600;study.render.resolution_y=1100
world=bpy.data.worlds.get(PREFIX+'Study world') or bpy.data.worlds.new(PREFIX+'Study world')
world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.03,.055,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.65;study.world=world
stage=material('Study floor',(.04,.045,.065))
stage.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
stage.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.1
floor_col=collection(study,'Presentation')
floor_obj=mesh(floor_col,None,'Study floor',[(-32,-14,-.025),(32,-14,-.025),(32,20,-.025),(-32,20,-.025)],[(0,1,2,3)],stage)
floor_obj['Portal presentation']=True
ld=bpy.data.lights.new(PREFIX+'Study softbox','AREA');ld.energy=3000;ld.shape='DISK';ld.size=20;ld.color=(.58,.65,1)
obj=mark(bpy.data.objects.new(ld.name,ld));floor_col.objects.link(obj);obj.location=(0,3,15)

def camera(scene,name,pos,target,ortho=None,lens=40):
    col=collection(scene,name+' camera');data=bpy.data.cameras.new(PREFIX+name);data.lens=lens;data.clip_end=500
    if ortho:data.type='ORTHO';data.ortho_scale=ortho
    obj=mark(bpy.data.objects.new(PREFIX+name,data));col.objects.link(obj);obj.location=pos
    obj.rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler()
    return obj

study.camera=camera(study,'Three portal designs',(11,32,14),(0,0,2.5),ortho=34)
views=[('designs',study,study.camera)]
if map_scene:
    root=roots[1];bpy.context.view_layer.update()
    f=Vector((*manifest[1]['forward'],0));side=Vector((f.y,-f.x,0));p=root.location
    close=camera(map_scene,'06 Enemy portal close-up',p+f*17+side*4+Vector((0,0,5)),p+Vector((0,0,2.7)),lens=40)
    views += [('portal',map_scene,close)]
    for key,prefix in [('overview','01 Battlefield overview'),('plan','02 Three-lane terrain plan')]:
        cam=next(o for o in map_scene.objects if o.type=='CAMERA' and o.name.startswith('Vestergate / '+prefix))
        views.append((key,map_scene,cam))
for s in [study]+([map_scene] if map_scene else []):
    s.render.engine='CYCLES';s.cycles.use_denoising=False;s.cycles.transparent_max_bounces=16
    s.render.threads_mode='FIXED';s.render.threads=8;s.frame_set(1)
    portal_glow(s)
study.view_settings.view_transform='AgX';study.view_settings.look='AgX - Medium High Contrast'
active=map_scene or study;bpy.context.window.scene=active
filename='vestergate_with_portals.blend' if map_scene else 'atheria_enemy_portals.blend'
(OUT/'PORTAL_LAYOUT.json').write_text(json.dumps(dict(designs=names,portals=manifest,animation_frames=[1,120],
    stage='Blender visual assets; Roblox spawning and VFX integration pending'),indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename))
if RENDER:
    wanted=os.environ.get('ATHERIA_PORTALS_VIEWS','designs,portal,overview,plan').split(',')
    for key,s,cam in views:
        if key not in wanted:continue
        old=(s.camera,s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage,s.cycles.samples,s.render.filepath)
        bpy.context.window.scene=s;s.camera=cam;s.render.resolution_x=1600
        s.render.resolution_y=1200 if key in ['overview','plan'] else 1100
        s.render.resolution_percentage=int(os.environ.get('ATHERIA_PORTALS_RESOLUTION_PERCENT','100'))
        s.cycles.samples=int(os.environ.get('ATHERIA_PORTALS_SAMPLES','32'))
        s.render.image_settings.file_format='PNG';s.render.filepath=str(OUT/('enemy_portals_'+key+'.png'))
        bpy.ops.render.render(write_still=True,scene=s.name)
        s.camera,s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage,s.cycles.samples,s.render.filepath=old
        print('PORTAL_RENDERED',key,flush=True)
    bpy.context.window.scene=active;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename))
print('ENEMY_PORTALS_READY',str(OUT/filename),flush=True)
