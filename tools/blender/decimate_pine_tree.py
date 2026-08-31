import bpy, os, sys

TARGETS = {
    "LOD0": 30000,
    "LOD1": 15000,
    "LOD2": 6000,
    "LOD3": 2000,
}


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


def apply_decimate_per_tree(target_tris: int):
    for obj in mesh_objects():
        current = mesh_tris(obj)
        if current <= target_tris:
            continue
        ratio = max(0.0005, min(1.0, target_tris / float(current)))
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        mod = obj.modifiers.new(name='ArcontMobileDecimate', type='DECIMATE')
        mod.decimate_type = 'COLLAPSE'
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.select_set(False)


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
        apply_decimate_per_tree(target)
        total = total_tris()
        max_per_tree = max_object_tris()
        out = os.path.join(out_dir, f'pine_tree_01_{name.lower()}.glb')
        export_glb(out)
        print(f'ARCONT_TREE_{name}_TOTAL_TRIS={total}')
        print(f'ARCONT_TREE_{name}_MAX_PER_TREE={max_per_tree}')
        if max_per_tree > int(target * 1.15):
            raise SystemExit(f'{name} exceeds per-tree triangle target: {max_per_tree} > {target}')

if __name__ == '__main__':
    main()
