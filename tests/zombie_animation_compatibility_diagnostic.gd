extends SceneTree

const MODEL := "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/InfectedCityMan.fbx"
const CLIPS := {
	"idle": "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/Zombie Idle.fbx",
	"idle_alt": "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/Zombie Idle2.fbx",
	"walk": "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/Zombie Walk.fbx",
	"walking": "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/Walking.fbx",
	"run": "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/Zombie Running.fbx",
	"attack": "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/Zombie Attack.fbx",
	"attack_alt": "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/Zombie Attack2.fbx",
	"hit": "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/Zombie Reaction Hit.fbx",
	"death": "res://assets/provisional/cc0_runtime/zombies/realistic_city_candidate/Zombie Dying.fbx",
}

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var failures: Array[String] = []
	var model_scene := load(MODEL) as PackedScene
	if model_scene == null:
		push_error("ZOMBIE_ANIM_DIAGNOSTIC: primary model missing")
		quit(1)
		return
	var model_root := model_scene.instantiate()
	var model_skeleton := _find_skeleton(model_root)
	if model_skeleton == null:
		failures.append("primary infected has no Skeleton3D")
	var model_bones := _bone_names(model_skeleton) if model_skeleton != null else PackedStringArray()
	print("ZOMBIE_MODEL_RIG|bones=%d|names=%s" % [model_bones.size(),model_bones])
	model_root.free()

	for semantic in CLIPS:
		var path: String = CLIPS[semantic]
		var packed := load(path) as PackedScene
		if packed == null:
			failures.append("missing clip %s: %s" % [semantic,path])
			continue
		var root_node := packed.instantiate()
		var skeleton := _find_skeleton(root_node)
		var player := _find_animation_player(root_node)
		var bones := _bone_names(skeleton) if skeleton != null else PackedStringArray()
		var common := _common_bones(model_bones,bones)
		var names := player.get_animation_list() if player != null else PackedStringArray()
		var transform_tracks := 0
		var bone_like_tracks := 0
		for anim_name in names:
			var animation := player.get_animation(anim_name)
			if animation == null: continue
			for i in range(animation.get_track_count()):
				if animation.track_get_type(i) in [Animation.TYPE_POSITION_3D,Animation.TYPE_ROTATION_3D,Animation.TYPE_SCALE_3D]:
					transform_tracks += 1
					if animation.track_get_path(i).get_subname_count() > 0: bone_like_tracks += 1
		print("ZOMBIE_CLIP_AUDIT|semantic=%s|path=%s|bones=%d|common=%d|animations=%s|transform_tracks=%d|bone_tracks=%d" % [semantic,path,bones.size(),common,names,transform_tracks,bone_like_tracks])
		if skeleton == null: failures.append("%s clip has no Skeleton3D" % semantic)
		if player == null or names.is_empty(): failures.append("%s clip has no animation" % semantic)
		if model_bones.size() > 0 and common < mini(12,model_bones.size()): failures.append("%s clip shares too few bones with primary model: %d" % [semantic,common])
		if transform_tracks == 0: failures.append("%s clip has no transform tracks" % semantic)
		root_node.free()

	if failures.is_empty():
		print("ARCONT ZOMBIE ANIMATION DIAGNOSTIC: semantic clip library is loadable and shares a usable humanoid rig vocabulary")
		quit(0)
		return
	for failure in failures:
		push_error("ZOMBIE_ANIM_DIAGNOSTIC: " + failure)
	quit(1)

func _find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D: return node as Skeleton3D
	for child in node.get_children():
		var found := _find_skeleton(child)
		if found != null: return found
	return null

func _find_animation_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer: return node as AnimationPlayer
	for child in node.get_children():
		var found := _find_animation_player(child)
		if found != null: return found
	return null

func _bone_names(skeleton: Skeleton3D) -> PackedStringArray:
	var out := PackedStringArray()
	if skeleton == null: return out
	for i in range(skeleton.get_bone_count()): out.append(skeleton.get_bone_name(i))
	return out

func _common_bones(a: PackedStringArray,b: PackedStringArray) -> int:
	var set_b := {}
	for name in b: set_b[String(name)] = true
	var count := 0
	for name in a:
		if set_b.has(String(name)): count += 1
	return count
