extends SceneTree

# Contract revision: branch-whorl close/mid pine derivatives must remain runtime-loadable.
func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var scene := load("res://scenes/world/forest_map_foundation.tscn") as PackedScene
	if scene == null:
		_fail("forest map scene must load")
		return
	var root := scene.instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame
	await process_frame
	var ecology := root.get_node_or_null("Ecology") as ForestEcology
	var bridge := root.get_node_or_null("AssetBridge") as ForestAssetBridge
	if ecology == null or bridge == null:
		_fail("ecology/asset bridge missing")
		return
	if not bridge._mobile_pine_lods_available():
		_fail("all five mobile pine resources must exist")
		return
	var paths := [bridge.pine_lod0_path, bridge.pine_lod1_path, bridge.pine_lod2_path, bridge.pine_lod3_path, bridge.pine_hlod_path]
	for path_variant: Variant in paths:
		var meshes := bridge._load_meshes(str(path_variant))
		if meshes.size() != ForestAssetBridge.EXPECTED_PINE_VARIANTS:
			_fail("pine resource must expose 3 variants: %s got=%d" % [str(path_variant), meshes.size()])
			return
	for close_path: String in [bridge.pine_lod0_path, bridge.pine_lod1_path, bridge.pine_lod2_path]:
		var close_meshes := bridge._load_meshes(close_path)
		for mesh: Mesh in close_meshes:
			if mesh.get_surface_count() < 2:
				_fail("close/mid pine must preserve separate trunk+foliage surfaces: %s surfaces=%d" % [close_path, mesh.get_surface_count()])
				return
			var material_count := 0
			for surface_i in range(mesh.get_surface_count()):
				if mesh.surface_get_material(surface_i) != null:
					material_count += 1
			if material_count < 2:
				_fail("close/mid pine must preserve trunk+foliage materials: %s materials=%d" % [close_path, material_count])
				return
	if bridge._load_first_mesh(bridge.rock_scene_path) == null:
		_fail("real rock mesh unavailable")
		return
	if bridge._load_first_mesh(bridge.stump_scene_path) == null:
		_fail("real stump mesh unavailable")
		return
	if not (ForestAssetBridge.TREE_LOD0_END < ForestAssetBridge.TREE_LOD1_END and ForestAssetBridge.TREE_LOD1_END < ForestAssetBridge.TREE_LOD2_END and ForestAssetBridge.TREE_LOD2_END < ForestAssetBridge.TREE_LOD3_END and ForestAssetBridge.TREE_LOD3_END < ForestAssetBridge.TREE_HLOD_END):
		_fail("LOD ranges must be strictly increasing")
		return
	var lod_counts := {"PineLOD0_30k_": 0, "PineLOD1_15k_": 0, "PineLOD2_6k_": 0, "PineLOD3_2k_": 0, "PineHLOD_96_": 0}
	var seen_variants: Dictionary = {}
	_collect_bridge_counts(bridge, lod_counts, seen_variants)
	var tree_count: int = ecology.tree_positions.size()
	for prefix: String in lod_counts.keys():
		if int(lod_counts[prefix]) != tree_count:
			_fail("LOD instance count mismatch %s expected=%d got=%d" % [prefix, tree_count, int(lod_counts[prefix])])
			return
	if seen_variants.size() != ForestAssetBridge.EXPECTED_PINE_VARIANTS:
		_fail("runtime must use all 3 pine variants, got=" + str(seen_variants.keys()))
		return
	print("FOREST_ASSET_BRIDGE_OK trees=", tree_count, " variants=", seen_variants.size(), " lod0=", lod_counts["PineLOD0_30k_"], " lod1=", lod_counts["PineLOD1_15k_"], " lod2=", lod_counts["PineLOD2_6k_"], " lod3=", lod_counts["PineLOD3_2k_"], " hlod=", lod_counts["PineHLOD_96_"])
	root.queue_free()
	quit(0)

func _collect_bridge_counts(node: Node, lod_counts: Dictionary, seen_variants: Dictionary) -> void:
	if node is MultiMeshInstance3D:
		var mm_node := node as MultiMeshInstance3D
		for prefix: String in lod_counts.keys():
			if mm_node.name.begins_with(prefix):
				if mm_node.multimesh != null:
					lod_counts[prefix] = int(lod_counts[prefix]) + mm_node.multimesh.instance_count
				var suffix := mm_node.name.trim_prefix(prefix)
				seen_variants[suffix] = true
	for child: Node in node.get_children():
		_collect_bridge_counts(child, lod_counts, seen_variants)

func _fail(message: String) -> void:
	push_error("FOREST_ASSET_BRIDGE_FAIL: " + message)
	quit(1)
