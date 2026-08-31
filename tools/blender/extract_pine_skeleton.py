import bpy, json, math, os, sys
from collections import defaultdict
from mathutils import Vector

BANDS = 28
SECTORS = 24
MIN_BRANCH_T = 0.18
MAX_BRANCH_T = 0.94
MAX_BRANCHES_PER_BAND = 6
MIN_EXTENT_FRAC = 0.025
TRUNK_RADIUS_FRAC = 0.022


def tri_count(poly):
    return max(0, len(poly.vertices) - 2)


def material_name(obj, index):
    if 0 <= index < len(obj.material_slots):
        slot = obj.material_slots[index]
        if slot.material:
            return slot.material.name
    return f"material_{index}"


def is_foliage(name):
    low = name.lower()
    return any(k in low for k in ("twig", "leaf", "needle", "foliage"))


def quantile(values, q):
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))]


def structural_vertices(obj):
    structural_mats = {
        i for i in range(len(obj.material_slots))
        if not is_foliage(material_name(obj, i))
    }
    used = set()
    for p in obj.data.polygons:
        if p.material_index in structural_mats:
            used.update(p.vertices)
    return [obj.data.vertices[i].co.copy() for i in sorted(used)], sorted(structural_mats)


def all_vertices(obj):
    return [v.co.copy() for v in obj.data.vertices]


def band_points(points, z0, z1, last=False):
    if last:
        return [p for p in points if z0 <= p.z <= z1]
    return [p for p in points if z0 <= p.z < z1]


