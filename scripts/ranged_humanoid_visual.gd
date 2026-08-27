extends Node3D

@export_file("*.png") var skin_path := "res://assets/provisional/characters/kenney_survivors/Skins/survivorFemaleA.png"
const IDLE_CLIP := "res://assets/provisional/characters/kenney_survivors/Animations/idle.fbx"
const RUN_CLIP := "res://assets/provisional/characters/kenney_survivors/Animations/run.fbx"

var host: CharacterBody3D
var player: AnimationPlayer
var state := ""

func _ready() -> void:
	host = get_parent() as CharacterBody3D
	var texture := load(skin_path) as Texture2D
	if texture: _skin(self, texture)
	player = AnimationPlayer.new()
	player.name = "LocomotionAnimationPlayer"
	player.root_node = NodePath("../OperatorModel")
	add_child(player)
	var library := AnimationLibrary.new()
	player.add_animation_library("", library)
	_add_clip(library, IDLE_CLIP, "Root|Idle", "idle")
	_add_clip(library, RUN_CLIP, "Root|Run", "run")
	_play("idle")

func _process(_delta: float) -> void:
	if host == null or player == null: return
	var speed := Vector2(host.velocity.x, host.velocity.z).length()
	if speed > 0.18:
		_play("run")
		player.speed_scale = clampf(speed / 3.8, 0.65, 1.35)
	else:
		_play("idle")
		player.speed_scale = 1.0

func _add_clip(library: AnimationLibrary, path: String, source: String, target: String) -> void:
	var packed := load(path) as PackedScene
	if packed == null: return
	var root := packed.instantiate()
	var source_player := _find_player(root)
	if source_player and source_player.has_animation(source):
		var anim := source_player.get_animation(source).duplicate(true) as Animation
		anim.loop_mode = Animation.LOOP_LINEAR
		library.add_animation(target, anim)
	root.free()

func _play(next: String) -> void:
	if state == next or not player.has_animation(next): return
	state = next
	player.play(next, 0.15)

func _find_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer: return node as AnimationPlayer
	for child in node.get_children():
		var found := _find_player(child)
		if found: return found
	return null

func _skin(node: Node, texture: Texture2D) -> void:
	if node is MeshInstance3D:
		var material := StandardMaterial3D.new()
		material.albedo_texture = texture
		material.roughness = 0.84
		(node as MeshInstance3D).material_override = material
	for child in node.get_children(): _skin(child, texture)
