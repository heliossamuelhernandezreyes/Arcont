import bpy, bmesh, json, math, os, sys
from mathutils import Vector

TARGET_FOLIAGE_TRIS = 14400
QUADS_PER_SPRAY = 3
TRIS_PER_SPRAY = QUADS_PER_SPRAY * 2
MIN_SPRAYS_PER_BRANCH = 12
MAX_SPRAYS_PER_BRANCH = 96
SPRAY_LENGTH_MIN = 0.085
SPRAY_LENGTH_MAX = 0.18
SPRAY_WIDTH_MIN = 0.032
SPRAY_WIDTH_MAX = 0.068
FOLIAGE_START_T = 0.30
TIP_BIAS_POWER = 0.88
VIRTUAL_TWIG_RADIUS_MIN = 0.025
VIRTUAL_TWIG_RADIUS_MAX = 0.19
VIRTUAL_TWIG_LANES = 5


def radial(p):
    return math.hypot(p.x, p.y)


def azimuth(p):
    return math.atan2(p.y, p.x)


def angular_distance(a, b):
    d = abs(a - b) % math.tau
    return min(d, math.tau - d)


def clean_path(branch):
    pts = [Vector(p) for p in branch.get('path', [])]
    if len(pts) < 2:
        return []
    if radial(pts[-1]) < radial(pts[0]):
        pts.reverse()
    farthest = max(pts, key=radial)
    dom = azimuth(farthest)
    pts = [p for p in pts if angular_distance(azimuth(p), dom) <= math.radians(42.0)]
    if len(pts) < 2:
        return []
    pts.sort(key=radial)
    out = [pts[0].copy()]
    for p in pts[1:]:
        if radial(p) > radial(out[-1]) + 0.025:
            out.append(p.copy())
    return out if len(out) >= 2 else []


def interpolate_polyline(pts, t):
    lengths = []
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = (b - a).length
        lengths.append(seg)
        total += seg
    if total <= 1e-6:
        return pts[-1].copy(), Vector((1, 0, 0))
    target = max(0.0, min(1.0, t)) * total
    acc = 0.0
    for i, seg in enumerate(lengths):
        if acc + seg >= target:
            u = (target - acc) / max(seg, 1e-6)
            p = pts[i].lerp(pts[i + 1], u)
            tangent = (pts[i + 1] - pts[i]).normalized()
            return p, tangent
        acc += seg
    return pts[-1].copy(), (pts[-1] - pts[-2]).normalized()


def hash01(a, b, c):
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


def local_frame(tangent, radial_dir):
    tangent = tangent.normalized()
    side = tangent.cross(Vector((0, 0, 1)))
    if side.length < 1e-5:
        side = radial_dir.cross(tangent)
    if side.length < 1e-5:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(tangent)
    if up.length < 1e-5:
        up = Vector((0, 0, 1))
    up.normalize()
    return side, up


