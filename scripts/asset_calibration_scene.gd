extends Node3D

const PLAYER_MODEL := "res://assets/provisional/characters/kenney_survivors/Model/characterMedium.fbx"
const CAR_MODEL := "res://assets/provisional/city/car_police.fbx"
const BUILDING_MODEL := "res://assets/provisional/city/building_A.fbx"

func _ready() -> void:
 _reference_box("HumanHeight",Vector3(-5.5,0.89,0),Vector3(0.55,1.78,0.35),Color(0.34,0.55,0.80))
 _reference_box("Door",Vector3(-3.7,1.05,0),Vector3(1.0,2.10,0.16),Color(0.55,0.58,0.62))
 _reference_box("WaistCover",Vector3(-2.0,0.5,0),Vector3(1.8,1.0,0.55),Color(0.45,0.48,0.50))
 _reference_box("HighCover",Vector3(0.0,0.75,0),Vector3(1.8,1.5,0.55),Color(0.40,0.43,0.46))
 _spawn_normalized(PLAYER_MODEL,Vector3(2.0,0,0),1.78,"human")
 _spawn_normalized(CAR_MODEL,Vector3(5.0,0,0),4.5,"vehicle")
 _spawn_normalized(BUILDING_MODEL,Vector3(10.0,0,0),16.0,"building")

func _spawn_normalized(path:String,pos:Vector3,target:float,kind:String)->Node3D:
 var packed:=load(path) as PackedScene
 if packed==null:return null
 var instance:=packed.instantiate() as Node3D
 if instance==null:return null
 instance.position=pos
 instance.set_meta("calibration_kind",kind)
 instance.set_meta("asset_source",path)
 add_child(instance)
 AssetScaleNormalizer.normalize_longest_extent(instance,target)
 return instance

func _reference_box(node_name:String,pos:Vector3,size:Vector3,color:Color)->void:
 var mesh_instance:=MeshInstance3D.new()
 mesh_instance.name=node_name
 mesh_instance.position=pos
 var mesh:=BoxMesh.new();mesh.size=size;mesh_instance.mesh=mesh
 var material:=StandardMaterial3D.new();material.albedo_color=color;material.roughness=0.86;mesh_instance.material_override=material
 add_child(mesh_instance)
