extends SceneTree

const MAIN:=preload("res://scenes/main.tscn")
const EXPECTED_IDS:= ["12g","ar5","p9","m90","br7"]
const EXPECTED_TARGETS:= [1.05,0.98,0.24,1.22,1.08]

func _init()->void:call_deferred("_run")

func _run()->void:
 var scene:=MAIN.instantiate();root.add_child(scene);await process_frame;await process_frame
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
  if String(gun.get_meta("art_status",""))!="CC0-PROVISIONAL":_fail("CC0 model failed to load slot %d status=%s"%[slot,String(gun.get_meta("art_status",""))]);return
  var source:=String(gun.get_meta("source_asset",""))
  if source.is_empty() or not ResourceLoader.exists(source):_fail("missing source asset slot %d"%slot);return
  var model:=gun.get_node_or_null("CC0Model") as Node3D
  if model==null:_fail("CC0Model adapter missing slot %d"%slot);return
  var extent:=AssetScaleNormalizer.longest_extent(model)
  if absf(extent-EXPECTED_TARGETS[slot])>0.035:_fail("weapon metric extent slot %d: %.3f target %.3f"%[slot,extent,EXPECTED_TARGETS[slot]]);return
  if muzzle.position.z>=-0.10:_fail("muzzle not forward slot %d"%slot);return
  if slot==4 and gun.get_node_or_null("BayonetMount")==null:_fail("bayonet mount missing");return
  if seen.has(visual_id):_fail("duplicate visual id %s"%visual_id);return
  seen[visual_id]=true
  print("CC0 WEAPON slot=%d id=%s extent=%.3f source=%s"%[slot,visual_id,extent,source])
 print("ARCONT CC0 WEAPONS: five imported metric weapon visuals OK")
 scene.queue_free();await process_frame;quit(0)

func _fail(message:String)->void:push_error(message);quit(1)
