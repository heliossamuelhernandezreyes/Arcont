extends Node3D
@export_file("*.png") var skin_path:="res://assets/provisional/characters/kenney_survivors/Skins/survivorMaleB.png"
@export var idle_clip:="res://assets/provisional/characters/kenney_survivors/Animations/idle.fbx"
@export var run_clip:="res://assets/provisional/characters/kenney_survivors/Animations/run.fbx"
@export var jump_clip:="res://assets/provisional/characters/kenney_survivors/Animations/jump.fbx"
@export var animation_blend:=0.16
@export var run_reference_speed:=6.2
@export var weapon_bone_name:="RightHand"
var animation_player:AnimationPlayer
var animation_tree:AnimationTree
var state_machine:AnimationNodeStateMachine
var state_playback:AnimationNodeStateMachinePlayback
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
var ads_weight:=0.0
var locomotion_input:=Vector2.ZERO
var ads_filter_track_count:=0
func _ready()->void:
 player_body=get_parent() as CharacterBody3D;base_position=position
 var scene:=get_tree().current_scene;if scene:budget=scene.get_node_or_null("PerformanceBudget")
 if player_body:
  weapon=player_body.get_node_or_null("Weapon")
  weapon_mount=get_node_or_null("WeaponMount") as Node3D
 var texture:=load(skin_path) as Texture2D;if texture!=null:_apply_skin_recursive(self,texture)
 _bind_weapon_to_hand();_setup_animation_player();call_deferred("_setup_animation_tree")
func _physics_process(delta:float)->void:
 if player_body==null or animation_tree==null:return
 if state_playback!=null and not state_playback.is_playing():
  state_playback.start("idle",true);current_state="idle"
 var speed:=Vector2(player_body.velocity.x,player_body.velocity.z).length();_update_locomotion_input(speed)
 if not player_body.is_on_floor():_play_state("jump")
 elif speed>0.25:_play_state("run");animation_tree.set("parameters/locomotion/run/run_speed/scale",clampf(speed/maxf(run_reference_speed,0.1),0.65,1.45))
 else:_play_state("idle")
 _update_tactical_pose(delta);_update_procedural(delta,speed)
func _update_locomotion_input(speed:float)->void:
 if speed<=0.05:locomotion_input=Vector2.ZERO;return
 var local_velocity:=player_body.global_transform.basis.inverse()*player_body.velocity
 locomotion_input=Vector2(local_velocity.x,-local_velocity.z).normalized()*clampf(speed/maxf(run_reference_speed,0.1),0.0,1.0)
func _weapon_stance()->Dictionary:
 var slot:=int(weapon.get("slot")) if weapon!=null else 1
 match slot:
  0:return {"hip_pos":Vector3(0.025,-0.035,-0.09),"ads_pos":Vector3(0.018,-0.018,-0.125),"hip_rot":Vector3(-7.0,90.0,-2.5),"ads_rot":Vector3(-3.8,90.0,-0.6)}
  1:return {"hip_pos":Vector3(0.02,-0.035,-0.075),"ads_pos":Vector3(0.014,-0.016,-0.115),"hip_rot":Vector3(-6.0,90.0,-2.0),"ads_rot":Vector3(-3.2,90.0,-0.5)}
  2:return {"hip_pos":Vector3(0.012,-0.025,-0.035),"ads_pos":Vector3(0.006,-0.012,-0.07),"hip_rot":Vector3(-3.0,90.0,-1.0),"ads_rot":Vector3(-1.5,90.0,-0.2)}
  3:return {"hip_pos":Vector3(0.02,-0.045,-0.115),"ads_pos":Vector3(0.012,-0.02,-0.145),"hip_rot":Vector3(-8.5,90.0,-2.0),"ads_rot":Vector3(-4.0,90.0,-0.5)}
  _:return {"hip_pos":Vector3(0.022,-0.038,-0.095),"ads_pos":Vector3(0.014,-0.018,-0.13),"hip_rot":Vector3(-7.0,90.0,-2.0),"ads_rot":Vector3(-3.5,90.0,-0.5)}
