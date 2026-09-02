import bpy, bmesh, json, math, os, sys
from mathutils import Vector

TRUNK_SIDES = 8
BRANCH_SIDES = 6
TARGET_STRUCTURE_TRIS = 10000
MIN_OBSERVATIONS = 2
MAX_BRANCHES = 48
MIN_BRANCH_PATH_NODES = 3
MIN_HORIZONTAL_SPAN_RATIO = 0.014
MAX_VERTICAL_TO_HORIZONTAL = 2.6
MAX_CONNECTOR_RATIO = 0.14
SECONDARY_MIN_SUPPORT = 24
SECONDARY_MIN_SCORE = 3.4
SECONDARY_MIN_EXTENT_RATIO = 0.026
MAX_AZIMUTH_DEVIATION_DEG = 42.0
MAX_LOCAL_TURN_DEG = 100.0
MIN_RADIAL_PROGRESS_RATIO = 0.004
DUPLICATE_Z_RATIO = 0.022
DUPLICATE_AZIMUTH_DEG = 15.0


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
    mesh = bpy.data.meshes.new(name + '_mesh')
    bm = bmesh.new()
    try:
        bm_verts = [bm.verts.new(tuple(v)) for v in verts]
        bm.verts.ensure_lookup_table()
        for face in faces:
            try:
                bm.faces.new([bm_verts[i] for i in face])
            except ValueError:
                pass
        bm.normal_update()
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return sides * 2 + (sides - 2) * 2


def radial(p):
    return math.hypot(p.x, p.y)


def azimuth(p):
    return math.atan2(p.y, p.x)


def angular_distance(a, b):
    d = abs(a - b) % math.tau
    return min(d, math.tau - d)


def normalize_branch_path(branch):
    pts = [Vector(p) for p in branch.get('path', [])]
    if len(pts) < MIN_BRANCH_PATH_NODES:
        return []
    # Occupancy tracks have no guaranteed direction. The endpoint nearest the
    # trunk is the root; reconstruction always proceeds outward.
    if radial(pts[-1]) < radial(pts[0]):
        pts.reverse()
    return pts


def clean_outward_path(branch, height):
    pts = normalize_branch_path(branch)
    if len(pts) < MIN_BRANCH_PATH_NODES:
        return []

    # Use the farthest observed point as the branch's dominant direction.
    farthest = max(pts, key=radial)
    dominant_az = azimuth(farthest)
    max_dev = math.radians(MAX_AZIMUTH_DEVIATION_DEG)
    min_progress = height * MIN_RADIAL_PROGRESS_RATIO

    # Sort by radius to remove occupancy-track loops/backtracking. Keep only
    # samples belonging to the same directional lobe as the farthest sample.
    candidates = [p.copy() for p in pts if angular_distance(azimuth(p), dominant_az) <= max_dev]
    if len(candidates) < 2:
        return []
    candidates.sort(key=radial)

    kept = [candidates[0]]
    for p in candidates[1:]:
        if radial(p) <= radial(kept[-1]) + min_progress:
            continue
        kept.append(p)
    if len(kept) < 2:
        return []

    # Remove sharp planar reversals that produce rectangular/kinked branches.
    filtered = [kept[0]]
    max_turn = math.radians(MAX_LOCAL_TURN_DEG)
    for i in range(1, len(kept) - 1):
        a = kept[i] - filtered[-1]
        b = kept[i + 1] - kept[i]
        a2 = Vector((a.x, a.y, 0.0))
        b2 = Vector((b.x, b.y, 0.0))
        if a2.length > 1e-5 and b2.length > 1e-5:
            turn = a2.angle(b2)
            if turn > max_turn:
                continue
        filtered.append(kept[i])
    filtered.append(kept[-1])

    if len(filtered) >= 3:
        smooth = [filtered[0].copy()]
        for i in range(1, len(filtered) - 1):
            smooth.append(filtered[i-1] * 0.16 + filtered[i] * 0.68 + filtered[i+1] * 0.16)
        smooth.append(filtered[-1].copy())
        filtered = smooth
    return filtered


def branch_metrics(branch, height):
    pts = clean_outward_path(branch, height)
    if len(pts) < 2:
        return None
    horizontal = 0.0
    vertical = 0.0
    for a, b in zip(pts, pts[1:]):
        d = b - a
        horizontal += math.hypot(d.x, d.y)
        vertical += abs(d.z)
    span = radial(pts[-1]) - radial(pts[0])
    return {
        'points': pts,
        'horizontal': horizontal,
        'vertical': vertical,
        'radial_span': span,
        'verticality': vertical / max(horizontal, height * 0.001),
    }


