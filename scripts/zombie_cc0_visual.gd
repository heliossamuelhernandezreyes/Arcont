extends Node3D

# Prefer the realistic human-proportioned infected only when its imported scene
# can actually satisfy the runtime semantic animation contract. Legacy
# Quaternius shells remain safety fallbacks until the realistic candidate has a
# compatible native/retargeted animation rig.
const HUMANOID_PATH := "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/InfectedCityMan.fbx"
const MALE_PATH := "res://assets/provisional/cc0_runtime/zombies/Zombie_Male.fbx"
const FEMALE_PATH := "res://assets/provisional/cc0_runtime/zombies/Zombie_Female.fbx"
const TARGET_HEIGHT_M := 1.82
const REQUIRED_IDLE_TOKENS := ["idle", "zombie"]
const REQUIRED_MOVE_TOKENS := ["walk", "run"]
const REQUIRED_ATTACK_TOKENS := ["punch", "attack"]

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
var animation_contract := "unresolved"
var animation_contract_failure := ""

func _ready() -> void:
 host = get_parent() as CharacterBody3D
 call_deferred("_build_shell")

func _build_shell() -> void:
 if host == null or not is_instance_valid(host): return
 var candidates := [HUMANOID_PATH, MALE_PATH, FEMALE_PATH]
 var rejected: Array[String] = []
 for path_variant in candidates:
  var path := String(path_variant)
  var packed := load(path) as PackedScene
  if packed == null:
   rejected.append("%s:missing" % path)
   continue
  var candidate := packed.instantiate() as Node3D
  if candidate == null:
   rejected.append("%s:instantiate_failed" % path)
   continue
  var candidate_player := _find_animation_player(candidate)
  var missing := _missing_required_semantics(candidate_player)
  if not missing.is_empty():
   rejected.append("%s:missing_%s" % [path, ",".join(missing)])
   candidate.free()
   continue
  model_root = candidate
  animation_player = candidate_player
  source_asset = path
  animation_contract = "semantic_native"
  break
 if model_root == null:
  animation_contract = "proxy_fallback"
  animation_contract_failure = ";".join(rejected)
  set_meta("animation_contract", animation_contract)
  set_meta("animation_contract_failure", animation_contract_failure)
  push_warning("ZOMBIE_ANIMATION_CONTRACT: no imported shell satisfies idle/move/attack semantics; using segmented proxy | %s" % animation_contract_failure)
  _set_proxy_visible(true)
  return
 model_root.name = "HumanoidInfectedModel"
 add_child(model_root)
 model_root.rotation_degrees = Vector3(0.0, 180.0, 0.0)
 AssetScaleNormalizer.normalize_longest_extent(model_root, TARGET_HEIGHT_M)
 model_root.set_meta("source_asset", source_asset)
 model_root.set_meta("art_status", "CC0-HUMANOID-INFECTED")
 model_root.set_meta("metric_target_extent_m", TARGET_HEIGHT_M)
 model_root.set_meta("animation_contract", animation_contract)
 set_meta("animation_contract", animation_contract)
 set_meta("animation_source_asset", source_asset)
 intact_origin = model_root.position
 intact_rotation = model_root.rotation_degrees
 shell_active = true
 fallback_locked = false
 death_locked = false
 action_lock = 0.0
 last_attack_timer = float(host.get("attack_timer"))
 _set_proxy_visible(false)
 if host.has_signal("limb_lost"): host.limb_lost.connect(_on_limb_lost)
 if host.has_signal("crawl_started"): host.crawl_started.connect(_on_crawl_started)
 if host.has_signal("staggered"): host.staggered.connect(_on_staggered)
 if host.has_signal("knocked_down"): host.knocked_down.connect(_on_knocked_down)
 if host.has_signal("died"): host.died.connect(_on_died)
 _play_best(REQUIRED_IDLE_TOKENS, false, true)

func _process(delta: float) -> void:
 if not shell_active or model_root == null or host == null: return
 _set_proxy_visible(false)
 if death_locked: return
 action_lock = maxf(action_lock - delta, 0.0)
 var attack_now := float(host.get("attack_timer"))
 if attack_now > last_attack_timer + 0.18:
  action_lock = maxf(action_lock, 0.46)
  _play_best(REQUIRED_ATTACK_TOKENS, false, true)
 last_attack_timer = attack_now
 var knocked := float(host.get("knockdown_timer")) > 0.0
 if knocked:
  model_root.position = intact_origin + Vector3(0, -0.45, 0)
  model_root.rotation_degrees = Vector3(intact_rotation.x, intact_rotation.y, intact_rotation.z + 72.0)
 else:
  model_root.position = intact_origin
  model_root.rotation_degrees = intact_rotation
 if action_lock > 0.0: return
 var speed := Vector2(host.velocity.x, host.velocity.z).length()
 if speed > 0.18 and not knocked: _play_best(REQUIRED_MOVE_TOKENS, true)
 else: _play_best(REQUIRED_IDLE_TOKENS, false)

