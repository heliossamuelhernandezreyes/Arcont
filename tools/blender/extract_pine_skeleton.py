import bpy, json, math, os, sys
from collections import defaultdict
from mathutils import Vector

BANDS = 32
SECTORS = 32
MIN_BRANCH_T = 0.18
MAX_BRANCH_T = 0.94
MAX_BRANCHES_PER_BAND = 8
MIN_EXTENT_FRAC = 0.025
TRUNK_RADIUS_FRAC = 0.020
RADIAL_SHELLS = 7
MIN_PATH_POINTS = 4
TRACK_MAX_BAND_GAP = 2
TRACK_MAX_ANGLE_DEG = 24.0
TRACK_MAX_TIP_FRAC = 0.12
TRACK_MAX_EXTENT_RATIO = 1.65


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


def angle_delta(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


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
    return Vector((
        sum(p.x for p in core) / len(core),
        sum(p.y for p in core) / len(core),
        sum(p.z for p in core) / len(core),
    ))


def crown_radius(points, center):
    if not points:
        return 0.0
    return quantile([math.hypot(p.x-center.x, p.y-center.y) for p in points], 0.98)


def shell_center(points):
    if not points:
        return None
    # Median coordinates resist twig/dead-branch outliers better than a raw mean.
    return Vector((
        quantile([p.x for p in points], 0.5),
        quantile([p.y for p in points], 0.5),
        quantile([p.z for p in points], 0.5),
    ))


def trace_candidate_path(center, pts, extent, trunk_radius):
    """Approximate a branch centerline from the actual structural vertices in one angular sector.

    Instead of drawing a single radial stick from trunk to the sector's farthest sample, we split
    the source vertices into radial shells and take a robust center in each shell. The result is a
    short polyline that follows bends/elevation changes present in the original Poly Haven mesh.
    """
    if extent <= trunk_radius:
        return []
    shells = []
    inner = max(trunk_radius, extent * 0.06)
    span = max(1e-6, extent - inner)
    for si in range(RADIAL_SHELLS):
        r0 = inner + span * (si / RADIAL_SHELLS)
        r1 = inner + span * ((si + 1) / RADIAL_SHELLS)
        shell = [p for r, p in pts if r0 <= r <= r1]
        c = shell_center(shell)
        if c is not None:
            shells.append((si, c, len(shell)))
    if len(shells) < MIN_PATH_POINTS - 1:
        return []

    path = [center.copy()]
    last = center
    for _si, p, support in shells:
        # Reject pathological jumps caused by unrelated geometry sharing a sector.
        if (p-last).length > max(extent * 0.48, trunk_radius * 5.0):
            continue
        if (p-last).length > trunk_radius * 0.30:
            path.append(p)
            last = p
    if len(path) < MIN_PATH_POINTS:
        return []
    return path


def candidate_from_sector(obj_height, bi, t, center, crown_r, si, pts):
    rs = [rp[0] for rp in pts]
    extent = quantile(rs, 0.98)
    min_extent = obj_height * MIN_EXTENT_FRAC
    if extent < min_extent or t < MIN_BRANCH_T or t > MAX_BRANCH_T:
        return None
    trunk_radius = obj_height * TRUNK_RADIUS_FRAC
    path = trace_candidate_path(center, pts, extent, trunk_radius)
    if not path:
        return None
    tip = path[-1]
    direction = tip-center
    if direction.length < 1e-5:
        return None
    angle = (math.degrees(math.atan2(direction.y, direction.x)) + 360.0) % 360.0
    support = len(pts)
    curvature = 0.0
    for i in range(1, len(path)-1):
        a = (path[i]-path[i-1]).normalized()
        b = (path[i+1]-path[i]).normalized()
        curvature += math.degrees(a.angle(b)) if a.length and b.length else 0.0
    score = extent * math.log2(2.0 + support) * (0.70 + 0.30*min(1.0, crown_r/max(extent, 1e-6)))
    return {
        "band": bi,
        "t": t,
        "sector": si,
        "angle_deg": angle,
        "extent": extent,
        "support": support,
        "score": score,
        "curvature_deg": curvature,
        "start": list(path[0]),
        "end": list(path[-1]),
        "direction": list(direction.normalized()),
        "crown_r98": crown_r,
        "path": [list(p) for p in path],
    }


def track_cost(a, b, height):
    gap = b["band"] - a["band"]
    if gap < 1 or gap > TRACK_MAX_BAND_GAP:
        return None
    da = angle_delta(a["angle_deg"], b["angle_deg"])
    if da > TRACK_MAX_ANGLE_DEG:
        return None
    ratio = max(a["extent"], b["extent"]) / max(1e-6, min(a["extent"], b["extent"]))
    if ratio > TRACK_MAX_EXTENT_RATIO:
        return None
    ta, tb = Vector(a["end"]), Vector(b["end"])
    tip_dist = (ta-tb).length
    if tip_dist > height * TRACK_MAX_TIP_FRAC:
        return None
    return da / TRACK_MAX_ANGLE_DEG + tip_dist / (height*TRACK_MAX_TIP_FRAC) + (ratio-1.0)*0.7 + (gap-1)*0.25


def merge_track(track, track_id):
    obs = sorted(track, key=lambda c: c["band"])
    strongest = max(obs, key=lambda c: c["score"])
    weights = [max(1e-6, c["score"]) for c in obs]
    sw = sum(weights)

    # Start at the weighted trunk attachment, then average equivalent radial samples from all
    # observations. This converts repeated vertical slices of one source branch into one curve.
    start = Vector((0,0,0))
    for c,w in zip(obs,weights):
        start += Vector(c["start"]) * (w/sw)
    max_nodes = max(len(c["path"]) for c in obs)
    merged = [start]
    for ni in range(1, max_nodes):
        acc = Vector((0,0,0)); ww = 0.0
        for c,w in zip(obs,weights):
            path = c["path"]
            if len(path) <= 1:
                continue
            src_i = min(len(path)-1, int(round(ni * (len(path)-1) / max(1, max_nodes-1))))
            acc += Vector(path[src_i]) * w
            ww += w
        if ww:
            p = acc / ww
            if (p-merged[-1]).length > 1e-4:
                merged.append(p)
    if len(merged) < 2:
        merged = [Vector(strongest["start"]), Vector(strongest["end"])]

    vec = merged[-1]-merged[0]
    return {
        "id": track_id,
        "observations": len(obs),
        "band_start": obs[0]["band"],
        "band_end": obs[-1]["band"],
        "t": sum(c["t"]*w for c,w in zip(obs,weights))/sw,
        "angle_deg": (math.degrees(math.atan2(vec.y,vec.x))+360.0)%360.0 if vec.length else strongest["angle_deg"],
        "extent": max((Vector(p)-merged[0]).length for p in merged),
        "support": sum(c["support"] for c in obs),
        "score": sum(c["score"] for c in obs) * (1.0 + 0.18*(len(obs)-1)),
        "crown_r98": max(c["crown_r98"] for c in obs),
        "path": [list(p) for p in merged],
        "start": list(merged[0]),
        "end": list(merged[-1]),
        "source_observations": [{"band":c["band"],"angle_deg":c["angle_deg"],"extent":c["extent"],"score":c["score"]} for c in obs],
    }


def build_tracks(candidates, height):
    by_band = defaultdict(list)
    for c in candidates:
        by_band[c["band"]].append(c)
    tracks = []
    assigned = set()
    ordered = sorted(candidates, key=lambda c: (-c["score"], c["band"]))
    for seed in ordered:
        sid = id(seed)
        if sid in assigned:
            continue
        track = [seed]
        assigned.add(sid)
        current = seed
        while True:
            choices = []
            for gap in range(1, TRACK_MAX_BAND_GAP+1):
                for nxt in by_band.get(current["band"]+gap, []):
                    if id(nxt) in assigned:
                        continue
                    cost = track_cost(current, nxt, height)
                    if cost is not None:
                        choices.append((cost, -nxt["score"], nxt))
            if not choices:
                break
            choices.sort(key=lambda x: (x[0], x[1]))
            nxt = choices[0][2]
            track.append(nxt)
            assigned.add(id(nxt))
            current = nxt
        tracks.append(track)

    merged = [merge_track(t, i) for i,t in enumerate(tracks)]
    # Remove single-slice weak duplicates around stronger continuous tracks.
    merged.sort(key=lambda b: b["score"], reverse=True)
    kept = []
    for b in merged:
        duplicate = False
        for k in kept:
            if abs(b["t"]-k["t"]) <= 1.5/BANDS and angle_delta(b["angle_deg"], k["angle_deg"]) <= 360.0/SECTORS*1.25:
                if b["observations"] <= k["observations"]:
                    duplicate = True
                    break
        if not duplicate:
            kept.append(b)
    kept.sort(key=lambda b: b["t"])
    for i,b in enumerate(kept):
        b["id"] = i
    return kept


def extract_variant(obj):
    structure, structural_mats = structural_vertices(obj)
    source = all_vertices(obj)
    zmin = min(p.z for p in source)
    zmax = max(p.z for p in source)
    height = max(1e-6, zmax-zmin)
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
            c = candidate_from_sector(height, bi, t, center, cr, si, pts)
            if c is not None:
                ranked.append(c)
        ranked.sort(key=lambda x: x["score"], reverse=True)
        selected = ranked[:MAX_BRANCHES_PER_BAND]
        bands.append({"t": t, "count": len(sb), "center": list(center), "crown_r98": cr, "branches": selected})
        candidates.extend(selected)

    branches = build_tracks(candidates, height)
    continuous = sum(1 for b in branches if b["observations"] >= 2)
    mean_nodes = sum(len(b["path"]) for b in branches) / max(1, len(branches))
    return {
        "name": obj.name,
        "height": height,
        "zmin": zmin,
        "zmax": zmax,
        "structural_materials": [{"index": i, "name": material_name(obj,i)} for i in structural_mats],
        "bands": bands,
        "candidate_count": len(candidates),
        "branches": branches,
        "branch_count": len(branches),
        "continuous_branch_count": continuous,
        "mean_path_nodes": mean_nodes,
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
            path = [Vector(p) for p in b["path"]]
            for p in path:
                p.x += xoff
            base_rad = max(h*0.00125, h*0.0046*(1.0-b["t"]*0.58))
            for si in range(len(path)-1):
                taper = max(0.34, 1.0 - 0.60*(si/max(1,len(path)-2)))
                cylinder_between(path[si], path[si+1], base_rad*taper, f'{data["name"]}_branch_{bi:03d}_{si:02d}')
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
    report = {
        "source": os.path.basename(source),
        "method": "radial-shell centerline tracing plus cross-band continuity tracking",
        "variants": extracted,
    }
    os.makedirs(os.path.dirname(out_json) or '.',exist_ok=True)
    with open(out_json,'w',encoding='utf-8') as f:
        json.dump(report,f,indent=2)
    for v in extracted:
        print(
            f'ARCONT_PINE_SKELETON_VARIANT={v["name"]} branches={v["branch_count"]} '
            f'continuous={v["continuous_branch_count"]} mean_nodes={v["mean_path_nodes"]:.2f} height={v["height"]:.3f}'
        )
    print('ARCONT_PINE_SKELETON_VARIANTS=',len(extracted))
    build_preview(extracted,out_glb)
    print('ARCONT_PINE_SKELETON_PREVIEW=',out_glb)


if __name__ == '__main__':
    main()
