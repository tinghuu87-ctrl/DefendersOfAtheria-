"""Render the open Vestergate map in Blender 4.3 through 5.0. Paste and Alt+P.
Saves seven views, a separate .blend, and copies any linked portal library.
"""
import bpy
import json
import math
import os
import shutil
from pathlib import Path
from mathutils import Vector

RENDER = os.environ.get('ATHERIA_MAP_RENDER', '1') == '1'
SAMPLES = int(os.environ.get('ATHERIA_MAP_SAMPLES', '96'))
RESOLUTION_PERCENT = int(os.environ.get('ATHERIA_MAP_PERCENT', '100'))
DENOISE = os.environ.get('ATHERIA_MAP_DENOISE', '1') == '1'
if bpy.data.filepath:
    default_out = Path(bpy.data.filepath).parent
    if Path(bpy.data.filepath).name != 'vestergate_render_ready.blend':
        default_out = default_out / 'Vestergate_Full_Render'
else:
    default_out = Path.home() / 'Vestergate_Full_Render'
OUT = Path(os.environ.get('ATHERIA_MAP_OUT', str(default_out))).resolve()
OUT.mkdir(parents=True, exist_ok=True)
scene = next((s for s in [bpy.context.scene] + list(bpy.data.scenes)
    if any(o.get('Enemy route') for o in s.objects)), None)
if scene is None:
    raise RuntimeError('Open your Vestergate map before running this script.')
bpy.context.window.scene = scene


def camera(key, position, target, lens=35, ortho=None):
    name = 'Vestergate / Full render / ' + key
    obj = scene.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector(target)-Vector(position)).to_track_quat('-Z', 'Y').to_euler()
    obj.data.type = 'ORTHO' if ortho else 'PERSP'
    obj.data.lens = lens
    obj.data.clip_start = .1
    obj.data.clip_end = 800
    obj.data.dof.use_dof = False
    if ortho:
        obj.data.ortho_scale = ortho
    return obj


def glow_compositor():
    if hasattr(scene, 'compositing_node_group'):
        tree = scene.compositing_node_group
        if tree is None:
            tree = bpy.data.node_groups.new('Vestergate / Render compositor', 'CompositorNodeTree')
            scene.compositing_node_group = tree
        if not any(s.item_type == 'SOCKET' and s.in_out == 'OUTPUT' and s.name == 'Image'
                   for s in tree.interface.items_tree):
            tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        output = next((n for n in tree.nodes if n.type == 'GROUP_OUTPUT' and n.is_active_output), None)
        output = output or tree.nodes.new('NodeGroupOutput')
    else:
        scene.use_nodes = True
        tree = scene.node_tree
        output = next((n for n in tree.nodes if n.type == 'COMPOSITE'), None)
        output = output or tree.nodes.new('CompositorNodeComposite')
    nodes, links = tree.nodes, tree.links
    for node in nodes:
        if node.type == 'R_LAYERS':
            node.scene = scene
    glow = nodes.get('Atheria Portal Glow') or nodes.get('Vestergate / Gentle bloom')
    if glow is None:
        socket = output.inputs['Image']
        previous = socket.links[0].from_socket if socket.is_linked else None
        if previous is None:
            layer = nodes.new('CompositorNodeRLayers')
            layer.scene = scene
            previous = layer.outputs['Image']
        glow = nodes.new('CompositorNodeGlare')
        glow.name = 'Vestergate / Gentle bloom'
        links.new(previous, glow.inputs['Image'])
        links.new(glow.outputs['Image'], socket)
    if glow.inputs.get('Type') is not None:
        glow.inputs['Type'].default_value = 'Fog Glow'
        glow.inputs['Quality'].default_value = 'Medium'
    else:
        glow.glare_type = 'FOG_GLOW'
        glow.quality = 'MEDIUM'
    if glow.inputs.get('Threshold') is not None:
        glow.inputs['Threshold'].default_value = 2
        glow.inputs['Size'].default_value = .25
        glow.inputs['Strength'].default_value = .25
    else:
        glow.threshold = 2
        glow.size = 8
        glow.mix = -.75


# A new world keeps the portal study's lighting independent.
world = bpy.data.worlds.get('Vestergate / Render daylight')
if world is None:
    world = bpy.data.worlds.new('Vestergate / Render daylight')
world.use_nodes = True
scene.world = world
nodes, links = world.node_tree.nodes, world.node_tree.links
nodes.clear()
sky = nodes.new('ShaderNodeTexSky')
sky_types = sky.bl_rna.properties['sky_type'].enum_items.keys()
sky.sky_type = 'NISHITA' if 'NISHITA' in sky_types else 'SINGLE_SCATTERING'
sky.sun_disc = False
sky.sun_elevation = math.radians(35)
sky.sun_rotation = math.radians(-35)
sky.air_density = 1.0
if hasattr(sky, 'dust_density'):
    sky.dust_density = .6
else:
    sky.aerosol_density = .6
