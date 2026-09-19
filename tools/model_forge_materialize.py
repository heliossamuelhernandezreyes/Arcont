#!/usr/bin/env python3
"""ARCONT Model Forge v0.1: conservative materializer for catalogued assets."""
import argparse, hashlib, json, shutil, sys, urllib.request, zipfile
from pathlib import Path

UA="ARCONT-Model-Forge/0.1 (+https://github.com/heliossamuelhernandezreyes/Arcont)"
MODEL_EXT={".glb",".gltf",".fbx",".obj",".dae",".blend"}

def load_record(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def gate(record):
    lic=record.get("license",{})
    if not lic.get("commercial_use"): raise SystemExit("license gate: commercial_use is not true")
    if not lic.get("modification"): raise SystemExit("license gate: modification is not true")
    return lic.get("name","UNKNOWN")

def download(url, dest):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    h=hashlib.sha256()
    with urllib.request.urlopen(req,timeout=60) as r, open(dest,"wb") as f:
        while True:
            chunk=r.read(1024*1024)
            if not chunk: break
            h.update(chunk); f.write(chunk)
    return h.hexdigest()

def inventory(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.suffix.lower() in MODEL_EXT)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("record")
    ap.add_argument("--url",required=True,help="Verified direct archive/model URL")
    ap.add_argument("--out",default="model-forge-work")
    a=ap.parse_args()
    rec=load_record(a.record); license_name=gate(rec)
    root=Path(a.out)/rec["id"]; root.mkdir(parents=True,exist_ok=True)
    archive=root/"source.bin"
    sha=download(a.url,archive)
    extracted=root/"extracted"; extracted.mkdir(exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z: z.extractall(extracted)
    else:
        shutil.copy2(archive,extracted/Path(a.url).name)
    models=inventory(extracted)
    manifest={
      "model_forge_version":"0.1",
      "asset_id":rec["id"],
      "source_url":a.url,
      "source_sha256":sha,
      "license":license_name,
      "model_files":models,
      "model_count":len(models)
    }
    (root/"materialization.manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest))
    if not models: raise SystemExit("no supported 3D model files found")

if __name__=="__main__": main()
