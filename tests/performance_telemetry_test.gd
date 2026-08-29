extends SceneTree

const OVERLAY_SCRIPT := preload("res://scripts/performance_overlay.gd")
const REQUIRED_KEYS := [
 "fps","process_ms","physics_ms","object_count","resource_count","node_count","orphan_nodes",
 "render_objects","render_primitives","draw_calls","video_mem_bytes","texture_mem_bytes","buffer_mem_bytes"
]

func _init()->void:
 call_deferred("_run")

func _run()->void:
 var failures:Array[String]=[]
 var overlay:=OVERLAY_SCRIPT.new()
 overlay.visible_on_start=false
 root.add_child(overlay)
 await process_frame
 await process_frame
 if not overlay.has_method("get_snapshot"):
  failures.append("PerformanceOverlay no expone get_snapshot")
 else:
  var snapshot:Dictionary=overlay.get_snapshot()
  for key in REQUIRED_KEYS:
   if not snapshot.has(key):
    failures.append("Falta monitor de rendimiento: "+String(key))
    continue
   var value=snapshot[key]
   if not (value is int or value is float):
    failures.append("Monitor no numérico: "+String(key))
   elif float(value)<0.0:
    failures.append("Monitor negativo inválido: "+String(key)+"="+str(value))
  if failures.is_empty():
   print("PERF_BASELINE_HEADLESS|fps=%.1f|process_ms=%.3f|physics_ms=%.3f|draw_calls=%d|render_objects=%d|render_primitives=%d|nodes=%d|objects=%d|resources=%d|video_mem=%d|texture_mem=%d|buffer_mem=%d" % [float(snapshot.fps),float(snapshot.process_ms),float(snapshot.physics_ms),int(snapshot.draw_calls),int(snapshot.render_objects),int(snapshot.render_primitives),int(snapshot.node_count),int(snapshot.object_count),int(snapshot.resource_count),int(snapshot.video_mem_bytes),int(snapshot.texture_mem_bytes),int(snapshot.buffer_mem_bytes)])
 overlay.queue_free()
 await process_frame
 if failures.is_empty():
  print("ARCONT PERF: observational telemetry contract OK; no hardware thresholds enforced")
  quit(0)
  return
 for failure in failures:push_error("ARCONT PERF: "+failure)
 quit(1)
