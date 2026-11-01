"""Blender 4.3/5: bake Vestergate materials and export Roblox FBX + PNGs.
Paste in the Text Editor and Alt+P with the map open. Source meshes stay intact.
"""
import bpy
import math
import os
import re
import json
from array import array
from pathlib import Path
from collections import defaultdict
from mathutils import Vector

TEXTURE_SIZE = int(os.environ.get('VESTERGATE_EXPORT_SIZE', '2048'))
MAX_TRIANGLES = 9000
BATCH_OBJECTS = 100
EXPORT_SCALE = 1.0
EXPORT_FRAME = 1
INCLUDE_SCALE_FIGURES = False
EMBED_TEXTURES = False  # Keep the complete PNG folder beside the FBX.
OUT = Path(os.environ.get('VESTERGATE_EXPORT_OUT',
    str(Path(bpy.data.filepath).parent / 'Vestergate_Roblox_Export'))).resolve()
assert bpy.data.filepath, 'Save your Blender file first.'
assert TEXTURE_SIZE >= 64 and TEXTURE_SIZE & (TEXTURE_SIZE-1) == 0
bpy.ops.export_scene.fbx.get_rna_type()
OUT.mkdir(parents=True, exist_ok=True)
original_scene = bpy.context.scene
active = bpy.context.view_layer.objects.active
selection = list(bpy.context.selected_objects)
old_mode = active.mode if active else 'OBJECT'
source = next((s for s in [original_scene]+list(bpy.data.scenes)
    if any(o.get('Enemy route') for o in s.objects)), None)
assert source is not None, 'Open the Vestergate map first.'
old_frame, old_subframe = source.frame_current, source.frame_subframe
if old_mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.window.scene = source
source.frame_set(EXPORT_FRAME)
bpy.context.view_layer.update()
baseline_meshes = set(bpy.data.meshes)
stage = bpy.data.scenes.new('Vestergate / Temporary Roblox export')
stage.unit_settings.system = source.unit_settings.system
stage.unit_settings.scale_length = source.unit_settings.scale_length
UV, SRC, GEN, LOCAL, OWNER = 'VGE_Atlas', 'VGE_Source', 'VGE_Generated', 'VGE_Local', 'VGE_Owner'
groups, origins, clones = defaultdict(list), {}, {}
materials, images, exported = [], [], []
manifest = dict(fbx='Vestergate.fbx', texture_size=TEXTURE_SIZE,
    export_scale=EXPORT_SCALE, source_unit='metres', frame=EXPORT_FRAME,
    normal_format='OpenGL tangent space (+Y)', atlases={}, meshes=[], batches=[],
    source_instances=0, realised_collection_meshes=0,
    portal_animation='Static exported pose; animate the portal effect in Roblox.')


def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def slug(name):
    return re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_')


def value(socket):
    if socket.is_linked:
        return socket.links[0].from_socket
    v = socket.default_value
    return v if isinstance(v, (int, float)) else tuple(v)


def plug(links, signal, socket):
    for link in list(socket.links):
        links.remove(link)
    if isinstance(signal, bpy.types.NodeSocket):
        links.new(signal, socket)
    elif isinstance(signal, (int, float)):
        socket.default_value = (signal, signal, signal, 1) if socket.type == 'RGBA' else signal
    else:
        socket.default_value = signal


def shader(node):
    while node.type == 'REROUTE':
        node = node.inputs[0].links[0].from_node
    return node