func _on_staggered(_enemy: Node, duration: float) -> void:
 if not shell_active or death_locked: return
 action_lock = maxf(action_lock, maxf(duration, 0.30))
 _play_best(["recievehit", "receivehit", "hit"], false, true)

func _on_knocked_down(_enemy: Node, duration: float) -> void:
 if not shell_active or death_locked: return
 action_lock = maxf(action_lock, minf(maxf(duration, 0.45), 0.85))
 _play_best(["sitdown", "defeat"], false, true)

func _on_died(_enemy: Node) -> void:
 if not shell_active: return
 death_locked = true
 action_lock = 999.0
 _play_best(["defeat", "death", "dying"], false, true)

func _on_limb_lost(_enemy: Node, _limb: String) -> void: _activate_segmented_fallback()
func _on_crawl_started(_enemy: Node) -> void: _activate_segmented_fallback()

func _activate_segmented_fallback() -> void:
 if fallback_locked: return
 fallback_locked = true
 shell_active = false
 death_locked = false
 animation_contract = "segmented_runtime_fallback"
 set_meta("animation_contract", animation_contract)
 if model_root: model_root.visible = false
 _set_proxy_visible(true)
 _sync_missing_proxy_parts()

func _set_proxy_visible(value: bool) -> void:
 if host == null: return
 for node_name in ["Body", "Head", "ArmL", "ArmR"]:
  var part := host.get_node_or_null(node_name) as Node3D
  if part: part.visible = value
 if value: _sync_missing_proxy_parts()

func _sync_missing_proxy_parts() -> void:
 if host == null: return
 var head := host.get_node_or_null("Head") as Node3D
 var arm_l := host.get_node_or_null("ArmL") as Node3D
 var arm_r := host.get_node_or_null("ArmR") as Node3D
 var leg_l := host.get_node_or_null("Body/LegL") as Node3D
 var leg_r := host.get_node_or_null("Body/LegR") as Node3D
 if head: head.visible = not bool(host.get("head_missing"))
 if arm_l: arm_l.visible = not bool(host.get("arm_l_missing"))
 if arm_r: arm_r.visible = not bool(host.get("arm_r_missing"))
 if leg_l: leg_l.visible = not bool(host.get("leg_l_disabled"))
 if leg_r: leg_r.visible = not bool(host.get("leg_r_disabled"))

func _play_best(tokens: Array, moving: bool, force := false) -> void:
 if animation_player == null: return
 if action_lock > 0.0 and not force: return
 var selected := _find_best_animation(animation_player, tokens)
 # Never silently substitute an unrelated animation. That old behavior allowed
 # RESET/unknown clips to satisfy structural tests while the mesh stayed in a
 # bind pose or played the wrong semantic action.
 if selected.is_empty():
  set_meta("missing_animation_semantic", ",".join(tokens))
  return
 if selected == current_anim and not force: return
 current_anim = selected
 animation_player.play(selected, 0.10)
 var anim := animation_player.get_animation(selected)
 if anim: anim.loop_mode = Animation.LOOP_LINEAR if moving or "idle" in selected.to_lower() else Animation.LOOP_NONE

func _missing_required_semantics(player: AnimationPlayer) -> Array[String]:
 var missing: Array[String] = []
 if player == null:
  missing.append("animation_player")
  return missing
 if _find_best_animation(player, REQUIRED_IDLE_TOKENS).is_empty(): missing.append("idle")
 if _find_best_animation(player, REQUIRED_MOVE_TOKENS).is_empty(): missing.append("move")
 if _find_best_animation(player, REQUIRED_ATTACK_TOKENS).is_empty(): missing.append("attack")
 return missing

func _find_best_animation(player: AnimationPlayer, tokens: Array) -> String:
 if player == null: return ""
 var names := player.get_animation_list()
 for token_variant in tokens:
  var token := String(token_variant).to_lower()
  for name_variant in names:
   var candidate := String(name_variant)
   if candidate == "RESET": continue
   if token in candidate.to_lower(): return candidate
 return ""

func get_shell_extent() -> float: return AssetScaleNormalizer.longest_extent(model_root) if model_root else 0.0
func get_source_asset() -> String: return source_asset
func get_animation_names() -> PackedStringArray: return animation_player.get_animation_list() if animation_player else PackedStringArray()
func get_current_animation() -> String: return current_anim
func get_animation_contract() -> String: return animation_contract
func is_shell_active() -> bool: return shell_active

func _find_animation_player(node: Node) -> AnimationPlayer:
 if node is AnimationPlayer: return node as AnimationPlayer
 for child in node.get_children():
  var found := _find_animation_player(child)
  if found != null: return found
 return null
