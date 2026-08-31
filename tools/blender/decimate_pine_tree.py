import bpy, os, sys

TARGETS = {
    "LOD0": 30000,
    "LOD1": 15000,
    "LOD2": 6000,
    "LOD3": 2000,
}

# Poly Haven's source variants are multi-million-triangle meshes. For the
# distant mobile LODs the required collapse ratio can be below 0.0005, so a
# hard floor at 0.0005 prevents Blender from ever reaching the target.
MIN_DECIMATE_RATIO = 0.00002
MAX_DECIMATE_PASSES = 5
TARGET_SAFETY = 0.94


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


def apply_decimate_per_tree(target_tris: int):
    for obj in mesh_objects():
        previous = mesh_tris(obj)
        if previous <= target_tris:
            continue

        for pass_index in range(MAX_DECIMATE_PASSES):
            current = mesh_tris(obj)
            if current <= target_tris:
                break

            # Aim slightly below the ceiling so rounding and disconnected
            # vegetation islands do not leave the output just over budget.
            ratio = (target_tris * TARGET_SAFETY) / float(current)
            ratio = max(MIN_DECIMATE_RATIO, min(1.0, ratio))
            _apply_decimate(obj, ratio)
            reduced = mesh_tris(obj)
            print(
                f'ARCONT_TREE_DECIMATE object={obj.name} pass={pass_index + 1} '
                f'before={current} after={reduced} target={target_tris} ratio={ratio:.8f}'
            )

            # Stop instead of looping pointlessly if Blender can no longer
            # collapse this mesh at the requested ratio.
            if reduced >= current:
                break
            previous = reduced

        final = mesh_tris(obj)
        if final > int(target_tris * 1.05):
            raise SystemExit(
                f'{obj.name} cannot reach triangle target: {final} > {target_tris}'
            )


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
        if max_per_tree > int(target * 1.05):
            raise SystemExit(f'{name} exceeds per-tree triangle target: {max_per_tree} > {target}')


if __name__ == '__main__':
    main()
