"""Finish the expanded Lantern Tavern in Blender 4.3+. Leaderboard stays blank.
Run with the expanded tavern scene active. Save after inspecting the result.
"""
import bpy, bmesh, math, random
from mathutils import Vector
s=bpy.context.scene
assert any('Leaderboard dark face' in o.name for o in s.objects),'Open the expanded tavern scene first.'
rng=random.Random(901)
name='Tavern / Finished details'
old=next((c for c in s.collection.children if c.get('atheria_tavern_finish') or c.name==name),None)
if old:
    for o in list(old.objects):bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.collections.remove(old)
col=bpy.data.collections.new(name);s.collection.children.link(col);col['atheria_tavern_finish']=True

def shader(mat,light,dark,stretch=(1,1,1),scale=6,rough=.7,metal=0):
    mat.diffuse_color=(*light,1);mat.use_nodes=True
    n=mat.node_tree.nodes;n.clear();l=mat.node_tree.links
    out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled')
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    l.new(p.outputs[0],out.inputs['Surface'])
    uv=n.new('ShaderNodeTexCoord');mult=n.new('ShaderNodeVectorMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=stretch
    l.new(uv.outputs['Generated'],mult.inputs[0])
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=3
    l.new(mult.outputs[0],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=(*dark,1)
    ramp.color_ramp.elements[1].position=.85;ramp.color_ramp.elements[1].color=(*light,1)
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.2;bump.inputs['Distance'].default_value=.014
    l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    return mat,p

def material(name,light,dark,**kw):
    m=bpy.data.materials.get('TF / '+name) or bpy.data.materials.new('TF / '+name)
    return shader(m,light,dark,**kw)[0]

used={m for o in s.objects if o.type in {'MESH','CURVE','FONT'} for m in o.data.materials if m}
for m in used:
    label=m.name.split(' / ')[-1].split('.')[0]
    if label=='timber':shader(m,(.21,.105,.048),(.065,.028,.013),stretch=(11,11,.45),rough=.77)
    elif label in ['floor','table'] or label.startswith('floor variation'):
        if label.startswith('floor variation'):
            index=int(label.rsplit(' ',1)[1]);base=(.32+index*.018,.17+index*.012,.078+index*.006)
        else:base=(.38,.205,.092) if label=='floor' else (.32,.16,.063)
        shader(m,base,tuple(v*.52 for v in base),stretch=(12,.5,6),scale=5,rough=.64)
    elif label=='plaster':shader(m,(.48,.405,.295),(.32,.27,.19),scale=24,rough=.92)
    elif label in ['stone','stone light']:
        light=(.36,.38,.34) if label=='stone' else (.53,.52,.44)
        m,p=shader(m,light,tuple(v*.7 for v in light),scale=18,rough=.86)
        n=m.node_tree.nodes;l=m.node_tree.links
        uv=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(1,1,1)
        # Object coordinates keep masonry courses at a consistent physical size.
        sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['Object'],sep.inputs[0])
        combine=n.new('ShaderNodeCombineXYZ');l.new(sep.outputs['X'],combine.inputs['X']);l.new(sep.outputs['Z'],combine.inputs['Y'])
        brick=n.new('ShaderNodeTexBrick');brick.inputs['Scale'].default_value=1.5
        brick.inputs['Brick Width'].default_value=.8;brick.inputs['Row Height'].default_value=.28
        brick.inputs['Mortar Size'].default_value=.012;brick.inputs['Mortar Smooth'].default_value=.006
        brick.inputs['Color1'].default_value=(*light,1);brick.inputs['Color2'].default_value=(*tuple(v*.75 for v in light),1)
        brick.inputs['Mortar'].default_value=(.12,.125,.11,1)
        l.new(combine.outputs[0],brick.inputs['Vector']);l.new(brick.outputs['Color'],p.inputs['Base Color'])
    elif label=='iron':shader(m,(.105,.12,.13),(.025,.033,.04),scale=9,rough=.34,metal=.8)
    elif label=='bronze':shader(m,(.52,.33,.11),(.22,.12,.035),scale=8,rough=.38,metal=.65)
    elif label=='mug':shader(m,(.47,.48,.44),(.20,.22,.21),scale=9,rough=.3,metal=.72)
    elif label=='bottle':
        _,p=shader(m,(.075,.20,.105),(.018,.052,.03),scale=4,rough=.2)
        p.inputs['Coat Weight'].default_value=.35
    elif label=='dark':shader(m,(.045,.055,.047),(.018,.023,.021),scale=15,rough=.9)
    elif label=='coals':
        _,p=shader(m,(.15,.035,.012),(.025,.008,.004),scale=22)
        p.inputs['Emission Color'].default_value=(.65,.07,.006,1);p.inputs['Emission Strength'].default_value=.8

wood=material('Barrel staves',(.34,.18,.075),(.12,.055,.022),stretch=(10,10,.4),rough=.73)
char=material('Charred timber',(.085,.043,.02),(.018,.012,.008),stretch=(10,10,.4),rough=.94)
ceramic=material('Glazed earthenware',(.54,.32,.16),(.29,.15,.065),scale=5,rough=.3)
bread=material('Rustic bread',(.58,.35,.12),(.28,.12,.025),scale=18,rough=.9)
liquid=material('Dark ale',(.055,.025,.008),(.025,.009,.003),scale=12,rough=.16)
rope=material('Rope',(.29,.20,.10),(.13,.09,.046),scale=24,rough=.95)
rugmat=material('Wine wool',(.23,.05,.038),(.085,.02,.018),scale=95,rough=.98)
trim=material('Woven rug border',(.39,.28,.13),(.21,.14,.065),scale=80,rough=.95)
metal=next(m for m in used if m.name.split(' / ')[-1].split('.')[0]=='iron')
gold=next(m for m in used if m.name.split(' / ')[-1].split('.')[0]=='bronze')
flame=bpy.data.materials.get('TF / Golden flame') or bpy.data.materials.new('TF / Golden flame');flame.use_nodes=True
p=flame.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(1,.45,.06,1)
p.inputs['Emission Color'].default_value=(1,.5,.09,1);p.inputs['Emission Strength'].default_value=4

def mesh(name,verts,faces,mat):
    data=bpy.data.meshes.new('TF / '+name);data.from_pydata(verts,[],faces);data.update()
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    o=bpy.data.objects.new('TF / '+name,data);col.objects.link(o);data.materials.append(mat);return o

def box(name,pos,size,mat):
    p=Vector(pos);h=Vector(size)/2
    vs=[p+Vector((x*h.x,y*h.y,z*h.z)) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    return mesh(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)

def curve(name,points,mat,width=.01):
    data=bpy.data.curves.new('TF / '+name,'CURVE');data.dimensions='3D';data.bevel_depth=width;data.bevel_resolution=2
    sp=data.splines.new('POLY');sp.points.add(len(points)-1)
    for p,v in zip(sp.points,points):p.co=(*v,1)
    o=bpy.data.objects.new('TF / '+name,data);col.objects.link(o);data.materials.append(mat);return o

def disc(name,pos,r,depth,mat):
    x,y,z=pos;n=24;vs=[(x+r*math.cos(i*math.tau/n),y+r*math.sin(i*math.tau/n),z+dz) for dz in [-depth/2,depth/2] for i in range(n)]
    return mesh(name,vs,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)

# Curved flames replace the pointed blockout cones.
for o in list(s.objects):
    if o.type!='MESH':continue
    label=o.name.split(' / ')[-1].split('.')[0]
    if label in ['Candle flame','Hearth flame']:
        zs=[v.co.z for v in o.data.vertices];height=max(zs)-min(zs)
        radius=max(Vector((v.co.x,v.co.y)).length for v in o.data.vertices)
        verts=[];faces=[];sides=12;levels=7
        for j in range(levels):
            t=j/(levels-1);r=radius*max(.015,math.sin(math.pi*(.12+.88*t)))**.8
            for i in range(sides):
                a=i*math.tau/sides;verts.append((r*math.cos(a)+radius*.65*t*t,r*math.sin(a),min(zs)+height*t))
        faces=[tuple(reversed(range(sides))),tuple(range((levels-1)*sides,levels*sides))]
        faces += [(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i) for j in range(levels-1) for i in range(sides)]
        new=mesh('Temporary flame',verts,faces,flame);o.data=new.data;bpy.data.objects.remove(new,do_unlink=True)
        for face in o.data.polygons:face.use_smooth=True
    elif label=='Hearth log':
        zs=[v.co.z for v in o.data.vertices];h=max(zs)-min(zs);n=12
        vs=[(.105*math.cos(i*math.tau/n),.105*math.sin(i*math.tau/n),z) for z in [-h/2,h/2] for i in range(n)]
        new=mesh('Temporary log',vs,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],char)
        o.data=new.data;bpy.data.objects.remove(new,do_unlink=True)
    elif label=='Stave barrel':
        o.data.materials.clear();o.data.materials.append(wood)
        zs=[v.co.z for v in o.data.vertices];r=max(Vector((v.co.x,v.co.y)).length for v in o.data.vertices)
        for i in range(12):
            a=i*math.tau/12;pts=[o.matrix_world@Vector((r*math.cos(a),r*math.sin(a),z)) for z in [min(zs)*.94,max(zs)*.94]]
            curve('Barrel stave seam',pts,char,.005)
    elif label=='Tankard':
        ps=[o.matrix_world@Vector(v) for v in o.bound_box];center=sum(ps,Vector())/8;top=max(p.z for p in ps)
        disc('Ale in tankard',(center.x,center.y,top+.003),.074,.008,liquid)
        curve('Tankard handle',[(center.x+.09+.065*math.sin(i*math.pi/20),center.y,center.z+.085*math.cos(i*math.pi/20)) for i in range(21)],metal,.014)
    elif label=='Chandelier chain':
        zs=[v.co.z for v in o.data.vertices];lo,hi=min(zs),max(zs);count=max(5,int((hi-lo)/.10));verts=[];faces=[]
        for j in range(count):
            for i in range(12):
                a=i*math.tau/12
                radial=Vector((math.cos(j*math.pi/2),math.sin(j*math.pi/2),0))
                for k in range(4):
                    b=k*math.tau/4
                    local=radial*((.035+.008*math.cos(b))*math.sin(a))+Vector((0,0,lo+(j+.5)*(hi-lo)/count+(.059+.008*math.cos(b))*math.cos(a)))
                    local+=Vector((-radial.y,radial.x,0))*(.008*math.sin(b));verts.append(o.matrix_world@local)
            base=j*48
            for i in range(12):
                for k in range(4):faces.append((base+i*4+k,base+((i+1)%12)*4+k,base+((i+1)%12)*4+(k+1)%4,base+i*4+(k+1)%4))
        mesh('Linked iron chain',verts,faces,metal);o.hide_render=True

# Small useful objects enrich tables without obstructing the floor routes.
for x,y in [(-.55,-2.65),(0,-.3),(6.35,2.75),(-2,5.85)]:
    disc('Earthenware plate',(x,y,1.14),.22,.035,ceramic)
    for dx,dy in [(-.07,0),(.05,.04)]:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.095,location=(x+dx,y+dy,1.22))
        o=bpy.context.object;o.name='TF / Bread roll';o.scale=(1.2,.8,.65)
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o);o.data.materials.append(bread)
box('Woven aisle rug',(3.8,.3,.062),(1.5,10.8,.015),rugmat)
for x in [3.08,4.52]:box('Rug border',(x,.3,.072),(.045,10.75,.006),trim)
for y in [-5.06,5.66]:box('Rug border',(3.8,y,.072),(1.47,.045,.006),trim)

