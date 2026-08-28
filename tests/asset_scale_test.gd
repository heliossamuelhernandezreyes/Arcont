extends SceneTree

func _init() -> void:
 var failures:Array[String]=[]
 var packed:=load("res://scenes/main.tscn") as PackedScene
 if packed==null:
  push_error("ARCONT SCALE: no se pudo cargar main")
  quit(1)
  return
 var main:=packed.instantiate()
 root.add_child(main)
 await process_frame
 await process_frame
 var district:=main.get_node_or_null("UrbanDistrict") as Node3D
 if district==null:
  failures.append("Falta UrbanDistrict")
 else:
  var counts:={"building":0,"vehicle":0,"prop":0}
  for child in district.get_children():
   if not child.has_meta("metric_longest_extent_m"):
    continue
   var klass:=String(child.get_meta("budget_class","prop"))
   counts[klass]=int(counts.get(klass,0))+1
   var target:=float(child.get_meta("metric_longest_extent_m",0.0))
   var measured:=AssetScaleNormalizer.longest_extent(child as Node3D)
   print("METRIC ASSET ",child.name," class=",klass," target=",target," measured=",measured," factor=",child.get_meta("metric_scale_factor",1.0)," source=",child.get_meta("asset_source",""))
   if target<=0.0:
    failures.append("Asset normalizado sin target: "+String(child.name))
   elif absf(measured-target)>maxf(0.10,target*0.04):
    failures.append("Escala métrica fuera de tolerancia: "+String(child.name)+" target="+str(target)+" measured="+str(measured))
  if int(counts["building"])<18:failures.append("No se normalizaron todos los edificios: "+str(counts["building"]))
  if int(counts["vehicle"])<6:failures.append("No se normalizaron todos los vehículos: "+str(counts["vehicle"]))
  if int(counts["prop"])<10:failures.append("No se normalizaron suficientes props: "+str(counts["prop"]))
 var operator:=main.get_node_or_null("Player/BodyVisual/OperatorModel") as Node3D
 if operator==null:failures.append("Falta OperatorModel")
 else:
  var s:=operator.scale
  if s.x<0.005 or s.x>0.02 or absf(s.x-s.y)>0.0001 or absf(s.x-s.z)>0.0001:failures.append("Escala de importación del operador fuera de contrato: "+str(s))
 var weapon_mount:=_find_named(main,"WeaponMount") as Node3D
 if weapon_mount==null:failures.append("Falta WeaponMount")
 else:
  var gs:=weapon_mount.global_transform.basis.get_scale()
  print("METRIC WEAPON GLOBAL SCALE: ",gs)
  if gs.x<0.25 or gs.x>4.0 or gs.y<0.25 or gs.y>4.0 or gs.z<0.25 or gs.z>4.0:failures.append("Escala global del arma fuera de contrato: "+str(gs))
 main.queue_free()
 await process_frame
 if failures.is_empty():
  print("ARCONT SCALE: metric asset contracts OK")
  quit(0)
  return
 for failure in failures:push_error("ARCONT SCALE: "+failure)
 quit(1)

func _find_named(node:Node,wanted:String)->Node:
 if String(node.name)==wanted:return node
 for child in node.get_children():
  var found:=_find_named(child,wanted)
  if found!=null:return found
 return null
