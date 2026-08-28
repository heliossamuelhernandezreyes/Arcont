extends Node3D
@export_file("*.png") var skin_path:="res://assets/provisional/characters/kenney_survivors/Skins/survivorMaleB.png"
@export var idle_clip:="res://assets/provisional/characters/kenney_survivors/Animations/idle.fbx"
@export var run_clip:="res://assets/provisional/characters/kenney_survivors/Animations/run.fbx"
@export var jump_clip:="res://assets/provisional/characters/kenney_survivors/Animations/jump.fbx"
@export var animation_blend:=0.16
@export var run_reference_speed:=6.2
@export var weapon_bone_name:="RightHand"
var animation_player:AnimationPlayer
var current_state:=""
var player_body:CharacterBody3D
var budget:Node
var weapon:Node
var weapon_mount:Node3D
var phase:=0.0
var update_accumulator:=0.0
var base_position:=Vector3.ZERO
var procedural_pitch:=0.0
var procedural_roll:=0.0
func _ready()->void:
 player_body=get_parent() as CharacterBody3D;base_position=position
 var scene:=get_tree().current_scene;if scene:budget=scene.get_node_or_null("PerformanceBudget")
 if player_body:
  weapon=player_body.get_node_or_null("Weapon")
  weapon_mount=get_node_or_null("WeaponMount") as Node3D
 var texture:=load(skin_path) as Texture2D;if texture!=null:_apply_skin_recursive(self,texture)
 _bind_weapon_to_hand()
 _setup_animation_player();_play_state("idle")
func _physics_process(delta:float)->void:
 if player_body==null or animation_player==null:return
 var speed:=Vector2(player_body.velocity.x,player_body.velocity.z).length()
 if not player_body.is_on_floor():_play_state("jump")
 elif speed>0.25:_play_state("run");animation_player.speed_scale=clampf(speed/maxf(run_reference_speed,0.1),0.65,1.45)
 else:_play_state("idle");animation_player.speed_scale=1.0
 _update_procedural(delta,speed)
func _bind_weapon_to_hand()->void:
 if weapon_mount==null:return
 var operator:=get_node_or_null("OperatorModel")
 if operator==null:return
 var skeleton:=_find_skeleton(operator)
 if skeleton==null:return
 if skeleton.find_bone(weapon_bone_name)<0:return
 var old_global:=weapon_mount.global_transform
 var attachment:=BoneAttachment3D.new();attachment.name="WeaponHandAttachment";attachment.bone_name=weapon_bone_name
 skeleton.add_child(attachment)
 weapon_mount.reparent(attachment,true)
 weapon_mount.global_transform=old_global
 weapon_mount.position=Vector3(0.02,-0.03,-0.08)
 weapon_mount.rotation_degrees=Vector3(-8.0,90.0,-2.0)
func _update_procedural(delta:float,speed:float)->void:
 var interval:=_quality_interval();update_accumulator+=delta;if interval>0.0 and update_accumulator<interval:return
 var step:=update_accumulator if interval>0.0 else delta;update_accumulator=0.0;phase+=step*(1.7+speed*0.22)
 var aiming:=weapon!=null and bool(weapon.get("aiming"));var moving:=clampf(speed/maxf(run_reference_speed,0.1),0.0,1.35);var stability:=0.42 if aiming else 1.0
 var target_y:=base_position.y+sin(phase*1.15)*0.010*stability+absf(sin(phase*2.2))*0.008*moving
 var local_velocity:=player_body.global_transform.basis.inverse()*player_body.velocity;var lateral:=clampf(local_velocity.x/maxf(run_reference_speed,0.1),-1.0,1.0);var forward:=clampf(-local_velocity.z/maxf(run_reference_speed,0.1),-1.0,1.0)
 procedural_roll=lerpf(procedural_roll,-lateral*3.0,minf(step*9.0,1.0));procedural_pitch=lerpf(procedural_pitch,forward*1.6-(1.8 if aiming else 0.0),minf(step*7.0,1.0));position.y=lerpf(position.y,target_y,minf(step*8.0,1.0));rotation_degrees.x=procedural_pitch;rotation_degrees.z=procedural_roll
func _quality_interval()->float:
 if budget and budget.has_method("get_animation_update_interval"):return float(budget.get_animation_update_interval())
 return 1.0/30.0 if OS.has_feature("mobile") else 0.0
func _setup_animation_player()->void:
 animation_player=AnimationPlayer.new();animation_player.name="LocomotionAnimationPlayer";animation_player.root_node=NodePath("OperatorModel");add_child(animation_player);var library:=AnimationLibrary.new();animation_player.add_animation_library("",library);_import_clip(library,idle_clip,"Root|Idle","idle",true);_import_clip(library,run_clip,"Root|Run","run",true);_import_clip(library,jump_clip,"Root|Jump","jump",false)
func _import_clip(library:AnimationLibrary,path:String,source_name:String,target_name:String,looped:bool)->void:
 var packed:=load(path) as PackedScene;if packed==null:return
 var clip_root:=packed.instantiate();var source:=_find_animation_player(clip_root)
 if source!=null and source.has_animation(source_name):
  var animation:=source.get_animation(source_name).duplicate(true) as Animation
  if animation!=null:animation.loop_mode=Animation.LOOP_LINEAR if looped else Animation.LOOP_NONE;library.add_animation(target_name,animation)
 clip_root.free()
func _play_state(state:String)->void:
 if animation_player==null or current_state==state or not animation_player.has_animation(state):return
 current_state=state;animation_player.play(state,animation_blend)
func _find_animation_player(node:Node)->AnimationPlayer:
 if node is AnimationPlayer:return node as AnimationPlayer
 for child in node.get_children():var found:=_find_animation_player(child);if found!=null:return found
 return null
func _find_skeleton(node:Node)->Skeleton3D:
 if node is Skeleton3D:return node as Skeleton3D
 for child in node.get_children():
  var found:=_find_skeleton(child)
  if found!=null:return found
 return null
func _apply_skin_recursive(node:Node,texture:Texture2D)->void:
 if node is MeshInstance3D:
  var mesh_instance:=node as MeshInstance3D;var material:=StandardMaterial3D.new();material.albedo_texture=texture;material.roughness=0.82;mesh_instance.material_override=material
 for child in node.get_children():_apply_skin_recursive(child,texture)
