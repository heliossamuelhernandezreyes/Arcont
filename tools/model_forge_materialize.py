#!/usr/bin/env python3
"""ARCONT Model Forge Stage 0: acquire a catalogued asset under canonical Vault policy."""
from __future__ import annotations
import argparse,hashlib,json,shutil,sys,urllib.request,zipfile
from pathlib import Path
try:
    from tools.license_policy import classify
except ModuleNotFoundError:
    from license_policy import classify

UA="ARCONT-Model-Forge/0.2 (+https://github.com/heliossamuelhernandezreyes/Arcont)"
MODEL_EXT={".glb",".gltf",".fbx",".obj",".dae",".blend"}

def load_record(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def gate(record):
    review=record.get("review",{})
    if review.get("license_verified") is not True: raise SystemExit("trust gate: license is not verified")
    lic=record.get("license",{})
    policy=classify(str(lic.get("name","")))
    if not policy: raise SystemExit("trust gate: license is unknown to canonical ARCONT policy")
    if policy.tier!="green" or not policy.portable_commercial_default:
        raise SystemExit(f"trust gate: {policy.canonical_name} is {policy.tier}, explicit project review required")
    if lic.get("commercial_use") is not True or lic.get("modification") is not True:
        raise SystemExit("trust gate: record does not explicitly permit commercial modification")
    return policy

def safe_extract(z,root):
    root=root.resolve()
    for info in z.infolist():
        target=(root/info.filename).resolve()
        if root not in target.parents and target!=root: raise SystemExit("unsafe archive path")
    z.extractall(root)

def download(url,dest):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    h=hashlib.sha256(); size=0
    with urllib.request.urlopen(req,timeout=60) as r, open(dest,"wb") as f:
        while True:
            chunk=r.read(1024*1024)
            if not chunk: break
            size+=len(chunk); h.update(chunk); f.write(chunk)
    return h.hexdigest(),size

def inventory(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.suffix.lower() in MODEL_EXT)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("record"); ap.add_argument("--url"); ap.add_argument("--out",default="model-forge-work"); a=ap.parse_args()
    rec=load_record(a.record); policy=gate(rec)
    url=a.url or rec.get("source",{}).get("download_url")
    if not url: raise SystemExit("no verified direct download URL in record; pass --url after source verification")
    root=Path(a.out)/rec["id"]; root.mkdir(parents=True,exist_ok=True)
    archive=root/"source.bin"; sha,size=download(url,archive)
    extracted=root/"extracted"; extracted.mkdir(exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z: safe_extract(z,extracted)
    else: shutil.copy2(archive,extracted/Path(url.split("?")[0]).name)
    models=inventory(extracted)
    manifest={"model_forge_version":"0.2","asset_id":rec["id"],"provider":rec.get("source",{}).get("provider"),
      "source_url":url,"source_sha256":sha,"source_size_bytes":size,"license":policy.canonical_name,
      "policy_tier":policy.tier,"model_files":models,"model_count":len(models)}
    (root/"materialization.manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest))
    return 0 if models else 2
if __name__=="__main__": raise SystemExit(main())