def bake_material(original, uv_name):
    key = (original, uv_name)
    if key in clones:
        return clones[key]
    mat = original.copy() if original else bpy.data.materials.new('VGE Fallback')
    mat.name = 'VGE Bake / '+(original.name if original else 'Fallback')
    mat.use_fake_user = False
    mat.use_nodes = True
    materials.append(mat)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    uv = nodes.new('ShaderNodeUVMap'); uv.uv_map = SRC
    attrs = {}
    for name in (GEN, LOCAL):
        attr = nodes.new('ShaderNodeAttribute'); attr.attribute_name = name
        attrs[name] = attr.outputs['Vector']
    for node in list(nodes):
        if node.type == 'TEX_COORD':
            assert node.object is None, 'Explicit Object-coordinate target: '+mat.name
            for name, replacement in [('UV', uv.outputs['UV']), ('Generated', attrs[GEN]), ('Object', attrs[LOCAL])]:
                for link in list(node.outputs[name].links):
                    target = link.to_socket; links.remove(link); links.new(replacement, target)
        elif node.type == 'UVMAP' and node != uv and node.uv_map in ('', uv_name):
            node.uv_map = SRC
        elif node.type.startswith('TEX_') and node.inputs.get('Vector') is not None and not node.inputs['Vector'].is_linked:
            links.new(uv.outputs['UV'] if node.type == 'TEX_IMAGE' else attrs[GEN], node.inputs['Vector'])
    output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
    assert output is not None and output.inputs['Surface'].is_linked, 'Missing surface: '+mat.name
    surface = shader(output.inputs['Surface'].links[0].from_node)
    factor = 1.0
    transparent = False
    if surface.type == 'MIX_SHADER':
        a = shader(surface.inputs[1].links[0].from_node)
        b = shader(surface.inputs[2].links[0].from_node)
        assert (a.type == 'BSDF_TRANSPARENT') != (b.type == 'BSDF_TRANSPARENT'), 'Unsupported shader mix: '+mat.name
        factor = value(surface.inputs[0]); transparent = True
        if b.type == 'BSDF_TRANSPARENT':
            inverse = nodes.new('ShaderNodeMath'); inverse.operation = 'SUBTRACT'
            inverse.inputs[0].default_value = 1; plug(links, factor, inverse.inputs[1])
            factor = inverse.outputs[0]; surface = a
        else:
            surface = b
    if surface.type == 'BSDF_PRINCIPLED':
        signals = dict(ColorMap=value(surface.inputs['Base Color']), RoughnessMap=value(surface.inputs['Roughness']),
            MetalnessMap=value(surface.inputs['Metallic']), EmissiveMask=value(surface.inputs['Emission Strength']))
        alpha = value(surface.inputs['Alpha'])
        normal = surface.outputs['BSDF']
    else:
        assert surface.type == 'EMISSION', 'Unsupported shader: '+mat.name
        signals = dict(ColorMap=value(surface.inputs['Color']), RoughnessMap=1., MetalnessMap=0.,
            EmissiveMask=value(surface.inputs['Strength']))
        alpha = 1.
        normal = nodes.new('ShaderNodeBsdfPrincipled').outputs['BSDF']
    if transparent:
        mul = nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        plug(links, alpha, mul.inputs[0]); plug(links, factor, mul.inputs[1]); alpha = mul.outputs[0]
    signals['AlphaMap'] = alpha
    emit = nodes.new('ShaderNodeEmission'); emit.inputs['Strength'].default_value = 1
    target = nodes.new('ShaderNodeTexImage'); target.name = 'VGE Bake target'
    strength = signals['EmissiveMask']
    item = dict(mat=mat, signals=signals, output=output, emit=emit, target=target, normal=normal,
        alpha=transparent or not isinstance(alpha, (int, float)) or alpha < .999,
        peak=float(strength) if isinstance(strength, (int, float)) else 16.)
    clones[key] = item
    return item


def set_channel(item, channel, peak):
    nodes, links = item['mat'].node_tree.nodes, item['mat'].node_tree.links
    if channel == 'NormalMap':
        links.new(item['normal'], item['output'].inputs['Surface'])
        return
    signal = item['signals'][channel]
    if channel == 'EmissiveMask':
        node = nodes.new('ShaderNodeMath'); node.operation = 'DIVIDE'
        plug(links, signal, node.inputs[0]); node.inputs[1].default_value = peak
        signal = node.outputs[0]
    plug(links, signal, item['emit'].inputs['Color'])
    links.new(item['emit'].outputs[0], item['output'].inputs['Surface'])


