import bpy, math, os, sys
from mathutils import Vector

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


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']


def total_tris():
    return sum(mesh_tris(o) for o in mesh_objects())


def max_object_tris():
    return max((mesh_tris(o) for o in mesh_objects()), default=0)


def _profile(obj, rings_count=PROFILE_RINGS):
    verts = [v.co.copy() for v in obj.data.vertices]
    if not verts:
        return []
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
        # Ignore rare scan/outlier points; retain the actual crown envelope.
        radius = radial[min(len(radial) - 1, int(len(radial) * 0.985))]
        radius = max(radius, height * 0.012)
        rings.append((cx, cy, z, radius))
    return rings


def _interp_profile(rings, t):
    if not rings:
        return (0.0, 0.0, 0.0, 1.0)
    f = max(0.0, min(1.0, t)) * (len(rings) - 1)
    i0 = int(math.floor(f))
    i1 = min(len(rings) - 1, i0 + 1)
    a = f - i0
    return tuple(rings[i0][j] * (1.0 - a) + rings[i1][j] * a for j in range(4))


def _halton(index, base):
    f = 1.0
    r = 0.0
    i = index
    while i > 0:
        f /= base
        r += f * (i % base)
        i //= base
    return r


def _find_material(obj, token, fallback_index=0):
    low_token = token.lower()
    for slot in obj.material_slots:
        if slot.material and low_token in slot.material.name.lower():
            return slot.material
    if obj.material_slots and obj.material_slots[min(fallback_index, len(obj.material_slots) - 1)].material:
        return obj.material_slots[min(fallback_index, len(obj.material_slots) - 1)].material
    mat = bpy.data.materials.new(name=f'ArcontFallback_{token}')
    mat.diffuse_color = (0.18, 0.28, 0.10, 1.0)
    return mat


def _compose_foliage_material(source):
    root = os.path.dirname(source)
    diff_path = os.path.join(root, 'pine_tree_01_twig_diff_1k.jpg')
    mask_candidates = [
        os.path.join(root, 'pine_tree_01_twig_alpha_1k.png'),
        os.path.join(root, 'pine_tree_01_twig_mask_1k.png'),
        os.path.join(root, 'pine_tree_01_twig_alpha_1k.jpg'),
        os.path.join(root, 'pine_tree_01_twig_mask_1k.jpg'),
    ]
    mask_path = next((p for p in mask_candidates if os.path.isfile(p)), None)
    if not os.path.isfile(diff_path) or mask_path is None:
        raise SystemExit('Pine foliage cards require twig diffuse + alpha/mask maps')

    diff = bpy.data.images.load(diff_path, check_existing=False)
    mask = bpy.data.images.load(mask_path, check_existing=False)
    width, height = diff.size
    if tuple(mask.size) != (width, height):
        mask.scale(width, height)

    try:
        import numpy as np
        d = np.empty(width * height * 4, dtype=np.float32)
        m = np.empty(width * height * 4, dtype=np.float32)
        diff.pixels.foreach_get(d)
        mask.pixels.foreach_get(m)
        rgba = d.reshape((-1, 4))
        mask_rgba = m.reshape((-1, 4))
        alpha = mask_rgba[:, 0:3].max(axis=1)
        # Poly Haven's alpha maps can be authored either white-on-black or the inverse.
        # Prefer the orientation whose mean keeps a plausible sparse foliage coverage.
        mean_alpha = float(alpha.mean())
        if mean_alpha > 0.72:
            alpha = 1.0 - alpha
        rgba[:, 3] = alpha
        packed = bpy.data.images.new('ArcontPineTwigRGBA', width=width, height=height, alpha=True)
        packed.pixels.foreach_set(rgba.reshape(-1))
        packed.update()
    except Exception as exc:
        raise SystemExit(f'cannot compose pine foliage alpha texture: {exc}')

    rgba_path = '/tmp/arcont_pine_twig_rgba.png'
    packed.filepath_raw = rgba_path
    packed.file_format = 'PNG'
    packed.save()

    mat = bpy.data.materials.new(name='Arcont_PineTwig_Cutout')
    mat.use_nodes = True
    try:
        mat.blend_method = 'CLIP'
        mat.alpha_threshold = 0.38
        mat.use_screen_refraction = False
    except Exception:
        pass
    mat.use_backface_culling = False
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = packed
    bsdf.inputs['Roughness'].default_value = 0.82
    links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    print(f'ARCONT_TREE_FOLIAGE_TEXTURE={rgba_path} mask={os.path.basename(mask_path)} mean_alpha={mean_alpha:.4f}')
    return mat


