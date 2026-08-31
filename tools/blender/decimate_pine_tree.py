import bpy, math, os, sys

TARGETS = {"LOD0": 30000, "LOD1": 15000, "LOD2": 6000, "LOD3": 2000}
CARD_CLUSTERS = {"LOD0": 7000, "LOD1": 3500, "LOD2": 1400}
CARD_SCALE = {"LOD0": 1.00, "LOD1": 1.28, "LOD2": 1.75}
PROFILE_RINGS = 28
LOD3_PROFILE_RINGS = 18
LOD3_PROFILE_SIDES = 12
HLOD_PROFILE_RINGS = 6
HLOD_PROFILE_SIDES = 6
HLOD_MAX_TRIS = 96


def mesh_tris(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def _halton(index, base):
    f, r, i = 1.0, 0.0, index
    while i > 0:
        f /= base
        r += f * (i % base)
        i //= base
    return r


def _find_material(obj, token, fallback_index=0):
    token = token.lower()
    for slot in obj.material_slots:
        if slot.material and token in slot.material.name.lower():
            return slot.material
    if obj.material_slots:
        slot = obj.material_slots[min(fallback_index, len(obj.material_slots) - 1)]
        if slot.material:
            return slot.material
    mat = bpy.data.materials.new(name=f'ArcontFallback_{token}')
    mat.diffuse_color = (0.18, 0.28, 0.10, 1.0)
    return mat


def _measure_profile(obj, rings_count=PROFILE_RINGS):
    verts = [v.co.copy() for v in obj.data.vertices]
    z_min = min(v.z for v in verts)
    z_max = max(v.z for v in verts)
    height = max(0.001, z_max - z_min)
    half_band = height / max(2.0, float(rings_count - 1))
    rings = []
    for ring_i in range(rings_count):
        t = ring_i / float(rings_count - 1)
        z = z_min + height * t
        band = [v for v in verts if abs(v.z - z) <= half_band]
        if not band:
            band = sorted(verts, key=lambda v: abs(v.z - z))[:256]
        cx = sum(v.x for v in band) / len(band)
        cy = sum(v.y for v in band) / len(band)
        radial = sorted(math.hypot(v.x - cx, v.y - cy) for v in band)
        radius = radial[min(len(radial) - 1, int(len(radial) * 0.985))]
        rings.append((cx, cy, z, max(radius, height * 0.012)))
    return rings


def _interp_profile(rings, t):
    f = max(0.0, min(1.0, t)) * (len(rings) - 1)
    i0, i1 = int(math.floor(f)), min(len(rings) - 1, int(math.floor(f)) + 1)
    a = f - i0
    return tuple(rings[i0][j] * (1.0 - a) + rings[i1][j] * a for j in range(4))


def _resample_profile(rings, count):
    return [_interp_profile(rings, i / float(count - 1)) for i in range(count)]


def _compose_foliage_material(source):
    root = os.path.dirname(source)
    diff_path = os.path.join(root, 'pine_tree_01_twig_diff_1k.jpg')
    candidates = [
        os.path.join(root, 'pine_tree_01_twig_alpha_1k.png'),
        os.path.join(root, 'pine_tree_01_twig_mask_1k.png'),
        os.path.join(root, 'pine_tree_01_twig_alpha_1k.jpg'),
        os.path.join(root, 'pine_tree_01_twig_mask_1k.jpg'),
    ]
    mask_path = next((p for p in candidates if os.path.isfile(p)), None)
    if not os.path.isfile(diff_path) or mask_path is None:
        raise SystemExit('Pine foliage cards require twig diffuse + alpha/mask maps')
    try:
        import numpy as np
        diff = bpy.data.images.load(diff_path, check_existing=False)
        mask = bpy.data.images.load(mask_path, check_existing=False)
        width, height = diff.size
        if tuple(mask.size) != (width, height):
            mask.scale(width, height)
        d = np.empty(width * height * 4, dtype=np.float32)
        m = np.empty(width * height * 4, dtype=np.float32)
        diff.pixels.foreach_get(d)
        mask.pixels.foreach_get(m)
        rgba = d.reshape((-1, 4))
        alpha = m.reshape((-1, 4))[:, 0:3].max(axis=1)
        mean_alpha = float(alpha.mean())
        if mean_alpha > 0.72:
            alpha = 1.0 - alpha
        rgba[:, 3] = alpha
        packed = bpy.data.images.new('ArcontPineTwigRGBA', width=width, height=height, alpha=True)
        packed.pixels.foreach_set(rgba.reshape(-1))
        packed.update()
    except Exception as exc:
        raise SystemExit(f'cannot compose pine foliage alpha texture: {exc}')
    packed.filepath_raw = '/tmp/arcont_pine_twig_rgba.png'
    packed.file_format = 'PNG'
    packed.save()
    mat = bpy.data.materials.new(name='Arcont_PineTwig_Cutout')
    mat.use_nodes = True
    mat.use_backface_culling = False
    try:
        mat.blend_method = 'CLIP'
        mat.alpha_threshold = 0.38
    except Exception:
        pass
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = packed
    bsdf.inputs['Roughness'].default_value = 0.82
    links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    print(f'ARCONT_TREE_FOLIAGE_TEXTURE=twig_rgba mask={os.path.basename(mask_path)} mean_alpha={mean_alpha:.4f}')
    return mat


def _append_quad(verts, faces, uvs, mats, points, mat_index):
    base = len(verts)
    verts.extend(points)
    faces.append((base, base + 1, base + 2, base + 3))
    uvs.extend(((0, 0), (1, 0), (1, 1), (0, 1)))
    mats.append(mat_index)


def _card_tree(desc, foliage_mat, label):
    rings = desc['rings']
    z_min, z_max = rings[0][2], rings[-1][2]
    height = z_max - z_min
    cx0, cy0 = rings[0][0], rings[0][1]
    verts, faces, uvs, mats = [], [], [], []
    trunk_sides = 14 if label == 'LOD0' else (12 if label == 'LOD1' else 10)
    trunk_rings = 10 if label == 'LOD0' else 8
    trunk_radius = max(height * 0.016, 0.08)
    for ri in range(trunk_rings):
        t0, t1 = ri / trunk_rings, (ri + 1) / trunk_rings
        z0, z1 = z_min + height * t0, z_min + height * t1
        r0, r1 = trunk_radius * (1 - 0.60 * t0), trunk_radius * (1 - 0.60 * t1)
        for side in range(trunk_sides):
            a0, a1 = math.tau * side / trunk_sides, math.tau * (side + 1) / trunk_sides
            _append_quad(verts, faces, uvs, mats, (
                (cx0 + math.cos(a0)*r0, cy0 + math.sin(a0)*r0, z0),
                (cx0 + math.cos(a1)*r0, cy0 + math.sin(a1)*r0, z0),
                (cx0 + math.cos(a1)*r1, cy0 + math.sin(a1)*r1, z1),
                (cx0 + math.cos(a0)*r1, cy0 + math.sin(a0)*r1, z1)), 0)
    count = CARD_CLUSTERS[label]
    scale_mul = CARD_SCALE[label]
    for n in range(1, count + 1):
        hq = _halton(n, 2)
        t = 0.10 + 0.86 * (1.0 - (1.0 - hq) ** 1.30)
        cx, cy, z, radius = _interp_profile(rings, t)
        angle = math.tau * _halton(n, 5)
        radial = radius * 0.90 * math.sqrt(_halton(n, 3))
        px, py = cx + math.cos(angle)*radial, cy + math.sin(angle)*radial
        pz = z + (_halton(n, 7) - 0.5) * height * 0.018
        width = max(height*0.022, min(height*0.070, radius*0.30)) * scale_mul
        card_h = width * (1.10 + 0.55 * _halton(n, 11))
        yaw = math.tau * _halton(n, 13)
        for cross in (0.0, math.pi * 0.5):
            a = yaw + cross
            ux, uy = math.cos(a)*width*0.5, math.sin(a)*width*0.5
            lean = (_halton(n + int(cross*100), 17) - 0.5) * width * 0.22
            dx, dy = math.cos(angle)*lean, math.sin(angle)*lean
            _append_quad(verts, faces, uvs, mats, (
                (px-ux, py-uy, pz-card_h*0.45), (px+ux, py+uy, pz-card_h*0.45),
                (px+ux+dx, py+uy+dy, pz+card_h*0.55), (px-ux+dx, py-uy+dy, pz+card_h*0.55)), 1)
    mesh = bpy.data.meshes.new(desc['name'] + f'_{label}_CardMesh')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(desc['trunk_mat'])
    mesh.materials.append(foliage_mat)
    mesh.update()
    uv = mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        poly.material_index = mats[poly.index]
        poly.use_smooth = poly.material_index == 0
        for li in poly.loop_indices:
            uv.data[li].uv = uvs[mesh.loops[li].vertex_index]
    obj = bpy.data.objects.new(desc['name'] + f'_{label}', mesh)
    bpy.context.collection.objects.link(obj)
    print(f'ARCONT_TREE_FOLIAGE_CARDS={count} label={label} object={desc["name"]} tris={mesh_tris(obj)}')
    return obj


def _profile_tree(desc, material, label, rings_count, sides_count):
    rings = _resample_profile(desc['rings'], rings_count)
    verts, uvs, faces = [], [], []
    for ri, (cx, cy, z, radius) in enumerate(rings):
        for side in range(sides_count):
            u = side / float(sides_count)
            a = math.tau * u
            verts.append((cx + math.cos(a)*radius, cy + math.sin(a)*radius, z))
            uvs.append((u, ri / float(rings_count - 1)))
    for ri in range(rings_count - 1):
        b, n = ri*sides_count, (ri+1)*sides_count
        for side in range(sides_count):
            s1 = (side + 1) % sides_count
            faces.append((b+side, b+s1, n+s1, n+side))
    faces.append(tuple(range(sides_count - 1, -1, -1)))
    top = (rings_count - 1)*sides_count
    faces.append(tuple(top+i for i in range(sides_count)))
    mesh = bpy.data.meshes.new(desc['name'] + f'_{label}Profile')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    uv = mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = uvs[mesh.loops[li].vertex_index]
    obj = bpy.data.objects.new(desc['name'] + f'_{label}', mesh)
    bpy.context.collection.objects.link(obj)
    print(f'ARCONT_TREE_PROFILE_FALLBACK label={label} object={desc["name"]} tris={mesh_tris(obj)} rings={rings_count} sides={sides_count}')
    return obj


def _export_selected(path, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True,
        export_apply=True, export_texcoords=True, export_normals=True,
        export_tangents=False, export_materials='EXPORT', export_image_format='AUTO')
    bpy.ops.object.select_all(action='DESELECT')


def _delete_objects(objects):
    for obj in objects:
        bpy.data.objects.remove(obj, do_unlink=True)


def _validate_and_export(out_dir, label, objects, ceiling):
    values = [mesh_tris(o) for o in objects]
    max_per_tree, total = max(values), sum(values)
    if len(objects) != 3:
        raise SystemExit(f'{label} expected 3 variants, got {len(objects)}')
    if max_per_tree > ceiling:
        raise SystemExit(f'{label} exceeds per-tree triangle target: {max_per_tree} > {ceiling}')
    _export_selected(os.path.join(out_dir, f'pine_tree_01_{label.lower()}.glb'), objects)
    print(f'ARCONT_TREE_{label}_TOTAL_TRIS={total}')
    print(f'ARCONT_TREE_{label}_MAX_PER_TREE={max_per_tree}')


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    if len(argv) != 2:
        raise SystemExit('usage: blender --background --python decimate_pine_tree.py -- input.gltf output_dir')
    source, out_dir = argv
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=source)
    originals = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    source_values = [mesh_tris(o) for o in originals]
    print(f'ARCONT_TREE_SOURCE_TOTAL_TRIS={sum(source_values)}')
    print(f'ARCONT_TREE_SOURCE_MAX_PER_TREE={max(source_values)}')
    print(f'ARCONT_TREE_VARIANTS={len(originals)}')
    if len(originals) != 3:
        raise SystemExit(f'expected 3 Pine Tree 01 variants, got {len(originals)}')
    descs = []
    for obj in originals:
        descs.append({
            'name': obj.name,
            'rings': _measure_profile(obj),
            'trunk_mat': _find_material(obj, 'trunk', 1),
            'twig_mat': _find_material(obj, 'twig', 0),
        })
        obj.hide_set(True)
        obj.hide_render = True
    foliage_mat = _compose_foliage_material(source)

    for label in ('LOD0', 'LOD1', 'LOD2'):
        generated = [_card_tree(desc, foliage_mat, label) for desc in descs]
        _validate_and_export(out_dir, label, generated, TARGETS[label])
        _delete_objects(generated)

    generated = [_profile_tree(desc, desc['twig_mat'], 'LOD3', LOD3_PROFILE_RINGS, LOD3_PROFILE_SIDES) for desc in descs]
    _validate_and_export(out_dir, 'LOD3', generated, TARGETS['LOD3'])
    _delete_objects(generated)

    generated = [_profile_tree(desc, desc['twig_mat'], 'HLOD', HLOD_PROFILE_RINGS, HLOD_PROFILE_SIDES) for desc in descs]
    _validate_and_export(out_dir, 'HLOD', generated, HLOD_MAX_TRIS)
    _delete_objects(generated)


if __name__ == '__main__':
    main()
