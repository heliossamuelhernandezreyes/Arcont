class_name WeaponVisualFactory
extends RefCounted

const VISUAL_IDS:= ["12g","ar5","p9","m90","br7"]
const TARGET_LENGTHS:= [1.05,0.98,0.24,1.22,1.08]
const MUZZLE_Z:= [-0.57,-0.54,-0.15,-0.66,-0.68]
const BASE:="res://assets/provisional/cc0_runtime/weapons/"
const SOURCE_PATHS:=[
 BASE+"Shotgun_1.fbx",
 BASE+"AssaultRifle2_1.fbx",
 BASE+"Pistol_1.fbx",
 BASE+"SniperRifle_1.fbx",
 BASE+"AssaultRifle_5.fbx"
]
const BAYONET_PATH:=BASE+"Bayonet.fbx"

static func build(parent:Node3D,slot:int,muzzle:Node3D=null)->void:
 parent.scale=Vector3.ONE
 for child in parent.get_children():
  parent.remove_child(child);child.queue_free()
 var i:=clampi(slot,0,VISUAL_IDS.size()-1)
 parent.set_meta("weapon_visual_id",VISUAL_IDS[i])
 parent.set_meta("art_status","CC0-PROVISIONAL")
 parent.set_meta("source_asset",SOURCE_PATHS[i])
 var ok:=_attach_metric_model(parent,SOURCE_PATHS[i],TARGET_LENGTHS[i],"CC0Model")
 if not ok:
  parent.set_meta("art_status","FALLBACK-PROXY")
  _fallback(parent,i)
 if i==4:_attach_bayonet(parent)
 if muzzle:
  var p:=muzzle.position;p.z=MUZZLE_Z[i];muzzle.position=p

static func _attach_metric_model(parent:Node3D,path:String,target_length:float,node_name:String)->bool:
 var packed:=load(path) as PackedScene
 if packed==null:return false
 var adapter:=Node3D.new();adapter.name=node_name;parent.add_child(adapter)
 var model:=packed.instantiate() as Node3D
 if model==null:parent.remove_child(adapter);adapter.queue_free();return false
 adapter.add_child(model)
 _orient_long_axis_to_z(adapter,model)
 _center_model(adapter,model)
 AssetScaleNormalizer.normalize_longest_extent(adapter,target_length)
 adapter.set_meta("source_asset",path)
 adapter.set_meta("target_length_m",target_length)
 return true

static func _orient_long_axis_to_z(adapter:Node3D,model:Node3D)->void:
 var b:=AssetScaleNormalizer.visual_bounds(adapter)
 if b.size.x>=b.size.y and b.size.x>=b.size.z:model.rotation_degrees.y=90.0
 elif b.size.y>=b.size.x and b.size.y>=b.size.z:model.rotation_degrees.x=90.0
 b=AssetScaleNormalizer.visual_bounds(adapter)
 var neg:=absf(b.position.z);var pos:=absf(b.end.z)
 if pos>neg:model.rotation_degrees.y+=180.0

static func _center_model(adapter:Node3D,model:Node3D)->void:
 var b:=AssetScaleNormalizer.visual_bounds(adapter);var c:=b.get_center();model.position+=Vector3(-c.x,-c.y,-c.z)

static func _attach_bayonet(parent:Node3D)->void:
 var holder:=Node3D.new();holder.name="BayonetMount";holder.position=Vector3(0,-0.03,-0.58);parent.add_child(holder)
 if not _attach_metric_model(holder,BAYONET_PATH,0.34,"CC0Bayonet"):
  var n:=MeshInstance3D.new();n.name="FallbackBayonet";var mesh:=BoxMesh.new();mesh.size=Vector3(0.025,0.045,0.34);n.mesh=mesh;n.position.z=-0.15;holder.add_child(n)

static func _fallback(parent:Node3D,slot:int)->void:
 var body:=MeshInstance3D.new();body.name="FallbackBody";var mesh:=BoxMesh.new();mesh.size=Vector3(0.18,0.14,TARGET_LENGTHS[slot]*0.72);body.mesh=mesh;parent.add_child(body)

static func source_path_for(slot:int)->String:return SOURCE_PATHS[clampi(slot,0,SOURCE_PATHS.size()-1)]
static func target_length_for(slot:int)->float:return TARGET_LENGTHS[clampi(slot,0,TARGET_LENGTHS.size()-1)]