def pbr_material(label, maps, peak, transparent):
    mat = bpy.data.materials.new(label+'_Material'); mat.use_nodes = True; materials.append(mat)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    p = nodes.get('Principled BSDF'); textures = {}
    for channel in ('ColorMap', 'RoughnessMap', 'MetalnessMap', 'NormalMap', 'EmissiveMask'):
        image = bpy.data.images.load(str(OUT/maps[channel]), check_existing=False)
        image.colorspace_settings.name = 'sRGB' if channel == 'ColorMap' else 'Non-Color'
        images.append(image)
        node = nodes.new('ShaderNodeTexImage'); node.image = image; textures[channel] = node
    for channel, name in [('ColorMap','Base Color'), ('RoughnessMap','Roughness'), ('MetalnessMap','Metallic')]:
        links.new(textures[channel].outputs['Color'], p.inputs[name])
    normal = nodes.new('ShaderNodeNormalMap')
    links.new(textures['NormalMap'].outputs['Color'], normal.inputs['Color'])
    links.new(normal.outputs['Normal'], p.inputs['Normal'])
    # FBX cannot serialize the mask-multiply node. Do not send the entire
    # colour atlas as an emissive texture; importers may interpret it as glow.
    # The Studio helper applies the actual baked mask after image upload.
    p.inputs['Emission Color'].default_value = (0,0,0,1)
    p.inputs['Emission Strength'].default_value = 0
    if transparent:
        links.new(textures['ColorMap'].outputs['Alpha'], p.inputs['Alpha'])
    return mat


def split_mesh(obj, label, material):
    mesh = obj.data; mesh.calc_loop_triangles()
    owners = mesh.attributes[OWNER].data; bins = defaultdict(list)
    for tri in mesh.loop_triangles:
        bins[owners[tri.polygon_index].value].append(tri)
    uv, normals, parts = mesh.uv_layers[UV], mesh.corner_normals, []
    for identifier, triangles in bins.items():
        name, transform = origins[identifier]
        inverse = transform.inverted(); normal_matrix = transform.to_3x3().transposed()
        for start in range(0, len(triangles), MAX_TRIANGLES):
            verts, faces, coords, shading = [], [], [], []
            for tri in triangles[start:start+MAX_TRIANGLES]:
                i = len(verts); faces.append((i,i+1,i+2))
                verts.extend(inverse @ mesh.vertices[j].co for j in tri.vertices)
                coords.extend(uv.data[j].uv.copy() for j in tri.loops)
                shading.extend((normal_matrix @ normals[j].vector).normalized() for j in tri.loops)
            part_name = f'{label}__{identifier:04d}_{slug(name.split(" / ")[-1])[:35]}_{start//MAX_TRIANGLES+1:02d}'
            data = bpy.data.meshes.new(part_name); data.from_pydata(verts, [], faces); data.update()
            layer = data.uv_layers.new(name=UV)
            for loop, coordinate in zip(layer.data, coords): loop.uv = coordinate
            for polygon in data.polygons: polygon.use_smooth = True
            data.normals_split_custom_set(shading); data.materials.append(material)
            part = bpy.data.objects.new(part_name, data); stage.collection.objects.link(part)
            part.parent = root; part.matrix_world = transform; parts.append(part)
            manifest['meshes'].append(dict(name=part_name, source=name, atlas=label, triangles=len(faces)))
    bpy.data.objects.remove(obj, do_unlink=True)
    return parts


