"""Reuse Atheria's portal assets in Blender 4.3+. Paste and press Alt+P.
Works with the existing portal file, or with Atheria_Portal_Library.blend
beside the current file. AUTO uses tagged lanes, selected empties, or the cursor.
"""
import bpy
import math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

MODE = 'AUTO'  # AUTO, LANES, MARKERS, or CURSOR
DESIGN = 'Voidmaw'  # Thornrift, Voidmaw, or Stormscar
SCALE = 1.0
FACING_DEGREES = 0.0  # Extra rotation around vertical Z
PLACEMENT_ID = 'EnemyPortal'  # Change for additional cursor placements
LIBRARY_PATH = ''  # Optional absolute path to Atheria_Portal_Library.blend
LINK_LIBRARY = True  # Linked assets update when their library is saved/reloaded
GROUND_OBJECT_NAME = ''  # Optional terrain mesh name; otherwise detected
LANE_DESIGNS = {'left': 'Thornrift', 'centre': 'Voidmaw', 'right': 'Stormscar'}
NAMES = ('Thornrift', 'Voidmaw', 'Stormscar')
CATALOG = 'b750b98f-12e8-43d4-98c9-89434be233ad'

def descendants(root):
    return [root]+[obj for child in root.children for obj in descendants(child)]

def asset(name):
    return next((c for c in bpy.data.collections if c.get('Atheria portal asset')==name),None)

def tag_asset(col,name):
    col['Atheria portal asset']=name;col.use_fake_user=True;col.asset_mark()
    col.asset_data.catalog_id=CATALOG
    col.asset_data.description='Reusable Atheria enemy portal: '+name
    for tag in ['Atheria','Enemy','Portal','Reusable']:col.asset_data.tags.new(tag)

def make_assets_from_models():
    for name in NAMES:
        if asset(name):continue
        candidates=[o for o in bpy.data.objects if o.get('Design') in [name,name+' study']
            and o.get('Atheria enemy portal asset')]
        source=next((o for o in candidates if o.get('Design')==name+' study'),None) or next(iter(candidates),None)
        if source is None:continue
        col=bpy.data.collections.new('Atheria Portal / '+name);copies={}
        objects=[o for o in descendants(source) if not any(t in o.name for t in ['ground rune arc',' / EnemySpawn',' / FirstWaypoint'])]
        for obj in objects:
            clone=obj.copy();clone.name='Portal master / '+obj.name.split(' / ',1)[-1]
            if 'Atheria enemy portal asset' in clone:del clone['Atheria enemy portal asset']
            clone['Atheria portal source']=True;col.objects.link(clone);copies[obj]=clone
        for obj,clone in copies.items():
            clone.parent=copies.get(obj.parent);clone.matrix_parent_inverse=Matrix.Identity(4)
            clone.matrix_basis=obj.matrix_basis.copy()
        root=copies[source];root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1)
        root['Design']=name
        tag_asset(col,name)
        if not asset('Ground runes'):
            ground=bpy.data.collections.new('Atheria Portal / Ground runes')
            for obj in descendants(source):
                if obj.type!='MESH' or 'ground rune arc' not in obj.name:continue
                clone=obj.copy();clone.data=obj.data.copy();clone.parent=None
                clone.matrix_world=Matrix.Identity(4)
                if 'Atheria enemy portal asset' in clone:del clone['Atheria enemy portal asset']
                clone['Atheria portal source']=True
                for v in clone.data.vertices:v.co.z=.045
                ground.objects.link(clone)
            tag_asset(ground,'Ground runes')

def ensure_assets():
    if all(asset(n) for n in (*NAMES,'Ground runes')):return
    candidates=[Path(LIBRARY_PATH).expanduser()] if LIBRARY_PATH else []
    if bpy.data.filepath:candidates.append(Path(bpy.data.filepath).parent/'Atheria_Portal_Library.blend')
    if '__file__' in globals():candidates.append(Path(__file__).resolve().parent/'Atheria_Portal_Library.blend')
    library=next((p for p in candidates if p.is_file()),None)
    if library:
        missing=['Atheria Portal / '+n for n in (*NAMES,'Ground runes') if not asset(n)]
        with bpy.data.libraries.load(str(library),link=LINK_LIBRARY) as (available,loaded):
            assert all(n in available.collections for n in missing),'Portal library is missing a required asset.'
            loaded.collections=missing
    else:make_assets_from_models()
    assert all(asset(n) for n in (*NAMES,'Ground runes')),'Open the portal-model file, or put Atheria_Portal_Library.blend beside your map and run again.'