def robust_center(points):
    if not points:
        return Vector((0, 0, 0))
    mx = quantile([p.x for p in points], 0.5)
    my = quantile([p.y for p in points], 0.5)
    ranked = sorted(points, key=lambda p: math.hypot(p.x - mx, p.y - my))
    core = ranked[:max(12, len(ranked) // 4)]
    return Vector((sum(p.x for p in core) / len(core), sum(p.y for p in core) / len(core), sum(p.z for p in core) / len(core)))


def crown_radius(points, center):
    if not points:
        return 0.0
    return quantile([math.hypot(p.x-center.x, p.y-center.y) for p in points], 0.98)


def extract_variant(obj):
    structure, structural_mats = structural_vertices(obj)
    source = all_vertices(obj)
    zmin = min(p.z for p in source)
    zmax = max(p.z for p in source)
    height = max(1e-6, zmax-zmin)
    min_extent = height * MIN_EXTENT_FRAC
    bands = []
    candidates = []

    for bi in range(BANDS):
        t0 = bi / float(BANDS)
        t1 = (bi+1) / float(BANDS)
        t = (t0+t1)*0.5
        lo = zmin + height*t0
        hi = zmin + height*t1
        sb = band_points(structure, lo, hi, bi == BANDS-1)
        ab = band_points(source, lo, hi, bi == BANDS-1)
        if not sb:
            bands.append({"t": t, "count": 0, "branches": []})
            continue
        center = robust_center(sb)
        cr = crown_radius(ab, center)
        sector_points = defaultdict(list)
        for p in sb:
            dx, dy = p.x-center.x, p.y-center.y
            r = math.hypot(dx, dy)
            if r <= height*TRUNK_RADIUS_FRAC:
                continue
            a = (math.atan2(dy, dx)+math.tau) % math.tau
            si = min(SECTORS-1, int(a/math.tau*SECTORS))
            sector_points[si].append((r,p))
        ranked = []
        for si, pts in sector_points.items():
            rs = [rp[0] for rp in pts]
            extent = quantile(rs, 0.98)
            if extent < min_extent or t < MIN_BRANCH_T or t > MAX_BRANCH_T:
                continue
            outer = [p for r,p in pts if r >= quantile(rs,0.75)]
            if not outer:
                continue
            tip = Vector((sum(p.x for p in outer)/len(outer), sum(p.y for p in outer)/len(outer), sum(p.z for p in outer)/len(outer)))
            direction = tip-center
            if direction.length < 1e-5:
                continue
            angle = (si+0.5)*360.0/SECTORS
            support = len(pts)
            score = extent * math.log2(2.0 + support) * (0.65 + 0.35*min(1.0, cr/max(extent,1e-6)))
            ranked.append({
                "band": bi, "t": t, "angle_deg": angle, "extent": extent,
                "support": support, "score": score,
                "start": [center.x, center.y, center.z],
                "end": [tip.x, tip.y, tip.z],
                "direction": list(direction.normalized()),
                "crown_r98": cr,
            })
        ranked.sort(key=lambda x: x["score"], reverse=True)
        selected = ranked[:MAX_BRANCHES_PER_BAND]
        bands.append({"t": t, "count": len(sb), "center": [center.x,center.y,center.z], "crown_r98": cr, "branches": selected})
        candidates.extend(selected)

    # Suppress near-duplicates across adjacent height bands while preserving strong silhouette branches.
    candidates.sort(key=lambda x: x["score"], reverse=True)
    kept = []
    for c in candidates:
        duplicate = False
        for k in kept:
            if abs(c["t"]-k["t"]) <= 1.5/BANDS:
                da = abs(c["angle_deg"]-k["angle_deg"])
                da = min(da, 360.0-da)
                if da <= 360.0/SECTORS*1.25:
                    duplicate = True
                    break
        if not duplicate:
            kept.append(c)
    kept.sort(key=lambda x: x["t"])

    return {
        "name": obj.name,
        "height": height,
        "zmin": zmin,
        "zmax": zmax,
        "structural_materials": [{"index": i, "name": material_name(obj,i)} for i in structural_mats],
        "bands": bands,
        "branches": kept,
        "branch_count": len(kept),
    }


def cylinder_between(start, end, radius, name):
    start, end = Vector(start), Vector(end)
    vec = end-start
    if vec.length < 1e-5:
        return None
    mid = (start+end)*0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=radius, depth=vec.length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector((0,0,1)).rotation_difference(vec.normalized())
    return obj


def build_preview(extracted, out_glb):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for vi, data in enumerate(extracted):
        h = data["height"]
        xoff = vi * h * 0.72
        trunk_start = Vector((xoff,0,data["zmin"]))
        trunk_end = Vector((xoff,0,data["zmax"]))
        cylinder_between(trunk_start,trunk_end,h*0.012,f'{data["name"]}_trunk')
        for bi,b in enumerate(data["branches"]):
            s = Vector(b["start"]); e = Vector(b["end"])
            s.x += xoff; e.x += xoff
            rad = max(h*0.0015, h*0.0045*(1.0-b["t"]*0.55))
            cylinder_between(s,e,rad,f'{data["name"]}_branch_{bi:03d}')
    os.makedirs(os.path.dirname(out_glb) or '.',exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out_glb, export_format='GLB')


def main():
    argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(argv) != 3:
        raise SystemExit('usage: blender --background --python extract_pine_skeleton.py -- source.gltf skeleton.json preview.glb')
    source,out_json,out_glb = argv
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=source)
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    extracted = [extract_variant(o) for o in objects]
    report = {"source": os.path.basename(source), "variants": extracted}
    os.makedirs(os.path.dirname(out_json) or '.',exist_ok=True)
    with open(out_json,'w',encoding='utf-8') as f:
        json.dump(report,f,indent=2)
    for v in extracted:
        print(f'ARCONT_PINE_SKELETON_VARIANT={v["name"]} branches={v["branch_count"]} height={v["height"]:.3f}')
    print('ARCONT_PINE_SKELETON_VARIANTS=',len(extracted))
    build_preview(extracted,out_glb)
    print('ARCONT_PINE_SKELETON_PREVIEW=',out_glb)


if __name__ == '__main__':
    main()
