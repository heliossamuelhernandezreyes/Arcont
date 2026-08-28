extends SceneTree

const MAIN:=preload("res://scenes/main.tscn")
const EXPECTED_IDS:= ["12g","ar5","p9","m90","br7"]
const REQUIRED_PARTS:= ["Pump","Magazine","Slide","ScopeBody","BayonetSpine"]
const MIN_PARTS:= [8,10,6,10,9]
const MIN_LENGTH:= [1.45,1.45,0.55,2.05,1.75]
const MAX_LENGTH:= [1.95,1.90,0.90,2.65,2.30]

func _init()->void:
 call_deferred("_run")

func _run()->void:
 var scene:=MAIN.instantiate()
 root.add_child(scene)
 await process_frame
 var weapon:=scene.get_node_or_null("Player/Weapon")
 var gun:=scene.get_node_or_null("Player/BodyVisual/WeaponMount/Gun") as MeshInstance3D
 var muzzle:=scene.get_node_or_null("Player/BodyVisual/WeaponMount/MuzzleFlash") as Node3D
 if weapon==null or gun==null or muzzle==null:_fail("weapon visual nodes missing");return
 var seen:={}
 for slot in range(5):
  if slot==0:weapon._build_weapon_visual()
  else:weapon.switch_weapon(slot)
  await process_frame
  var visual_id:=String(gun.get_meta("weapon_visual_id",""))
  if visual_id!=EXPECTED_IDS[slot]:_fail("wrong visual id slot %d: %s"%[slot,visual_id]);return
  if String(gun.get_meta("art_status",""))!="ART-PASS-1-PROXY":_fail("missing art status slot %d"%slot);return
  if gun.get_child_count()<MIN_PARTS[slot]:_fail("too few silhouette parts slot %d: %d"%[slot,gun.get_child_count()]);return
  if gun.get_node_or_null(REQUIRED_PARTS[slot])==null:_fail("signature part missing slot %d: %s"%[slot,REQUIRED_PARTS[slot]]);return
  var bounds:=_bounds(gun)
  var length:=bounds.size.z
  if length<MIN_LENGTH[slot] or length>MAX_LENGTH[slot]:_fail("weapon length outside contract slot %d: %.3f m"%[slot,length]);return
  if muzzle.position.z>=bounds.position.z+0.18:_fail("muzzle is not near forward end slot %d"%slot);return
  if seen.has(visual_id):_fail("duplicate visual id %s"%visual_id);return
  seen[visual_id]=true
  print("WEAPON VISUAL slot=%d id=%s parts=%d length_m=%.3f muzzle_z=%.3f"%[slot,visual_id,gun.get_child_count(),length,muzzle.position.z])
 print("ARCONT WEAPONS: five distinct metric silhouette contracts OK")
 scene.queue_free()
 await process_frame
 quit(0)

func _bounds(parent:Node3D)->AABB:
 var first:=true
 var result:=AABB()
 for child in parent.get_children():
  if child is MeshInstance3D:
   var mi:=child as MeshInstance3D
   if mi.mesh==null:continue
   var local:=mi.get_aabb()
   var transformed:=_transform_aabb(local,mi.transform)
   if first:result=transformed;first=false
   else:result=result.merge(transformed)
 return result

func _transform_aabb(box:AABB,xform:Transform3D)->AABB:
 var corners:=PackedVector3Array()
 for x in [0.0,1.0]:
  for y in [0.0,1.0]:
   for z in [0.0,1.0]:corners.append(xform*(box.position+Vector3(box.size.x*x,box.size.y*y,box.size.z*z)))
 var minv:=corners[0];var maxv:=corners[0]
 for p in corners:minv=minv.min(p);maxv=maxv.max(p)
 return AABB(minv,maxv-minv)

func _fail(message:String)->void:
 push_error(message)
 quit(1)