def _append_quad(verts, faces, uvs, material_indices, points, mat_index):
    base = len(verts)
    verts.extend(points)
    faces.append((base, base + 1, base + 2, base + 3))
    uvs.extend(((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)))
    material_indices.append(mat_index)


def _build_card_tree(source_obj, foliage_mat, label, cluster_count):
    rings = _profile(source_obj)
    if not rings:
        raise SystemExit(f'cannot measure {source_obj.name}')
    z_min = rings[0][2]
    z_max = rings[-1][2]
    height = z_max - z_min
    cx0, cy0 = rings[0][0], rings[0][1]
    trunk_mat = _find_material(source_obj, 'trunk', 1)

    verts, faces, uvs, material_indices = [], [], [], []
    trunk_sides = 14 if label == 'LOD0' else (12 if label == 'LOD1' else 10)
    trunk_rings = 10 if label == 'LOD0' else 8
    trunk_radius = max(height * 0.016, 0.08)
    for ri in range(trunk_rings):
        t0 = ri / float(trunk_rings)
        t1 = (ri + 1) / float(trunk_rings)
        z0 = z_min + height * t0
        z1 = z_min + height * t1
        r0 = trunk_radius * (1.0 - 0.60 * t0)
        r1 = trunk_radius * (1.0 - 0.60 * t1)
        for side in range(trunk_sides):
            a0 = math.tau * side / trunk_sides
            a1 = math.tau * (side + 1) / trunk_sides
            p0 = (cx0 + math.cos(a0) * r0, cy0 + math.sin(a0) * r0, z0)
            p1 = (cx0 + math.cos(a1) * r0, cy0 + math.sin(a1) * r0, z0)
            p2 = (cx0 + math.cos(a1) * r1, cy0 + math.sin(a1) * r1, z1)
            p3 = (cx0 + math.cos(a0) * r1, cy0 + math.sin(a0) * r1, z1)
            _append_quad(verts, faces, uvs, material_indices, (p0, p1, p2, p3), 0)

    scale_mul = CARD_SCALE[label]
    for n in range(1, cluster_count + 1):
        # Bias toward the lower/middle crown while retaining the measured taper.
        hq = _halton(n, 2)
        t = 0.10 + 0.86 * (1.0 - (1.0 - hq) ** 1.30)
        cx, cy, z, radius = _interp_profile(rings, t)
        radial_q = math.sqrt(_halton(n, 3))
        angle = math.tau * _halton(n, 5)
        radial = radius * 0.90 * radial_q
        px = cx + math.cos(angle) * radial
        py = cy + math.sin(angle) * radial
        pz = z + (_halton(n, 7) - 0.5) * height * 0.018
        local_width = max(height * 0.022, min(height * 0.070, radius * 0.30)) * scale_mul
        local_height = local_width * (1.10 + 0.55 * _halton(n, 11))
        yaw = math.tau * _halton(n, 13)
        for cross in (0.0, math.pi * 0.5):
            a = yaw + cross
            ux, uy = math.cos(a) * local_width * 0.5, math.sin(a) * local_width * 0.5
            lean = (_halton(n + int(cross * 100), 17) - 0.5) * local_width * 0.22
            p0 = (px - ux, py - uy, pz - local_height * 0.45)
            p1 = (px + ux, py + uy, pz - local_height * 0.45)
            p2 = (px + ux + math.cos(angle) * lean, py + uy + math.sin(angle) * lean, pz + local_height * 0.55)
            p3 = (px - ux + math.cos(angle) * lean, py - uy + math.sin(angle) * lean, pz + local_height * 0.55)
            _append_quad(verts, faces, uvs, material_indices, (p0, p1, p2, p3), 1)

    mesh = bpy.data.meshes.new(source_obj.name + f'_{label}_CardMesh')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(trunk_mat)
    mesh.materials.append(foliage_mat)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        poly.material_index = material_indices[poly.index]
        for loop_index in poly.loop_indices:
            vi = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uvs[vi]
    for poly in mesh.polygons:
        poly.use_smooth = poly.material_index == 0

    obj = bpy.data.objects.new(source_obj.name + f'_{label}', mesh)
    bpy.context.collection.objects.link(obj)
    print(f'ARCONT_TREE_FOLIAGE_CARDS={cluster_count} label={label} object={source_obj.name} tris={mesh_tris(obj)}')
    return obj