def export_fbx(filename, parts):
    select(parts+[root])
    bpy.ops.export_scene.fbx(filepath=str(OUT/filename), use_selection=True,
        object_types={'MESH','EMPTY'}, use_mesh_modifiers=False, use_triangles=True,
        use_tspace=True, mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
        path_mode='COPY' if EMBED_TEXTURES else 'RELATIVE', embed_textures=EMBED_TEXTURES,
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', global_scale=EXPORT_SCALE,
        axis_forward='-Z', axis_up='Y')


root = bpy.data.objects.new('Vestergate_ExportOrigin', None); stage.collection.objects.link(root)
try:
    dg = bpy.context.evaluated_depsgraph_get()
    # Snapshot meshes inside the iterator: depsgraph instance wrappers are temporary.
    for instance in dg.object_instances:
        obj = instance.object
        if not instance.show_self or obj.hide_render or obj.type not in {'MESH','CURVE','SURFACE','FONT'}: continue
        original = obj.original
        if not INCLUDE_SCALE_FIGURES and any('Scale figures' in c.name for c in original.users_collection): continue
        name = original.name
        if instance.is_instance and instance.parent: name = instance.parent.original.name+' / '+name
        transform = instance.matrix_world.copy()
        mesh = bpy.data.meshes.new_from_object(obj, preserve_all_data_layers=True, depsgraph=dg)
        if not mesh.polygons: bpy.data.meshes.remove(mesh); continue
        local = [v.co.copy() for v in mesh.vertices]
        low = Vector(tuple(min(v[i] for v in local) for i in range(3)))
        size = Vector(tuple(max(v[i] for v in local) for i in range(3)))-low
        generated = [tuple((v[i]-low[i])/size[i] if abs(size[i])>1e-9 else .5 for i in range(3)) for v in local]
        mesh.transform(transform)
        if transform.determinant() < 0: mesh.flip_normals()
        for tag, values in [(GEN, generated), (LOCAL, local)]:
            attr = mesh.attributes.new(tag, 'FLOAT_VECTOR', 'CORNER')
            attr.data.foreach_set('vector', [c for loop in mesh.loops for c in values[loop.vertex_index]])
        identifier = len(origins)
        owner = mesh.attributes.new(OWNER, 'INT', 'FACE'); owner.data.foreach_set('value', [identifier]*len(mesh.polygons))
        original_uv = mesh.uv_layers.active; uv_name = original_uv.name if original_uv else ''
        if original_uv: original_uv.name = SRC
        else: mesh.uv_layers.new(name=SRC)
        slots = list(mesh.materials) or [None]; indices = [p.material_index for p in mesh.polygons]
        items = [bake_material(m, uv_name) for m in slots]
        mesh.materials.clear()
        for item in items: mesh.materials.append(item['mat'])
        for polygon, index in zip(mesh.polygons, indices): polygon.material_index = min(index,len(slots)-1)
        portal = original.get('Atheria portal source') or name.startswith('Portal ground FX') or 'Atheria enemy portals /' in name
        category = ('Portal energy' if any(n.type in {'EMISSION','BSDF_TRANSPARENT'} for m in slots if m for n in m.node_tree.nodes)
                    else 'Portal frames') if portal else original.users_collection[0].name.split(' / ',1)[-1]
        proxy = bpy.data.objects.new('VGE Temporary / '+name, mesh); stage.collection.objects.link(proxy)
        groups[category].append(proxy); origins[identifier] = (name, transform)
        manifest['source_instances'] += 1
        manifest['realised_collection_meshes'] += int(instance.is_instance)
    assert groups, 'No renderable map geometry found.'
    bpy.context.window.scene = stage
    stage.render.engine = 'CYCLES'; stage.cycles.samples = 1; stage.cycles.use_denoising = False
    stage.render.threads_mode = 'FIXED'; stage.render.threads = min(5,os.cpu_count() or 1)
    stage.render.bake.margin = max(2,round(TEXTURE_SIZE/256))
    stage.render.bake.use_selected_to_active = False
    stage.render.bake.normal_space = 'TANGENT'
    stage.render.bake.normal_r = 'POS_X'; stage.render.bake.normal_g = 'POS_Y'; stage.render.bake.normal_b = 'POS_Z'
    for index,(category, proxies) in enumerate(sorted(groups.items()),1):
        label = f'VG{index:02d}'; print('BAKING_SECTION', label, category, flush=True)
        select(proxies)
        if len(proxies)>1: bpy.ops.object.join()
        joined = bpy.context.object
        tri = joined.modifiers.new('Bake triangles', 'TRIANGULATE')
        if hasattr(tri,'keep_custom_normals'): tri.keep_custom_normals = True
        bpy.ops.object.modifier_apply(modifier=tri.name)
        atlas = joined.data.uv_layers.new(name=UV); joined.data.uv_layers.active = atlas; atlas.active_render = True
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.005, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        used = [v for v in clones.values() if v['mat'] in list(joined.data.materials)]
        alpha = any(v['alpha'] for v in used); peak = max(1., max(v['peak'] for v in used))
        maps = {}; alpha_values = None
        channels = (['AlphaMap'] if alpha else [])+['ColorMap','RoughnessMap','MetalnessMap','EmissiveMask','NormalMap']
        for channel in channels:
            image = bpy.data.images.new(label+'_'+channel, TEXTURE_SIZE, TEXTURE_SIZE,
                alpha=alpha and channel=='ColorMap', is_data=channel!='ColorMap')
            images.append(image)
            image.colorspace_settings.name = 'sRGB' if channel=='ColorMap' else 'Non-Color'
            image.alpha_mode = 'CHANNEL_PACKED'
            for item in used:
                set_channel(item, channel, peak); item['target'].image = image
                item['mat'].node_tree.nodes.active = item['target']
            bpy.ops.object.bake(type='NORMAL' if channel=='NormalMap' else 'EMIT', use_clear=True, uv_layer=UV)
            if channel=='AlphaMap' or (channel=='ColorMap' and alpha):
                pixels = array('f',[0.])*(TEXTURE_SIZE*TEXTURE_SIZE*4); image.pixels.foreach_get(pixels)
                if channel=='AlphaMap': alpha_values = pixels[0::4]
                else: pixels[3::4] = alpha_values; image.pixels.foreach_set(pixels)
                del pixels
            filename = label+'_'+channel+'.png'; image.filepath_raw = str(OUT/filename)
            image.file_format = 'PNG'; image.save(); maps[channel] = filename
            for item in used: item['target'].image = None
            images.remove(image); bpy.data.images.remove(image)
        material = pbr_material(label, maps, peak, alpha)
        manifest['atlases'][label] = dict(section=category, maps=maps, transparency=alpha, emissive_strength=peak)
        parts = split_mesh(joined, label, material); exported.extend(parts)
        for start in range(0,len(parts),BATCH_OBJECTS):
            filename = f'{label}_Batch_{start//BATCH_OBJECTS+1:02d}.fbx'
            export_fbx(filename, parts[start:start+BATCH_OBJECTS]); manifest['batches'].append(filename)
        for image in images: image.buffers_free()
    export_fbx('Vestergate.fbx', exported)
    (OUT/'TEXTURE_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
    rows = [f'    {label} = {{ColorMap=0, NormalMap=0, RoughnessMap=0, MetalnessMap=0, EmissiveMask=0, Strength={info["emissive_strength"]}, Transparent={str(info["transparency"]).lower()}, NoCollision={str(info["section"].startswith("Portal") or info["section"]=="Ground greenery").lower()}}}, -- {info["section"]}'
        for label,info in manifest['atlases'].items()]
    lua = '''-- Upload the PNGs as images, then enter their image asset IDs below.
-- Select your imported map in Studio and run this in the Command Bar.
local maps = {
ROWS
}
local roots = game:GetService('Selection'):Get()
assert(#roots > 0, 'Select the imported map first.')
local count = 0
local function apply(part)
    if not part:IsA('MeshPart') then return end
    local row = maps[part.Name:match('^(VG%d%d)__')]
    if not row then return end
    for _,key in ipairs({'ColorMap','NormalMap','RoughnessMap','MetalnessMap'}) do
        if row[key] == 0 then warn('Fill in the image IDs for '..part.Name); return end
    end
    local surface = part:FindFirstChildOfClass('SurfaceAppearance') or Instance.new('SurfaceAppearance')
    for _,key in ipairs({'ColorMap','NormalMap','RoughnessMap','MetalnessMap'}) do
        surface[key] = 'rbxassetid://'..row[key]
    end
    surface.AlphaMode = row.Transparent and Enum.AlphaMode.Transparency or Enum.AlphaMode.Overlay
    pcall(function() surface.EmissiveStrength = 0 end)
    if row.EmissiveMask ~= 0 then
        local ok,err = pcall(function()
            surface.EmissiveMaskContent = Content.fromUri('rbxassetid://'..row.EmissiveMask)
            surface.EmissiveStrength = row.Strength
            surface.EmissiveTint = Color3.new(1,1,1)
        end)
        if not ok then warn('Set the emissive properties manually: '..tostring(err)) end
    end
    surface.Color = Color3.new(1,1,1); surface.Parent = part
    part.Color = Color3.new(1,1,1); part.Anchored = true; part.DoubleSided = true
    if row.NoCollision then part.CanCollide = false; part.CanTouch = false; part.CanQuery = false end
    count += 1
end
for _,root in ipairs(roots) do
    apply(root)
    for _,part in ipairs(root:GetDescendants()) do apply(part) end
end
print('Applied map textures to '..count..' MeshParts.')
'''.replace('ROWS','\n'.join(rows))
    (OUT/'APPLY_TEXTURES.lua').write_text(lua)
    (OUT/'ROBLOX_IMPORT.txt').write_text(
        '1. Keep all PNGs beside Vestergate.fbx; import that FBX through Studio Import 3D.\n'
        '2. For smaller imports use the *_Batch_*.fbx files instead, preserving their file origin. Do not import both versions.\n'
        '3. Upload the PNGs as images, enter the IDs in APPLY_TEXTURES.lua, select the imported map and run the helper.\n'
        '4. ColorMap is sRGB. All other maps are linear data. The ColorMap already contains portal alpha; AlphaMap is a separate backup.\n'
        '5. Normal maps use OpenGL +Y. Mesh pieces contain at most 9000 triangles. Reference mannequins are excluded by default.\n'
        '6. Portals export in a static pose. Recreate animation, bloom, lights and gameplay in Roblox.\n'
        '7. Check scale with a Roblox character. Authoring dimensions are approximately 126 x 140 metres.\n'
        '8. Test collisions: ground, roads, bridge and ledges need suitable collision; foliage and portal effects should not obstruct players.\n')
    print('VESTERGATE_EXPORT_COMPLETE',str(OUT),len(exported),'meshes',flush=True)
finally:
    if bpy.context.object and bpy.context.object.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    for obj in list(stage.objects): bpy.data.objects.remove(obj,do_unlink=True)
    bpy.context.window.scene = source; source.frame_set(old_frame, subframe=old_subframe)
    bpy.context.window.scene = original_scene
    bpy.data.scenes.remove(stage)
    for mesh in list(bpy.data.meshes):
        if mesh not in baseline_meshes and mesh.users == 0: bpy.data.meshes.remove(mesh)
    for material in materials:
        if material.users == 0: bpy.data.materials.remove(material)
    for image in images:
        if image.users == 0: bpy.data.images.remove(image)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in selection: obj.select_set(True)
    bpy.context.view_layer.objects.active = active
    if old_mode != 'OBJECT' and active: bpy.ops.object.mode_set(mode=old_mode)
