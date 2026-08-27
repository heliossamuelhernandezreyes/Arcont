#!/usr/bin/env python3
"""Generate a modular low-poly humanoid OBJ for Arcont.

No third-party packages required. The OBJ keeps body parts as separate objects so
it can be imported into Nomad Sculpt and later used for modular gore/rigging.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "character_config.json"
OUTPUT_DIR = ROOT / "output"


class ObjBuilder:
    def __init__(self) -> None:
        self.vertices: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, ...]] = []
        self.objects: list[tuple[str, int, int]] = []

    def add_object(self, name: str, verts, faces) -> None:
        start_v = len(self.vertices)
        start_f = len(self.faces)
        self.vertices.extend(verts)
        for face in faces:
            self.faces.append(tuple(start_v + i + 1 for i in face))
        self.objects.append((name, start_f, len(self.faces)))

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        object_index = 0
        with path.open("w", encoding="utf-8") as f:
            f.write("# Arcont modular low-poly character\n")
            for v in self.vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            for face_index, face in enumerate(self.faces):
                while object_index < len(self.objects) and face_index == self.objects[object_index][1]:
                    f.write(f"o {self.objects[object_index][0]}\n")
                    object_index += 1
                f.write("f " + " ".join(str(i) for i in face) + "\n")


def ring_mesh(center, axis, length, radii, segments=16, rings=6):
    """Tapered rounded tube aligned to X, Y or Z, mostly quad topology."""
    cx, cy, cz = center
    verts = []
    faces = []
    rx0, rz0, rx1, rz1 = radii

    for r in range(rings + 1):
        t = r / rings
        smooth = 0.5 - 0.5 * math.cos(math.pi * t)
        a = -length / 2 + length * t
        rx = rx0 + (rx1 - rx0) * smooth
        rz = rz0 + (rz1 - rz0) * smooth
        # Slight rounding near endpoints without collapsing them; keeps clean gore cuts.
        bulge = 0.94 + 0.06 * math.sin(math.pi * t)
        for s in range(segments):
            ang = 2 * math.pi * s / segments
            u = math.cos(ang) * rx * bulge
            v = math.sin(ang) * rz * bulge
            if axis == "y":
                verts.append((cx + u, cy + a, cz + v))
            elif axis == "x":
                verts.append((cx + a, cy + u, cz + v))
            else:
                verts.append((cx + u, cy + v, cz + a))

    for r in range(rings):
        for s in range(segments):
            n = (s + 1) % segments
            a = r * segments + s
            b = r * segments + n
            c = (r + 1) * segments + n
            d = (r + 1) * segments + s
            faces.append((a, b, c, d))

    # Flat cap n-gons preserve clean modular cut surfaces.
    faces.append(tuple(range(segments - 1, -1, -1)))
    base = rings * segments
    faces.append(tuple(base + s for s in range(segments)))
    return verts, faces


def ellipsoid(center, radii, segments=16, rings=12):
    cx, cy, cz = center
    rx, ry, rz = radii
    verts = []
    faces = []

    for r in range(rings + 1):
        phi = math.pi * r / rings
        y = math.cos(phi) * ry
        rr = math.sin(phi)
        for s in range(segments):
            theta = 2 * math.pi * s / segments
            verts.append((cx + math.cos(theta) * rx * rr,
                          cy + y,
                          cz + math.sin(theta) * rz * rr))

    for r in range(rings):
        for s in range(segments):
            n = (s + 1) % segments
            faces.append((r * segments + s,
                          r * segments + n,
                          (r + 1) * segments + n,
                          (r + 1) * segments + s))
    return verts, faces


def box(name, center, size):
    cx, cy, cz = center
    sx, sy, sz = (v / 2 for v in size)
    verts = [
        (cx-sx, cy-sy, cz-sz), (cx+sx, cy-sy, cz-sz),
        (cx+sx, cy+sy, cz-sz), (cx-sx, cy+sy, cz-sz),
        (cx-sx, cy-sy, cz+sz), (cx+sx, cy-sy, cz+sz),
        (cx+sx, cy+sy, cz+sz), (cx-sx, cy+sy, cz+sz),
    ]
    faces = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(4,0,3,7)]
    return name, verts, faces


def generate(cfg: dict) -> tuple[ObjBuilder, int]:
    p = cfg["proportions"]
    seg = int(cfg.get("radial_segments", 16))
    H = float(cfg.get("height_m", 1.78))
    gap = float(cfg.get("gore", {}).get("cut_gap_m", 0.008))

    # Normalize authored proportions around the requested total height.
    authored = p["head_height"] + p["neck_height"] + p["torso_height"] + p["pelvis_height"] + p["thigh_length"] + p["shin_length"] + 0.10
    k = H / authored
    q = {key: value * k for key, value in p.items()}

    b = ObjBuilder()
    ground = 0.0
    shin_y = ground + q["shin_length"] / 2 + 0.08 * k
    knee_y = shin_y + q["shin_length"] / 2 + gap
    thigh_y = knee_y + q["thigh_length"] / 2 + gap
    hip_y = thigh_y + q["thigh_length"] / 2 + gap
    pelvis_y = hip_y + q["pelvis_height"] / 2
    torso_y = pelvis_y + q["pelvis_height"] / 2 + q["torso_height"] / 2 + gap
    shoulder_y = torso_y + q["torso_height"] / 2 - 0.06 * k
    neck_y = torso_y + q["torso_height"] / 2 + q["neck_height"] / 2 + gap
    head_y = neck_y + q["neck_height"] / 2 + q["head_height"] / 2 + gap

    # Core
    verts, faces = ellipsoid((0, head_y, 0), (q["head_width"]/2, q["head_height"]/2, q["head_depth"]/2), seg, 12)
    b.add_object("head", verts, faces)
    verts, faces = ring_mesh((0, neck_y, 0), "y", q["neck_height"], (0.055*k,0.055*k,0.060*k,0.060*k), seg, 3)
    b.add_object("neck", verts, faces)
    verts, faces = ring_mesh((0, torso_y, 0), "y", q["torso_height"], (q["waist_width"]/2, q["torso_depth"]/2, q["shoulder_width"]/2, q["torso_depth"]/2), seg, 10)
    b.add_object("torso", verts, faces)
    verts, faces = ring_mesh((0, pelvis_y, 0), "y", q["pelvis_height"], (q["waist_width"]*0.48, q["torso_depth"]*0.52, q["waist_width"]*0.56, q["torso_depth"]*0.58), seg, 5)
    b.add_object("pelvis", verts, faces)

    # Arms in T-pose for easy rigging and Nomad editing.
    side = q["shoulder_width"] / 2
    for sign, suffix in ((-1, "L"), (1, "R")):
        upper_x = sign * (side + q["upper_arm_length"] / 2 + gap)
        fore_x = sign * (side + q["upper_arm_length"] + q["forearm_length"] / 2 + gap*2)
        hand_x = sign * (side + q["upper_arm_length"] + q["forearm_length"] + q["hand_length"] / 2 + gap*3)
        verts, faces = ring_mesh((upper_x, shoulder_y, 0), "x", q["upper_arm_length"], (q["arm_radius"],q["arm_radius"],q["arm_radius"]*0.86,q["arm_radius"]*0.86), seg, 6)
        b.add_object(f"upper_arm_{suffix}", verts, faces)
        verts, faces = ring_mesh((fore_x, shoulder_y, 0), "x", q["forearm_length"], (q["arm_radius"]*0.82,q["arm_radius"]*0.82,q["arm_radius"]*0.62,q["arm_radius"]*0.62), seg, 6)
        b.add_object(f"forearm_{suffix}", verts, faces)
        n, v, f = box(f"hand_{suffix}", (hand_x, shoulder_y, 0), (q["hand_length"], q["arm_radius"]*1.35, q["arm_radius"]*0.95))
        b.add_object(n, v, f)

    # Legs
    leg_x = q["waist_width"] * 0.26
    for sign, suffix in ((-1, "L"), (1, "R")):
        x = sign * leg_x
        verts, faces = ring_mesh((x, thigh_y, 0), "y", q["thigh_length"], (q["leg_radius"]*0.92,q["leg_radius"]*0.92,q["leg_radius"]*1.12,q["leg_radius"]*1.05), seg, 8)
        b.add_object(f"thigh_{suffix}", verts, faces)
        verts, faces = ring_mesh((x, shin_y, 0), "y", q["shin_length"], (q["leg_radius"]*0.72,q["leg_radius"]*0.72,q["leg_radius"]*0.88,q["leg_radius"]*0.88), seg, 8)
        b.add_object(f"shin_{suffix}", verts, faces)
        n, v, f = box(f"foot_{suffix}", (x, 0.055*k, -q["foot_length"]*0.12), (q["leg_radius"]*1.65, 0.11*k, q["foot_length"]))
        b.add_object(n, v, f)

    quads = sum(1 for face in b.faces if len(face) == 4)
    return b, quads


def main() -> None:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    builder, quads = generate(cfg)
    name = cfg.get("name", "arcont_character")
    out = OUTPUT_DIR / f"{name}.obj"
    builder.write(out)
    print(f"Generated: {out}")
    print(f"Vertices: {len(builder.vertices)}")
    print(f"Faces: {len(builder.faces)}")
    print(f"Quad faces: {quads}")
    print(f"Target quads: {cfg.get('target_quads', 'n/a')}")
    print("Body parts remain separate for gore, rigging and Nomad editing.")


if __name__ == "__main__":
    main()