def _profile_silhouette(obj, rings_count=LOD3_PROFILE_RINGS, sides_count=LOD3_PROFILE_SIDES, label='LOD3'):
    rings = _profile(obj, rings_count)
    if not rings:
        return
    new_verts, uvs = [], []
    for ring_i, (cx, cy, z, radius) in enumerate(rings):
        v = ring_i / float(rings_count - 1)
        for side in range(sides_count):
            u = side / float(sides_count)
            angle = math.tau * u
            new_verts.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius, z))
            uvs.append((u, v))
    faces = []
    for ring in range(rings_count - 1):
        base = ring * sides_count
        nxt = (ring + 1) * sides_count
        for side in range(sides_count):
            s1 = (side + 1) % sides_count
            faces.append((base + side, base + s1, nxt + s1, nxt + side))
    faces.append(tuple(range(sides_count - 1, -1, -1)))
    top = (rings_count - 1) * sides_count
    faces.append(tuple(top + i for i in range(sides_count)))
    new_mesh = bpy.data.meshes.new(obj.name + f'_{label}Profile')
    new_mesh.from_pydata(new_verts, [], faces)
    new_mesh.update()
    uv_layer = new_mesh.uv_layers.new(name='UVMap')
    for poly in new_mesh.polygons:
        for loop_index in poly.loop_indices:
            uv_layer.data[loop_index].uv = uvs[new_mesh.loops[loop_index].vertex_index]
    source_mat = _find_material(obj, 'twig', 0)
    new_mesh.materials.append(source_mat)
    obj.data = new_mesh
    obj.location = (0.0, 0.0, 0.0)
    print(f'ARCONT_TREE_PROFILE_FALLBACK label={label} object={obj.name} tris={mesh_tris(obj)} rings={rings_count} sides={sides_count}')


def export_glb(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', export_apply=True,
        export_texcoords=True, export_normals=True, export_tangents=False,
        export_materials='EXPORT', export_image_format='AUTO',
    )


def build_card_lod(source, out_dir, label, target):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=source)
    originals = list(mesh_objects())
    foliage_mat = _compose_foliage_material(source)
    generated = []
    for obj in originals:
        generated.append(_build_card_tree(obj, foliage_mat, label, CARD_CLUSTERS[label]))
    for obj in originals:
        bpy.data.objects.remove(obj, do_unlink=True)
    total = total_tris()
    max_per_tree = max_object_tris()
    if len(generated) != 3:
        raise SystemExit(f'{label} expected 3 variants, got {len(generated)}')
    if max_per_tree > target:
        raise SystemExit(f'{label} exceeds per-tree triangle target: {max_per_tree} > {target}')
    out = os.path.join(out_dir, f'pine_tree_01_{label.lower()}.glb')
    export_glb(out)
    print(f'ARCONT_TREE_{label}_TOTAL_TRIS={total}')
    print(f'ARCONT_TREE_{label}_MAX_PER_TREE={max_per_tree}')


def build_profile_lod(source, out_dir, label, rings, sides, max_tris):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=source)
    for obj in mesh_objects():
        _profile_silhouette(obj, rings_count=rings, sides_count=sides, label=label)
    total = total_tris()
    max_per_tree = max_object_tris()
    if max_per_tree > max_tris:
        raise SystemExit(f'{label} exceeds per-tree triangle target: {max_per_tree} > {max_tris}')
    out = os.path.join(out_dir, f'pine_tree_01_{label.lower()}.glb')
    export_glb(out)
    print(f'ARCONT_TREE_{label}_TOTAL_TRIS={total}')
    print(f'ARCONT_TREE_{label}_MAX_PER_TREE={max_per_tree}')


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    if len(argv) != 2:
        raise SystemExit('usage: blender --background --python decimate_pine_tree.py -- input.gltf output_dir')
    source, out_dir = argv
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=source)
    print(f'ARCONT_TREE_SOURCE_TOTAL_TRIS={total_tris()}')
    print(f'ARCONT_TREE_SOURCE_MAX_PER_TREE={max_object_tris()}')
    print(f'ARCONT_TREE_VARIANTS={len(mesh_objects())}')

    build_card_lod(source, out_dir, 'LOD0', TARGETS['LOD0'])
    build_card_lod(source, out_dir, 'LOD1', TARGETS['LOD1'])
    build_card_lod(source, out_dir, 'LOD2', TARGETS['LOD2'])
    build_profile_lod(source, out_dir, 'LOD3', LOD3_PROFILE_RINGS, LOD3_PROFILE_SIDES, TARGETS['LOD3'])
    build_profile_lod(source, out_dir, 'HLOD', HLOD_PROFILE_RINGS, HLOD_PROFILE_SIDES, HLOD_MAX_TRIS)


if __name__ == '__main__':
    main()