func _update_tactical_pose(delta:float)->void:
 var aiming:=weapon!=null and bool(weapon.get("aiming"));ads_weight=move_toward(ads_weight,1.0 if aiming else 0.0,delta*7.5)
 if animation_tree:animation_tree.set("parameters/ads_layer/blend_amount",ads_weight)
 if weapon_mount:
  var stance:=_weapon_stance();var hip_pos:Vector3=stance["hip_pos"];var ads_pos:Vector3=stance["ads_pos"];var hip_rot:Vector3=stance["hip_rot"];var ads_rot:Vector3=stance["ads_rot"]
  weapon_mount.position=weapon_mount.position.lerp(hip_pos.lerp(ads_pos,ads_weight),clampf(delta*13.0,0.0,1.0));weapon_mount.rotation_degrees=weapon_mount.rotation_degrees.lerp(hip_rot.lerp(ads_rot,ads_weight),clampf(delta*13.0,0.0,1.0))
func get_locomotion_input()->Vector2:return locomotion_input
func get_ads_weight()->float:return ads_weight
func get_ads_filter_track_count()->int:return ads_filter_track_count
func get_weapon_stance_slot()->int:return int(weapon.get("slot")) if weapon!=null else -1
func _bind_weapon_to_hand()->void:
 if weapon_mount==null:return
 var operator:=get_node_or_null("OperatorModel");if operator==null:return
 var skeleton:=_find_skeleton(operator);if skeleton==null or skeleton.find_bone(weapon_bone_name)<0:return
 var attachment:=BoneAttachment3D.new();attachment.name="WeaponHandAttachment";attachment.bone_name=weapon_bone_name;skeleton.add_child(attachment)
 weapon_mount.reparent(attachment,false);var stance:=_weapon_stance();weapon_mount.position=stance["hip_pos"];weapon_mount.rotation_degrees=stance["hip_rot"]
func _update_procedural(delta:float,speed:float)->void:
 var interval:=_quality_interval();update_accumulator+=delta;if interval>0.0 and update_accumulator<interval:return
 var step:=update_accumulator if interval>0.0 else delta;update_accumulator=0.0;phase+=step*(1.7+speed*0.22)
 var moving:=clampf(speed/maxf(run_reference_speed,0.1),0.0,1.35);var stability:=lerpf(1.0,0.32,ads_weight)
 var target_y:=base_position.y+sin(phase*1.15)*0.006*stability+absf(sin(phase*2.2))*0.005*moving*stability
 procedural_roll=lerpf(procedural_roll,-locomotion_input.x*lerpf(2.4,0.8,ads_weight),minf(step*9.0,1.0));procedural_pitch=lerpf(procedural_pitch,locomotion_input.y*lerpf(0.9,0.25,ads_weight),minf(step*7.0,1.0));position.y=lerpf(position.y,target_y,minf(step*8.0,1.0));rotation_degrees.x=procedural_pitch;rotation_degrees.z=procedural_roll
func _quality_interval()->float:
 if budget and budget.has_method("get_animation_update_interval"):return float(budget.get_animation_update_interval())
 return 1.0/30.0 if OS.has_feature("mobile") else 0.0
func _setup_animation_player()->void:
 animation_player=AnimationPlayer.new();animation_player.name="LocomotionAnimationPlayer";animation_player.root_node=NodePath("OperatorModel");add_child(animation_player)
 var library:=AnimationLibrary.new();animation_player.add_animation_library("",library);_import_clip(library,idle_clip,"Root|Idle","idle",true);_import_clip(library,run_clip,"Root|Run","run",true);_import_clip(library,jump_clip,"Root|Jump","jump",false);_import_clip(library,idle_clip,"Root|0_Targeting Pose","targeting_pose",true)
