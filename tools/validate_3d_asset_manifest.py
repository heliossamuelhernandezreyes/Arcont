#!/usr/bin/env python3
import json, sys
from pathlib import Path

REQUIRED={"version","id","class","source","delivery","geometry","materials","lods","license"}
BUDGET={"hero":30000,"troop":18000,"creep":10000,"prop":8000,"structure":60000}

def validate(path: Path):
    d=json.loads(path.read_text(encoding="utf-8"))
    errors=[]
    missing=REQUIRED-set(d)
    if missing: errors.append("missing: "+", ".join(sorted(missing)))
    if d.get("delivery",{}).get("format")!="glb": errors.append("delivery.format must be glb")
    cls=d.get("class")
    tris=d.get("geometry",{}).get("lod0_triangles",0)
    if cls in BUDGET and tris>BUDGET[cls]: errors.append(f"LOD0 {tris} exceeds {cls} starting budget {BUDGET[cls]}")
    ratios=[x.get("ratio",0) for x in d.get("lods",[])]
    if not ratios or ratios[0]!=1.0: errors.append("LOD0 ratio must be 1.0")
    if any(b>=a for a,b in zip(ratios,ratios[1:])): errors.append("LOD ratios must strictly decrease")
    return errors

if __name__=="__main__":
    targets=[Path(x) for x in sys.argv[1:]] or list(Path("templates/3d-assets").glob("*.manifest.json"))
    failed=False
    for p in targets:
        e=validate(p)
        if e:
            failed=True
            print(f"FAIL {p}: " + "; ".join(e))
        else:
            print(f"OK {p}")
    raise SystemExit(1 if failed else 0)
