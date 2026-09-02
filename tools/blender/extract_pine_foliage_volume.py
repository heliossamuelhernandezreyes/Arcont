import bpy, json, math, os, sys
from collections import defaultdict
from mathutils import Vector

VOXEL_SIZE = 0.18
SAMPLE_CAP = 360000
TARGET_POINTS = 2600


def material_name(obj, index):
    if 0 <= index < len(obj.material_slots):
        slot = obj.material_slots[index]
        if slot.material:
            return slot.material.name
    return ''


def foliage_index(obj):
    for i, slot in enumerate(obj.material_slots):
        name = material_name(obj, i).lower()
        if any(k in name for k in ('twig', 'leaf', 'needle', 'foliage')):
            return i
    return None


def foliage_vertices(obj, mat_index):
    used = set()
    for p in obj.data.polygons:
        if p.material_index == mat_index:
            used.update(p.vertices)
    ids = sorted(used)
    if len(ids) > SAMPLE_CAP:
        step = len(ids) / float(SAMPLE_CAP)
        ids = [ids[int(i * step)] for i in range(SAMPLE_CAP)]
    return [obj.data.vertices[i].co.copy() for i in ids]


def hash01(i):
    x = math.sin((i + 1) * 12.9898) * 43758.5453
    return x - math.floor(x)


def extract(obj):
    mi = foliage_index(obj)
    if mi is None:
        raise RuntimeError(f'No foliage material found for {obj.name}')
    verts = foliage_vertices(obj, mi)
    if not verts:
        raise RuntimeError(f'No foliage vertices found for {obj.name}')
    zmin = min(v.z for v in verts)
    zmax = max(v.z for v in verts)
    height = max(1e-6, zmax - zmin)
    voxels = defaultdict(lambda: [Vector((0, 0, 0)), 0])
    for v in verts:
        key = (math.floor(v.x / VOXEL_SIZE), math.floor(v.y / VOXEL_SIZE), math.floor(v.z / VOXEL_SIZE))
        voxels[key][0] += v
        voxels[key][1] += 1
    cells = []
    max_count = max(c[1] for c in voxels.values())
    for key, (summed, count) in voxels.items():
        p = summed / count
        r = math.hypot(p.x, p.y)
        if r < height * 0.018:
            continue
        density = math.sqrt(count / max_count)
        score = count * (0.78 + 0.22 * min(1.0, r / max(0.1, height * 0.18)))
        cells.append((score, key, p, count, density))
    cells.sort(key=lambda x: x[0], reverse=True)
    # Preserve the densest source cells, then add deterministic spatial coverage from the remainder.
    keep_dense = min(len(cells), int(TARGET_POINTS * 0.72))
    selected = cells[:keep_dense]
    remainder = cells[keep_dense:]
    need = min(len(remainder), TARGET_POINTS - len(selected))
    if need > 0:
        stride = len(remainder) / float(need)
        selected.extend(remainder[min(len(remainder)-1, int((i + hash01(i)) * stride))] for i in range(need))
    selected.sort(key=lambda x: (x[2].z, math.atan2(x[2].y, x[2].x), math.hypot(x[2].x, x[2].y)))
    points = []
    for _, key, p, count, density in selected:
        radial = Vector((p.x, p.y, 0.0))
        if radial.length < 1e-6:
            radial = Vector((1, 0, 0))
        radial.normalize()
        points.append({
            'position': [round(p.x, 5), round(p.y, 5), round(p.z, 5)],
            'direction': [round(radial.x, 5), round(radial.y, 5), 0.0],
            'density': round(density, 5),
            'samples': count,
            'voxel': list(key),
        })
    return {
        'name': obj.name,
        'height': height,
        'source_foliage_vertices_sampled': len(verts),
        'occupied_voxels': len(voxels),
        'points': points,
    }


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(argv) != 2:
        raise SystemExit('usage: blender --background --python extract_pine_foliage_volume.py -- source.gltf out.json')
    source, out = argv
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=source)
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    variants = [extract(o) for o in objects]
    payload = {
        'representation': 'source_twig_voxel_volume_points',
        'voxel_size_m': VOXEL_SIZE,
        'target_points_per_variant': TARGET_POINTS,
        'variants': variants,
    }
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    for v in variants:
        print(f"ARCONT_PINE_FOLIAGE_VOLUME={v['name']} sampled={v['source_foliage_vertices_sampled']} voxels={v['occupied_voxels']} points={len(v['points'])}")
    print('ARCONT_PINE_FOLIAGE_VOLUME_VARIANTS=', len(variants))


if __name__ == '__main__':
    main()
