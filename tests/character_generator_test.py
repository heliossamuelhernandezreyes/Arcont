#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "tools" / "character_generator" / "generate_character.py"
OUT = ROOT / "tools" / "character_generator" / "output" / "arcont_survivor_base.obj"

subprocess.run([sys.executable, str(GEN)], cwd=ROOT, check=True)
if not OUT.is_file() or OUT.stat().st_size < 1000:
    raise SystemExit("Survivor generator did not produce a usable OBJ")

vertices = []
objects = set()
faces = 0
for line in OUT.read_text(encoding="utf-8").splitlines():
    if line.startswith("v "):
        _, x, y, z = line.split()
        vertices.append((float(x), float(y), float(z)))
    elif line.startswith("o "):
        objects.add(line[2:].strip())
    elif line.startswith("f "):
        faces += 1

required = {
    "head", "neck", "torso", "pelvis",
    "upper_arm_L", "upper_arm_R", "forearm_L", "forearm_R",
    "hand_L", "hand_R", "thigh_L", "thigh_R", "shin_L", "shin_R",
    "foot_L", "foot_R",
}
missing = sorted(required - objects)
if missing:
    raise SystemExit(f"Missing modular body objects: {missing}")
if len(vertices) < 500 or faces < 500:
    raise SystemExit(f"Unexpectedly low geometry: vertices={len(vertices)} faces={faces}")

xs = [v[0] for v in vertices]
ys = [v[1] for v in vertices]
zs = [v[2] for v in vertices]
size = (max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))
height = size[1]
if not (1.65 <= height <= 1.90):
    raise SystemExit(f"Generated character is not meter-scale: bounds={size}")
if max(size) > 2.1:
    raise SystemExit(f"Generated character bounds are implausible: {size}")

print(f"ARCONT CHARACTER GENERATOR OK: vertices={len(vertices)} faces={faces} objects={len(objects)} bounds_m={size}")
