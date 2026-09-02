import bpy, bmesh, json, math, os, sys
from mathutils import Vector

TARGET_FOLIAGE_TRIS = 14400
QUADS_PER_SPRAY = 3
TRIS_PER_SPRAY = QUADS_PER_SPRAY * 2
TARGET_SPRAYS = TARGET_FOLIAGE_TRIS // TRIS_PER_SPRAY
SPRAY_LENGTH_MIN = 0.10
SPRAY_LENGTH_MAX = 0.22
SPRAY_WIDTH_MIN = 0.038
SPRAY_WIDTH_MAX = 0.082
POSITION_JITTER = 0.055


def hash01(a, b, c=0.0):
    x = math.sin(a * 12.9898 + b * 78.233 + c * 37.719) * 43758.5453
    return x - math.floor(x)


def add_card(bm, uv_layer, center, along, width_axis, length, width):
    along = along.normalized()
    width_axis = width_axis.normalized()
    hl = length * 0.5
    hw = width * 0.5
    corners = [
        center - along * hl - width_axis * hw,
        center + along * hl - width_axis * hw,
        center + along * hl + width_axis * hw,
        center - along * hl + width_axis * hw,
    ]
    verts = [bm.verts.new(tuple(v)) for v in corners]
    face = bm.faces.new(verts)
    for loop, uv in zip(face.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv_layer].uv = uv
    return 2


def local_frame(direction):
    along = direction.normalized() if direction.length > 1e-6 else Vector((1, 0, 0))
    side = along.cross(Vector((0, 0, 1)))
    if side.length < 1e-5:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(along)
    if up.length < 1e-5:
        up = Vector((0, 0, 1))
    up.normalize()
    return along, side, up


