extends Node3D

@export_file("*.png") var skin_path := "res://assets/provisional/characters/kenney_survivors/Skins/survivorMaleB.png"

func _ready() -> void:
	var texture := load(skin_path) as Texture2D
	if texture == null:
		return
	_apply_skin_recursive(self, texture)

func _apply_skin_recursive(node: Node, texture: Texture2D) -> void:
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		var material := StandardMaterial3D.new()
		material.albedo_texture = texture
		material.roughness = 0.82
		mesh_instance.material_override = material
	for child in node.get_children():
		_apply_skin_recursive(child, texture)
