#!/usr/bin/env python3
"""Inspect glTF/GLB without third-party Python dependencies."""
from __future__ import annotations
import argparse,json,struct
from pathlib import Path

def load_gltf(path:Path):
    if path.suffix.lower()==".gltf": return json.loads(path.read_text(encoding="utf-8"))
    raw=path.read_bytes()
    if len(raw)<20 or raw[:4]!=b"glTF": raise ValueError("not a GLB file")
    version,total=struct.unpack_from("<II",raw,4)
    if version!=2 or total!=len(raw): raise ValueError("invalid GLB v2 header")
    off=12; doc=None
    while off+8<=len(raw):
        n,typ=struct.unpack_from("<II",raw,off); off+=8
        chunk=raw[off:off+n]; off+=n
        if typ==0x4E4F534A: doc=json.loads(chunk.rstrip(b" \t\r\n\x00").decode("utf-8"))
    if doc is None: raise ValueError("GLB has no JSON chunk")
    return doc

def component_count(t):
    return {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT2":4,"MAT3":9,"MAT4":16}.get(t)

def inspect(path:Path):
    d=load_gltf(path); acc=d.get("accessors",[])
    triangles=0; vertices=0; primitives=0
    for mesh in d.get("meshes",[]):
      for p in mesh.get("primitives",[]):
        primitives+=1
        mode=p.get("mode",4)
        if "POSITION" in p.get("attributes",{}):
          i=p["attributes"]["POSITION"]
          if isinstance(i,int) and i<len(acc): vertices+=int(acc[i].get("count",0))
        if mode==4:
          if isinstance(p.get("indices"),int) and p["indices"]<len(acc): triangles+=int(acc[p["indices"]].get("count",0))//3
          elif "POSITION" in p.get("attributes",{}):
            i=p["attributes"]["POSITION"]; triangles+=int(acc[i].get("count",0))//3
    images=d.get("images",[])
    return {
      "path":str(path),"format":path.suffix.lower().lstrip("."),
      "meshes":len(d.get("meshes",[])),"primitives":primitives,
      "vertices_referenced":vertices,"triangles":triangles,
      "materials":len(d.get("materials",[])),"textures":len(d.get("textures",[])),"images":len(images),
      "nodes":len(d.get("nodes",[])),"skins":len(d.get("skins",[])),
      "animations":len(d.get("animations",[])),"cameras":len(d.get("cameras",[])),
      "extensions_used":d.get("extensionsUsed",[]),"extensions_required":d.get("extensionsRequired",[]),
      "generator":d.get("asset",{}).get("generator"),"gltf_version":d.get("asset",{}).get("version")
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("paths",nargs="+"); ap.add_argument("--out")
    a=ap.parse_args(); reports=[]
    for s in a.paths:
      p=Path(s)
      if p.suffix.lower() not in {".glb",".gltf"}: continue
      reports.append(inspect(p))
    text=json.dumps({"model_forge_inspection_version":1,"assets":reports},indent=2)
    if a.out: Path(a.out).write_text(text,encoding="utf-8")
    print(text)
    return 0 if reports else 2
if __name__=="__main__": raise SystemExit(main())
