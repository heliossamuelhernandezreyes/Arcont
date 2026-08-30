extends SceneTree
const MODEL := "res://assets/provisional/characters/kenney_survivors/Model/characterMedium.fbx"
const CLIPS := ["res://assets/provisional/characters/kenney_survivors/Animations/idle.fbx","res://assets/provisional/characters/kenney_survivors/Animations/run.fbx","res://assets/provisional/characters/kenney_survivors/Animations/jump.fbx"]
func _init()->void:
 var failures:Array[String]=[];var model_bones:Array[String]=[]
 var packed:=load(MODEL) as PackedScene
 if packed==null:failures.append("No se pudo cargar modelo riggeado")
 else:
  var model:=packed.instantiate();var skeletons:=_find_by_class(model,"Skeleton3D")
  if skeletons.is_empty():failures.append("El modelo no contiene Skeleton3D")
  else:
   var skeleton:=skeletons[0] as Skeleton3D;model_bones=_bone_names(skeleton)
   for required_bone in ["RightHand","LeftHand"]:
    if skeleton.find_bone(required_bone)<0:failures.append("Falta hueso requerido: "+required_bone)
   print("RIG MODEL bones=",model_bones.size()," ",model_bones)
  model.free()
 for clip_path in CLIPS:
  var clip_packed:=load(clip_path) as PackedScene
  if clip_packed==null:failures.append("No se pudo cargar clip: "+clip_path);continue
  var clip:=clip_packed.instantiate();var clip_skeletons:=_find_by_class(clip,"Skeleton3D")
  if clip_skeletons.is_empty():failures.append("Clip sin Skeleton3D: "+clip_path)
  elif _bone_names(clip_skeletons[0] as Skeleton3D)!=model_bones:failures.append("Rig incompatible con modelo: "+clip_path)
  var clip_players:=_find_by_class(clip,"AnimationPlayer")
  if clip_players.is_empty():failures.append("Clip sin AnimationPlayer: "+clip_path)
  for p in clip_players:
   var player:=p as AnimationPlayer;var list:=player.get_animation_list();print("CLIP ANIMS ",clip_path,": ",list)
   if list.is_empty():failures.append("Clip sin animaciones: "+clip_path)
  clip.free()
 var main_packed:=load("res://scenes/main.tscn") as PackedScene
 if main_packed==null:failures.append("No se pudo cargar main para probar locomoción")
 else:
  var main:=main_packed.instantiate();root.add_child(main);await process_frame;await process_frame;await physics_frame;await physics_frame
  var body_visual:=main.get_node_or_null("Player/BodyVisual")
  var operator:=main.get_node_or_null("Player/BodyVisual/OperatorModel") as Node3D
  if operator==null:failures.append("Falta OperatorModel runtime")
  else:
   var s:=operator.scale;print("PLAYER MODEL SCALE: ",s)
   if s.x<0.035 or s.x>0.06 or s.y<0.035 or s.y>0.06 or s.z<0.035 or s.z>0.06:failures.append("Escala del jugador fuera del contrato TPS humano: "+str(s))
  var rig:=main.get_node_or_null("Player/CameraRig") as Node3D
  var arm:=main.get_node_or_null("Player/CameraRig/SpringArm3D") as SpringArm3D
  var cam:=main.get_node_or_null("Player/CameraRig/SpringArm3D/Camera3D") as Camera3D
  if rig==null or arm==null or cam==null:failures.append("Falta rig TPS completo")
  else:
   print("TPS CONTRACT pivot_y=",rig.position.y," arm=",arm.spring_length," shoulder_origin=",arm.position," camera_local=",cam.position)
   if rig.position.y<1.35 or rig.position.y>1.85:failures.append("Altura de pivote TPS inválida: "+str(rig.position.y))
   if arm.spring_length<3.5 or arm.spring_length>5.5:failures.append("SpringArm fuera de rango TPS exploración: "+str(arm.spring_length))
   if absf(arm.position.x)<0.45 or absf(arm.position.x)>1.15:failures.append("Offset de hombro SpringArm inválido: "+str(arm.position.x))
   if cam.get_parent()!=arm:failures.append("Camera3D debe ser hija directa del SpringArm para conservar la solución nativa de colisión")
   if absf(cam.position.x)>0.05 or absf(cam.position.y)>0.05:failures.append("Camera3D adquirió deriva lateral/vertical local inesperada: "+str(cam.position))
   if not cam.current:failures.append("Camera3D TPS no es current")
  var locomotion:=main.get_node_or_null("Player/BodyVisual/LocomotionAnimationPlayer") as AnimationPlayer
  if locomotion==null:failures.append("No se creó AnimationPlayer de locomoción en runtime")
  else:
   for expected in ["idle","run","jump","targeting_pose"]:
    if not locomotion.has_animation(expected):failures.append("Falta animación runtime: "+expected)
   print("RUNTIME PLAYER ANIMS: ",locomotion.get_animation_list())
  var tree:=main.get_node_or_null("Player/BodyVisual/LocomotionAnimationTree") as AnimationTree
  if tree==null:failures.append("No se creó AnimationTree de locomoción en runtime")
  else:
   if not tree.active:failures.append("AnimationTree runtime no está activo")
   var blend_root:=tree.tree_root as AnimationNodeBlendTree
   if blend_root==null:failures.append("AnimationTree no usa BlendTree raíz para ADS")
   else:
    var machine:=blend_root.get_node("locomotion") as AnimationNodeStateMachine;var ads_layer:=blend_root.get_node("ads_layer") as AnimationNodeBlend2
    if machine==null:failures.append("Falta state machine locomotion anidada")
    else:
     for state in ["idle","run","jump"]:
      if not machine.has_node(state):failures.append("Falta estado AnimationTree: "+state)
    if ads_layer==null:failures.append("Falta capa Blend2 ADS")
    elif not ads_layer.filter_enabled:failures.append("Capa ADS no tiene filtro de huesos activo")
    else:
     if body_visual!=null and body_visual.has_method("get_ads_filter_track_count"):
      var filtered_count:=int(body_visual.get_ads_filter_track_count());print("ADS FILTERED IMPORT TRACKS: ",filtered_count)
      if filtered_count<8:failures.append("Filtro ADS no enlazó suficientes tracks reales del tren superior: "+str(filtered_count))
     if locomotion!=null and locomotion.has_animation("targeting_pose"):
      var pose:=locomotion.get_animation("targeting_pose");var upper_filtered:=0;var lower_filtered:=0
      for i in pose.get_track_count():
       var track_path:=pose.track_get_path(i);var track_text:=String(track_path)
       if ads_layer.is_path_filtered(track_path):
        if _is_lower_body_track(track_text):lower_filtered+=1
        else:upper_filtered+=1
      print("ADS FILTER AUDIT upper=",upper_filtered," lower=",lower_filtered)
      if upper_filtered<8:failures.append("Filtro ADS runtime no contiene suficientes tracks superiores")
      if lower_filtered>0:failures.append("Filtro ADS contamina tren inferior: "+str(lower_filtered)+" tracks")
   var playback:=tree.get("parameters/locomotion/playback") as AnimationNodeStateMachinePlayback
   if playback==null:failures.append("AnimationTree sin playback runtime")
   else:
    var current:=String(playback.get_current_node());print("RUNTIME ANIMATION STATE: ",current," playing=",playback.is_playing())
    if not playback.is_playing():failures.append("AnimationTree sigue detenido; produciría bind/T-pose")
    if current not in ["idle","run","jump"]:failures.append("Estado AnimationTree no salió de Start: "+current)
   if tree.get("parameters/locomotion/run/run_speed/scale")==null:failures.append("Falta parámetro runtime de velocidad de carrera")
   if tree.get("parameters/ads_layer/blend_amount")==null:failures.append("Falta parámetro runtime ADS")
  if body_visual!=null:
   var attachment:=_find_named(body_visual,"WeaponHandAttachment") as BoneAttachment3D
   if attachment==null:failures.append("No se creó BoneAttachment3D del arma")
   elif attachment.bone_name!="RightHand":failures.append("El arma no está enlazada a RightHand")
   var mounted_weapon:=_find_named(body_visual,"WeaponMount") as Node3D
   if mounted_weapon==null:failures.append("Falta WeaponMount runtime")
   else:
    var global_scale:=mounted_weapon.global_transform.basis.get_scale();print("WEAPON GLOBAL SCALE: ",global_scale)
    if global_scale.x<0.45 or global_scale.x>2.2 or global_scale.y<0.45 or global_scale.y>2.2 or global_scale.z<0.45 or global_scale.z>2.2:failures.append("Escala global del arma incoherente: "+str(global_scale))
  main.queue_free();await process_frame
 if failures.is_empty():print("ARCONT RIG: compatibility + human TPS scale + normalized hand weapon + spring-arm shoulder TPS + playing ADS AnimationTree OK");quit(0);return
 for failure in failures:push_error("ARCONT RIG: "+failure)
 quit(1)
func _is_lower_body_track(path:String)->bool:
 for token in ["Hips","UpLeg","Leg","Foot","Toe","Heel","Knee"]:
  if path.contains(token):return true
 return false
func _bone_names(skeleton:Skeleton3D)->Array[String]:
 var names:Array[String]=[]
 for i in skeleton.get_bone_count():names.append(skeleton.get_bone_name(i))
 return names
func _find_by_class(root_node:Node,wanted_class:String)->Array[Node]:
 var out:Array[Node]=[]
 if root_node.get_class()==wanted_class:out.append(root_node)
 for child in root_node.get_children():out.append_array(_find_by_class(child,wanted_class))
 return out
func _find_named(root_node:Node,wanted_name:String)->Node:
 if root_node.name==wanted_name:return root_node
 for child in root_node.get_children():
  var found:=_find_named(child,wanted_name)
  if found!=null:return found
 return null
