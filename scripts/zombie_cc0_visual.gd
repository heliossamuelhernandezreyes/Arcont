extends Node3D

# Prefer the realistic human-proportioned infected already audited in runtime.
# Legacy Quaternius shells remain fallbacks until the realistic candidate has a
# complete native animation/dismemberment rig.
const HUMANOID_PATH := "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/InfectedCityMan.fbx"
const MALE_PATH := "res://assets/provisional/cc0_runtime/zombies/Zombie_Male.fbx"
const FEMALE_PATH := "res://assets/provisional/cc0_runtime/zombies/Zombie_Female.fbx"
const TARGET_HEIGHT_M := 1.82

var host: CharacterBody3D
var model_root: Node3D
var animation_player: AnimationPlayer
var shell_active := false
var fallback_locked := false
var source_asset := ""
var current_anim := ""
var intact_origin := Vector3.ZERO
var intact_rotation := Vector3.ZERO
var action_lock := 0.0
var last_attack_timer := 0.0
var death_locked := false

func _ready() -> void:
 host = get_parent() as CharacterBody3D
 call_deferred("_build_shell")

func _build_shell() -> void:
 if host == null or not is_instance_valid(host): return
 var candidates := [HUMANOID_PATH,MALE_PATH,FEMALE_PATH]
 # Humanoid is deliberately first; legacy variants are safety fallbacks only.
 for path_variant in candidates:
  var path:=String(path_variant)
  var packed:=load(path) as PackedScene
  if packed==null: continue
  model_root=packed.instantiate() as Node3D
  if model_root==null: continue
  source_asset=path
  break
 if model_root==null:
  _set_proxy_visible(true)
  return
 model_root.name="HumanoidInfectedModel"
 add_child(model_root)
 model_root.rotation_degrees=Vector3(0.0,180.0,0.0)
 AssetScaleNormalizer.normalize_longest_extent(model_root,TARGET_HEIGHT_M)
 model_root.set_meta("source_asset",source_asset)
 model_root.set_meta("art_status","CC0-HUMANOID-INFECTED")
 model_root.set_meta("metric_target_extent_m",TARGET_HEIGHT_M)
 animation_player=_find_animation_player(model_root)
 intact_origin=model_root.position
 intact_rotation=model_root.rotation_degrees
 shell_active=true
 fallback_locked=false
 death_locked=false
 action_lock=0.0
 last_attack_timer=float(host.get("attack_timer"))
 _set_proxy_visible(false)
 if host.has_signal("limb_lost"): host.limb_lost.connect(_on_limb_lost)
 if host.has_signal("crawl_started"): host.crawl_started.connect(_on_crawl_started)
 if host.has_signal("staggered"): host.staggered.connect(_on_staggered)
 if host.has_signal("knocked_down"): host.knocked_down.connect(_on_knocked_down)
 if host.has_signal("died"): host.died.connect(_on_died)
 _play_best(["idle","zombie","walk"],false,true)

func _process(delta: float) -> void:
 if not shell_active or model_root==null or host==null:return
 _set_proxy_visible(false)
 if death_locked:return
 action_lock=maxf(action_lock-delta,0.0)
 var attack_now:=float(host.get("attack_timer"))
 if attack_now>last_attack_timer+0.18:
  action_lock=maxf(action_lock,0.46)
  _play_best(["punch","attack"],false,true)
 last_attack_timer=attack_now
 var knocked:=float(host.get("knockdown_timer"))>0.0
 if knocked:
  model_root.position=intact_origin+Vector3(0,-0.45,0)
  model_root.rotation_degrees=Vector3(intact_rotation.x,intact_rotation.y,intact_rotation.z+72.0)
 else:
  model_root.position=intact_origin
  model_root.rotation_degrees=intact_rotation
 if action_lock>0.0:return
 var speed:=Vector2(host.velocity.x,host.velocity.z).length()
 if speed>0.18 and not knocked:_play_best(["walk","run","zombie"],true)
 else:_play_best(["idle","zombie"],false)

func _on_staggered(_enemy:Node,duration:float)->void:
 if not shell_active or death_locked:return
 action_lock=maxf(action_lock,maxf(duration,0.30));_play_best(["recievehit","receivehit","hit"],false,true)
func _on_knocked_down(_enemy:Node,duration:float)->void:
 if not shell_active or death_locked:return
 action_lock=maxf(action_lock,minf(maxf(duration,0.45),0.85));_play_best(["sitdown","defeat"],false,true)
func _on_died(_enemy:Node)->void:
 if not shell_active:return
 death_locked=true;action_lock=999.0;_play_best(["defeat"],false,true)
func _on_limb_lost(_enemy:Node,_limb:String)->void:_activate_segmented_fallback()
func _on_crawl_started(_enemy:Node)->void:_activate_segmented_fallback()

func _activate_segmented_fallback()->void:
 if fallback_locked:return
 fallback_locked=true;shell_active=false;death_locked=false
 if model_root:model_root.visible=false
 _set_proxy_visible(true);_sync_missing_proxy_parts()

func _set_proxy_visible(value:bool)->void:
 if host==null:return
 for node_name in ["Body","Head","ArmL","ArmR"]:
  var part:=host.get_node_or_null(node_name) as Node3D
  if part:part.visible=value
 if value:_sync_missing_proxy_parts()

func _sync_missing_proxy_parts()->void:
 if host==null:return
 var head:=host.get_node_or_null("Head") as Node3D
 var arm_l:=host.get_node_or_null("ArmL") as Node3D
 var arm_r:=host.get_node_or_null("ArmR") as Node3D
 var leg_l:=host.get_node_or_null("Body/LegL") as Node3D
 var leg_r:=host.get_node_or_null("Body/LegR") as Node3D
 if head:head.visible=not bool(host.get("head_missing"))
 if arm_l:arm_l.visible=not bool(host.get("arm_l_missing"))
 if arm_r:arm_r.visible=not bool(host.get("arm_r_missing"))
 if leg_l:leg_l.visible=not bool(host.get("leg_l_disabled"))
 if leg_r:leg_r.visible=not bool(host.get("leg_r_disabled"))

func _play_best(tokens:Array,moving:bool,force:=false)->void:
 if animation_player==null:return
 if action_lock>0.0 and not force:return
 var names:=animation_player.get_animation_list()
 if names.is_empty():return
 var selected:=""
 for token_variant in tokens:
  var token:=String(token_variant).to_lower()
  for name_variant in names:
   var candidate:=String(name_variant)
   if token in candidate.to_lower():selected=candidate;break
  if not selected.is_empty():break
 if selected.is_empty():
  for name_variant in names:
   var candidate:=String(name_variant)
   if candidate!="RESET":selected=candidate;break
 if selected.is_empty() or (selected==current_anim and not force):return
 current_anim=selected
 animation_player.play(selected,0.10)
 var anim:=animation_player.get_animation(selected)
 if anim:anim.loop_mode=Animation.LOOP_LINEAR if moving or "idle" in selected.to_lower() else Animation.LOOP_NONE

func get_shell_extent()->float:return AssetScaleNormalizer.longest_extent(model_root) if model_root else 0.0
func get_source_asset()->String:return source_asset
func get_animation_names()->PackedStringArray:return animation_player.get_animation_list() if animation_player else PackedStringArray()
func get_current_animation()->String:return current_anim
func is_shell_active()->bool:return shell_active
func _find_animation_player(node:Node)->AnimationPlayer:
 if node is AnimationPlayer:return node as AnimationPlayer
 for child in node.get_children():
  var found:=_find_animation_player(child)
  if found!=null:return found
 return null
