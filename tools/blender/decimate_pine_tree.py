import bpy, math, os, sys
from mathutils import Vector

TARGETS = {"LOD0": 30000, "LOD1": 15000, "LOD2": 6000, "LOD3": 2000}
BRANCH_LAYERS = {"LOD0": 48, "LOD1": 34, "LOD2": 22}
BRANCHES_PER_LAYER = {"LOD0": 8, "LOD1": 7, "LOD2": 6}
TWIGS_PER_BRANCH = {"LOD0": 8, "LOD1": 4, "LOD2": 2}
BRANCH_SIDES = {"LOD0": 6, "LOD1": 6, "LOD2": 5}
PROFILE_RINGS = 28
LOD3_PROFILE_RINGS = 18
LOD3_PROFILE_SIDES = 12
HLOD_PROFILE_RINGS = 6
HLOD_PROFILE_SIDES = 6
HLOD_MAX_TRIS = 96


def mesh_tris(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


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
    i0 = int(math.floor(f))
    i1 = min(len(rings) - 1, i0 + 1)
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
        alpha = np.clip((alpha - 0.30) / 0.48, 0.0, 1.0)
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
        mat.alpha_threshold = 0.50
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
    verts.extend(tuple(p) for p in points)
    faces.append((base, base + 1, base + 2, base + 3))
    uvs.extend(((0, 0), (1, 0), (1, 1), (0, 1)))
    mats.append(mat_index)


def _append_tapered_segment(verts, faces, uvs, mats, start, end, r0, r1, sides, mat_index=0):
    start, end = Vector(start), Vector(end)
    axis = end - start
    if axis.length < 1e-5:
        return
    tangent = axis.normalized()
    helper = Vector((0, 0, 1)) if abs(tangent.z) < 0.90 else Vector((1, 0, 0))
    right = tangent.cross(helper).normalized()
    up = right.cross(tangent).normalized()
    base = len(verts)
    for ring, (center, radius) in enumerate(((start, r0), (end, r1))):
        for side in range(sides):
            a = math.tau * side / sides
            p = center + (right * math.cos(a) + up * math.sin(a)) * radius
            verts.append(tuple(p))
            uvs.append((side / float(sides), float(ring)))
    for side in range(sides):
        s1 = (side + 1) % sides
        faces.append((base + side, base + s1, base + sides + s1, base + sides + side))
        mats.append(mat_index)


def _append_twig_cross(verts, faces, uvs, mats, center, tangent, width, height, mat_index=1, phase=0.0):
    center = Vector(center)
    tangent = Vector(tangent).normalized()
    helper = Vector((0, 0, 1)) if abs(tangent.z) < 0.92 else Vector((1, 0, 0))
    side = tangent.cross(helper).normalized()
    normal = tangent.cross(side).normalized()
    for turn in (phase, phase + math.pi * 0.5):
        across = (side * math.cos(turn) + normal * math.sin(turn)).normalized() * width * 0.5
        along = tangent * height * 0.5
        _append_quad(verts, faces, uvs, mats, (
            center - across - along,
            center + across - along,
            center + across + along,
            center - across + along,
        ), mat_index)


def _branch_tree(desc, foliage_mat, label):
    rings = desc['rings']
    z_min, z_max = rings[0][2], rings[-1][2]
    height = z_max - z_min
    verts, faces, uvs, mats = [], [], [], []
    sides = BRANCH_SIDES[label]

    trunk_steps = 14 if label == 'LOD0' else (11 if label == 'LOD1' else 8)
    for i in range(trunk_steps):
        t0, t1 = i / float(trunk_steps), (i + 1) / float(trunk_steps)
        x0, y0, z0, _ = _interp_profile(rings, t0)
        x1, y1, z1, _ = _interp_profile(rings, t1)
        r0 = max(height * 0.0045, height * 0.018 * (1.0 - 0.72 * t0))
        r1 = max(height * 0.0035, height * 0.018 * (1.0 - 0.72 * t1))
        _append_tapered_segment(verts, faces, uvs, mats, (x0, y0, z0), (x1, y1, z1), r0, r1, sides, 0)

    layers = BRANCH_LAYERS[label]
    per_layer = BRANCHES_PER_LAYER[label]
    twigs = TWIGS_PER_BRANCH[label]
    branch_count = 0
    card_count = 0
    for layer in range(layers):
        lt = layer / float(max(1, layers - 1))
        t = 0.16 + 0.75 * lt
        cx, cy, cz, crown_r = _interp_profile(rings, t)
        phase = layer * 2.399963229728653
        taper = 1.0 - max(0.0, (t - 0.70) / 0.28) * 0.55
        branch_len = max(height * 0.035, crown_r * 0.92 * taper)
        for branch_i in range(per_layer):
            angle = phase + math.tau * branch_i / per_layer
            radial = Vector((math.cos(angle), math.sin(angle), 0.0))
            start = Vector((cx, cy, cz))
            mid = start + radial * branch_len * 0.56 + Vector((0, 0, height * (0.012 - 0.022 * lt)))
            end = start + radial * branch_len + Vector((0, 0, height * (0.010 - 0.040 * lt)))
            base_r = max(height * 0.0017, crown_r * 0.030)
            _append_tapered_segment(verts, faces, uvs, mats, start, mid, base_r, base_r * 0.58, sides, 0)
            _append_tapered_segment(verts, faces, uvs, mats, mid, end, base_r * 0.58, base_r * 0.18, sides, 0)
            branch_count += 1
            tangent = (end - start).normalized()
            for twig_i in range(twigs):
                q = 0.28 + 0.68 * ((twig_i + 0.5) / twigs)
                center = start.lerp(end, q)
                center.z += math.sin((twig_i + branch_i) * 1.7) * height * 0.0025
                width = max(height * 0.020, crown_r * (0.20 + 0.05 * ((twig_i + branch_i) % 3)))
                card_h = width * (1.30 if label == 'LOD0' else (1.42 if label == 'LOD1' else 1.55))
                _append_twig_cross(verts, faces, uvs, mats, center, tangent, width, card_h, 1,
                                   phase=(branch_i * 0.37 + twig_i * 0.61))
                card_count += 1

    top_cx, top_cy, top_z, top_r = _interp_profile(rings, 0.94)
    for i in range(10 if label == 'LOD0' else (8 if label == 'LOD1' else 6)):
        a = math.tau * i / (10 if label == 'LOD0' else (8 if label == 'LOD1' else 6))
        tangent = Vector((math.cos(a) * 0.35, math.sin(a) * 0.35, 0.94)).normalized()
        center = Vector((top_cx, top_cy, top_z)) + tangent * height * 0.035
        _append_twig_cross(verts, faces, uvs, mats, center, tangent, max(height * 0.025, top_r * 0.7), height * 0.050, 1, a * 0.5)
        card_count += 1

    mesh = bpy.data.meshes.new(desc['name'] + f'_{label}_BranchMesh')
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
    print(f'ARCONT_TREE_BRANCHES={branch_count} label={label} object={desc["name"]}')
    print(f'ARCONT_TREE_FOLIAGE_CARDS={card_count} label={label} object={desc["name"]} tris={mesh_tris(obj)}')
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
        generated = [_branch_tree(desc, foliage_mat, label) for desc in descs]
        _validate_and_export(out_dir, label, generated, TARGETS[label])
        _delete_objects(generated)

    lod3 = [_profile_tree(desc, desc['twig_mat'], 'LOD3', LOD3_PROFILE_RINGS, LOD3_PROFILE_SIDES) for desc in descs]
    _validate_and_export(out_dir, 'LOD3', lod3, TARGETS['LOD3'])
    _delete_objects(lod3)

    hlod = [_profile_tree(desc, desc['twig_mat'], 'HLOD', HLOD_PROFILE_RINGS, HLOD_PROFILE_SIDES) for desc in descs]
    _validate_and_export(out_dir, 'HLOD', hlod, HLOD_MAX_TRIS)
    _delete_objects(hlod)

    print('ARCONT_TREE_LOD_BUILD_OK')


if __name__ == '__main__':
    main()
