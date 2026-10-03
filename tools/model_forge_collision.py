#!/usr/bin/env python3
"""Emit collision policy/recipe; collision remains gameplay-owned and deliberately simpler than render art."""
import argparse,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser(); p.add_argument("model"); p.add_argument("--out",required=True); p.add_argument("--mode",choices=["box","convex","manual"],default="box"); a=p.parse_args()
 recipe={"version":1,"render_asset":a.model,"mode":a.mode,"principle":"collision represents gameplay, not render detail","game_validation_required":True}
 Path(a.out).write_text(json.dumps(recipe,indent=2),encoding="utf-8"); print(json.dumps(recipe))
if __name__=="__main__": main()