# Narrow lattice windows with cool daylight, between the structural posts.
window=material('Blue leaded glass',(.11,.23,.29),(.035,.09,.12),scale=8,rough=.3)
p=window.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(.14,.29,.40,1);p.inputs['Emission Strength'].default_value=.35
for x,y in [(-8.96,-1.8),(8.96,4.9)]:
    box('Leaded window glass',(x,y,2.65),(.045,1,1.65),window)
    for yy in [y-.55,y+.55]:box('Window jamb',(x*.997,yy,2.65),(.12,.11,1.85),wood)
    for zz in [1.78,3.52]:box('Window rail',(x*.997,y,zz),(.12,1.2,.12),wood)
    for slope in [-1,1]:
        for intercept in [-1,-.5,0,.5,1]:
            points=[]
            for u in [-.48,.48]:
                v=slope*u+intercept
                if -.79<=v<=.79:points.append((u,v))
            for v in [-.79,.79]:
                u=(v-intercept)/slope
                if -.48<=u<=.48:points.append((u,v))
            if len(points)>=2:curve('Diamond glazing lead',[(x*.996,y+u,2.65+v) for u,v in points[:2]],metal,.014)
    data=bpy.data.lights.new('TF Window fill','AREA');data.energy=65;data.size=1.2;data.color=(.58,.75,1)
    o=bpy.data.objects.new('TF Window fill',data);col.objects.link(o);o.location=(x*.94,y,2.65)
    o.rotation_euler=(Vector((0,y,1.9))-o.location).to_track_quat('-Z','Y').to_euler()