def branch_is_plausible(branch, height, secondary=False):
    m = branch_metrics(branch, height)
    if not m:
        return False
    if m['radial_span'] < height * MIN_HORIZONTAL_SPAN_RATIO:
        return False
    if m['verticality'] > MAX_VERTICAL_TO_HORIZONTAL:
        return False
    if secondary:
        return (
            branch.get('support', 0) >= SECONDARY_MIN_SUPPORT
            and branch.get('score', 0.0) >= SECONDARY_MIN_SCORE
            and branch.get('extent', 0.0) >= height * SECONDARY_MIN_EXTENT_RATIO
        )
    return branch.get('observations', 1) >= MIN_OBSERVATIONS


def trunk_radius_at_z(height, zmin, zmax, z):
    t = max(0.0, min(1.0, (z - zmin) / max(1e-5, zmax - zmin)))
    return height * (0.018 * (1.0 - t) + 0.006 * t)


def attach_path_to_trunk(branch, height, zmin, zmax):
    pts = clean_outward_path(branch, height)
    if len(pts) < 2:
        return [], 0.0
    root = pts[0]
    r = radial(root)
    trunk_r = trunk_radius_at_z(height, zmin, zmax, root.z)
    if r > 1e-5:
        trunk_root = Vector((root.x / r * trunk_r, root.y / r * trunk_r, root.z))
    else:
        trunk_root = Vector((trunk_r, 0.0, root.z))
    connector = (root - trunk_root).length
    if connector > height * MAX_CONNECTOR_RATIO:
        return [], connector
    if connector > height * 0.004:
        mid = trunk_root.lerp(root, 0.55)
        mid.z += min(height * 0.003, connector * 0.05)
        pts = [trunk_root, mid] + pts
    else:
        pts = [trunk_root] + pts
    return pts, connector


def branch_priority(b):
    obs = b.get('observations', 1)
    extent = b.get('extent', 0.0)
    score = b.get('score', 0.0)
    support = b.get('support', 0)
    return score * max(0.25, extent) * math.log2(1.0 + obs) * (1.0 + min(0.30, math.log2(1.0 + support) * 0.03))


def branch_signature(branch, height):
    pts = clean_outward_path(branch, height)
    if len(pts) < 2:
        return None
    return pts[0].z, azimuth(pts[-1]), radial(pts[-1])


def is_duplicate_branch(branch, selected, height):
    sig = branch_signature(branch, height)
    if sig is None:
        return True
    z, az, reach = sig
    for other in selected:
        osig = branch_signature(other, height)
        if osig is None:
            continue
        oz, oaz, oreach = osig
        if (
            abs(z - oz) <= height * DUPLICATE_Z_RATIO
            and angular_distance(az, oaz) <= math.radians(DUPLICATE_AZIMUTH_DEG)
            and abs(reach - oreach) <= height * 0.10
        ):
            return True
    return False


def estimate_branch_tris(branch, height, zmin, zmax):
    pts, _ = attach_path_to_trunk(branch, height, zmin, zmax)
    return max(0, len(pts) - 1) * (BRANCH_SIDES * 2 + (BRANCH_SIDES - 2) * 2)


def select_branches(variant, trunk_tris):
    height = variant['height']
    zmin = variant['zmin']
    zmax = variant['zmax']
    primary = [b for b in variant.get('branches', []) if branch_is_plausible(b, height, False)]
    secondary = [b for b in variant.get('branches', []) if b.get('observations', 1) < MIN_OBSERVATIONS and branch_is_plausible(b, height, True)]
    primary.sort(key=branch_priority, reverse=True)
    secondary.sort(key=branch_priority, reverse=True)

    selected = []
    used = trunk_tris
    primary_selected = 0
    secondary_selected = 0
    duplicate_rejected = 0
    for pool, secondary_pool in ((primary, False), (secondary, True)):
        for branch in pool:
            if is_duplicate_branch(branch, selected, height):
                duplicate_rejected += 1
                continue
            cost = estimate_branch_tris(branch, height, zmin, zmax)
            if cost <= 0 or used + cost > TARGET_STRUCTURE_TRIS:
                continue
            selected.append(branch)
            used += cost
            if secondary_pool:
                secondary_selected += 1
            else:
                primary_selected += 1
            if len(selected) >= MAX_BRANCHES:
                break
        if len(selected) >= MAX_BRANCHES:
            break
    return selected, used, len(primary), len(secondary), primary_selected, secondary_selected, duplicate_rejected


