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
 var environment:=main.get_node_or_null("ForestVillage") as Node3D
 if environment==null:
  environment=main.get_node_or_null("UrbanDistrict") as Node3D
 if environment==null:
  failures.append("Falta entorno métrico ForestVillage/UrbanDistrict")
 else:
  var counts:={"building":0,"vehicle":0,"prop":0,"environment":0}
  var normalized_total:=0
  for child in _all_nodes(environment):
   if not child.has_meta("metric_longest_extent_m"):
    continue
   if not child is Node3D:
    continue
   normalized_total+=1
   var klass:=String(child.get_meta("budget_class","prop"))
   counts[klass]=int(counts.get(klass,0))+1
   var target:=float(child.get_meta("metric_longest_extent_m",0.0))
   var measured:=AssetScaleNormalizer.longest_extent(child as Node3D)
   print("METRIC ASSET ",child.name," class=",klass," target=",target," measured=",measured," factor=",child.get_meta("metric_scale_factor",1.0)," source=",child.get_meta("asset_source",""))
   if target<=0.0:
    failures.append("Asset normalizado sin target: "+String(child.name))
   elif absf(measured-target)>maxf(0.10,target*0.04):
    failures.append("Escala métrica fuera de tolerancia: "+String(child.name)+" target="+str(target)+" measured="+str(measured))
  if normalized_total<30:failures.append("Muy pocos assets del entorno tienen contrato métrico: "+str(normalized_total))
  if int(counts["environment"])<12:failures.append("Muy pocos elementos estructurales normalizados: "+str(counts["environment"]))
  if int(counts["prop"])<10:failures.append("No se normalizaron suficientes props: "+str(counts["prop"]))
  var village_assets:=0
  var forest_assets:=0
  for child in _all_nodes(environment):
   if not child.has_meta("metric_longest_extent_m"):continue
   var layer:=String(child.get_meta("art_layer",""))
   if layer=="village":village_assets+=1
   if layer in ["canopy","canopy_frame","understory","ground_detail","landform","story_prop"]:forest_assets+=1
  if village_assets<8:failures.append("Faltan edificios del pueblo bajo contrato métrico: "+str(village_assets))
  if forest_assets<20:failures.append("Faltan assets forestales bajo contrato métrico: "+str(forest_assets))
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

func _all_nodes(node:Node)->Array[Node]:
 var result:Array[Node]=[node]
 for child in node.get_children():result.append_array(_all_nodes(child))
 return result

func _find_named(node:Node,wanted:String)->Node:
 if String(node.name)==wanted:return node
 for child in node.get_children():
  var found:=_find_named(child,wanted)
  if found!=null:return found
 return null
