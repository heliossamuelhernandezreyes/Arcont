#!/usr/bin/env python3
"""Create a deterministic game-staging bundle manifest without writing another repository."""
import argparse,hashlib,json,shutil
from pathlib import Path
def sha(p):
 h=hashlib.sha256(p.read_bytes()).hexdigest(); return h
def main():
 p=argparse.ArgumentParser(); p.add_argument("model"); p.add_argument("--semantic-id",required=True); p.add_argument("--out",required=True); p.add_argument("--collision-recipe"); a=p.parse_args()
 src=Path(a.model); root=Path(a.out)/a.semantic_id.replace(".","/"); root.mkdir(parents=True,exist_ok=True); dst=root/"asset.glb"; shutil.copy2(src,dst)
 m={"version":1,"semantic_id":a.semantic_id,"file":"asset.glb","sha256":sha(dst),"source":str(src),"collision_recipe":a.collision_recipe,"runtime_evidence_required":True}
 (root/"asset.manifest.json").write_text(json.dumps(m,indent=2),encoding="utf-8"); print(json.dumps(m))
if __name__=="__main__": main()
