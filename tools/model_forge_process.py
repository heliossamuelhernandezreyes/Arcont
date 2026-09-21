#!/usr/bin/env python3
"""ARCONT Model Forge processor adapter.
Orchestrates pinned external processors; refuses silent fallbacks.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path

def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1<<20),b""): h.update(c)
 return h.hexdigest()

def require(name):
 p=shutil.which(name)
 if not p: raise SystemExit(f"required processor not found: {name}")
 return p

def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 if p.returncode: raise SystemExit(f"processor failed ({p.returncode}): {' '.join(cmd)}\n{p.stderr[-4000:]}")
 return p

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("--out",required=True)
 ap.add_argument("--ratio",type=float,default=1.0); ap.add_argument("--keep-names",action="store_true")
 a=ap.parse_args(); src=Path(a.input); dst=Path(a.out); dst.parent.mkdir(parents=True,exist_ok=True)
 if src.suffix.lower() not in {".glb",".gltf",".obj"}: raise SystemExit("processor accepts GLB/glTF/OBJ; DCC conversion required for this source")
 if not 0<a.ratio<=1: raise SystemExit("ratio must be >0 and <=1")
 tool=require("gltfpack"); cmd=[tool,"-i",str(src),"-o",str(dst)]
 if a.ratio<1: cmd += ["-si",str(a.ratio)]
 if a.keep_names: cmd += ["-kn","-km"]
 p=run(cmd)
 evidence={"version":1,"processor":"gltfpack","command":cmd[1:],"input_sha256":digest(src),"output_sha256":digest(dst),
           "input_size_bytes":src.stat().st_size,"output_size_bytes":dst.stat().st_size,"ratio_requested":a.ratio}
 Path(str(dst)+".process.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")
 print(json.dumps(evidence,indent=2))
if __name__=="__main__": main()
