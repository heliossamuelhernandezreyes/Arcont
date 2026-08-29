extends CanvasLayer
class_name PerformanceOverlay

@export var visible_on_start := true
@export var sample_interval := 0.25
var panel:Label
var sample_timer:=0.0
var shown:=true

func _ready()->void:
 layer=50
 shown=visible_on_start
 panel=Label.new();panel.name="PerformanceReadout";panel.position=Vector2(12,170);panel.add_theme_font_size_override("font_size",11);panel.mouse_filter=Control.MOUSE_FILTER_IGNORE;add_child(panel)
 set_meta("telemetry_contract","GODOT-PERFORMANCE-MONITORS-V1")
 set_process(true);set_process_input(true);_refresh()

func _process(delta:float)->void:
 sample_timer+=delta
 if sample_timer>=sample_interval:sample_timer=0.0;_refresh()

func _input(event:InputEvent)->void:
 if event is InputEventKey and event.pressed and not event.echo and event.keycode==KEY_F3:toggle()
 elif event is InputEventScreenTouch and event.pressed:
  var p:Vector2=(event as InputEventScreenTouch).position
  if p.x<=190.0 and p.y>=145.0 and p.y<=315.0:toggle()

func toggle()->void:
 shown=not shown
 if panel:panel.visible=shown

func get_snapshot()->Dictionary:
 return {
  "fps":float(Performance.get_monitor(Performance.TIME_FPS)),
  "process_ms":float(Performance.get_monitor(Performance.TIME_PROCESS))*1000.0,
  "physics_ms":float(Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS))*1000.0,
  "object_count":int(Performance.get_monitor(Performance.OBJECT_COUNT)),
  "resource_count":int(Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT)),
  "node_count":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)),
  "orphan_nodes":int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)),
  "render_objects":int(Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)),
  "render_primitives":int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)),
  "draw_calls":int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)),
  "video_mem_bytes":int(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED)),
  "texture_mem_bytes":int(Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)),
  "buffer_mem_bytes":int(Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED))
 }

func _mib(bytes:int)->float:return float(bytes)/(1024.0*1024.0)

func _refresh()->void:
 if panel==null:return
 panel.visible=shown
 if not shown:return
 var m:=get_snapshot()
 var active:=get_tree().get_nodes_in_group("enemies_active").size()
 var scene:=get_tree().current_scene;var tier:=-1;var ai_ms:=0.0;var detail:=1.0
 if scene:
  var budget:=scene.get_node_or_null("PerformanceBudget")
  if budget:
   tier=int(budget.get("tier"));ai_ms=float(budget.get("ai_interval"))*1000.0
   if budget.has_method("get_enemy_detail_scale"):detail=float(budget.get_enemy_detail_scale())
 panel.text=("PERF [tap]\nFPS %3d  CPU %.2f ms  PHY %.2f ms\nDRAW %d  VISOBJ %d  PRIM %d\nNODES %d  OBJ %d  RES %d\nVRAM %.1f MiB  TEX %.1f  BUF %.1f\nENEMIES %02d  TIER %d  AI %.0f ms  DETAIL %.0f%%" % [roundi(float(m.fps)),float(m.process_ms),float(m.physics_ms),int(m.draw_calls),int(m.render_objects),int(m.render_primitives),int(m.node_count),int(m.object_count),int(m.resource_count),_mib(int(m.video_mem_bytes)),_mib(int(m.texture_mem_bytes)),_mib(int(m.buffer_mem_bytes)),active,tier,ai_ms,detail*100.0])
