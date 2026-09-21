#!/usr/bin/env python3
"""Offline Model Forge smoke pipeline: fixture -> inspect -> validate -> evidence."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("--profile",required=True); ap.add_argument("--out",default="model-forge-evidence"); a=ap.parse_args()
    model=Path(a.model); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    inspection=out/"inspection.json"
    subprocess.run([sys.executable,"tools/model_forge_inspect.py",str(model),"--out",str(inspection)],check=True)
    v=subprocess.run([sys.executable,"tools/model_forge_validate.py",str(inspection),"--profile",a.profile],capture_output=True,text=True)
    (out/"production-validation.json").write_text(v.stdout,encoding="utf-8")
    manifest={"version":1,"input":{"path":str(model),"sha256":sha256(model),"size_bytes":model.stat().st_size},
      "profile":a.profile,"inspection_sha256":sha256(inspection),"production_validation_exit":v.returncode}
    (out/"evidence.manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))
    return v.returncode
if __name__=="__main__": raise SystemExit(main())
