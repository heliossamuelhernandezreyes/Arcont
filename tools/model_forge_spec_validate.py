#!/usr/bin/env python3
"""Run Khronos glTF Validator as a strict Model Forge gate."""
import argparse,json,shutil,subprocess
from pathlib import Path
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("--out",required=True); a=ap.parse_args()
 exe=shutil.which("gltf_validator")
 if not exe: raise SystemExit("required validator not found: gltf_validator")
 p=subprocess.run([exe,"-o",a.model],capture_output=True,text=True)
 Path(a.out).write_text(p.stdout,encoding="utf-8")
 try: report=json.loads(p.stdout); errors=report.get("issues",{}).get("numErrors",0)
 except Exception: raise SystemExit("validator did not return JSON")
 print(json.dumps({"returncode":p.returncode,"errors":errors,"report":a.out}))
 return 1 if p.returncode or errors else 0
if __name__=="__main__": raise SystemExit(main())
