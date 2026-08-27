extends Node

signal profile_changed(ai_interval: float, gore_parts: int)
signal animation_quality_changed(level: int)

@export var sample_interval := 1.0
@export var low_fps_threshold := 42.0
@export var recovery_fps_threshold := 56.0

var tier := 0
var sample_timer := 0.0
var ai_interval := 0.08
var gore_parts := 6
var procedural_animation_level := 2

func _ready() -> void:
	_apply_tier(1 if OS.has_feature("mobile") else 0)

func _process(delta: float) -> void:
	sample_timer += delta
	if sample_timer < sample_interval:
		return
	sample_timer = 0.0
	var fps := float(Engine.get_frames_per_second())
	if fps > 0.0 and fps < low_fps_threshold and tier < 2:
		_apply_tier(tier + 1)
	elif fps >= recovery_fps_threshold and tier > (1 if OS.has_feature("mobile") else 0):
		_apply_tier(tier - 1)

func _apply_tier(value: int) -> void:
	tier = clampi(value, 0, 2)
	match tier:
		0:
			ai_interval = 0.065
			gore_parts = 6
			procedural_animation_level = 2
		1:
			ai_interval = 0.11
			gore_parts = 4
			procedural_animation_level = 1
		2:
			ai_interval = 0.17
			gore_parts = 2
			procedural_animation_level = 0
	profile_changed.emit(ai_interval, gore_parts)
	animation_quality_changed.emit(procedural_animation_level)

func get_animation_quality() -> int:
	return procedural_animation_level

func get_animation_update_interval() -> float:
	match procedural_animation_level:
		2: return 0.0
		1: return 1.0 / 30.0
		_: return 1.0 / 18.0
