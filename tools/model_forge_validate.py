#!/usr/bin/env python3
"""Production-budget validator for Model Forge inspection reports."""
import argparse,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("report"); ap.add_argument("--profile",required=True); a=ap.parse_args()
    report=json.loads(Path(a.report).read_text()); profile=json.loads(Path(a.profile).read_text())
    b=profile["budgets"]; failed=0; result=[]
    for x in report.get("assets",[]):
      errors=[]
      if x.get("triangles",0)>b["triangles_max"]: errors.append(f"triangles {x['triangles']} > {b['triangles_max']}")
      if x.get("materials",0)>b["materials_max"]: errors.append(f"materials {x['materials']} > {b['materials_max']}")
      if x.get("gltf_version")!="2.0": errors.append("not glTF 2.0")
      if errors: failed+=1
      result.append({"path":x.get("path"),"ok":not errors,"errors":errors})
    print(json.dumps({"profile":profile["id"],"ok":failed==0,"assets":result},indent=2))
    return 1 if failed else 0
if __name__=="__main__": raise SystemExit(main())
