extends SceneTree

const MODEL := "res://assets/provisional/characters/kenney_survivors/Model/characterMedium.fbx"
const CLIPS := [
	"res://assets/provisional/characters/kenney_survivors/Animations/idle.fbx",
	"res://assets/provisional/characters/kenney_survivors/Animations/run.fbx",
	"res://assets/provisional/characters/kenney_survivors/Animations/jump.fbx"
]

func _init() -> void:
	var failures: Array[String] = []
	var model_bones: Array[String] = []
	var packed := load(MODEL) as PackedScene
	if packed == null:
		failures.append("No se pudo cargar modelo riggeado")
	else:
		var model := packed.instantiate()
		var skeletons := _find_by_class(model, "Skeleton3D")
		if skeletons.is_empty(): failures.append("El modelo no contiene Skeleton3D")
		else:
			var skeleton := skeletons[0] as Skeleton3D
			model_bones = _bone_names(skeleton)
			for required_bone in ["RightHand", "LeftHand"]:
				if skeleton.find_bone(required_bone) < 0: failures.append("Falta hueso requerido: " + required_bone)
			print("RIG MODEL bones=", model_bones.size(), " ", model_bones)
		model.free()
	for clip_path in CLIPS:
		var clip_packed := load(clip_path) as PackedScene
		if clip_packed == null:
			failures.append("No se pudo cargar clip: " + clip_path)
			continue
		var clip := clip_packed.instantiate()
		var clip_skeletons := _find_by_class(clip, "Skeleton3D")
		if clip_skeletons.is_empty(): failures.append("Clip sin Skeleton3D: " + clip_path)
		else:
			var clip_bones := _bone_names(clip_skeletons[0] as Skeleton3D)
			if clip_bones != model_bones: failures.append("Rig incompatible con modelo: " + clip_path)
		var clip_players := _find_by_class(clip, "AnimationPlayer")
		if clip_players.is_empty(): failures.append("Clip sin AnimationPlayer: " + clip_path)
		for p in clip_players:
			var player := p as AnimationPlayer
			var list := player.get_animation_list()
			print("CLIP ANIMS ", clip_path, ": ", list)
			if list.is_empty(): failures.append("Clip sin animaciones: " + clip_path)
			if player.has_animation("Root|0_Targeting Pose"):
				_print_animation_tracks(player.get_animation("Root|0_Targeting Pose"), clip_path)
		clip.free()

	var main_packed := load("res://scenes/main.tscn") as PackedScene
	if main_packed == null:
		failures.append("No se pudo cargar main para probar locomoción")
	else:
		var main := main_packed.instantiate()
		root.add_child(main)
		await process_frame
		await process_frame
		var body_visual := main.get_node_or_null("Player/BodyVisual")
		var locomotion := main.get_node_or_null("Player/BodyVisual/LocomotionAnimationPlayer") as AnimationPlayer
		if locomotion == null:
			failures.append("No se creó AnimationPlayer de locomoción en runtime")
		else:
			for expected in ["idle", "run", "jump"]:
				if not locomotion.has_animation(expected): failures.append("Falta animación runtime: " + expected)
			print("RUNTIME PLAYER ANIMS: ", locomotion.get_animation_list())
		var tree := main.get_node_or_null("Player/BodyVisual/LocomotionAnimationTree") as AnimationTree
		if tree == null:
			failures.append("No se creó AnimationTree de locomoción en runtime")
		else:
			if not tree.active: failures.append("AnimationTree runtime no está activo")
			var machine := tree.tree_root as AnimationNodeStateMachine
			if machine == null:
				failures.append("AnimationTree no usa state machine")
			else:
				for state in ["idle", "run", "jump"]:
					if not machine.has_node(state): failures.append("Falta estado AnimationTree: " + state)
			var playback := tree.get("parameters/playback") as AnimationNodeStateMachinePlayback
			if playback == null: failures.append("AnimationTree sin playback runtime")
			elif not playback.is_playing(): failures.append("State machine runtime no está reproduciendo")
			else: print("RUNTIME ANIMATION STATE: ", playback.get_current_node())
			var run_scale = tree.get("parameters/run/run_speed/scale")
			if run_scale == null: failures.append("Falta parámetro runtime de velocidad de carrera")
			else: print("RUNTIME RUN SCALE: ", run_scale)
		if body_visual != null:
			var attachment := _find_named(body_visual, "WeaponHandAttachment") as BoneAttachment3D
			if attachment == null: failures.append("No se creó BoneAttachment3D del arma")
			elif attachment.bone_name != "RightHand": failures.append("El arma no está enlazada a RightHand")
		var operator_skeletons := _find_by_class(main.get_node("Player/BodyVisual/OperatorModel"), "Skeleton3D")
		if operator_skeletons.is_empty(): failures.append("Operador instanciado sin Skeleton3D")
		main.queue_free()
		await process_frame

	if failures.is_empty():
		print("ARCONT RIG: compatibility + AnimationTree runtime OK")
		quit(0)
		return
	for failure in failures: push_error("ARCONT RIG: " + failure)
	quit(1)

func _print_animation_tracks(animation: Animation, source_path: String) -> void:
	print("TARGETING POSE TRACK AUDIT ", source_path, " tracks=", animation.get_track_count())
	for i in animation.get_track_count():
		print("TARGET TRACK ", i, " type=", animation.track_get_type(i), " path=", animation.track_get_path(i))

func _bone_names(skeleton: Skeleton3D) -> Array[String]:
	var names: Array[String] = []
	for i in skeleton.get_bone_count(): names.append(skeleton.get_bone_name(i))
	return names

func _find_by_class(root_node: Node, wanted_class: String) -> Array[Node]:
	var out: Array[Node] = []
	if root_node.get_class() == wanted_class: out.append(root_node)
	for child in root_node.get_children(): out.append_array(_find_by_class(child, wanted_class))
	return out

func _find_named(root_node: Node, wanted_name: String) -> Node:
	if root_node.name == wanted_name: return root_node
	for child in root_node.get_children():
		var found := _find_named(child, wanted_name)
		if found != null: return found
	return null
