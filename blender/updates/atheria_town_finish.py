"""Atheria town finishing pass. Run in Blender's Scripting workspace on v05.
Preserves the connected roads/walls, inscriptions and statue weapon poses.
Repeatable: new detail geometry is isolated in collection 16 / Finished town.
No external textures, add-ons, NPCs or downloads are required.
"""
import bpy, bmesh, math, random
from mathutils import Matrix, Vector

s = bpy.context.scene
if not bpy.data.objects.get('V05 Joined masonry wall network'):
    raise RuntimeError('Open the revision 05 Atheria town before running this update.')
rng = random.Random(61031)
collection_name = '16 / Finished town'
old = bpy.data.collections.get(collection_name)
if old:
    for ob in list(old.objects): bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(old)
finish = bpy.data.collections.new(collection_name)
s.collection.children.link(finish)

def surface(name, a, b, scale=5, roughness=.72, stretch=(1,1,1), metallic=0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*a, 1); m.use_nodes = True
    n = m.node_tree.nodes; n.clear(); links = m.node_tree.links
    out = n.new('ShaderNodeOutputMaterial'); shader = n.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    links.new(shader.outputs['BSDF'], out.inputs['Surface'])
    tex = n.new('ShaderNodeTexCoord'); mapping = n.new('ShaderNodeVectorMath')
    mapping.operation = 'MULTIPLY'; mapping.inputs[1].default_value = stretch
    links.new(tex.outputs['Generated'], mapping.inputs[0])
    noise = n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 2.5
    links.new(mapping.outputs[0], noise.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=.18; ramp.color_ramp.elements[0].color=(*b,1)
    ramp.color_ramp.elements[1].position=.82; ramp.color_ramp.elements[1].color=(*a,1)
    links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],shader.inputs['Base Color'])
    bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.16
    bump.inputs['Distance'].default_value=.025
    links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],shader.inputs['Normal'])
    return m

def finish_existing(name,a,b,**kw):
    if bpy.data.materials.get(name): return surface(name,a,b,**kw)

finish_existing('plaster',(.79,.68,.48),(.59,.49,.34),scale=7)
finish_existing('wood',(.24,.12,.055),(.09,.038,.019),scale=5,stretch=(8,8,.35))
finish_existing('wood_light',(.48,.28,.115),(.26,.125,.043),scale=4,stretch=(9,9,.4))
finish_existing('bark',(.26,.15,.075),(.11,.065,.032),scale=5,stretch=(5,5,.4))
finish_existing('grass',(.18,.32,.15),(.085,.19,.105),scale=18)
finish_existing('grass_light',(.35,.48,.16),(.18,.31,.095),scale=6)
finish_existing('leaf',(.12,.34,.22),(.045,.17,.13),scale=6)
finish_existing('leaf_light',(.35,.49,.20),(.15,.32,.13),scale=6)
finish_existing('soil',(.17,.125,.075),(.075,.065,.045),scale=24)
finish_existing('cliff',(.29,.35,.38),(.135,.20,.24),scale=5,stretch=(1,1,5))
finish_existing('cliff_light',(.37,.41,.40),(.23,.29,.30),scale=7,stretch=(1,1,4))
finish_existing('canvas',(.48,.10,.31),(.29,.045,.18),scale=80,roughness=.9)
finish_existing('canvas_light',(.88,.67,.32),(.65,.43,.15),scale=80,roughness=.9)
finish_existing('iron',(.13,.17,.19),(.045,.065,.08),scale=8,roughness=.38,metallic=.7)
finish_existing('stone_dark',(.30,.35,.36),(.16,.22,.25),scale=8)
finish_existing('stone_light',(.61,.65,.62),(.43,.49,.49),scale=8)
for m in list(bpy.data.materials):
    if m.name.startswith('Paving variation'):
        c=tuple(m.diffuse_color[:3]); surface(m.name,tuple(min(1,x*1.08) for x in c),tuple(x*.82 for x in c),scale=18)

gold = surface('V06 aged gilt accents',(.68,.43,.12),(.35,.20,.045),scale=8,roughness=.35,metallic=.65)
petals = [surface('V06 blossom '+str(i),a,b,scale=4) for i,(a,b) in enumerate([
    ((.70,.26,.52),(.36,.07,.28)),((.84,.65,.22),(.55,.29,.07)),((.57,.52,.85),(.27,.21,.49))])]
roof_sets=[]
for label,c in [('teal',(.075,.32,.28)),('rust',(.40,.14,.075)),('blue',(.065,.20,.36))]:
    roof_sets.append([surface('V06 '+label+' shingle '+str(i),tuple(v*(.88+i*.075) for v in c),tuple(v*.65 for v in c),scale=8,roughness=.77) for i in range(5)])