background = nodes.new('ShaderNodeBackground')
background.inputs['Strength'].default_value = .22
backdrop = nodes.new('ShaderNodeBackground')
backdrop.inputs['Color'].default_value = (.13, .22, .30, 1)
backdrop.inputs['Strength'].default_value = .8
path = nodes.new('ShaderNodeLightPath')
camera_mask = nodes.new('ShaderNodeMath')
camera_mask.operation = 'MULTIPLY'
camera_mask.inputs[1].default_value = 1
mix = nodes.new('ShaderNodeMixShader')
output = nodes.new('ShaderNodeOutputWorld')
links.new(sky.outputs['Color'], background.inputs['Color'])
links.new(path.outputs['Is Camera Ray'], camera_mask.inputs[0])
links.new(camera_mask.outputs[0], mix.inputs[0])
links.new(background.outputs['Background'], mix.inputs[1])
links.new(backdrop.outputs['Background'], mix.inputs[2])
links.new(mix.outputs[0], output.inputs['Surface'])
for obj in scene.objects:
    if obj.type != 'LIGHT':
        continue
    if obj.name.startswith('Vestergate / Afternoon sun'):
        obj.data.energy = 2.2
        obj.data.color = (1.0, .88, .70)
        obj.data.angle = math.radians(7)
    elif obj.name.startswith('Vestergate / Sky softbox'):
        obj.data.energy = 7000
    elif obj.name.startswith('Vestergate / Crystal glow'):
        obj.data.energy = 180

views = {
    'overview': camera('overview', (108,133,119), (0,3,1), ortho=185),
    'plan': camera('plan', (0,6,170), (0,6,0), ortho=200),
    'arrival': camera('arrival', (0,-44.5,3.8), (0,-10,2), lens=26),
    'gate': camera('gate', (35,-7,19), (0,-44,6.4), lens=32),
    'woodland': camera('woodland', (-62,1,26), (-27,23,1), lens=35),
    'centre': camera('centre', (18,52,24), (-3,16,1), lens=34),
    'ridge': camera('ridge', (53,38,34), (29,23,4), lens=36),
}
# Spend more samples on the hero view; denoising cleans the closer views.
view_samples = {key: min(SAMPLES, 32 if key == 'plan' else 48) for key in views}
view_samples['overview'] = SAMPLES
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = .015
scene.cycles.adaptive_min_samples = min(16, SAMPLES)
scene.cycles.use_denoising = DENOISE
scene.cycles.max_bounces = 8
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 3
scene.cycles.transparent_max_bounces = 24
scene.cycles.sample_clamp_indirect = 4
scene.render.threads_mode = 'FIXED'
scene.render.threads = max(1, min(8, os.cpu_count() or 1))
scene.render.resolution_x = 1920
scene.render.resolution_y = 1440
scene.render.resolution_percentage = RESOLUTION_PERCENT
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
scene.render.film_transparent = False
scene.render.use_compositing = True
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = 0
scene.frame_set(1)
glow_compositor()

# Copy linked assets before saving so the output folder can travel together.
libraries = []
for library in bpy.data.libraries:
    source = Path(bpy.path.abspath(library.filepath)).resolve()
    if not source.is_file():
        raise RuntimeError('Missing linked library: ' + str(source))
    folder = OUT / 'Libraries'
    folder.mkdir(exist_ok=True)
    target = folder / source.name
    if source != target:
        shutil.copy2(source, target)
    catalog = source.parent / 'blender_assets.cats.txt'
    if catalog.is_file() and catalog.resolve() != (folder / catalog.name).resolve():
        shutil.copy2(catalog, folder / catalog.name)
    library.filepath = str(target)
    libraries.append(target)

scene.camera = views['overview']
native = OUT / 'vestergate_render_ready.blend'
scene.render.filepath = str(OUT / 'vestergate_overview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(native))
for library, target in zip(bpy.data.libraries, libraries):
    library.filepath = bpy.path.relpath(str(target))
bpy.ops.wm.save_as_mainfile(filepath=str(native))

wanted = os.environ.get('ATHERIA_MAP_VIEWS', ','.join(views)).split(',')
completed = []
try:
    if RENDER:
        for key in wanted:
            if key not in views:
                raise ValueError('Unknown camera: ' + key)
            scene.camera = views[key]
            scene.cycles.samples = view_samples[key]
            camera_mask.inputs[1].default_value = 1 if scene.camera.data.type == 'ORTHO' else 0
            scene.render.filepath = str(OUT / ('vestergate_' + key + '.png'))
            try:
                bpy.ops.render.render(write_still=True, scene=scene.name)
            except RuntimeError as error:
                if not scene.cycles.use_denoising or not any(
                        word in str(error).lower() for word in ('denois', 'oidn')):
                    raise
                scene.cycles.use_denoising = False
                print('Denoising unavailable in this Blender build; rendering without it.')
                bpy.ops.render.render(write_still=True, scene=scene.name)
            completed.append(key)
            print('VESTERGATE_RENDERED', key, flush=True)
finally:
    scene.camera = views['overview']
    scene.cycles.samples = SAMPLES
    camera_mask.inputs[1].default_value = 1
    scene.render.filepath = str(OUT / 'vestergate_overview.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(native))
    (OUT / 'RENDER_MANIFEST.json').write_text(json.dumps(dict(
        blender_version=bpy.app.version_string,
        samples=SAMPLES,
        samples_by_view=view_samples,
        resolution=[1920,1440],
        resolution_percent=RESOLUTION_PERCENT,
        denoising=scene.cycles.use_denoising,
        rendered_views=completed,
        cameras={key: dict(position=list(obj.location), lens=obj.data.lens,
            type=obj.data.type) for key,obj in views.items()},
        linked_libraries=[str(p.relative_to(OUT)) for p in libraries],
        native_file=native.name,
    ), indent=2))
print('FULL_MAP_READY', str(OUT), flush=True)
