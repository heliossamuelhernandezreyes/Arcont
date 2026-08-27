extends Node

@export var hitmarker_time:=0.10
@export var muzzle_time:=0.045
@export var decal_lifetime:=5.0
@export var blood_lifetime:=0.35
@export var shake_decay:=10.0
@export var mobile_effect_scale:=0.65
@onready var camera:Camera3D=$"../Player/CameraRig/Camera3D"
@onready var hitmarker:Label=$"../HUD/HitMarker"
@onready var muzzle:OmniLight3D=$"../Player/BodyVisual/WeaponMount/MuzzleFlash"
var hitmarker_timer:=0.0
var muzzle_timer:=0.0
var shake_strength:=0.0
var visual_scale:=1.0
var audio_player:AudioStreamPlayer
var audio_generator:AudioStreamGenerator
func _ready()->void:
 visual_scale=mobile_effect_scale if OS.has_feature("mobile") else 1.0;hitmarker.visible=false;muzzle.visible=false;_setup_placeholder_audio()
func _process(delta:float)->void:
 if hitmarker_timer>0.0:hitmarker_timer-=delta;hitmarker.visible=hitmarker_timer>0.0
 if muzzle_timer>0.0:muzzle_timer-=delta;muzzle.visible=muzzle_timer>0.0
 shake_strength=move_toward(shake_strength,0.0,shake_decay*delta)
 if camera:
  camera.h_offset=randf_range(-1.0,1.0)*shake_strength*0.018;camera.v_offset=randf_range(-1.0,1.0)*shake_strength*0.012
  if shake_strength<=0.001:camera.h_offset=0.0;camera.v_offset=0.0
func on_shot_fired()->void:muzzle_timer=muzzle_time;muzzle.visible=true;shake_strength=maxf(shake_strength,0.55*visual_scale);_play_placeholder_shot()
func on_hit_feedback(hit_point:Vector3,hit_normal:Vector3,organic:bool)->void:
 hitmarker_timer=hitmarker_time;hitmarker.visible=true;shake_strength=maxf(shake_strength,0.28*visual_scale)
 if organic:_spawn_blood(hit_point,hit_normal)
 else:_spawn_impact_decal(hit_point,hit_normal)
func _spawn_blood(hit_point:Vector3,hit_normal:Vector3)->void:
 var root:=get_tree().current_scene;if root==null:return
 var puff:=MeshInstance3D.new();var sphere:=SphereMesh.new();sphere.radius=0.08*visual_scale;sphere.height=0.16*visual_scale;puff.mesh=sphere;var mat:=StandardMaterial3D.new();mat.albedo_color=Color(0.35,0.015,0.02,0.78);mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;puff.material_override=mat;root.add_child(puff);puff.global_position=hit_point+hit_normal*0.025;var tween:=puff.create_tween();tween.tween_property(puff,"scale",Vector3.ONE*2.3,blood_lifetime);tween.parallel().tween_property(mat,"albedo_color:a",0.0,blood_lifetime);tween.tween_callback(puff.queue_free)
func _spawn_impact_decal(hit_point:Vector3,hit_normal:Vector3)->void:
 var root:=get_tree().current_scene;if root==null:return
 var mark:=MeshInstance3D.new();var quad:=QuadMesh.new();quad.size=Vector2(0.10,0.10)*visual_scale;mark.mesh=quad;var mat:=StandardMaterial3D.new();mat.albedo_color=Color(0.06,0.06,0.06,0.9);mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;mark.material_override=mat;root.add_child(mark);mark.global_position=hit_point+hit_normal*0.012;if absf(hit_normal.dot(Vector3.UP))<0.99:mark.look_at(hit_point+hit_normal,Vector3.UP);root.get_tree().create_timer(decal_lifetime).timeout.connect(mark.queue_free)
func _setup_placeholder_audio()->void:
 audio_player=AudioStreamPlayer.new();audio_generator=AudioStreamGenerator.new();audio_generator.mix_rate=22050.0;audio_generator.buffer_length=0.12;audio_player.stream=audio_generator;audio_player.volume_db=-8.0;add_child(audio_player);audio_player.play()
func _play_placeholder_shot()->void:
 if audio_player==null or not audio_player.playing:return
 var playback:=audio_player.get_stream_playback() as AudioStreamGeneratorPlayback;if playback==null:return
 var frames:=1500
 for i in frames:
  var t:=float(i)/audio_generator.mix_rate;var env:=exp(-34.0*t);var sample:=clampf((sin(TAU*82.0*t)*0.55+randf_range(-1.0,1.0)*0.45)*env,-1.0,1.0);playback.push_frame(Vector2(sample,sample))
