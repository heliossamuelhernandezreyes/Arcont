import bpy, math, os, sys
from mathutils import Vector

TARGETS = {
    "LOD0": 30000,
    "LOD1": 15000,
    "LOD2": 6000,
    "LOD3": 2000,
}

MIN_DECIMATE_RATIO = 0.00002
MAX_DECIMATE_PASSES = 5
TARGET_SAFETY = 0.94
LOD3_PROFILE_RINGS = 18
LOD3_PROFILE_SIDES = 12
HLOD_PROFILE_RINGS = 6
HLOD_PROFILE_SIDES = 6
HLOD_MAX_TRIS = 96


def mesh_tris(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    return len(mesh.loop_triangles)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']


def total_tris():
    return sum(mesh_tris(o) for o in mesh_objects())


def max_object_tris():
    meshes = mesh_objects()
    return max((mesh_tris(o) for o in meshes), default=0)


def _apply_decimate(obj, ratio: float):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mod = obj.modifiers.new(name='ArcontMobileDecimate', type='DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)


def _profile_silhouette(obj, rings_count=LOD3_PROFILE_RINGS, sides_count=LOD3_PROFILE_SIDES, label='LOD3'):
    """Replace a tree with a measured ring-profile silhouette.

    Height, crown width and taper are measured from the real Poly Haven source.
    This avoids keeping thousands of disconnected foliage islands at distances
    where silhouette matters more than individual twigs.
    """
    source_mesh = obj.data
    verts = [v.co.copy() for v in source_mesh.vertices]
    if not verts:
        return

    z_min = min(v.z for v in verts)
    z_max = max(v.z for v in verts)
    height = max(0.001, z_max - z_min)

    rings = []
    half_band = height / max(2.0, float(rings_count - 1))
    for ring_index in range(rings_count):
        t = ring_index / float(rings_count - 1)
        z = z_min + height * t
        band = [v for v in verts if abs(v.z - z) <= half_band]
        if not band:
            band = sorted(verts, key=lambda v: abs(v.z - z))[:256]
        cx = sum(v.x for v in band) / len(band)
        cy = sum(v.y for v in band) / len(band)
        radius = max(math.hypot(v.x - cx, v.y - cy) for v in band)
        radius = max(radius, height * 0.008)
        rings.append((cx, cy, z, radius))

    new_verts = []
    uvs = []
    for ring_index, (cx, cy, z, radius) in enumerate(rings):
        v = ring_index / float(rings_count - 1)
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
            vertex_index = new_mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uvs[vertex_index]

    for material in source_mesh.materials:
        new_mesh.materials.append(material)
    obj.data = new_mesh
    print(
        f'ARCONT_TREE_PROFILE_FALLBACK label={label} object={obj.name} '
        f'tris={mesh_tris(obj)} rings={rings_count} sides={sides_count}'
    )


def apply_decimate_per_tree(target_tris: int, allow_profile_fallback: bool = False):
    for obj in mesh_objects():
        if mesh_tris(obj) <= target_tris:
            continue

        for pass_index in range(MAX_DECIMATE_PASSES):
            current = mesh_tris(obj)
            if current <= target_tris:
                break
            ratio = (target_tris * TARGET_SAFETY) / float(current)
            ratio = max(MIN_DECIMATE_RATIO, min(1.0, ratio))
            _apply_decimate(obj, ratio)
            reduced = mesh_tris(obj)
            print(
                f'ARCONT_TREE_DECIMATE object={obj.name} pass={pass_index + 1} '
                f'before={current} after={reduced} target={target_tris} ratio={ratio:.8f}'
            )
            if reduced >= current:
                break

        final = mesh_tris(obj)
        if final > int(target_tris * 1.05) and allow_profile_fallback:
            _profile_silhouette(obj)
            final = mesh_tris(obj)
        if final > int(target_tris * 1.05):
            raise SystemExit(f'{obj.name} cannot reach triangle target: {final} > {target_tris}')


def export_glb(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_materials='EXPORT',
        export_image_format='AUTO',
    )


def build_hlod(source: str, out_dir: str):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=source)
    for obj in mesh_objects():
        _profile_silhouette(
            obj,
            rings_count=HLOD_PROFILE_RINGS,
            sides_count=HLOD_PROFILE_SIDES,
            label='HLOD',
        )
    total = total_tris()
    max_per_tree = max_object_tris()
    if max_per_tree > HLOD_MAX_TRIS:
        raise SystemExit(f'HLOD exceeds per-tree triangle target: {max_per_tree} > {HLOD_MAX_TRIS}')
    out = os.path.join(out_dir, 'pine_tree_01_hlod.glb')
    export_glb(out)
    print(f'ARCONT_TREE_HLOD_TOTAL_TRIS={total}')
    print(f'ARCONT_TREE_HLOD_MAX_PER_TREE={max_per_tree}')


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

    for name, target in TARGETS.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=source)
        apply_decimate_per_tree(target, allow_profile_fallback=(name == 'LOD3'))
        total = total_tris()
        max_per_tree = max_object_tris()
        out = os.path.join(out_dir, f'pine_tree_01_{name.lower()}.glb')
        export_glb(out)
        print(f'ARCONT_TREE_{name}_TOTAL_TRIS={total}')
        print(f'ARCONT_TREE_{name}_MAX_PER_TREE={max_per_tree}')
        if max_per_tree > int(target * 1.05):
            raise SystemExit(f'{name} exceeds per-tree triangle target: {max_per_tree} > {target}')

    build_hlod(source, out_dir)


if __name__ == '__main__':
    main()
