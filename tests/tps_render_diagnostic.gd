extends SceneTree

const MAIN := preload("res://scenes/main.tscn")

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var failures: Array[String] = []
	var main := MAIN.instantiate()
	root.add_child(main)
	for _i in range(8): await process_frame
	var menu := main.get_node_or_null("MainMenu")
	if menu != null and menu.has_method("_start"):
		menu.call("_start")
	for _i in range(45): await process_frame
	for _i in range(4): await physics_frame

	var player := main.get_node_or_null("Player") as CharacterBody3D
	var camera := main.get_node_or_null("Player/CameraRig/SpringArm3D/Camera3D") as Camera3D
	var rig := main.get_node_or_null("Player/CameraRig") as Node3D
	var arm := main.get_node_or_null("Player/CameraRig/SpringArm3D") as SpringArm3D
	var operator := main.get_node_or_null("Player/BodyVisual/OperatorModel") as Node3D
	if player == null: failures.append("Player missing")
	if camera == null: failures.append("Camera3D missing")
	if rig == null: failures.append("CameraRig missing")
	if arm == null: failures.append("SpringArm3D missing")
	if operator == null: failures.append("OperatorModel missing")
	if not failures.is_empty():
		_finish(main, failures)
		return

	var viewport_size := root.get_viewport().get_visible_rect().size
	var visible_geometry: Array[GeometryInstance3D] = []
	_collect_geometry(operator, visible_geometry)
	if visible_geometry.is_empty(): failures.append("Operator has no GeometryInstance3D descendants")

	var front_count := 0
	var on_screen_count := 0
	var visible_count := 0
	var points: Array[Vector3] = []
	for geometry in visible_geometry:
		if geometry.visible and geometry.is_visible_in_tree(): visible_count += 1
		var mesh_instance := geometry as MeshInstance3D
		if mesh_instance == null or mesh_instance.mesh == null: continue
		var aabb := mesh_instance.mesh.get_aabb()
		var center := mesh_instance.global_transform * aabb.get_center()
		points.append(center)
		if not camera.is_position_behind(center):
			front_count += 1
			var screen := camera.unproject_position(center)
			if screen.x >= 0.0 and screen.y >= 0.0 and screen.x <= viewport_size.x and screen.y <= viewport_size.y:
				on_screen_count += 1

	var target := player.global_position + Vector3.UP * rig.position.y
	var actual_distance := camera.global_position.distance_to(target)
	print("TPS_RENDER_DIAGNOSTIC|viewport=%s|camera=%s|player=%s|distance=%.3f|spring=%.3f|operator_visible=%s|geometry=%d|visible_geometry=%d|front=%d|on_screen=%d" % [viewport_size,camera.global_position,player.global_position,actual_distance,arm.spring_length,operator.visible,visible_geometry.size(),visible_count,front_count,on_screen_count])
	for i in range(mini(points.size(), 8)):
		var p := points[i]
		print("TPS_RENDER_POINT|i=%d|world=%s|behind=%s|screen=%s" % [i,p,camera.is_position_behind(p),camera.unproject_position(p) if not camera.is_position_behind(p) else Vector2(-1,-1)])

	if not operator.visible: failures.append("OperatorModel root is hidden")
	if visible_count == 0: failures.append("All operator geometry is hidden in tree")
	if front_count == 0: failures.append("No operator mesh center lies in front of Camera3D")
	if on_screen_count == 0: failures.append("No operator mesh center projects inside the viewport")
	if actual_distance < 1.0: failures.append("TPS camera collapsed unexpectedly in open startup view: %.3f m" % actual_distance)

	_finish(main, failures)

func _collect_geometry(node: Node, out: Array[GeometryInstance3D]) -> void:
	if node is GeometryInstance3D:
		out.append(node as GeometryInstance3D)
	for child in node.get_children():
		_collect_geometry(child, out)

func _finish(main: Node, failures: Array[String]) -> void:
	main.queue_free()
	await process_frame
	if failures.is_empty():
		print("ARCONT TPS RENDER: operator has visible geometry projected into live TPS viewport")
		quit(0)
		return
	for failure in failures:
		push_error("ARCONT TPS RENDER: " + failure)
	quit(1)
