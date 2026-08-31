import bpy, json, math, os, sys
from collections import defaultdict

PROFILE_BANDS = 24
RADIAL_BINS = 12
SAMPLE_CAP = 250000


def tri_count(poly):
    return max(0, len(poly.vertices) - 2)


def material_name(obj, index):
    if 0 <= index < len(obj.material_slots):
        slot = obj.material_slots[index]
        if slot.material:
            return slot.material.name
    return f"material_{index}"


def quantile(values, q):
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))]


def sampled_vertices(obj, material_index=None):
    mesh = obj.data
    if material_index is None:
        ids = range(len(mesh.vertices))
    else:
        used = set()
        for p in mesh.polygons:
            if p.material_index == material_index:
                used.update(p.vertices)
        ids = sorted(used)
    ids = list(ids)
    if len(ids) > SAMPLE_CAP:
        step = len(ids) / float(SAMPLE_CAP)
        ids = [ids[int(i * step)] for i in range(SAMPLE_CAP)]
    return [mesh.vertices[i].co.copy() for i in ids]


def analyze_object(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    verts = [v.co for v in mesh.vertices]
    zmin = min(v.z for v in verts)
    zmax = max(v.z for v in verts)
    height = zmax - zmin
    xmin, xmax = min(v.x for v in verts), max(v.x for v in verts)
    ymin, ymax = min(v.y for v in verts), max(v.y for v in verts)

    tris_by_mat = defaultdict(int)
    polys_by_mat = defaultdict(int)
    for p in mesh.polygons:
        tris_by_mat[p.material_index] += tri_count(p)
        polys_by_mat[p.material_index] += 1

    materials = []
    bark_index = None
    twig_index = None
    for mi in sorted(tris_by_mat):
        name = material_name(obj, mi)
        entry = {
            "index": mi,
            "name": name,
            "triangles": tris_by_mat[mi],
            "polygons": polys_by_mat[mi],
        }
        materials.append(entry)
        low = name.lower()
        if bark_index is None and ("bark" in low or "trunk" in low):
            bark_index = mi
        if twig_index is None and ("twig" in low or "leaf" in low or "needle" in low or "foliage" in low):
            twig_index = mi

    # Crown occupancy by height. This gives us source-derived silhouette/negative-space targets.
    sample = sampled_vertices(obj)
    bands = []
    for bi in range(PROFILE_BANDS):
        t0 = bi / PROFILE_BANDS
        t1 = (bi + 1) / PROFILE_BANDS
        lo, hi = zmin + height * t0, zmin + height * t1
        band = [v for v in sample if (lo <= v.z < hi or (bi == PROFILE_BANDS - 1 and v.z <= hi))]
        if not band:
            bands.append({"t": (t0+t1)*0.5, "count": 0, "cx": 0, "cy": 0, "r50": 0, "r90": 0, "r98": 0})
            continue
        cx = sum(v.x for v in band) / len(band)
        cy = sum(v.y for v in band) / len(band)
        radii = [math.hypot(v.x-cx, v.y-cy) for v in band]
        bands.append({
            "t": (t0+t1)*0.5,
            "count": len(band),
            "cx": cx,
            "cy": cy,
            "r50": quantile(radii, 0.50),
            "r90": quantile(radii, 0.90),
            "r98": quantile(radii, 0.98),
        })

    # Bark-only directional occupancy. If bark is separable, this tells us whether source-derived
    # branch directions can replace procedural whorls without reconstructing every original triangle.
    bark_stats = None
    if bark_index is not None:
        bark = sampled_vertices(obj, bark_index)
        bark_stats = {"sample_vertices": len(bark), "bands": []}
        for bi in range(PROFILE_BANDS):
            t0 = bi / PROFILE_BANDS
            t1 = (bi + 1) / PROFILE_BANDS
            lo, hi = zmin + height * t0, zmin + height * t1
            band = [v for v in bark if (lo <= v.z < hi or (bi == PROFILE_BANDS - 1 and v.z <= hi))]
            if not band:
                bark_stats["bands"].append({"t": (t0+t1)*0.5, "count": 0, "directions": []})
                continue
            # Robust trunk center estimate from the innermost radial half around median XY.
            mx = quantile([v.x for v in band], 0.50)
            my = quantile([v.y for v in band], 0.50)
            ranked = sorted(band, key=lambda v: math.hypot(v.x-mx, v.y-my))
            core = ranked[:max(8, len(ranked)//3)]
            cx = sum(v.x for v in core) / len(core)
            cy = sum(v.y for v in core) / len(core)
            bins = [0] * RADIAL_BINS
            extents = [0.0] * RADIAL_BINS
            for v in band:
                dx, dy = v.x-cx, v.y-cy
                r = math.hypot(dx, dy)
                if r <= height * 0.012:
                    continue
                a = (math.atan2(dy, dx) + math.tau) % math.tau
                idx = min(RADIAL_BINS-1, int(a / math.tau * RADIAL_BINS))
                bins[idx] += 1
                extents[idx] = max(extents[idx], r)
            directions = []
            for idx, count in enumerate(bins):
                if count:
                    directions.append({
                        "angle_deg": (idx + 0.5) * 360.0 / RADIAL_BINS,
                        "samples": count,
                        "extent": extents[idx],
                    })
            directions.sort(key=lambda d: (d["extent"], d["samples"]), reverse=True)
            bark_stats["bands"].append({"t": (t0+t1)*0.5, "count": len(band), "cx": cx, "cy": cy, "directions": directions[:6]})

    return {
        "name": obj.name,
        "vertices": len(mesh.vertices),
        "polygons": len(mesh.polygons),
        "triangles": len(mesh.loop_triangles),
        "materials": materials,
        "bark_material_index": bark_index,
        "foliage_material_index": twig_index,
        "bounds": {"x": [xmin, xmax], "y": [ymin, ymax], "z": [zmin, zmax], "height": height},
        "profile": bands,
        "bark_directional_occupancy": bark_stats,
    }


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 2:
        raise SystemExit("usage: blender --background --python analyze_pine_source.py -- source.gltf report.json")
    source, out = argv
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=source)
    objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    report = {
        "source": os.path.basename(source),
        "mesh_objects": len(objects),
        "objects": [analyze_object(o) for o in objects],
    }
    report["total_triangles"] = sum(o["triangles"] for o in report["objects"])
    report["all_have_bark_split"] = all(o["bark_material_index"] is not None for o in report["objects"])
    report["all_have_foliage_split"] = all(o["foliage_material_index"] is not None for o in report["objects"])
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("ARCONT_PINE_ANALYSIS_OBJECTS=", report["mesh_objects"])
    print("ARCONT_PINE_ANALYSIS_TOTAL_TRIS=", report["total_triangles"])
    print("ARCONT_PINE_ANALYSIS_BARK_SPLIT=", report["all_have_bark_split"])
    print("ARCONT_PINE_ANALYSIS_FOLIAGE_SPLIT=", report["all_have_foliage_split"])
    for o in report["objects"]:
        print("ARCONT_PINE_VARIANT", o["name"], "tris=", o["triangles"], "height=", round(o["bounds"]["height"], 3), "materials=", [(m["name"], m["triangles"]) for m in o["materials"]])


if __name__ == "__main__":
    main()
