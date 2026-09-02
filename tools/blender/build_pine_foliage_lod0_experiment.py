import bpy, bmesh, json, math, os, sys
from mathutils import Vector

TARGET_FOLIAGE_TRIS = 15000
QUADS_PER_CLUSTER = 3
TRIS_PER_CLUSTER = QUADS_PER_CLUSTER * 2
MIN_CLUSTERS_PER_BRANCH = 12
MAX_CLUSTERS_PER_BRANCH = 96
CARD_LENGTH_MIN = 0.18
CARD_LENGTH_MAX = 0.34
CARD_WIDTH_MIN = 0.065
CARD_WIDTH_MAX = 0.12


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
    pts = [p for p in pts if angular_distance(azimuth(p), dom) <= math.radians(45.0)]
    if len(pts) < 2:
        return []
    pts.sort(key=radial)
    out = [pts[0].copy()]
    for p in pts[1:]:
        if radial(p) > radial(out[-1]) + 0.03:
            out.append(p.copy())
    return out if len(out) >= 2 else []


def interpolate_polyline(pts, t):
    if not pts:
        return Vector((0, 0, 0)), Vector((1, 0, 0))
    if len(pts) == 1:
        return pts[0].copy(), Vector((1, 0, 0))
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
    uvs = ((0, 0), (1, 0), (1, 1), (0, 1))
    for loop, uv in zip(face.loops, uvs):
        loop[uv_layer].uv = uv
    return 2


def build_foliage_mesh(variant, report, xoff):
    selected_ids = set(report.get('selected_ids', []))
    branches = [b for b in variant.get('branches', []) if b.get('id') in selected_ids]
    prepared = []
    total_weight = 0.0
    for branch in branches:
        pts = clean_path(branch)
        if len(pts) < 2:
            continue
        reach = max(0.1, radial(pts[-1]) - radial(pts[0]))
        prepared.append((branch, pts, reach))
        total_weight += reach

    target_clusters = max(1, TARGET_FOLIAGE_TRIS // TRIS_PER_CLUSTER)
    mesh = bpy.data.meshes.new(variant['name'] + '_foliage_mesh')
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    tris = 0
    clusters = 0
    try:
        for bi, (branch, pts, reach) in enumerate(prepared):
            share = target_clusters * reach / max(total_weight, 1e-6)
            count = int(max(MIN_CLUSTERS_PER_BRANCH, min(MAX_CLUSTERS_PER_BRANCH, round(share))))
            for ci in range(count):
                # Foliage begins away from the trunk and becomes denser toward the tip.
                q = (ci + 0.55) / count
                t = 0.32 + 0.66 * (q ** 0.82)
                center, tangent = interpolate_polyline(pts, t)
                if tangent.length < 1e-5:
                    continue
                center.x += xoff
                phase = hash01(bi + 1, ci + 3, variant['height'])
                phase2 = hash01(ci + 11, bi + 7, variant['height'] * 0.37)
                # Compact needle spray around the actual branch, not a crown-filling billboard.
                radial_dir = Vector((center.x - xoff, center.y, 0.0))
                if radial_dir.length < 1e-5:
                    radial_dir = Vector((1, 0, 0))
                radial_dir.normalize()
                side = tangent.cross(Vector((0, 0, 1)))
                if side.length < 1e-5:
                    side = Vector((1, 0, 0))
                side.normalize()
                center += side * ((phase - 0.5) * 0.12) + Vector((0, 0, (phase2 - 0.5) * 0.10))
                length = CARD_LENGTH_MIN + (CARD_LENGTH_MAX - CARD_LENGTH_MIN) * (0.35 + 0.65 * phase)
                width = CARD_WIDTH_MIN + (CARD_WIDTH_MAX - CARD_WIDTH_MIN) * phase2
                spray_axis = (tangent * 0.72 + radial_dir * 0.20 + Vector((0, 0, 0.08))).normalized()
                for qi in range(QUADS_PER_CLUSTER):
                    ang = math.tau * qi / QUADS_PER_CLUSTER + phase * 0.45
                    w = side * math.cos(ang) + Vector((0, 0, 1)) * math.sin(ang)
                    tris += add_card(bm, uv_layer, center, spray_axis, w, length, width)
                clusters += 1
        bm.normal_update()
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    obj = bpy.data.objects.new(variant['name'] + '_foliage', mesh)
    bpy.context.collection.objects.link(obj)
    return obj, {'clusters': clusters, 'tris': tris, 'branches': len(prepared)}


def make_foliage_material(diff_path, alpha_path):
    mat = bpy.data.materials.new('pine_twig_compact')
    mat.use_nodes = True
    mat.surface_render_method = 'DITHERED' if hasattr(mat, 'surface_render_method') else mat.blend_method
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


def setup_preview(variants, total_span):
    max_h = max(v['height'] for v in variants)
    cam_data = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    target = Vector((total_span * 0.5, 0, max_h * 0.50))
    cam.location = (target.x, -max_h * 2.6, target.z)
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO'
    # Width-aware framing so A/B/C are all visible, unlike structural run #12.
    aspect = 1500.0 / 900.0
    cam.data.ortho_scale = max(max_h * 1.18, total_span / aspect * 1.18)
    sun_data = bpy.data.lights.new('Sun', 'SUN')
    sun_data.energy = 2.5
    sun = bpy.data.objects.new('Sun', sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(35), math.radians(-25), math.radians(25))
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new('ArcontPineFoliagePreviewWorld')
        bpy.context.scene.world = world
    world.use_nodes = False
    world.color = (0.06, 0.07, 0.06)


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
    mat = make_foliage_material(diff_path, alpha_path)
    xoff = 0.0
    stats = []
    for variant in variants:
        obj, st = build_foliage_mesh(variant, reports[variant['name']], xoff)
        assign_material(obj, mat)
        st['name'] = variant['name']
        stats.append(st)
        xoff += variant['height'] * 0.72
    total_span = xoff + variants[-1]['height'] * 0.20

    os.makedirs(os.path.dirname(out_glb) or '.', exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out_glb, export_format='GLB')
    setup_preview(variants, total_span)
    render_png(out_png)
    payload = {'target_foliage_tris': TARGET_FOLIAGE_TRIS, 'quads_per_cluster': QUADS_PER_CLUSTER, 'variants': stats}
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    for st in stats:
        print(f"ARCONT_PINE_FOLIAGE_EXPERIMENT={st['name']} branches={st['branches']} clusters={st['clusters']} tris={st['tris']}")
    print('ARCONT_PINE_FOLIAGE_PREVIEW=', out_png)
    print('ARCONT_PINE_FOLIAGE_GLB=', out_glb)


if __name__ == '__main__':
    main()