def place(scene, key, design, position, yaw, scale, terrain=None):
    assert design in NAMES and scale>0
    col=next((c for c in scene.collection.children if c.get('Atheria portal placements')),None)
    if col is None:
        col=bpy.data.collections.new('Atheria / Reusable portal placements')
        col['Atheria portal placements']=True;scene.collection.children.link(col)
    old=next((o for o in scene.objects if o.get('Atheria portal placement')==key),None)
    if old:
        for obj in reversed(descendants(old)):bpy.data.objects.remove(obj,do_unlink=True)
    obj=bpy.data.objects.new('Enemy portal / '+key,None);col.objects.link(obj)
    obj.instance_type='COLLECTION';obj.instance_collection=asset(design)
    obj.location=position;obj.rotation_euler[2]=yaw;obj.scale=(scale,)*3
    obj['Atheria portal placement']=key;obj['Design']=design
    obj['Lane']=key
    # Keep the linked rune collection available after saving and reopening.
    obj['Ground rune asset']=asset('Ground runes')
    obj['CanCollide']=False;obj['CanTouch']=False;obj['CanQuery']=False
    bpy.context.view_layer.update()
    bvh=None
    if terrain:
        bvh=BVHTree.FromPolygons([terrain.matrix_world@v.co for v in terrain.data.vertices],
            [tuple(p.vertices) for p in terrain.data.polygons])
    for source in asset('Ground runes').objects:
        child=bpy.data.objects.new('Portal ground FX / '+key,source.data);col.objects.link(child);child.parent=obj
        child['CanCollide']=False;child['CanTouch']=False;child['CanQuery']=False
        child.visible_diffuse=False;child.visible_glossy=False;child.visible_shadow=False
        if terrain:
            shrink=child.modifiers.new('Conform to this map terrain','SHRINKWRAP')
            shrink.target=terrain;shrink.wrap_method='PROJECT';shrink.wrap_mode='ABOVE_SURFACE';shrink.use_project_z=True
            shrink.use_positive_direction=True;shrink.use_negative_direction=True;shrink.offset=.045
    for label,distance in [('EnemySpawn',.9),('FirstWaypoint',3.2)]:
        marker=bpy.data.objects.new(label+' / '+key,None);col.objects.link(marker);marker.parent=obj
        p=obj.matrix_world@Vector((0,distance,0));height=position[2]
        if bvh:
            hit=bvh.ray_cast(Vector((p.x,p.y,p.z+100)),Vector((0,0,-1)),200)[0]
            if hit is not None:height=hit.z
        marker.location=obj.matrix_world.inverted()@Vector((p.x,p.y,height+.12))
        marker.empty_display_size=.25;marker['Portal marker']=label
    return obj

def main():
    scene=bpy.context.scene;assert SCALE>0,'SCALE must be positive.'
    ensure_assets()
    bpy.context.view_layer.update()
    terrain=scene.objects.get(GROUND_OBJECT_NAME) if GROUND_OBJECT_NAME else next((o for o in scene.objects
        if o.type=='MESH' and (o.get('Portal ground') or 'Grassland and terraced ridge foundation' in o.name or o.name=='Terrain')),None)
    roads=[o for o in scene.objects if o.type=='MESH' and o.get('Enemy route')]
    markers=[o for o in bpy.context.selected_objects if o.type=='EMPTY' and not o.get('Atheria portal placement')]
    mode=MODE if MODE!='AUTO' else ('LANES' if roads else 'MARKERS' if markers else 'CURSOR')
    specs=[];extra=math.radians(FACING_DEGREES)
    ground_bvh=BVHTree.FromPolygons([terrain.matrix_world@v.co for v in terrain.data.vertices],
        [tuple(p.vertices) for p in terrain.data.polygons]) if terrain else None
    if mode=='LANES':
        assert roads,'No tagged lane meshes. Use MARKERS or CURSOR on other map layouts.'
        for road in roads:
            columns=road.data.polygons[0].vertices[1]
            assert 2<=columns<len(road.data.vertices)//2,'Unsupported lane mesh; use an empty spawn marker.'
            a=sum((road.matrix_world@v.co for v in road.data.vertices[:columns]),Vector())/columns
            b=sum((road.matrix_world@v.co for v in road.data.vertices[columns:2*columns]),Vector())/columns
            direction=Vector((b.x-a.x,b.y-a.y)).normalized();key=str(road.get('Lane',road.name))
            hit=ground_bvh.ray_cast(a+Vector((0,0,100)),Vector((0,0,-1)),200)[0] if ground_bvh else None
            a.z=hit.z if hit is not None else a.z-.065
            specs.append((key,LANE_DESIGNS.get(key,DESIGN),tuple(a),math.atan2(-direction.x,direction.y)+extra))
        # Migrate legacy model hierarchies in this scene after their assets exist.
        legacy=[o for o in scene.objects if o.get('Atheria enemy portal asset') and o.get('Design')]
        for root in legacy:
            for obj in reversed(descendants(root)):bpy.data.objects.remove(obj,do_unlink=True)
    elif mode=='MARKERS':
        assert markers,'Select one or more empty spawn markers.'
        specs=[(o.name,DESIGN,tuple(o.matrix_world.translation),o.matrix_world.to_euler().z+extra) for o in markers]
    elif mode=='CURSOR':specs=[(PLACEMENT_ID,DESIGN,tuple(scene.cursor.location),extra)]
    else:raise ValueError('MODE must be AUTO, LANES, MARKERS or CURSOR.')
    for key,design,position,yaw in specs:place(scene,key,design,position,yaw,SCALE,terrain)
    scene.use_nodes=True;nodes,links=scene.node_tree.nodes,scene.node_tree.links
    if not nodes.get('Atheria Portal Glow'):
        composite=next((n for n in nodes if n.type=='COMPOSITE'),None) or nodes.new('CompositorNodeComposite')
        previous=composite.inputs['Image'].links[0].from_socket if composite.inputs['Image'].is_linked else None
        if previous is None:
            layer=nodes.new('CompositorNodeRLayers');layer.scene=scene;previous=layer.outputs['Image']
        glow=nodes.new('CompositorNodeGlare');glow.name='Atheria Portal Glow'
        glow.glare_type='FOG_GLOW';glow.threshold=2;glow.size=8;glow.mix=-.60
        links.new(previous,glow.inputs['Image']);links.new(glow.outputs['Image'],composite.inputs['Image'])
    if scene.render.engine=='CYCLES':scene.cycles.transparent_max_bounces=max(16,scene.cycles.transparent_max_bounces)
    scene['Enemy portal workflow']='Shared collection assets with independent placement transforms'
    print('Reusable portals placed:',len(specs),'Mode:',mode,'Save your Blender file.')

if __name__=='__main__':main()
