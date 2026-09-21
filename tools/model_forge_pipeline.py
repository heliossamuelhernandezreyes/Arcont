#!/usr/bin/env python3
"""Model Forge evidence pipeline: inspect -> optional spec gate -> production gate -> collision recipe -> evidence."""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1<<20),b""): h.update(c)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("--profile",required=True); ap.add_argument("--out",default="model-forge-evidence"); ap.add_argument("--require-spec-validator",action="store_true"); a=ap.parse_args()
 model=Path(a.model); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
 inspection=out/"inspection.json"
 subprocess.run([sys.executable,"tools/model_forge_inspect.py",str(model),"--out",str(inspection)],check=True)
 spec_status="not-requested"
 if a.require_spec_validator:
  if not shutil.which("gltf_validator"): raise SystemExit("spec validator required but unavailable")
  subprocess.run([sys.executable,"tools/model_forge_spec_validate.py",str(model),"--out",str(out/"gltf-validator.json")],check=True); spec_status="passed"
 v=subprocess.run([sys.executable,"tools/model_forge_validate.py",str(inspection),"--profile",a.profile],capture_output=True,text=True)
 (out/"production-validation.json").write_text(v.stdout,encoding="utf-8")
 subprocess.run([sys.executable,"tools/model_forge_collision.py",str(model),"--out",str(out/"collision.recipe.json")],check=True)
 manifest={"version":2,"input":{"path":str(model),"sha256":sha(model),"size_bytes":model.stat().st_size},"profile":a.profile,
  "inspection_sha256":sha(inspection),"spec_validation":spec_status,"production_validation_exit":v.returncode,
  "collision_recipe_sha256":sha(out/"collision.recipe.json")}
 (out/"evidence.manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8"); print(json.dumps(manifest,indent=2)); return v.returncode
if __name__=="__main__": raise SystemExit(main())
