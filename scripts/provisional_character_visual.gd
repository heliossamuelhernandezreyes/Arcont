extends Node3D

@export_file("*.png") var skin_path := "res://assets/provisional/characters/kenney_survivors/Skins/survivorMaleB.png"
@export var idle_clip := "res://assets/provisional/characters/kenney_survivors/Animations/idle.fbx"
@export var run_clip := "res://assets/provisional/characters/kenney_survivors/Animations/run.fbx"
@export var jump_clip := "res://assets/provisional/characters/kenney_survivors/Animations/jump.fbx"
@export var animation_blend := 0.16
@export var run_reference_speed := 6.2

var animation_player: AnimationPlayer
var current_state := ""
var player_body: CharacterBody3D

func _ready() -> void:
	player_body = get_parent() as CharacterBody3D
	var texture := load(skin_path) as Texture2D
	if texture != null: _apply_skin_recursive(self, texture)
	_setup_animation_player()
	_play_state("idle")

func _physics_process(_delta: float) -> void:
	if player_body == null or animation_player == null: return
	var horizontal_speed := Vector2(player_body.velocity.x, player_body.velocity.z).length()
	if not player_body.is_on_floor():
		_play_state("jump")
	elif horizontal_speed > 0.25:
		_play_state("run")
		animation_player.speed_scale = clampf(horizontal_speed / maxf(run_reference_speed, 0.1), 0.65, 1.45)
	else:
		_play_state("idle")
		animation_player.speed_scale = 1.0

func _setup_animation_player() -> void:
	animation_player = AnimationPlayer.new()
	animation_player.name = "LocomotionAnimationPlayer"
	animation_player.root_node = NodePath("../OperatorModel")
	add_child(animation_player)
	var library := AnimationLibrary.new()
	animation_player.add_animation_library("", library)
	_import_clip(library, idle_clip, "Root|Idle", "idle", true)
	_import_clip(library, run_clip, "Root|Run", "run", true)
	_import_clip(library, jump_clip, "Root|Jump", "jump", false)

func _import_clip(library: AnimationLibrary, path: String, source_name: String, target_name: String, looped: bool) -> void:
	var packed := load(path) as PackedScene
	if packed == null: return
	var clip_root := packed.instantiate()
	var source_player := _find_animation_player(clip_root)
	if source_player != null and source_player.has_animation(source_name):
		var animation := source_player.get_animation(source_name).duplicate(true) as Animation
		if animation != null:
			animation.loop_mode = Animation.LOOP_LINEAR if looped else Animation.LOOP_NONE
			library.add_animation(target_name, animation)
	clip_root.free()

func _play_state(state: String) -> void:
	if animation_player == null or current_state == state or not animation_player.has_animation(state): return
	current_state = state
	animation_player.play(state, animation_blend)

func _find_animation_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer: return node as AnimationPlayer
	for child in node.get_children():
		var found := _find_animation_player(child)
		if found != null: return found
	return null

func _apply_skin_recursive(node: Node, texture: Texture2D) -> void:
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		var material := StandardMaterial3D.new()
		material.albedo_texture = texture
		material.roughness = 0.82
		mesh_instance.material_override = material
	for child in node.get_children(): _apply_skin_recursive(child, texture)