for o in s.objects:
    if o.type!='LIGHT':continue
    if o.name.startswith('Chandelier pool'):o.data.color=(1,.78,.48)
    elif o.name.startswith('Wall flame'):o.data.color=(1,.6,.3)
    elif o.name.startswith('Hearth warm pool'):o.data.color=(1,.48,.19)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.23
# Readable soft fill, still subordinate to the hearth and candles.
data=bpy.data.lights.new('TF Warm room bounce','AREA');data.energy=180;data.size=7;data.color=(1,.82,.61)
o=bpy.data.objects.new('TF Warm room bounce',data);col.objects.link(o);o.location=(0,-1,4.25)

# Keep the leaderboard entirely blank.
for o in list(s.objects):
    if any('leaderboard' in c.name.lower() for c in o.users_collection) and o.type=='FONT':bpy.data.objects.remove(o,do_unlink=True)
    elif o.name.startswith('Tavern / Leaderboard row divider'):bpy.data.objects.remove(o,do_unlink=True)
s.cycles.samples=96;s.cycles.adaptive_threshold=.035
s.render.resolution_x=1400;s.render.resolution_y=1050
s['Tavern finish']='Aged timber, plaster, masonry, iron chains, tableware, lattice windows, layered warm/cool light.'
s['Leaderboard']='Blank framed face; clear viewing area retained.'
bpy.context.view_layer.update()
print('TAVERN_FINISH_APPLIED',len(col.objects),'detail objects',flush=True)
