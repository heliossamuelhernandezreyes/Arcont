import bpy, bmesh, json, math, os, sys
from mathutils import Vector

TARGET_FOLIAGE_TRIS = 14400
QUADS_PER_TWIGLET = 3
TRIS_PER_TWIGLET = QUADS_PER_TWIGLET * 2
TARGET_TWIGLETS = TARGET_FOLIAGE_TRIS // TRIS_PER_TWIGLET
TWIGLET_LENGTH_MIN = 0.22
TWIGLET_LENGTH_MAX = 0.46
CARD_LENGTH_MIN = 0.12
CARD_LENGTH_MAX = 0.24
CARD_WIDTH_MIN = 0.06
CARD_WIDTH_MAX = 0.13
POSITION_JITTER = 0.07
DENSE_SCALE_MIN = 0.92
DENSE_SCALE_MAX = 1.30

# Crops from the original Pine Tree 01 Twig atlas. One material stays batchable;
# each tiny branchlet uses three related but different atlas regions.
UV_VARIANTS = (
    (0.03, 0.08, 0.70, 0.92),
    (0.30, 0.08, 0.97, 0.92),
    (0.12, 0.02, 0.88, 0.72),
    (0.12, 0.28, 0.88, 0.98),
    (0.02, 0.02, 0.98, 0.98),
)


def hash01(a, b, c=0.0):
    x = math.sin(a * 12.9898 + b * 78.233 + c * 37.719) * 43758.5453
    return x - math.floor(x)


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