def build_variant(variant, xoff):
    h = variant['height']
    zmin = variant['zmin']
    zmax = variant['zmax']
    trunk_tris = cylinder_between((xoff, 0, zmin), (xoff, 0, zmax), h*0.018, h*0.006, TRUNK_SIDES, variant['name'] + '_trunk')
    selected, estimated, pc, sc, ps, ss, dup = select_branches(variant, trunk_tris)
    actual = trunk_tris
    connected = 0
    rejected_detached = 0
    max_connector = 0.0
    selected_ids = []
    for bi, branch in enumerate(selected):
        pts, connector = attach_path_to_trunk(branch, h, zmin, zmax)
        if not pts:
            rejected_detached += 1
            continue
        connected += 1
        max_connector = max(max_connector, connector)
        selected_ids.append(branch.get('id'))
        for p in pts:
            p.x += xoff
        base = h * (0.0046 * (1.0 - min(0.85, branch.get('t', 0.5))*0.48))
        seg_count = max(1, len(pts)-1)
        for si in range(seg_count):
            f0 = 1.0 - 0.74 * (si / seg_count)
            f1 = 1.0 - 0.74 * ((si+1) / seg_count)
            actual += cylinder_between(
                pts[si], pts[si+1],
                max(h*0.00105, base*f0),
                max(h*0.00070, base*f1),
                BRANCH_SIDES,
                f"{variant['name']}_b{bi:02d}_s{si:02d}"
            )
    return {
        'name': variant['name'], 'height': h,
        'primary_candidates': pc, 'secondary_candidates': sc,
        'primary_selected': ps, 'secondary_selected': ss,
        'selected_branches': len(selected), 'connected_branches': connected,
        'rejected_detached': rejected_detached, 'duplicate_rejected': dup,
        'max_connector': max_connector, 'estimated_tris': estimated,
        'actual_tris': actual, 'selected_ids': selected_ids,
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
    total_span = sum(v['height'] * 0.72 for v in variants[:-1]) + variants[-1]['height'] * 0.5
    cam_data = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    target = Vector((total_span * 0.42, 0, max_h * 0.50))
    cam.location = (target.x, -max_h * 2.4, target.z)
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = max_h * 1.16
    light_data = bpy.data.lights.new('Sun','SUN')
    light_data.energy = 3.0
    light = bpy.data.objects.new('Sun', light_data)
    bpy.context.collection.objects.link(light)
    light.rotation_euler = (math.radians(35), math.radians(-20), math.radians(30))
    scene = bpy.context.scene
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new('ArcontStructuralPreviewWorld')
        scene.world = world
    world.use_nodes = False
    world.color = (0.08, 0.08, 0.08)


def render_png(path):
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
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
    for variant in variants:
        reports.append(build_variant(variant, xoff))
        xoff += variant['height'] * 0.72
    make_material()
    os.makedirs(os.path.dirname(out_glb) or '.', exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out_glb, export_format='GLB')
    setup_camera_and_light(variants)
    render_png(out_png)
    report = {
        'target_structure_tris': TARGET_STRUCTURE_TRIS,
        'max_branches': MAX_BRANCHES,
        'filters': {
            'max_azimuth_deviation_deg': MAX_AZIMUTH_DEVIATION_DEG,
            'max_local_turn_deg': MAX_LOCAL_TURN_DEG,
            'min_radial_progress_ratio': MIN_RADIAL_PROGRESS_RATIO,
            'duplicate_z_ratio': DUPLICATE_Z_RATIO,
            'duplicate_azimuth_deg': DUPLICATE_AZIMUTH_DEG,
        },
        'variants': reports,
    }
    with open(out_json,'w',encoding='utf-8') as f:
        json.dump(report,f,indent=2)
    for r in reports:
        print(
            f"ARCONT_PINE_STRUCTURAL_EXPERIMENT={r['name']} connected={r['connected_branches']} "
            f"primary={r['primary_selected']} secondary={r['secondary_selected']} "
            f"candidates={r['primary_candidates']}+{r['secondary_candidates']} tris={r['actual_tris']} "
            f"duplicates={r['duplicate_rejected']} rejected_detached={r['rejected_detached']} "
            f"max_connector={r['max_connector']:.3f} mean_obs={r['mean_observations']:.2f}"
        )
    print('ARCONT_PINE_STRUCTURAL_PREVIEW=', out_png)
    print('ARCONT_PINE_STRUCTURAL_GLB=', out_glb)


if __name__ == '__main__':
    main()
