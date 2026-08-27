extends SceneTree

const MODEL := "res://assets/provisional/characters/kenney_survivors/Model/characterMedium.fbx"
const CLIPS := [
	"res://assets/provisional/characters/kenney_survivors/Animations/idle.fbx",
	"res://assets/provisional/characters/kenney_survivors/Animations/run.fbx",
	"res://assets/provisional/characters/kenney_survivors/Animations/jump.fbx"
]

func _init() -> void:
	var failures: Array[String] = []
	var packed := load(MODEL) as PackedScene
	if packed == null:
		failures.append("No se pudo cargar modelo riggeado")
	else:
		var model := packed.instantiate()
		print("RIG MODEL TREE")
		_dump_tree(model, "")
		var skeletons := _find_by_class(model, "Skeleton3D")
		var players := _find_by_class(model, "AnimationPlayer")
		print("RIG skeletons=", skeletons.size(), " animation_players=", players.size())
		if skeletons.is_empty(): failures.append("El modelo no contiene Skeleton3D")
		for p in players:
			print("MODEL ANIMS ", p.name, ": ", (p as AnimationPlayer).get_animation_list())
		model.free()
	for clip_path in CLIPS:
		var clip_packed := load(clip_path) as PackedScene
		if clip_packed == null:
			failures.append("No se pudo cargar clip: " + clip_path)
			continue
		var clip := clip_packed.instantiate()
		print("RIG CLIP ", clip_path)
		_dump_tree(clip, "")
		var clip_players := _find_by_class(clip, "AnimationPlayer")
		if clip_players.is_empty(): failures.append("Clip sin AnimationPlayer: " + clip_path)
		for p in clip_players:
			var list := (p as AnimationPlayer).get_animation_list()
			print("CLIP ANIMS ", p.name, ": ", list)
			if list.is_empty(): failures.append("Clip sin animaciones: " + clip_path)
		clip.free()
	if failures.is_empty():
		print("ARCONT RIG: assets OK")
		quit(0)
		return
	for failure in failures: push_error("ARCONT RIG: " + failure)
	quit(1)

func _dump_tree(node: Node, prefix: String) -> void:
	print(prefix, node.name, " [", node.get_class(), "]")
	for child in node.get_children(): _dump_tree(child, prefix + "  ")

func _find_by_class(root: Node, class_name: String) -> Array[Node]:
	var out: Array[Node] = []
	if root.get_class() == class_name: out.append(root)
	for child in root.get_children(): out.append_array(_find_by_class(child, class_name))
	return out
