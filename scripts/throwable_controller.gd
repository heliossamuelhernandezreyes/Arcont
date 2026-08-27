extends Node
class_name ThrowableController

signal throwable_changed(kind:String,remaining:int)
const THROWABLE_SCRIPT=preload("res://scripts/throwable.gd")
@export var throw_speed:=14.0
@export var upward_boost:=4.2
var selected:="GRENADE"
var inventory:={"GRENADE":3,"DECOY":3,"EMP":2}
var player:Node3D
var hud_label:Label

func _ready()->void:
	add_to_group("throwable_controller")
	call_deferred("_bind_player")
	call_deferred("_bind_hud")

func _bind_player()->void:
	player=get_tree().get_first_node_in_group("player") as Node3D

func _bind_hud()->void:
	var scene:=get_tree().current_scene
	if scene:hud_label=scene.get_node_or_null("HUD/Throwable") as Label
	_update_hud()

func _unhandled_input(event:InputEvent)->void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode==KEY_F:throw_selected()
		elif event.keycode==KEY_V:cycle_throwable()

func cycle_throwable()->void:
	match selected:
		"GRENADE":selected="DECOY"
		"DECOY":selected="EMP"
		_:selected="GRENADE"
	_emit_state()

func throw_selected()->bool:
	if player==null or not is_instance_valid(player):_bind_player()
	if player==null:return false
	var count:=int(inventory.get(selected,0))
	if count<=0:return false
	var camera:=player.get_node_or_null("CameraRig/Camera3D") as Camera3D
	if camera==null:return false
	var projectile:=THROWABLE_SCRIPT.new() as RigidBody3D
	get_tree().current_scene.add_child(projectile)
	projectile.global_position=camera.global_position+(-camera.global_transform.basis.z)*0.75
	projectile.configure(selected,player)
	projectile.linear_velocity=(-camera.global_transform.basis.z)*throw_speed+Vector3.UP*upward_boost
	projectile.angular_velocity=Vector3(5.0,3.0,2.0)
	inventory[selected]=count-1
	_emit_state()
	return true

func mobile_throw()->void:throw_selected()
func mobile_cycle()->void:cycle_throwable()

func _emit_state()->void:
	var remaining:=int(inventory.get(selected,0))
	throwable_changed.emit(selected,remaining)
	_update_hud()

func _update_hud()->void:
	if hud_label==null or not is_instance_valid(hud_label):return
	var short_name:=selected
	match selected:
		"GRENADE":short_name="GRANADA"
		"DECOY":short_name="SEÑUELO"
		"EMP":short_name="EMP"
	hud_label.text="ARROJABLE // %s  x%d"%[short_name,int(inventory.get(selected,0))]
