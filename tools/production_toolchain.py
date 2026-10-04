#!/usr/bin/env python3
"""Single entry point for Arcont production preparation and evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

try:
    from tools.production_assets import digest, local, stage, validate_plan
    from tools.production_recipes import animation_profile, sector
    from tools.production_evidence import summarize, compare
    from tools.production_finish import review
    from tools.production_bundle import materialize
except ModuleNotFoundError:
    from production_assets import digest, local, stage, validate_plan
    from production_recipes import animation_profile, sector
    from production_evidence import summarize, compare
    from production_finish import review
    from production_bundle import materialize

ROOT = Path(__file__).resolve().parents[1]


def doctor(root):
    manifest = json.loads((root / "production-toolchain.json").read_text())
    failures=[]
    for component in manifest["components"]:
        for path, sha in component["files"].items():
            file=local(root,path)
            if not file.is_file() or digest(file)!=sha:
                failures.append(path)
    return {"ok":not failures,"release":manifest["release"],"failures":failures,
            "components":[x["id"] for x in manifest["components"]],
            "limits":manifest["limits"]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="operation",required=True)
    sub.add_parser("doctor")
    assets=sub.add_parser("assets")
    assets.add_argument("plan",type=Path); assets.add_argument("--project",type=Path,required=True)
    assets.add_argument("--stage",help="project-relative immutable candidate parent; omit for validation")
    for name in ("animation", "sector", "observe"):
        p=sub.add_parser(name); p.add_argument("record",type=Path)
        if name=="observe": p.add_argument("--before",type=Path)
    finish=sub.add_parser("finish")
    finish.add_argument("record",type=Path)
    finish.add_argument("--profile",type=Path,default=ROOT/"templates/production/tps-mobile-finish.profile.json")
    bundle=sub.add_parser("bundle")
    bundle.add_argument("record",type=Path)
    bundle.add_argument("--project",type=Path,required=True)
    bundle.add_argument("--replace",action="store_true")
    args=parser.parse_args()
    try:
        if args.operation=="doctor": result=doctor(ROOT)
        elif args.operation=="assets":
            plan=json.loads(args.plan.read_text())
            result=stage(args.project,plan,args.stage) if args.stage else validate_plan(args.project,plan)
        else:
            record=json.loads(args.record.read_text())
            if args.operation=="bundle": result=materialize(args.project,record['source'],record['destination'],record['files'],args.replace)
            elif args.operation=="finish": result=review(json.loads(args.profile.read_text()),record)
            elif args.operation=="sector": result=sector(record)
            elif args.operation=="animation":
                animation_profile(record); result={"ok":True,"clips":len(record["clips"]),"mapped_bones":len(record["bone_map"]),"scope":"profile contract; native adapter acceptance required"}
            else: result={"ok":True,"summary":compare(json.loads(args.before.read_text()),record) if args.before else summarize(record)}
    except (ValueError,KeyError,OSError,TypeError) as exc:
        result={"ok":False,"error":str(exc)}
    print(json.dumps(result,indent=2,allow_nan=False))
    return 0 if result.get("ok") and result.get("technical_passed",True) else 1


if __name__=="__main__": raise SystemExit(main())