def add_card(bm, uv_layer, center, along, width_axis, length, width, uv_rect, flip_u=False, flip_v=False):
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
    u0, v0, u1, v1 = uv_rect
    if flip_u:
        u0, u1 = u1, u0
    if flip_v:
        v0, v1 = v1, v0
    for loop, uv in zip(face.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        loop[uv_layer].uv = uv
    return 2


def choose_points(points, target):
    if len(points) <= target:
        return list(points)
    weighted = sorted(
        enumerate(points),
        key=lambda kv: (-float(kv[1].get('density', 0.0)), kv[1]['position'][2], math.atan2(kv[1]['position'][1], kv[1]['position'][0])),
    )
    dense_n = min(target // 2, len(weighted))
    chosen = [p for _, p in weighted[:dense_n]]
    remainder = [p for _, p in weighted[dense_n:]]
    need = target - len(chosen)
    if need > 0 and remainder:
        stride = len(remainder) / float(need)
        chosen.extend(remainder[min(len(remainder)-1, int((i + 0.5) * stride))] for i in range(need))
    return chosen[:target]


def build_foliage_mesh(variant, xoff):
    source_points = variant.get('points', [])
    selected = choose_points(source_points, TARGET_TWIGLETS)
    mesh = bpy.data.meshes.new(variant['name'] + '_source_volume_twiglets_mesh')
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    tris = 0
    points_out = []
    crop_histogram = [0] * len(UV_VARIANTS)
    try:
        for i, src in enumerate(selected):
            h = [hash01(i + 1 + k * 29, 7 + k * 11, variant.get('height', 1.0) * (0.31 + 0.17*k)) for k in range(9)]
            center = Vector(src['position'])
            center.x += xoff
            density = max(0.0, min(1.0, float(src.get('density', 0.5))))
            radial = Vector((src['direction'][0], src['direction'][1], 0.0))
            if radial.length < 1e-5:
                radial = Vector((1, 0, 0))
            radial.normalize()
            tangential = Vector((-radial.y, radial.x, 0.0))
            center += radial * ((h[0] - 0.5) * POSITION_JITTER)
            center += tangential * ((h[1] - 0.5) * POSITION_JITTER)
            center.z += (h[2] - 0.5) * POSITION_JITTER

            # One source point becomes one short 3D twiglet, not three coplanar cards.
            base_dir = (radial * (0.52 + 0.18*h[3]) + tangential * ((h[4]-0.5)*0.42) + Vector((0,0,0.10 + 0.28*(h[5]-0.5)))).normalized()
            along, side, up = local_frame(base_dir)
            density_scale = DENSE_SCALE_MIN + (DENSE_SCALE_MAX - DENSE_SCALE_MIN) * math.sqrt(density)
            twiglet_length = (TWIGLET_LENGTH_MIN + (TWIGLET_LENGTH_MAX - TWIGLET_LENGTH_MIN) * h[6]) * density_scale
            bend_side = side * ((h[7]-0.5) * twiglet_length * 0.34)
            bend_up = up * ((h[8]-0.35) * twiglet_length * 0.24)

            crop_index = min(len(UV_VARIANTS)-1, int(h[3] * len(UV_VARIANTS)))
            crop_histogram[crop_index] += 1
            segment_meta = []
            for qi, t in enumerate((0.22, 0.56, 0.88)):
                # Curved local trajectory. Mid/tip cards occupy different positions and planes,
                # creating a compact ramilla volume for the same six triangles.
                curve = (t * t)
                seg_center = center + along * ((t - 0.5) * twiglet_length) + bend_side * curve + bend_up * curve
                tangent = (along + bend_side * (2.0*t/max(twiglet_length, 1e-5)) + bend_up * (2.0*t/max(twiglet_length, 1e-5))).normalized()
                seg_along, seg_side, seg_up = local_frame(tangent)
                fan = (qi - 1) * math.radians(47.0) + (h[(qi+1) % len(h)] - 0.5) * math.radians(30.0)
                width_axis = (seg_side * math.cos(fan) + seg_up * math.sin(fan)).normalized()

                taper = (1.08, 0.92, 0.72)[qi]
                card_length = (CARD_LENGTH_MIN + (CARD_LENGTH_MAX - CARD_LENGTH_MIN) * h[(qi+4) % len(h)]) * density_scale * taper
                card_width = (CARD_WIDTH_MIN + (CARD_WIDTH_MAX - CARD_WIDTH_MIN) * h[(qi+6) % len(h)]) * density_scale * taper
                uv_i = (crop_index + qi) % len(UV_VARIANTS)
                tris += add_card(
                    bm, uv_layer, seg_center, seg_along, width_axis, card_length, card_width, UV_VARIANTS[uv_i],
                    flip_u=hash01(i, qi + 101, h[4]) > 0.5,
                    flip_v=hash01(i, qi + 151, h[1]) > 0.78,
                )
                segment_meta.append({
                    't': t,
                    'center': [round(seg_center.x,5), round(seg_center.y,5), round(seg_center.z,5)],
                    'length': round(card_length,5), 'width': round(card_width,5), 'uv_variant': uv_i,
                })

            points_out.append({
                'source_voxel': src.get('voxel'), 'source_samples': src.get('samples', 0), 'density': round(density,5),
                'position': [round(center.x,5), round(center.y,5), round(center.z,5)],
                'direction': [round(along.x,5), round(along.y,5), round(along.z,5)],
                'twiglet_length': round(twiglet_length,5), 'segments': segment_meta,
            })
        bm.normal_update()
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    obj = bpy.data.objects.new(variant['name'] + '_source_volume_twiglets', mesh)
    bpy.context.collection.objects.link(obj)
    return obj, {'name': variant['name'], 'source_points': len(source_points), 'twiglets': len(selected), 'tris': tris, 'uv_variant_histogram': crop_histogram, 'points': points_out}


def make_foliage_material(diff_path, alpha_path):
    mat = bpy.data.materials.new('pine_twig_source_volume_twiglet_atlas')
    mat.use_nodes = True
    if hasattr(mat, 'surface_render_method'):
        mat.surface_render_method = 'DITHERED'
    elif hasattr(mat, 'blend_method'):
        mat.blend_method = 'CLIP'
        if hasattr(mat, 'alpha_threshold'):
            mat.alpha_threshold = 0.28
    if hasattr(mat, 'use_transparency_overlap'):
        mat.use_transparency_overlap = False
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in list(nodes): nodes.remove(n)
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    tex = nodes.new('ShaderNodeTexImage')
    alpha = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(diff_path)
    alpha.image = bpy.data.images.load(alpha_path)
    alpha.image.colorspace_settings.name = 'Non-Color'
    links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(alpha.outputs['Color'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.74
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


def setup_preview(objects):
    coords = [obj.matrix_world @ Vector(c) for obj in objects for c in obj.bound_box]
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
    cam.data.ortho_scale = max(extent.z * 1.18, extent.x / (1500.0/900.0) * 1.18)
    sun_data = bpy.data.lights.new('Sun', 'SUN'); sun_data.energy = 2.3
    sun = bpy.data.objects.new('Sun', sun_data); bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(35), math.radians(-25), math.radians(25))
    world = bpy.context.scene.world or bpy.data.worlds.new('ArcontPineFoliagePreviewWorld')
    bpy.context.scene.world = world; world.use_nodes = False; world.color = (0.055,0.065,0.055)


def render_png(path):
    scene = bpy.context.scene
    try: scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError: scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1500; scene.render.resolution_y = 900; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(argv) != 7:
        raise SystemExit('usage: blender --background --python build_pine_foliage_lod0_experiment.py -- foliage_volume.json structural.glb twig_diff twig_alpha out.glb out.json out.png')
    volume_path, structural_glb, diff_path, alpha_path, out_glb, out_json, out_png = argv
    volume = json.load(open(volume_path, 'r', encoding='utf-8'))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=structural_glb)
    structural_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    mat = make_foliage_material(diff_path, alpha_path)
    xoff = 0.0; stats = []; foliage_objects = []
    for variant in volume['variants']:
        obj, st = build_foliage_mesh(variant, xoff)
        obj.data.materials.append(mat); foliage_objects.append(obj); stats.append(st)
        xoff += variant['height'] * 0.72
    os.makedirs(os.path.dirname(out_glb) or '.', exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out_glb, export_format='GLB')
    setup_preview(structural_objects + foliage_objects); render_png(out_png)
    payload = {
        'representation': 'source_twig_volume_volumetric_twiglets',
        'source_representation': volume.get('representation'),
        'target_foliage_tris': TARGET_FOLIAGE_TRIS,
        'quads_per_twiglet': QUADS_PER_TWIGLET,
        'uv_variants': [list(v) for v in UV_VARIANTS],
        'runtime_intent': 'Godot MultiMesh; each source foliage point becomes one compact curved 3-card twiglet sharing one atlas/material',
        'variants': stats,
    }
    with open(out_json, 'w', encoding='utf-8') as f: json.dump(payload, f, indent=2)
    for st in stats:
        print(f"ARCONT_PINE_FOLIAGE_EXPERIMENT={st['name']} source_points={st['source_points']} twiglets={st['twiglets']} tris={st['tris']} uv_variants={st['uv_variant_histogram']}")
    print('ARCONT_PINE_FOLIAGE_POINTS_TOTAL=', sum(st['twiglets'] for st in stats))
    print('ARCONT_PINE_FOLIAGE_PREVIEW=', out_png)
    print('ARCONT_PINE_FOLIAGE_GLB=', out_glb)

if __name__ == '__main__':
    main()