def geom(name,vs,fs,mats,indices=None):
    data=bpy.data.meshes.new('V06 '+name); data.from_pydata(vs,[],fs);data.update()
    ob=bpy.data.objects.new('V06 '+name,data);finish.objects.link(ob)
    for mat in mats: data.materials.append(mat)
    if indices:
        for p,i in zip(data.polygons,indices):p.material_index=i
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    return ob

def block(name,center,size,mat,transform=Matrix.Identity(4)):
    c=Vector(center);h=Vector(size)*.5
    vs=[transform @ (c+Vector((x*h.x,y*h.y,z*h.z))) for x,y,z in
        [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    ob=geom(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],[mat])
    bevel=ob.modifiers.new('Soft crafted edges','BEVEL');bevel.width=.035;bevel.segments=2
    return ob

def line(name,points,mat,radius=.04):
    data=bpy.data.curves.new('V06 '+name,'CURVE');data.dimensions='3D';data.resolution_u=2
    data.bevel_depth=radius;data.bevel_resolution=2
    spline=data.splines.new('POLY');spline.points.add(len(points)-1)
    for p,v in zip(spline.points,points):p.co=(*v,1)
    ob=bpy.data.objects.new('V06 '+name,data);finish.objects.link(ob);data.materials.append(mat);return ob

# Shingles form actual overlapping, staggered courses, batched into six meshes.
buildings=[('Tavern',-29,-18,13,12,7.3,90,0),('Forge',-24,23,17,9,7.5,0,1),('Quest Hall',29,16,12,12,9,-90,2)]
for label,x,y,w,d,h,angle,palette in buildings:
    xf=Matrix.Translation((x,y,.3)) @ Matrix.Rotation(math.radians(angle),4,'Z')
    half=(w+1.5)/2; depth=d+1.6; rise=4.4; rows=10; columns=math.ceil(depth/.85)
    for side in [-1,1]:
        vs=[];fs=[];mi=[]
        for row in range(rows):
            t0=row/rows; t1=min(1,(row+1.13)/rows)
            shift=.5 if row%2 else 0
            for j in range(-1,columns+1):
                ya=max(-depth/2,-depth/2+(j+shift)*depth/columns)
                yb=min(depth/2,-depth/2+(j+shift+1)*depth/columns-.025)
                if yb<=ya:continue
                # The top of each course overlaps the next, with a rounded stone lip.
                coords=[(side*half*(1-t0),ya,h+rise*t0+.065),
                        (side*half*(1-t0),yb,h+rise*t0+.065),
                        (side*half*(1-t1),yb,h+rise*t1+.08),
                        (side*half*(1-t1),ya,h+rise*t1+.08)]
                k=len(vs);vs.extend([xf@Vector(p) for p in coords]);fs.append(tuple(range(k,k+4)));mi.append(rng.randrange(5))
        ob=geom(label+' layered shingle slope '+str(side),vs,fs,roof_sets[palette],mi)
        solid=ob.modifiers.new('Tile thickness','SOLIDIFY');solid.thickness=.055
        bevel=ob.modifiers.new('Weathered tile lips','BEVEL');bevel.width=.025;bevel.segments=2
    for j in range(columns):
        yy=-depth/2+(j+.5)*depth/columns
        block(label+' ridge cap',(0,yy,h+rise+.15),(.42,depth/columns-.025,.23),roof_sets[palette][3],xf)
    # Gable ornaments repeat the sacred crystal motif, without extra sign clutter.
    for yy in [-d/2-.19,d/2+.19]:
        pts=[(0,yy,h+2.85),(.45,yy,h+2.1),(0,yy,h+1.35),(-.45,yy,h+2.1),(0,yy,h+2.85)]
        line(label+' gable crystal inlay',[xf@Vector(p) for p in pts],gold,.055)
    # Recessed panel bays receive lower carved trim and small bronze corner studs.
    for xx in [-w/2,w/2]:
        for yy in [-d/2,d/2]:
            block(label+' bronze corner foot',(xx,yy,1.24),(.48,.48,.12),gold,xf)

# Draw finite flower clusters inside existing raised beds only; paths stay clear.
soil_objects=[o for o in s.objects if o.type=='MESH' and o.name.startswith('Garden soil')]
for index,soil in enumerate(soil_objects):
    bb=[soil.matrix_world@Vector(v) for v in soil.bound_box]
    lo=Vector(tuple(min(p[i] for p in bb) for i in range(3)));hi=Vector(tuple(max(p[i] for p in bb) for i in range(3)))
    for j in range(8):
        x=rng.uniform(lo.x+.18,hi.x-.18);y=rng.uniform(lo.y+.18,hi.y-.18);z=hi.z+.33+rng.random()*.20
        line('flower stem',[(x,y,hi.z),(x+.035,y,z)],bpy.data.materials['leaf'],.018)
        vs=[];fs=[]
        for k in range(5):
            a=k*math.tau/5;v=len(vs)
            vs.extend([(x,y,z),(x+.14*math.cos(a-.32),y+.14*math.sin(a-.32),z+.03),
                       (x+.21*math.cos(a),y+.21*math.sin(a),z+.06),
                       (x+.14*math.cos(a+.32),y+.14*math.sin(a+.32),z+.03)])
            fs.append((v,v+1,v+2,v+3))
        geom('garden blossoms',vs,fs,[petals[(index+j)%3]])

# Fountain jets and concentric ripples give the market a visible source of motion.
water=surface('V06 turquoise fountain water',(.11,.48,.51),(.025,.20,.25),scale=16,roughness=.19,metallic=.25)
oldwater=bpy.data.objects.get('Fountain water surface')
if oldwater:oldwater.data.materials.clear();oldwater.data.materials.append(water)
for a in range(0,360,60):
    a=math.radians(a);points=[]
    for j in range(25):
        t=j/24;r=.65+.80*t;z=2.26+.85*math.sin(math.pi*t)-1.10*t
        points.append((17+r*math.cos(a),-16+r*math.sin(a),z))
    line('falling fountain stream',points,water,.028)
for r in [.73,1.12,1.55]:
    line('fountain ripple',[(17+r*math.cos(j*math.tau/96),-16+r*math.sin(j*math.tau/96),1.149) for j in range(97)],water,.012)

# Canvas edge stitching follows the existing market canopies exactly.
for ob in list(s.objects):
    if ob.type=='MESH' and ob.name.startswith('Plum and gold canopy'):
        verts=[ob.matrix_world@v.co for v in ob.data.vertices]
        for p in ob.data.polygons:
            for a,b in zip(p.vertices,list(p.vertices[1:])+[p.vertices[0]]):
                if a<b:line('market canopy piping',[verts[a]+Vector((0,0,.015)),verts[b]+Vector((0,0,.015))],gold,.018)

# Preserve outward-facing arch stone surfaces in a freshly rebuilt scene too.
for ob in s.objects:
    if ob.type=='MESH' and 'voussoir' in ob.name:
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()

def town_camera(key,pos,target,scale=None,lens=28):
    data=bpy.data.cameras.new('V06 '+key);ob=bpy.data.objects.new('V06 '+key,data);finish.objects.link(ob)
    ob.location=pos;ob.rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler()
    data.lens=lens;data.clip_end=1000
    if scale:
        data.type='ORTHO';data.ortho_scale=scale
        # Keep the entire orthographic ray plane outside foreground walls.
        ob.location += ob.rotation_euler.to_quaternion() @ Vector((0,0,100))
    return ob

TOWN_CAMERAS={
 'town':town_camera('Town overview',(83,-112,119),(0,1,2),112),
 'tavern':town_camera('Tavern courtyard',(-6,-30,13),(-26,-16,4),38),
 'forge':town_camera('Forge courtyard',(-3,-1,16),(-23,20,5),42),
 'sanctuary':town_camera('Sanctuary and quest hall',(1,-1,13),(18,18,5),46),
 'market':town_camera('Festival court',(43,-39,20),(19,-17,2),43),
 'street':town_camera('Arrival street',(-15,-28,3.3),(-2,-2,6),lens=25),
}
s.render.engine='CYCLES';s.cycles.samples=128;s.cycles.use_adaptive_sampling=True
s.cycles.adaptive_threshold=.035
try:
    import _cycles
    s.cycles.use_denoising=bool(getattr(_cycles,'with_openimagedenoise',False))
except ImportError:s.cycles.use_denoising=False
s.render.resolution_x=1600;s.render.resolution_y=1200;s.render.resolution_percentage=100
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
s.camera=TOWN_CAMERAS['town']
s['Revision']='06 — full town materials, shingled roofs, gilt detailing, planted gardens and working fountain'
s['Finish note']='Procedural stylized town art pass; no external textures. Static fountain arcs preview future Roblox VFX.'
bpy.context.view_layer.update()
print('ATHERIA_TOWN_FINISHED',len(finish.objects),'new detail objects',flush=True)
