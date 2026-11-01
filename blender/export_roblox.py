"""Blender 4.3+: bake Atheria's colors and export a textured Roblox FBX.
Open the finished town, save the .blend, then run this entire script.
The original scene is preserved. No external images or add-ons are needed
apart from Blender's bundled FBX exporter.
"""
import bpy
import math
import json
import re
from pathlib import Path

# SETTINGS --------------------------------------------------------------
TEXTURE_SIZE = 2048          # Use 4096 for sharper close-up textures.
MAX_TRIANGLES = 9000         # Split larger meshes into smaller MeshParts.
ONLY_SELECTED = False       # False exports the whole town.
KEEP_EXPORT_SCENE = True    # Inspect baked results in Atheria_Export_*.
EXPORT_SCALE = 1.0

SOURCE_UV = 'Atheria_SourceUV'
EXPORT_UV = 'Atheria_ExportUV'
if not bpy.data.filepath:
    raise RuntimeError('Save your town .blend file before exporting.')
try:
    bpy.ops.export_scene.fbx.get_rna_type()
except Exception as exc:
    raise RuntimeError('Enable/install Blender\'s FBX exporter first.') from exc

output = Path(bpy.data.filepath).parent / 'Atheria_Roblox_Export'
output.mkdir(parents=True, exist_ok=True)
source_scene = bpy.context.scene
source_active = bpy.context.view_layer.objects.active
source_selection = list(bpy.context.selected_objects)
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
depsgraph = bpy.context.evaluated_depsgraph_get()
objects = source_selection if ONLY_SELECTED else list(source_scene.objects)
renderable = set()
def collect_renderable(collection):
    if collection.hide_render:
        return
    renderable.update(collection.objects)
    for child in collection.children:
        collect_renderable(child)
collect_renderable(source_scene.collection)
objects = [obj for obj in objects if not obj.hide_render
           and obj in renderable
           and obj.type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'META'}]
if not objects:
    raise RuntimeError('There is no exportable geometry.')

stage = bpy.data.scenes.new('Atheria_Export')
stage.unit_settings.system = source_scene.unit_settings.system
stage.unit_settings.scale_length = source_scene.unit_settings.scale_length
groups = {}
temporary_materials = {}
exported = []
manifest = {'fbx': 'Atheria_Town.fbx', 'textures': [], 'meshes': [],
            'note': 'Base-color maps are sRGB. One texture/material per mesh. '
                    'Blender lights and emission do not transfer.'}

def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

def bake_material(original, old_uv_name):
    key = (original.name if original else '', old_uv_name)
    if key in temporary_materials:
        return temporary_materials[key]
    if original:
        material = original.copy()
    else:
        material = bpy.data.materials.new('Export fallback')
    material.name = 'BAKE_' + (original.name if original else 'fallback')
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Source UVs must keep driving the old shader after the atlas UV is added.
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = SOURCE_UV
    for node in list(nodes):
        if node.type == 'UVMAP' and node != uv and node.uv_map == old_uv_name:
            node.uv_map = SOURCE_UV
        if node.type == 'TEX_COORD':
            for link in list(node.outputs['UV'].links):
                socket = link.to_socket
                links.remove(link)
                links.new(uv.outputs['UV'], socket)
        if node.type == 'TEX_IMAGE' and not node.inputs['Vector'].is_linked:
            links.new(uv.outputs['UV'], node.inputs['Vector'])

    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    emission = next((n for n in nodes if n.type == 'EMISSION'), None)
    color = principled.inputs['Base Color'] if principled else (
        emission.inputs['Color'] if emission else None)
    shader = nodes.new('ShaderNodeEmission')
    shader.inputs['Strength'].default_value = 1
    if color and color.is_linked:
        links.new(color.links[0].from_socket, shader.inputs['Color'])
    else:
        shader.inputs['Color'].default_value = (
            color.default_value if color else material.diffuse_color)
    outputs = [n for n in nodes if n.type == 'OUTPUT_MATERIAL']
    if not outputs:
        outputs = [nodes.new('ShaderNodeOutputMaterial')]
    for node in outputs:
        links.new(shader.outputs[0], node.inputs['Surface'])
    # EMIT baking captures painted color even for fully metallic materials.
    target = nodes.new('ShaderNodeTexImage')
    target.name = 'ATHERIA_BAKE_TARGET'
    nodes.active = target
    temporary_materials[key] = material
    return material

def textured_material(label, image):
    material = bpy.data.materials.new(label + '_Material')
    material.use_nodes = True
    nodes = material.node_tree.nodes
    shader = nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = 0.75
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = image
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = EXPORT_UV
    material.node_tree.links.new(uv.outputs['UV'], texture.inputs['Vector'])
    material.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    return material

def split_mesh(obj, label, part_label=None):
    mesh = obj.data
    mesh.calc_loop_triangles()
    triangles = list(mesh.loop_triangles)
    uv = mesh.uv_layers[EXPORT_UV]
    normals = mesh.corner_normals
    parts = []
    for start in range(0, len(triangles), MAX_TRIANGLES):
        batch = triangles[start:start + MAX_TRIANGLES]
        vertices, faces, coordinates, shading = [], [], [], []
        for triangle in batch:
            first = len(vertices)
            vertices.extend(mesh.vertices[i].co.copy() for i in triangle.vertices)
            faces.append((first, first + 1, first + 2))
            coordinates.extend(uv.data[i].uv.copy() for i in triangle.loops)
            shading.extend(normals[i].vector.copy() for i in triangle.loops)
        data = bpy.data.meshes.new(label + '_mesh')
        data.from_pydata(vertices, [], faces)
        data.update()
        layer = data.uv_layers.new(name=EXPORT_UV)
        for loop, coordinate in zip(layer.data, coordinates):
            loop.uv = coordinate
        for polygon in data.polygons:
            polygon.use_smooth = True
        data.normals_split_custom_set(shading)
        data.materials.append(mesh.materials[0])
        part = bpy.data.objects.new((part_label or label) + '_' + str(len(parts) + 1).zfill(3), data)
        stage.collection.objects.link(part)
        part.matrix_world = obj.matrix_world.copy()
        part['ColorMap'] = label + '_Color.png'
        parts.append(part)
        manifest['meshes'].append({'name': part.name, 'triangles': len(batch),
                                  'color_map': label + '_Color.png'})
    bpy.data.objects.remove(obj, do_unlink=True)
    return parts