func _setup_animation_tree()->void:
 if animation_player==null or not is_inside_tree():return
 state_machine=AnimationNodeStateMachine.new();state_machine.add_node("idle",_animation_node("idle"),Vector2(0,0))
 var run_scale:=AnimationNodeTimeScale.new();var run_tree:=AnimationNodeBlendTree.new();run_tree.add_node("run_anim",_animation_node("run"),Vector2(-120,0));run_tree.add_node("run_speed",run_scale,Vector2(80,0));run_tree.connect_node("run_speed",0,"run_anim");run_tree.connect_node("output",0,"run_speed");state_machine.add_node("run",run_tree,Vector2(220,0));state_machine.add_node("jump",_animation_node("jump"),Vector2(110,-150));state_machine.set_start_node("idle")
 _connect_state("idle","run",animation_blend);_connect_state("run","idle",animation_blend);_connect_state("idle","jump",0.08);_connect_state("run","jump",0.08);_connect_state("jump","idle",0.12);_connect_state("jump","run",0.12)
 var root_blend:=AnimationNodeBlendTree.new();root_blend.add_node("locomotion",state_machine,Vector2(-260,0));root_blend.add_node("targeting_pose",_animation_node("targeting_pose"),Vector2(-260,180))
 var ads_layer:=AnimationNodeBlend2.new();ads_layer.filter_enabled=true;root_blend.add_node("ads_layer",ads_layer,Vector2(20,70));root_blend.connect_node("ads_layer",0,"locomotion");root_blend.connect_node("ads_layer",1,"targeting_pose");root_blend.connect_node("output",0,"ads_layer");_configure_ads_filter(ads_layer)
 animation_tree=AnimationTree.new();animation_tree.name="LocomotionAnimationTree";add_child(animation_tree);animation_tree.anim_player=animation_tree.get_path_to(animation_player);animation_tree.tree_root=root_blend;animation_tree.active=true;animation_tree.set("parameters/ads_layer/blend_amount",0.0)
 state_playback=animation_tree.get("parameters/locomotion/playback") as AnimationNodeStateMachinePlayback
 if state_playback!=null:state_playback.start("idle",true);current_state="idle"
func _configure_ads_filter(layer:AnimationNodeBlend2)->void:
 ads_filter_track_count=0
 if animation_player==null or not animation_player.has_animation("targeting_pose"):return
 var upper_body:={"Spine":true,"Chest":true,"UpperChest":true,"Neck":true,"Head":true,"LeftShoulder":true,"LeftArm":true,"LeftForeArm":true,"LeftHand":true,"LeftHandIndex1":true,"LeftHandIndex2":true,"LeftHandIndex3":true,"LeftHandThumb1":true,"LeftHandThumb2":true,"RightShoulder":true,"RightArm":true,"RightForeArm":true,"RightHand":true,"RightHandIndex1":true,"RightHandIndex2":true,"RightHandIndex3":true,"RightHandThumb1":true,"RightHandThumb2":true}
 var pose:=animation_player.get_animation("targeting_pose")
 for i in pose.get_track_count():
  var path:=pose.track_get_path(i)
  if path.get_subname_count()==0:continue
  var bone:=String(path.get_subname(path.get_subname_count()-1))
  if upper_body.has(bone):layer.set_filter_path(path,true);ads_filter_track_count+=1
func _animation_node(name:String)->AnimationNodeAnimation:var node:=AnimationNodeAnimation.new();node.animation=StringName(name);return node
func _connect_state(from_state:String,to_state:String,xfade:float)->void:var transition:=AnimationNodeStateMachineTransition.new();transition.xfade_time=xfade;transition.reset=true;state_machine.add_transition(from_state,to_state,transition)
func _play_state(state:String)->void:
 if current_state==state:return
 current_state=state;if state_playback!=null:state_playback.travel(state)
func _import_clip(library:AnimationLibrary,path:String,source_name:String,target_name:String,looped:bool)->void:
 var packed:=load(path) as PackedScene;if packed==null:return
 var clip_root:=packed.instantiate();var source:=_find_animation_player(clip_root)
 if source!=null and source.has_animation(source_name):
  var animation:=source.get_animation(source_name).duplicate(true) as Animation
  if animation!=null:animation.loop_mode=Animation.LOOP_LINEAR if looped else Animation.LOOP_NONE;library.add_animation(target_name,animation)
 clip_root.free()
func _find_animation_player(node:Node)->AnimationPlayer:
 if node is AnimationPlayer:return node as AnimationPlayer
 for child in node.get_children():var found:=_find_animation_player(child);if found!=null:return found
 return null
func _find_skeleton(node:Node)->Skeleton3D:
 if node is Skeleton3D:return node as Skeleton3D
 for child in node.get_children():var found:=_find_skeleton(child);if found!=null:return found
 return null
func _apply_skin_recursive(node:Node,texture:Texture2D)->void:
 if node is MeshInstance3D:
  var mesh_instance:=node as MeshInstance3D;var material:=StandardMaterial3D.new();material.albedo_texture=texture;material.roughness=0.82;mesh_instance.material_override=material
 for child in node.get_children():_apply_skin_recursive(child,texture)
