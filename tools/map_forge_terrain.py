"""Explicit, reversible heightfield brush operations; no map design generator."""
import copy
import math


MODES = ("raise", "lower", "flatten", "smooth", "paint", "hole", "fill")


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def brush(state, options):
    result = copy.deepcopy(state)
    fields = result["map"].get("authoring", {}).get("heightfields", [])
    selected = [f for f in fields if f.get("id") == options.get("heightfield_id")]
    if len(selected) != 1:
        raise ValueError("brush requires a unique heightfield_id")
    f = selected[0]
    cols, rows = f.get("columns"), f.get("rows")
    if not all(number(n) and n == int(n) and 2 <= n <= 2049 for n in (cols, rows)):
        raise ValueError("heightfield dimensions must be integral and in [2,2049]")
    cols, rows = int(cols), int(rows)
    heights = f.get("heights")
    spacing = f.get("spacing", [1, 1])
    origin = f.get("position", [0, 0, 0])
    center = options.get("center")
    radius, strength = options.get("radius"), options.get("strength", 1)
    mode = options.get("mode")
    if not isinstance(heights, list) or len(heights) != cols * rows or not all(number(h) for h in heights):
        raise ValueError("heightfield heights must match dimensions and be finite")
    if not isinstance(spacing, list) or len(spacing) != 2 or not all(number(n) and n > 0 for n in spacing):
        raise ValueError("heightfield spacing must be two positive numbers")
    if not isinstance(origin, list) or len(origin) != 3 or not all(number(n) for n in origin):
        raise ValueError("heightfield position must be finite xyz")
    if not isinstance(center, list) or len(center) != 2 or not all(number(n) for n in center):
        raise ValueError("brush center must be finite world [x,z]")
    if mode not in MODES or not number(radius) or radius <= 0 or not number(strength) or strength < 0:
        raise ValueError("invalid brush mode, radius or strength")
    target = options.get("height", 0)
    if not number(target):
        raise ValueError("brush height must be finite")
    material = options.get("material")
    if mode == "paint" and material not in {m["id"] for m in result["map"].get("authoring", {}).get("materials", [])}:
        raise ValueError("paint material must exist in authoring.materials")
    cell_count = (cols - 1) * (rows - 1)
    paint = f.get("paint", [f.get("material", "earth_dark")] * cell_count)
    holes = f.get("holes", [False] * cell_count)
    if not isinstance(paint, list) or len(paint) != cell_count or not isinstance(holes, list) or len(holes) != cell_count:
        raise ValueError("heightfield paint and holes must match cell dimensions")
    original = heights[:]
    changed = 0
    for z in range(rows if mode not in ("paint", "hole", "fill") else rows - 1):
        for x in range(cols if mode not in ("paint", "hole", "fill") else cols - 1):
            offset = 0.5 if mode in ("paint", "hole", "fill") else 0
            distance = math.hypot(origin[0] + (x + offset) * spacing[0] - center[0], origin[2] + (z + offset) * spacing[1] - center[1])
            if distance >= radius:
                continue
            weight = 1 - distance / radius
            if mode in ("paint", "hole", "fill"):
                i = z * (cols - 1) + x
                if mode == "paint":
                    paint[i] = material
                else:
                    holes[i] = mode == "hole"
            else:
                i = z * cols + x
                if mode in ("raise", "lower"):
                    heights[i] += strength * weight * (1 if mode == "raise" else -1)
                else:
                    value = target
                    if mode == "smooth":
                        neighbors = [original[nz * cols + nx] for nz in range(max(0, z - 1), min(rows, z + 2)) for nx in range(max(0, x - 1), min(cols, x + 2))]
                        value = sum(neighbors) / len(neighbors)
                    heights[i] += (value - original[i]) * min(strength, 1) * weight
            changed += 1
    if mode == "paint":
        f["paint"] = paint
    if mode in ("hole", "fill"):
        f["holes"] = holes
    if changed == 0:
        raise ValueError("brush does not intersect this heightfield")
    return result
