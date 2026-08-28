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
 set_process(true);set_process_input(true);_refresh()

func _process(delta:float)->void:
 sample_timer+=delta
 if sample_timer>=sample_interval:sample_timer=0.0;_refresh()

func _input(event:InputEvent)->void:
 if event is InputEventKey and event.pressed and not event.echo and event.keycode==KEY_F3:toggle()
 elif event is InputEventScreenTouch and event.pressed:
  var p:=event.position
  if p.x<=150.0 and p.y>=145.0 and p.y<=225.0:toggle()

func toggle()->void:
 shown=not shown
 if panel:panel.visible=shown

func _refresh()->void:
 if panel==null:return
 panel.visible=shown
 if not shown:return
 var fps:=float(Engine.get_frames_per_second());var frame_ms:=1000.0/maxf(fps,1.0)
 var active:=get_tree().get_nodes_in_group("enemies_active").size()
 var scene:=get_tree().current_scene;var tier:=-1;var ai_ms:=0.0;var detail:=1.0
 if scene:
  var budget:=scene.get_node_or_null("PerformanceBudget")
  if budget:
   tier=int(budget.get("tier"));ai_ms=float(budget.get("ai_interval"))*1000.0
   if budget.has_method("get_enemy_detail_scale"):detail=float(budget.get_enemy_detail_scale())
 panel.text="PERF [tap]\nFPS %3d  %.1f ms\nENEMIES %02d  TIER %d\nAI %.0f ms  DETAIL %.0f%%"%[roundi(fps),frame_ms,active,tier,ai_ms,detail*100.0]
