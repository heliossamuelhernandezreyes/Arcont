"""Frame distributions with explicit measurement scope and compatible comparisons."""
from __future__ import annotations
import math
import statistics


def summarize(record):
    scope = record.get("scope")
    if scope not in {"linux-rendered", "android-device"}:
        raise ValueError("measurement scope must be explicit")
    for key in ("device", "engine", "renderer", "resolution", "build", "scenario", "warmup_frames"):
        if key not in record:
            raise ValueError("missing performance provenance: " + key)
    for key in ("device", "engine", "renderer", "build", "scenario"):
        if not isinstance(record[key], str) or not record[key].strip():
            raise ValueError("empty performance provenance: " + key)
    resolution = record["resolution"]
    if not isinstance(resolution, list) or len(resolution) != 2 or any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in resolution):
        raise ValueError("invalid measurement resolution")
    warmup = record["warmup_frames"]
    if isinstance(warmup, bool) or not isinstance(warmup, int) or warmup < 30:
        raise ValueError("at least 30 warmup frames required")
    samples = record["frame_wall_ms"]
    if len(samples) < 30 or any(isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) or v <= 0 for v in samples):
        raise ValueError("at least 30 positive finite frame samples required")
    ordered = sorted(samples)
    def percentile(q):
        index = (len(ordered)-1)*q
        lower = math.floor(index)
        upper = math.ceil(index)
        return ordered[lower] + (ordered[upper]-ordered[lower])*(index-lower)
    return {"scope": scope, "sample_count": len(samples), "mean_ms": statistics.mean(samples),
            "p50_ms": percentile(.5), "p95_ms": percentile(.95), "p99_ms": percentile(.99),
            "max_ms": max(samples), "measurement_scope": scope,
            "limits": ["wall frame intervals; not isolated GPU time or touch latency",
                       "short runner observations do not establish sustained handset performance"]}


def compare(before, after):
    for key in ("scope","device","engine","renderer","resolution","build","scenario","warmup_frames"):
        if before.get(key) != after.get(key):
            raise ValueError("incompatible performance records: " + key)
    a,b=summarize(before),summarize(after)
    return {"before":a,"after":b,"p95_delta_percent":(b["p95_ms"]/a["p95_ms"]-1)*100,
            "classification":"descriptive comparison; repeat runs before regression decisions"}
