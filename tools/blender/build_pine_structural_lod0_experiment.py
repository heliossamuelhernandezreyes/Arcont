import bpy, bmesh, json, math, os, sys
from mathutils import Vector

TRUNK_SIDES = 8
BRANCH_SIDES = 6
TARGET_STRUCTURE_TRIS = 10000
MIN_OBSERVATIONS = 2
MAX_BRANCHES = 36


def cylinder_between(start, end, r0, r1, sides, name):
    a = Vector(start)
    b = Vector(end)
    axis = b - a
    if axis.length < 1e-5:
        return 0
    z = axis.normalized()
    helper = Vector((0, 0, 1))
    if abs(z.dot(helper)) > 0.96:
        helper = Vector((1, 0, 0))
    x = z.cross(helper).normalized()
    y = z.cross(x).normalized()
    verts = []
    faces = []
    for i in range(sides):
        ang = math.tau * i / sides
        d = x * math.cos(ang) + y * math.sin(ang)
        verts.append(a + d * r0)
        verts.append(b + d * r1)
    for i in range(sides):
        ni = (i + 1) % sides
        faces.append((2*i, 2*ni, 2*ni+1, 2*i+1))
    faces.append(tuple(2*i for i in range(sides)))
    faces.append(tuple(2*i+1 for i in reversed(range(sides))))

    # Build through bmesh rather than Mesh.from_pydata. This is stable across
    # the Blender package/API used by GitHub Actions and avoids the runtime
    # AttributeError seen in the structural experiment job.
    mesh = bpy.data.meshes.new(name + '_mesh')
    bm = bmesh.new()
    try:
        bm_verts = [bm.verts.new(tuple(v)) for v in verts]
        bm.verts.ensure_lookup_table()
        for face in faces:
            try:
                bm.faces.new([bm_verts[i] for i in face])
            except ValueError:
                # A duplicate face would only be a malformed primitive; keep
                # the rest of the diagnostic mesh exportable instead of
                # crashing the whole analysis workflow.
                pass
        bm.normal_update()
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return sides * 2 + (sides - 2) * 2


def branch_priority(b):
    obs = b.get('observations', 1)
    extent = b.get('extent', 0.0)
    score = b.get('score', 0.0)
    path = b.get('path', [])
    curvature_bonus = 1.0 + min(0.4, max(0, len(path)-4) * 0.04)
    return score * max(0.25, extent) * math.log2(1.0 + obs) * curvature_bonus


def estimate_branch_tris(branch, sides=BRANCH_SIDES):
    segs = max(0, len(branch.get('path', [])) - 1)
    return segs * (sides * 2 + (sides - 2) * 2)


def select_branches(variant, trunk_tris):
    candidates = [b for b in variant.get('branches', []) if b.get('observations', 1) >= MIN_OBSERVATIONS and len(b.get('path', [])) >= 3]
    candidates.sort(key=branch_priority, reverse=True)
    selected = []
    used = trunk_tris
    for b in candidates:
        cost = estimate_branch_tris(b)
        if selected and used + cost > TARGET_STRUCTURE_TRIS:
            continue
        selected.append(b)
        used += cost
        if len(selected) >= MAX_BRANCHES:
            break
    return selected, used, len(candidates)


def build_variant(variant, xoff):
    h = variant['height']
    zmin = variant['zmin']
    zmax = variant['zmax']
    trunk_center = Vector((xoff, 0, zmin))
    trunk_top = Vector((xoff, 0, zmax))
    trunk_tris = cylinder_between(trunk_center, trunk_top, h*0.018, h*0.006, TRUNK_SIDES, variant['name'] + '_trunk')
    selected, estimated, candidate_count = select_branches(variant, trunk_tris)
    actual = trunk_tris
    for bi, b in enumerate(selected):
        pts = [Vector(p) for p in b['path']]
        for p in pts:
            p.x += xoff
        base = h * (0.0048 * (1.0 - min(0.85, b.get('t', 0.5))*0.5))
        for si in range(len(pts)-1):
            f0 = 1.0 - 0.68 * (si / max(1, len(pts)-1))
            f1 = 1.0 - 0.68 * ((si+1) / max(1, len(pts)-1))
            actual += cylinder_between(pts[si], pts[si+1], max(h*0.0012, base*f0), max(h*0.0009, base*f1), BRANCH_SIDES, f"{variant['name']}_b{bi:02d}_s{si:02d}")
    return {
        'name': variant['name'],
        'height': h,
        'continuous_candidates': candidate_count,
        'selected_branches': len(selected),
        'estimated_tris': estimated,
        'actual_tris': actual,
        'selected_ids': [b.get('id') for b in selected],
        'mean_observations': sum(b.get('observations',1) for b in selected)/max(1,len(selected)),
    }


def make_material():
    mat = bpy.data.materials.new('structural_debug')
    mat.diffuse_color = (0.22, 0.13, 0.06, 1.0)
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.data.materials.append(mat)


def setup_camera_and_light(variants):
    max_h = max(v['height'] for v in variants)
    span = sum(v['height']*0.72 for v in variants[:-1]) + variants[-1]['height']*0.5
    cam_data = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = (span*0.45, -max_h*2.25, max_h*0.50)
    cam.rotation_euler = (math.radians(90), 0, 0)
    direction = Vector((span*0.45, 0, max_h*0.50)) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = max_h*1.16
    light_data = bpy.data.lights.new('Sun','SUN')
    light_data.energy = 3.0
    light = bpy.data.objects.new('Sun', light_data)
    bpy.context.collection.objects.link(light)
    light.rotation_euler = (math.radians(35), math.radians(-20), math.radians(30))
    world = bpy.context.scene.world
    world.color = (0.08,0.08,0.08)


def render_png(path):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = path
    scene.render.film_transparent = False
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(argv) != 4:
        raise SystemExit('usage: blender --background --python build_pine_structural_lod0_experiment.py -- skeleton.json out.glb out.json out.png')
    src, out_glb, out_json, out_png = argv
    data = json.load(open(src, 'r', encoding='utf-8'))
    variants = data['variants']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    reports = []
    xoff = 0.0
    for v in variants:
        reports.append(build_variant(v, xoff))
        xoff += v['height'] * 0.72
    make_material()
    os.makedirs(os.path.dirname(out_glb) or '.', exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out_glb, export_format='GLB')
    setup_camera_and_light(variants)
    render_png(out_png)
    report = {
        'target_structure_tris': TARGET_STRUCTURE_TRIS,
        'min_observations': MIN_OBSERVATIONS,
        'max_branches': MAX_BRANCHES,
        'variants': reports,
    }
    with open(out_json,'w',encoding='utf-8') as f:
        json.dump(report,f,indent=2)
    for r in reports:
        print(f"ARCONT_PINE_STRUCTURAL_EXPERIMENT={r['name']} selected={r['selected_branches']} candidates={r['continuous_candidates']} tris={r['actual_tris']} mean_obs={r['mean_observations']:.2f}")
    print('ARCONT_PINE_STRUCTURAL_PREVIEW=', out_png)
    print('ARCONT_PINE_STRUCTURAL_GLB=', out_glb)


if __name__ == '__main__':
    main()
