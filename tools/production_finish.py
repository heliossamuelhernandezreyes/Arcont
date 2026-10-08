"""Validate native TPS measurements without converting them into an art/FPS claim."""
from __future__ import annotations
import math


def number(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("finite numeric measurement required")
    return float(value)


def vector(value, length):
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{length}-component vector required")
    return [number(x) for x in value]


def review(profile, record):
    if profile.get("version") != 1 or record.get("version") != 1:
        raise ValueError("unsupported finish profile/record version")
    if record.get("scope") != "godot-native-controlled-motion":
        raise ValueError("controlled native motion scope required; no inferred device result")
    if not isinstance(record.get("engine"), dict) or not record["engine"].get("hash"):
        raise ValueError("exact engine identity required")
    if not isinstance(record.get("source_hashes"), dict) or not record["source_hashes"]:
        raise ValueError("source hashes required")
    for path, digest in record["source_hashes"].items():
        if not path or not isinstance(digest,str) or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("invalid source hash")
    cadence_limit=number(profile["limits"]["cadence_relative_error"])
    drift_limit=number(profile["limits"]["stance_drift_m"])
    grip_limit=number(profile["limits"]["grip_error_m"])
    if any(x <= 0 for x in (cadence_limit,drift_limit,grip_limit)):
        raise ValueError("positive finish limits required")
    minimum=profile["minimum_contact_samples_per_case"]
    if isinstance(minimum,bool) or not isinstance(minimum,int) or minimum<10:
        raise ValueError("at least ten contact samples per case required")
    cases=profile["required_motion_cases"]
    if not isinstance(cases,list) or not cases or len(set(cases))!=len(cases):
        raise ValueError("unique motion cases required")
    checks=[]
    for case in cases:
        matches=[x for x in record.get("cadence",[]) if x.get("case")==case]
        if len(matches)!=1:raise ValueError("one signed cadence observation required for "+case)
        value=matches[0]
        body=vector(value["body_velocity_xz"],2)
        delta=vector(value["foot_displacement_xz"],2)
        elapsed=number(value["sample_seconds"])
        scale=number(value["time_scale"])
        if elapsed<=0 or scale<=0 or math.hypot(*body)<0.1:
            raise ValueError("positive elapsed time, cadence and movement speed required")
        error=math.hypot(*(body[i]+delta[i]/elapsed*scale for i in range(2)))/math.hypot(*body)
        checks.append({"id":case+".signed_cadence","value":error,"limit":cadence_limit,"ok":error<=cadence_limit})
        contacts=[x for x in record.get("contacts",[]) if x.get("case")==case]
        if len(contacts)<minimum or {x.get("foot") for x in contacts}!={"L","R"}:
            raise ValueError("both feet and sufficient contact samples required for "+case)
        maximum=0.0
        for sample in contacts:
            actual=vector(sample["position"],3); anchor=vector(sample["anchor"],3)
            if number(sample["time_s"])<0:raise ValueError("non-negative sample time required")
            maximum=max(maximum,math.dist(actual,anchor))
        checks.append({"id":case+".stance_drift","value":maximum,"limit":drift_limit,"ok":maximum<=drift_limit,"samples":len(contacts)})
    grips=record.get("grips",[])
    if not grips or {x.get("hand") for x in grips}!={"L","R"}:
        raise ValueError("both weapon hand measurements required")
    errors=[number(x["error_m"]) for x in grips]
    if any(x<0 for x in errors):raise ValueError("non-negative grip error required")
    checks.append({"id":"weapon.grips","value":max(errors),"limit":grip_limit,"ok":max(errors)<=grip_limit,"samples":len(errors)})
    notes=record.get("visual_review",{})
    if not notes.get("reviewer") or not isinstance(notes.get("notes"),str) or not notes["notes"].strip():
        raise ValueError("explicit visual reviewer and notes required")
    return {"ok":True,"technical_passed":all(x["ok"] for x in checks),"checks":checks,
        "visual_review":notes,"scope":record["scope"],"engine":record["engine"],
        "limits":["Technical motion acceptance is not AAA art approval.",
            "Controlled motion observations do not establish complete gameplay animation quality.",
            "Android performance, thermal stability and touch comfort require device observations."]}