def choose_points(points, target):
    if len(points) <= target:
        return list(points)
    # Density-aware stratified selection: keep source shape instead of simply taking the densest cells.
    weighted = sorted(
        enumerate(points),
        key=lambda kv: (
            -float(kv[1].get('density', 0.0)),
            kv[1]['position'][2],
            math.atan2(kv[1]['position'][1], kv[1]['position'][0]),
        ),
    )
    dense_n = min(target // 2, len(weighted))
    chosen = [p for _, p in weighted[:dense_n]]
    remainder = [p for _, p in weighted[dense_n:]]
    need = target - len(chosen)
    if need > 0 and remainder:
        stride = len(remainder) / float(need)
        for i in range(need):
            idx = min(len(remainder) - 1, int((i + 0.5) * stride))
            chosen.append(remainder[idx])
    return chosen[:target]


def build_foliage_mesh(variant, xoff):
    source_points = variant.get('points', [])
    selected = choose_points(source_points, TARGET_SPRAYS)
    mesh = bpy.data.meshes.new(variant['name'] + '_source_volume_foliage_mesh')
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    tris = 0
    points_out = []
    try:
        for i, src in enumerate(selected):
            h0 = hash01(i + 1, len(selected), variant.get('height', 1.0))
            h1 = hash01(i + 17, 3, variant.get('height', 1.0))
            h2 = hash01(i + 41, 7, variant.get('height', 1.0))
            h3 = hash01(i + 83, 11, variant.get('height', 1.0))
            h4 = hash01(i + 131, 13, variant.get('height', 1.0))

            center = Vector(src['position'])
            center.x += xoff
            density = max(0.0, min(1.0, float(src.get('density', 0.5))))
            radial = Vector((src['direction'][0], src['direction'][1], 0.0))
            if radial.length < 1e-5:
                radial = Vector((1, 0, 0))
            radial.normalize()

            # The source voxel gives crown position. Add only tiny deterministic sub-voxel variation.
            tangential = Vector((-radial.y, radial.x, 0.0))
            center += radial * ((h0 - 0.5) * POSITION_JITTER)
            center += tangential * ((h1 - 0.5) * POSITION_JITTER)
            center.z += (h2 - 0.5) * POSITION_JITTER

            # Needle spray direction follows the source radial lobe but avoids the rigid horizontal look.
            along = (radial * (0.68 + 0.16 * h3) +
                     tangential * ((h4 - 0.5) * 0.34) +
                     Vector((0, 0, 0.18 + 0.30 * (h2 - 0.5)))).normalized()
            along, side, up = local_frame(along)

            density_scale = 0.82 + 0.34 * math.sqrt(max(0.0, density))
            length = (SPRAY_LENGTH_MIN + (SPRAY_LENGTH_MAX - SPRAY_LENGTH_MIN) * h1) * density_scale
            width = (SPRAY_WIDTH_MIN + (SPRAY_WIDTH_MAX - SPRAY_WIDTH_MIN) * h3) * density_scale
            roll = (h0 - 0.5) * math.radians(54.0)

            for qi in range(QUADS_PER_SPRAY):
                ang = math.tau * qi / QUADS_PER_SPRAY + roll
                width_axis = side * math.cos(ang) + up * math.sin(ang)
                tris += add_card(bm, uv_layer, center, along, width_axis, length, width)

            points_out.append({
                'source_voxel': src.get('voxel'),
                'source_samples': src.get('samples', 0),
                'density': round(density, 5),
                'position': [round(center.x, 5), round(center.y, 5), round(center.z, 5)],
                'direction': [round(along.x, 5), round(along.y, 5), round(along.z, 5)],
                'length': round(length, 5),
                'width': round(width, 5),
                'roll': round(roll, 5),
                'tint_seed': [round(h2, 4), round(h3, 4), round(h4, 4)],
            })
        bm.normal_update()
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    obj = bpy.data.objects.new(variant['name'] + '_source_volume_foliage', mesh)
    bpy.context.collection.objects.link(obj)
    return obj, {
        'name': variant['name'],
        'source_points': len(source_points),
        'sprays': len(selected),
        'tris': tris,
        'points': points_out,
    }


def make_foliage_material(diff_path, alpha_path):
    mat = bpy.data.materials.new('pine_twig_source_volume_micro_sprite')
    mat.use_nodes = True
    if hasattr(mat, 'surface_render_method'):
        mat.surface_render_method = 'DITHERED'
    elif hasattr(mat, 'blend_method'):
        mat.blend_method = 'CLIP'
        if hasattr(mat, 'alpha_threshold'):
            mat.alpha_threshold = 0.35
    if hasattr(mat, 'use_transparency_overlap'):
        mat.use_transparency_overlap = False
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    tex = nodes.new('ShaderNodeTexImage')
    alpha = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(diff_path)
    alpha.image = bpy.data.images.load(alpha_path)
    alpha.image.colorspace_settings.name = 'Non-Color'
    links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(alpha.outputs['Color'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.78
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


def setup_preview(objects):
    coords = []
    for obj in objects:
        for corner in obj.bound_box:
            coords.append(obj.matrix_world @ Vector(corner))
    mins = Vector((min(p.x for p in coords), min(p.y for p in coords), min(p.z for p in coords)))
    maxs = Vector((max(p.x for p in coords), max(p.y for p in coords), max(p.z for p in coords)))
    center = (mins + maxs) * 0.5
    extent = maxs - mins
    cam_data = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = (center.x, center.y - max(extent.z * 2.25, extent.x * 1.7), center.z)
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO'
    aspect = 1500.0 / 900.0
    cam.data.ortho_scale = max(extent.z * 1.18, extent.x / aspect * 1.18)
    sun_data = bpy.data.lights.new('Sun', 'SUN')
    sun_data.energy = 2.3
    sun = bpy.data.objects.new('Sun', sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(35), math.radians(-25), math.radians(25))
    world = bpy.context.scene.world or bpy.data.worlds.new('ArcontPineFoliagePreviewWorld')
    bpy.context.scene.world = world
    world.use_nodes = False
    world.color = (0.055, 0.065, 0.055)


def render_png(path):
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(argv) != 7:
        raise SystemExit('usage: blender --background --python build_pine_foliage_lod0_experiment.py -- foliage_volume.json structural.glb twig_diff twig_alpha out.glb out.json out.png')
    volume_path, structural_glb, diff_path, alpha_path, out_glb, out_json, out_png = argv
    volume = json.load(open(volume_path, 'r', encoding='utf-8'))
    variants = volume['variants']

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=structural_glb)
    structural_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    mat = make_foliage_material(diff_path, alpha_path)

    xoff = 0.0
    stats = []
    foliage_objects = []
    for variant in variants:
        obj, st = build_foliage_mesh(variant, xoff)
        obj.data.materials.append(mat)
        foliage_objects.append(obj)
        stats.append(st)
        xoff += variant['height'] * 0.72

    os.makedirs(os.path.dirname(out_glb) or '.', exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out_glb, export_format='GLB')
    setup_preview(structural_objects + foliage_objects)
    render_png(out_png)
    payload = {
        'representation': 'source_twig_volume_foliage_points_micro_sprites',
        'source_representation': volume.get('representation'),
        'target_foliage_tris': TARGET_FOLIAGE_TRIS,
        'quads_per_spray': QUADS_PER_SPRAY,
        'sprite_size_m': {'length': [SPRAY_LENGTH_MIN, SPRAY_LENGTH_MAX], 'width': [SPRAY_WIDTH_MIN, SPRAY_WIDTH_MAX]},
        'runtime_intent': 'Godot MultiMesh; compact crossed-sprite spray mesh instanced at source-derived twig-volume points with deterministic transform/tint variation',
        'variants': stats,
    }
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    for st in stats:
        print(f"ARCONT_PINE_FOLIAGE_EXPERIMENT={st['name']} source_points={st['source_points']} sprays={st['sprays']} tris={st['tris']}")
    print('ARCONT_PINE_FOLIAGE_POINTS_TOTAL=', sum(st['sprays'] for st in stats))
    print('ARCONT_PINE_FOLIAGE_PREVIEW=', out_png)
    print('ARCONT_PINE_FOLIAGE_GLB=', out_glb)


if __name__ == '__main__':
    main()