def build_foliage_mesh(variant, report, xoff):
    selected_ids = set(report.get('selected_ids', []))
    branches = [b for b in variant.get('branches', []) if b.get('id') in selected_ids]
    prepared = []
    total_weight = 0.0
    for branch in branches:
        pts = clean_path(branch)
        if len(pts) < 2:
            continue
        reach = max(0.08, radial(pts[-1]) - radial(pts[0]))
        weight = math.sqrt(reach)
        prepared.append((branch, pts, reach, weight))
        total_weight += weight

    target_sprays = max(1, TARGET_FOLIAGE_TRIS // TRIS_PER_SPRAY)
    mesh = bpy.data.meshes.new(variant['name'] + '_foliage_points_mesh')
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    tris = 0
    sprays = 0
    points = []
    try:
        for bi, (branch, pts, reach, weight) in enumerate(prepared):
            share = target_sprays * weight / max(total_weight, 1e-6)
            count = int(max(MIN_SPRAYS_PER_BRANCH, min(MAX_SPRAYS_PER_BRANCH, round(share))))
            for si in range(count):
                q = (si + 0.5) / count
                # Populate the whole terminal portion instead of placing a tuft only at the tip.
                t = FOLIAGE_START_T + (1.0 - FOLIAGE_START_T) * (q ** TIP_BIAS_POWER)
                center, tangent = interpolate_polyline(pts, t)
                if tangent.length < 1e-5:
                    continue
                center.x += xoff

                h0 = hash01(bi + 1, si + 3, variant['height'])
                h1 = hash01(si + 11, bi + 7, variant['height'] * 0.37)
                h2 = hash01(si + 29, bi + 17, variant['height'] * 0.73)
                h3 = hash01(si + 43, bi + 23, variant['height'] * 1.13)
                h4 = hash01(si + 61, bi + 31, variant['height'] * 1.71)

                radial_dir = Vector((center.x - xoff, center.y, 0.0))
                if radial_dir.length < 1e-5:
                    radial_dir = Vector((1, 0, 0))
                radial_dir.normalize()
                side, up = local_frame(tangent, radial_dir)

                terminal = max(0.0, min(1.0, (t - FOLIAGE_START_T) / max(1e-6, 1.0 - FOLIAGE_START_T)))
                lane = si % VIRTUAL_TWIG_LANES
                lane_phase = math.tau * lane / VIRTUAL_TWIG_LANES
                phase = lane_phase + (h0 - 0.5) * 0.95 + terminal * 1.15
                twig_radius = (VIRTUAL_TWIG_RADIUS_MIN +
                               (VIRTUAL_TWIG_RADIUS_MAX - VIRTUAL_TWIG_RADIUS_MIN) *
                               (0.18 + 0.82 * terminal) * (0.65 + 0.35 * h4))
                # Virtual secondary twigs create crown volume around the measured source branch.
                offset_dir = side * math.cos(phase) + up * math.sin(phase)
                center += offset_dir * twig_radius
                center += tangent * ((h2 - 0.5) * min(0.11, reach * 0.06))
                center += radial_dir * ((h1 - 0.5) * 0.035)

                length = SPRAY_LENGTH_MIN + (SPRAY_LENGTH_MAX - SPRAY_LENGTH_MIN) * (0.25 + 0.75 * h2)
                width = SPRAY_WIDTH_MIN + (SPRAY_WIDTH_MAX - SPRAY_WIDTH_MIN) * h3
                # Sprays follow the branch but fan slightly along their virtual twig direction.
                spray_axis = (tangent * 0.70 + offset_dir * (0.18 + 0.10 * h4) + radial_dir * 0.08).normalized()
                roll = (h0 - 0.5) * math.radians(38.0)
                tint = [0.84 + 0.16 * h1, 0.89 + 0.11 * h2, 0.82 + 0.18 * h3]

                for qi in range(QUADS_PER_SPRAY):
                    ang = math.tau * qi / QUADS_PER_SPRAY + roll
                    width_axis = side * math.cos(ang) + up * math.sin(ang)
                    tris += add_card(bm, uv_layer, center, spray_axis, width_axis, length, width)

                points.append({
                    'branch_id': branch.get('id'),
                    'terminal_t': round(t, 5),
                    'virtual_twig_lane': lane,
                    'position': [round(center.x, 5), round(center.y, 5), round(center.z, 5)],
                    'direction': [round(spray_axis.x, 5), round(spray_axis.y, 5), round(spray_axis.z, 5)],
                    'length': round(length, 5),
                    'width': round(width, 5),
                    'roll': round(roll, 5),
                    'tint': [round(v, 4) for v in tint],
                })
                sprays += 1
        bm.normal_update()
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    obj = bpy.data.objects.new(variant['name'] + '_foliage_points', mesh)
    bpy.context.collection.objects.link(obj)
    return obj, {'sprays': sprays, 'tris': tris, 'branches': len(prepared), 'points': points}


def make_foliage_material(diff_path, alpha_path):
    mat = bpy.data.materials.new('pine_twig_micro_sprite')
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


def assign_material(obj, mat):
    obj.data.materials.append(mat)


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
    cam.location = (center.x, center.y - max(extent.z * 2.2, extent.x * 1.7), center.z)
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO'
    aspect = 1500.0 / 900.0
    cam.data.ortho_scale = max(extent.z * 1.16, extent.x / aspect * 1.16)
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
    if len(argv) != 8:
        raise SystemExit('usage: blender --background --python build_pine_foliage_lod0_experiment.py -- skeleton.json structural.json structural.glb twig_diff twig_alpha out.glb out.json out.png')
    skeleton_path, report_path, structural_glb, diff_path, alpha_path, out_glb, out_json, out_png = argv
    skeleton = json.load(open(skeleton_path, 'r', encoding='utf-8'))
    report = json.load(open(report_path, 'r', encoding='utf-8'))
    variants = skeleton['variants']
    reports = {r['name']: r for r in report['variants']}

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=structural_glb)
    structural_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    mat = make_foliage_material(diff_path, alpha_path)

    xoff = 0.0
    stats = []
    foliage_objects = []
    for variant in variants:
        obj, st = build_foliage_mesh(variant, reports[variant['name']], xoff)
        assign_material(obj, mat)
        foliage_objects.append(obj)
        st['name'] = variant['name']
        stats.append(st)
        xoff += variant['height'] * 0.72

    os.makedirs(os.path.dirname(out_glb) or '.', exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out_glb, export_format='GLB')
    setup_preview(structural_objects + foliage_objects)
    render_png(out_png)
    payload = {
        'representation': 'terminal_branch_volume_foliage_points_micro_sprites',
        'target_foliage_tris': TARGET_FOLIAGE_TRIS,
        'quads_per_spray': QUADS_PER_SPRAY,
        'sprite_size_m': {'length': [SPRAY_LENGTH_MIN, SPRAY_LENGTH_MAX], 'width': [SPRAY_WIDTH_MIN, SPRAY_WIDTH_MAX]},
        'foliage_start_t': FOLIAGE_START_T,
        'virtual_twig_radius_m': [VIRTUAL_TWIG_RADIUS_MIN, VIRTUAL_TWIG_RADIUS_MAX],
        'virtual_twig_lanes': VIRTUAL_TWIG_LANES,
        'runtime_intent': 'Godot MultiMesh; one tiny crossed-sprite mesh instanced through the terminal branch volume with per-instance transform/tint variation',
        'variants': stats,
    }
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    for st in stats:
        print(f"ARCONT_PINE_FOLIAGE_EXPERIMENT={st['name']} branches={st['branches']} sprays={st['sprays']} tris={st['tris']}")
    print('ARCONT_PINE_FOLIAGE_POINTS_TOTAL=', sum(st['sprays'] for st in stats))
    print('ARCONT_PINE_FOLIAGE_PREVIEW=', out_png)
    print('ARCONT_PINE_FOLIAGE_GLB=', out_glb)


if __name__ == '__main__':
    main()
