#!/usr/bin/env python3
"""Visual Director P2: conservative, camera-space AABB visibility diagnostics.

Read-only and geometry-proxy based, not actual GPU depth buffer, beauty, or a
claim that a player can/cannot see a target. Source must come from a real camera
export to justify statements about the played scene.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

MAX_OBJECTS = 512
NEAR = 0.05

def _vec(data: object, label: str, *, positive: bool = False) -> tuple[float,float,float]:
    if not isinstance(data, list) or len(data) != 3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in data):
        raise ValueError(label + " requires three finite coordinates")
    v = tuple(float(x) for x in data)
    if positive and any(x <= 0 for x in v):
        raise ValueError(label + " dimensions must be positive")
    return v

def _sub(a,b):
    return tuple(x-y for x,y in zip(a,b))

def _dot(a,b):
    return sum(x*y for x,y in zip(a,b))

def _cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def _unit(a):
    norm = math.sqrt(_dot(a,a))
    if norm < 1e-6:
        raise ValueError("camera eye/target and up vector must be non-degenerate")
    return tuple(x/norm for x in a)

def _bbox_intersection(a,b):
    left=max(a[0],b[0]); top=max(a[1],b[1])
    right=min(a[2],b[2]); bottom=min(a[3],b[3])
    return max(0.0,right-left)*max(0.0,bottom-top)

def _bbox_area(a):
    return max(0.0,a[2]-a[0])*max(0.0,a[3]-a[1])

def analyze_shot(data: dict) -> dict:
    if not isinstance(data,dict) or data.get("protocol")!="arcont-camera-shot" or data.get("version")!=1:
        raise ValueError("requires arcont-camera-shot protocol v1")
    cam=data.get("camera")
    if not isinstance(cam,dict):
        raise ValueError("camera object required")
    eye=_vec(cam.get("position"),"camera.position")
    target=_vec(cam.get("target"),"camera.target")
    up=_unit(_vec(cam.get("up",[0,1,0]),"camera.up"))
    forward=_unit(_sub(target,eye))
    right=_unit(_cross(forward,up))
    up=_unit(_cross(right,forward))
    viewport=cam.get("viewport")
    if not isinstance(viewport,list) or len(viewport)!=2 or any(type(v) is not int or v<128 or v>8192 for v in viewport):
        raise ValueError("viewport must have two realistic integer dimensions")
    w,h=viewport
    fov=cam.get("fov_y_degrees")
    if type(fov) not in (float,int) or not math.isfinite(fov) or not 15<=fov<=140:
        raise ValueError("finite vertical camera FOV must be 15..140 degrees")
    tan_y=math.tan(math.radians(fov)*0.5)
    tan_x=tan_y*w/h
    objects=data.get("objects")
    if not isinstance(objects,list) or len(objects)>MAX_OBJECTS:
        raise ValueError("bounded list of up to 512 object AABBs required")
    reticle=data.get("reticle_region",[0.46,0.46,0.54,0.54])
    if not isinstance(reticle,list) or len(reticle)!=4 or any(type(x) not in (int,float) or not math.isfinite(x) for x in reticle):
        raise ValueError("reticle_region requires finite 0..1 screen rectangle")
    if not (0<=reticle[0]<reticle[2]<=1 and 0<=reticle[1]<reticle[3]<=1):
        raise ValueError("reticle_region must be ordered and within viewport")
    rrect=(reticle[0]*w,reticle[1]*h,reticle[2]*w,reticle[3]*h)
    records=[]
    identifiers=set()
    for obj in objects:
        if not isinstance(obj,dict):
            raise ValueError("object entries must be dictionaries")
        oid=obj.get("id")
        if not isinstance(oid,str) or not oid or len(oid)>128 or oid in identifiers:
            raise ValueError("object ID empty, repeated or oversize")
        identifiers.add(oid)
        center=_vec(obj.get("center"),oid+".center")
        size=_vec(obj.get("size"),oid+".size",positive=True)
        role=obj.get("role","structure")
        if role not in {"structure","functional","dressing","player","enemy","objective","cover"}:
            raise ValueError("unsupported object role")
        depths=[]
        sx=[];sy=[];near_cross=False
        for signs in itertools.product((-0.5,0.5),repeat=3):
            corner=tuple(center[i]+size[i]*signs[i] for i in range(3))
            delta=_sub(corner,eye)
            depth=_dot(delta,forward)
            if depth<=NEAR:
                near_cross=True
                continue
            depths.append(depth)
            ndcx=_dot(delta,right)/(depth*tan_x)
            ndcy=_dot(delta,up)/(depth*tan_y)
            sx.append((ndcx+1)*w*0.5)
            sy.append((1-ndcy)*h*0.5)
        if not depths:
            continue
        if near_cross:
            # The box intersects the near plane: conservative full-screen bound.
            rect=(0.0,0.0,float(w),float(h))
        else:
            rect=(max(0,min(sx)),max(0,min(sy)),min(float(w),max(sx)),min(float(h),max(sy)))
        area=_bbox_area(rect)
        if area<=0:
            continue
        records.append({"id":oid,"role":role,"rect_px":[round(v,3) for v in rect],
                        "_rect":rect,"_nearest_depth":min(depths),
                        "_furthest_depth":max(depths),
                        "screen_fraction":round(area/(w*h),6),
                        "reticle_overlap_fraction":round(_bbox_intersection(rect,rrect)/_bbox_area(rrect),6),
                        "near_plane_uncertain":near_cross})
    visible_by_id={p["id"]:p for p in records}
    alerts=[]
    targets=[p for p in records if p["role"] in {"enemy","objective"}]
    for shape in records:
        if shape["role"] in {"enemy","objective","player"}:
            continue
        frac=shape["screen_fraction"]
        if frac>=0.12:
            alerts.append({"kind":"large_screen_obstruction","object_id":shape["id"],"screen_fraction":frac,
                           "basis":"projected world-space AABB; not pixel visibility"})
        if shape["reticle_overlap_fraction"]>=0.35 and shape["_nearest_depth"]>NEAR:
            alerts.append({"kind":"reticle_region_intersection","object_id":shape["id"],
                           "region_fraction":shape["reticle_overlap_fraction"],
                           "basis":"projected AABB, not geometry raycast"})
        for actor in targets:
            if actor["id"]==shape["id"] or shape["_nearest_depth"]>=actor["_furthest_depth"]:
                continue
            overlap=_bbox_intersection(shape["_rect"],actor["_rect"])
            frac_target=overlap/max(1,_bbox_area(actor["_rect"]))
            if frac_target>=0.20:
                classification="likely_depth_order" if shape["_furthest_depth"]<actor["_nearest_depth"] else "ambiguous_depth_order"
                alerts.append({"kind":"possible_target_occlusion","object_id":shape["id"],"target_id":actor["id"],
                               "target_rect_overlap_fraction":round(frac_target,6),
                               "depth_classification":classification,
                               "basis":"AABB screen overlap and interval depth, NOT actual visible pixels"})
    alerts.sort(key=lambda a:(a["object_id"],a["kind"],a.get("target_id","")))
    clean=[{k:v for k,v in row.items() if not k.startswith("_")} for row in records]
    digest=hashlib.sha256(json.dumps(data,sort_keys=True,allow_nan=False,separators=(",",":")).encode()).hexdigest()
    return {"ok":True,"protocol":"arcont-visual-camera-diagnostics","version":1,
            "shot_sha256":digest,"capture_source":data.get("capture_source","unspecified"),
            "engine_executed":False,"writes_performed":False,
            "camera":{"viewport":viewport,"fov_y_degrees":fov},
            "projected_objects":clean,"alerts":alerts,
            "summary":{"input_objects":len(objects),"visible_aabb_projections":len(records),
                       "potential_issues":len(alerts)},
            "limitations":["Projective proxy only; no triangle depth/occlusion test or pixel segmentation",
                           "No automatic beauty score, AAA claim or performance measurement",
                           "Caller must independently verify shot's native Godot provenance and camera transform"]}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("shot",type=Path)
    a=p.parse_args()
    try:
        if a.shot.is_symlink() or a.shot.stat().st_size>2*1024*1024:
            raise ValueError("unsafe or oversized shot file")
        data=json.loads(a.shot.read_text(encoding="utf-8"))
        result=analyze_shot(data)
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as e:
        print(json.dumps({"ok":False,"error":str(e),"writes_performed":False}))
        return 1
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