try:
    # Evaluate modifiers and convert text/curves on copies, never on the town.
    for source in objects:
        evaluated = source.evaluated_get(depsgraph)
        mesh = bpy.data.meshes.new_from_object(
            evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
        if not mesh.polygons:
            bpy.data.meshes.remove(mesh)
            continue
        proxy = bpy.data.objects.new('BAKE_' + source.name, mesh)
        stage.collection.objects.link(proxy)
        proxy.matrix_world = source.matrix_world.copy()
        original_uv = mesh.uv_layers.active
        old_uv_name = original_uv.name if original_uv else ''
        if original_uv:
            original_uv.name = SOURCE_UV
        else:
            mesh.uv_layers.new(name=SOURCE_UV)
        source_materials = list(mesh.materials) or [None]
        material_indices = [polygon.material_index for polygon in mesh.polygons]
        mesh.materials.clear()
        for material in source_materials:
            mesh.materials.append(bake_material(material, old_uv_name))
        for polygon, material_index in zip(mesh.polygons, material_indices):
            polygon.material_index = min(material_index, len(source_materials) - 1)
        atlas = mesh.uv_layers.new(name=EXPORT_UV)
        mesh.uv_layers.active = atlas
        atlas.active_render = True
        category = source.users_collection[0].name if source.users_collection else 'Town'
        groups.setdefault(category, []).append(proxy)

    bpy.context.window.scene = stage
    stage.render.engine = 'CYCLES'
    stage.cycles.samples = 1
    stage.cycles.use_denoising = False
    stage.render.bake.margin = 8
    stage.render.bake.use_selected_to_active = False

    for index, (category, proxies) in enumerate(sorted(groups.items()), 1):
        label = 'Atheria_' + str(index).zfill(2) + '_' + re.sub(r'[^A-Za-z0-9]+', '_', category).strip('_')
        print('BAKING', label, len(proxies), 'objects', flush=True)
        select(proxies)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.006,
                                 area_weight=0.5, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        image = bpy.data.images.new(label + '_Color', width=TEXTURE_SIZE,
                                    height=TEXTURE_SIZE, alpha=False)
        image.colorspace_settings.name = 'sRGB'
        for proxy in proxies:
            for material in proxy.data.materials:
                node = material.node_tree.nodes['ATHERIA_BAKE_TARGET']
                node.image = image
                material.node_tree.nodes.active = node
        bpy.ops.object.bake(type='EMIT', use_clear=True, uv_layer=EXPORT_UV)
        image.filepath_raw = str(output / (label + '_Color.png'))
        image.file_format = 'PNG'
        image.save()
        manifest['textures'].append({'section': category, 'file': label + '_Color.png'})

        # Share an atlas while keeping source objects separate. Joining distant
        # pieces can make Roblox collision hulls span otherwise empty space.
        baked_material = textured_material(label, image)
        for object_index, proxy in enumerate(proxies, 1):
            proxy.data.materials.clear()
            proxy.data.materials.append(baked_material)
            for polygon in proxy.data.polygons:
                polygon.material_index = 0
            for name in [layer.name for layer in proxy.data.uv_layers if layer.name != EXPORT_UV]:
                proxy.data.uv_layers.remove(proxy.data.uv_layers[name])
            part_label = label + '_' + str(object_index).zfill(3)
            exported.extend(split_mesh(proxy, label, part_label))

    if not exported:
        raise RuntimeError('No meshes were produced.')
    select(exported)
    bpy.ops.export_scene.fbx(
        filepath=str(output / 'Atheria_Town.fbx'), use_selection=True,
        object_types={'MESH'}, use_mesh_modifiers=False, use_triangles=True,
        mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
        path_mode='COPY', embed_textures=True, use_custom_props=True,
        global_scale=EXPORT_SCALE, axis_forward='-Z', axis_up='Y')
    (output / 'TEXTURE_MANIFEST.json').write_text(json.dumps(manifest, indent=2))
    (output / 'ROBLOX_IMPORT.txt').write_text(
        'Import Atheria_Town.fbx using Roblox Studio\'s 3D Importer.\n'
        'Keep the PNGs beside the FBX. Inspect the preview before importing.\n'
        'If a texture is missing, upload the matching PNG and assign its asset ID\n'
        'to a SurfaceAppearance.ColorMap under that MeshPart. The JSON manifest\n'
        'matches every mesh name to its color texture. Use white MeshPart.Color\n'
        'and Transparency=0 so the texture is not tinted or faded.\n'
        'Set collidable wall/arch MeshParts to CollisionFidelity =\n'
        'PreciseConvexDecomposition in Studio and test all passageways.\n'
        'Base-color maps use sRGB. Set lighting and glow separately in Studio.\n')
    print('EXPORT COMPLETE:', output, flush=True)
finally:
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.window.scene = source_scene
    bpy.ops.object.select_all(action='DESELECT')
    for obj in source_selection:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = source_active
    if not KEEP_EXPORT_SCENE:
        for obj in list(stage.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.scenes.remove(stage)
