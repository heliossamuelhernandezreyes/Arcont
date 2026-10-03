"""Reusable animation profile and explicit tactical-sector contract validation."""
from __future__ import annotations
import math
import re


def finite_number(value, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError("invalid finite measurement")
    return value


def animation_profile(profile):
    if profile.get("version") != 1 or not profile.get("clips") or not profile.get("bone_map"):
        raise ValueError("animation profile needs clips and an explicit bone map")
    names = list(profile["bone_map"].values())
    if len(names) != len(set(names)) or any(not isinstance(x, str) or not x for x in names):
        raise ValueError("bone mapping is not one-to-one")
    finite_number(profile["translation_scale"], 0.01, 100)
    if len(profile["clips"]) != len(set(profile["clips"])):
        raise ValueError("duplicate animation clips")
    if any(not isinstance(x, str) or not x for x in [*profile["bone_map"], *profile["clips"]]):
        raise ValueError("bone and clip names must be nonempty strings")
    for key in ("source_model", "target_model", "source_library"):
        path = profile.get(key)
        if not isinstance(path, str) or not path.startswith("res://") or ".." in path.split("/"):
            raise ValueError("animation resources must be project-owned res paths")
    skeleton = profile.get("target_skeleton_path")
    if not isinstance(skeleton, str) or not skeleton or skeleton.startswith("/") or ":" in skeleton or ".." in skeleton.split("/"):
        raise ValueError("target skeleton must be a model-relative node path")
    return profile


def sector(recipe):
    """Author supplies the entire layout. No stochastic or hidden geometry choices."""
    if recipe.get("version") != 1 or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", recipe.get("id", "")):
        raise ValueError("invalid sector identity")
    floor = recipe["floor"]
    if len(floor["size"]) != 2:
        raise ValueError("floor size needs two dimensions")
    width, depth = [finite_number(x, 4, 512) for x in floor["size"]]
    objects = []
    ids = set()
    for item in recipe["covers"]:
        if item["id"] in ids:
            raise ValueError("duplicate cover ID")
        ids.add(item["id"])
        if len(item["position"]) != 2 or len(item["size"]) != 3:
            raise ValueError("invalid cover dimensions")
        x, z = [finite_number(x, -512, 512) for x in item["position"]]
        sx, height, sz = [finite_number(x, 0.1, 30) for x in item["size"]]
        if abs(x) + sx / 2 > width / 2 or abs(z) + sz / 2 > depth / 2:
            raise ValueError("cover extends outside sector")
        if item.get("vaultable") and not 0.45 <= height <= 1.35:
            raise ValueError("vaultable cover violates the declared traversal range")
        objects.append({**item, "bounds": [x-sx/2, z-sz/2, x+sx/2, z+sz/2]})
    routes = recipe["routes"]
    if len(routes) < 2 or len({x["id"] for x in routes}) != len(routes):
        raise ValueError("sector requires distinct authored routes")
    for route in routes:
        radius = finite_number(route["clearance_radius"], 0.1, 4)
        points = route["points"]
        if len(points) < 2:
            raise ValueError("route requires at least two points")
        for point in points:
            if len(point) != 2:
                raise ValueError("route point requires x/z")
            x, z = [finite_number(v, -512, 512) for v in point]
            if abs(x)+radius > width/2 or abs(z)+radius > depth/2:
                raise ValueError("route clearance extends outside sector")
        for a, b in zip(points, points[1:]):
            if a == b:
                raise ValueError("route contains a zero-length segment")
            # Slab intersection tests the swept horizontal clearance against each box.
            for obstacle in objects:
                xmin, zmin, xmax, zmax = obstacle["bounds"]
                low, high = 0.0, 1.0
                for origin, delta, lo, hi in [(a[0],b[0]-a[0],xmin-radius,xmax+radius),
                                             (a[1],b[1]-a[1],zmin-radius,zmax+radius)]:
                    if abs(delta) < 1e-12:
                        if not lo <= origin <= hi:
                            low, high = 1.0, 0.0
                            break
                    else:
                        t1,t2=(lo-origin)/delta,(hi-origin)/delta
                        low,high=max(low,min(t1,t2)),min(high,max(t1,t2))
                if low <= high:
                    raise ValueError(f"route {route['id']} intersects cover {obstacle['id']}")
    return {"ok": True, "id": recipe["id"], "covers": len(objects), "routes": len(routes),
            "limits": ["axis-aligned authored geometry; physical paths require engine acceptance"]}
