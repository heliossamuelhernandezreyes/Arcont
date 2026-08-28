class_name WeaponVisualFactory
extends RefCounted

# ART-PASS-1 silhouette builder for the five gameplay weapons.
# This is intentionally independent from ballistics so authored GLB scenes can
# replace these meshes later without changing weapon mechanics.

const VISUAL_IDS:= ["12g","ar5","p9","m90","br7"]
const MUZZLE_Z:= [-1.10,-1.02,-0.50,-1.46,-1.23]

static func build(parent:Node3D,slot:int,muzzle:Node3D=null)->void:
 for child in parent.get_children():child.queue_free()
 parent.set_meta("weapon_visual_id",VISUAL_IDS[clampi(slot,0,VISUAL_IDS.size()-1)])
 parent.set_meta("art_status","ART-PASS-1-PROXY")
 if muzzle:
  var p:=muzzle.position;p.z=MUZZLE_Z[clampi(slot,0,MUZZLE_Z.size()-1)];muzzle.position=p
 var mats:=_materials()
 match slot:
  0:_shotgun(parent,mats)
  1:_ar5(parent,mats)
  2:_p9(parent,mats)
  3:_m90(parent,mats)
  _:_br7(parent,mats)

static func _materials()->Dictionary:
 return {
  "gunmetal":_mat(Color(0.075,0.085,0.095),0.72,0.30),
  "dark":_mat(Color(0.018,0.022,0.027),0.55,0.48),
  "polymer":_mat(Color(0.075,0.085,0.078),0.0,0.76),
  "olive":_mat(Color(0.19,0.22,0.15),0.05,0.70),
  "hazard":_mat(Color(0.42,0.19,0.055),0.22,0.58),
  "blade":_mat(Color(0.43,0.47,0.50),0.86,0.22),
  "optic":_mat(Color(0.025,0.045,0.055),0.16,0.16)
 }

static func _shotgun(p:Node3D,m:Dictionary)->void:
 _box(p,"Receiver",Vector3(0,0,0.02),Vector3(0.22,0.17,0.50),m.gunmetal)
 _box(p,"Stock",Vector3(0,-0.015,0.47),Vector3(0.20,0.16,0.46),m.polymer)
 _box(p,"StockPad",Vector3(0,-0.01,0.72),Vector3(0.21,0.18,0.07),m.dark)
 _cyl(p,"Barrel",Vector3(0,0.045,-0.63),0.034,0.98,m.dark)
 _cyl(p,"Tube",Vector3(0,-0.045,-0.56),0.030,0.82,m.gunmetal)
 _box(p,"Pump",Vector3(0,-0.07,-0.38),Vector3(0.19,0.13,0.30),m.hazard)
 _box(p,"HeatShield",Vector3(0,0.095,-0.34),Vector3(0.14,0.035,0.44),m.gunmetal)
 _box(p,"RearSight",Vector3(0,0.12,0.08),Vector3(0.08,0.05,0.06),m.dark)
 _box(p,"FrontSight",Vector3(0,0.105,-0.94),Vector3(0.035,0.055,0.035),m.hazard)

static func _ar5(p:Node3D,m:Dictionary)->void:
 _box(p,"UpperReceiver",Vector3(0,0.035,0.02),Vector3(0.20,0.12,0.45),m.gunmetal)
 _box(p,"LowerReceiver",Vector3(0,-0.065,0.05),Vector3(0.18,0.12,0.34),m.dark)
 _box(p,"Stock",Vector3(0,-0.01,0.48),Vector3(0.18,0.15,0.42),m.olive)
 _box(p,"ButtPad",Vector3(0,-0.01,0.72),Vector3(0.19,0.18,0.06),m.dark)
 _box(p,"Handguard",Vector3(0,0.02,-0.38),Vector3(0.18,0.15,0.48),m.olive)
 _cyl(p,"Barrel",Vector3(0,0.025,-0.78),0.027,0.54,m.dark)
 _cyl(p,"MuzzleDevice",Vector3(0,0.025,-1.00),0.040,0.13,m.gunmetal)
 _box(p,"Magazine",Vector3(0,-0.20,0.00),Vector3(0.13,0.31,0.18),m.dark,Vector3(-8,0,0))
 _box(p,"Grip",Vector3(0,-0.19,0.27),Vector3(0.13,0.28,0.13),m.polymer,Vector3(-14,0,0))
 _box(p,"TopRail",Vector3(0,0.115,-0.13),Vector3(0.11,0.035,0.58),m.dark)
 _box(p,"CompactOptic",Vector3(0,0.18,-0.06),Vector3(0.11,0.10,0.18),m.optic)

static func _p9(p:Node3D,m:Dictionary)->void:
 _box(p,"Slide",Vector3(0,0.055,-0.08),Vector3(0.16,0.105,0.39),m.gunmetal)
 _box(p,"Frame",Vector3(0,-0.025,-0.03),Vector3(0.15,0.105,0.31),m.dark)
 _box(p,"Grip",Vector3(0,-0.19,0.11),Vector3(0.145,0.29,0.16),m.polymer,Vector3(-10,0,0))
 _box(p,"MagazineBase",Vector3(0,-0.35,0.14),Vector3(0.155,0.045,0.18),m.dark)
 _cyl(p,"Barrel",Vector3(0,0.055,-0.34),0.021,0.22,m.dark)
 _box(p,"RearSight",Vector3(0,0.13,0.04),Vector3(0.10,0.045,0.045),m.dark)
 _box(p,"FrontSight",Vector3(0,0.13,-0.27),Vector3(0.035,0.045,0.035),m.hazard)

static func _m90(p:Node3D,m:Dictionary)->void:
 _box(p,"Receiver",Vector3(0,0.025,0.02),Vector3(0.20,0.15,0.55),m.gunmetal)
 _box(p,"Chassis",Vector3(0,-0.05,0.30),Vector3(0.20,0.16,0.50),m.olive)
 _box(p,"Stock",Vector3(0,-0.02,0.72),Vector3(0.18,0.15,0.42),m.polymer)
 _box(p,"CheekRest",Vector3(0,0.105,0.58),Vector3(0.16,0.07,0.28),m.olive)
 _cyl(p,"LongBarrel",Vector3(0,0.035,-0.91),0.025,1.28,m.dark)
 _cyl(p,"MuzzleBrake",Vector3(0,0.035,-1.43),0.046,0.17,m.gunmetal)
 _cyl(p,"ScopeBody",Vector3(0,0.19,-0.10),0.048,0.46,m.dark)
 _cyl(p,"ScopeFront",Vector3(0,0.19,-0.35),0.068,0.10,m.optic)
 _cyl(p,"ScopeRear",Vector3(0,0.19,0.15),0.060,0.10,m.optic)
 _box(p,"Bolt",Vector3(0.14,0.05,0.07),Vector3(0.18,0.045,0.055),m.gunmetal)
 _box(p,"Magazine",Vector3(0,-0.18,0.02),Vector3(0.13,0.27,0.16),m.dark)

static func _br7(p:Node3D,m:Dictionary)->void:
 _box(p,"Receiver",Vector3(0,0.02,0.02),Vector3(0.21,0.16,0.53),m.gunmetal)
 _box(p,"Stock",Vector3(0,-0.01,0.50),Vector3(0.19,0.15,0.45),m.polymer)
 _box(p,"Handguard",Vector3(0,0.015,-0.40),Vector3(0.18,0.15,0.52),m.olive)
 _cyl(p,"Barrel",Vector3(0,0.025,-0.84),0.027,0.58,m.dark)
 _box(p,"Magazine",Vector3(0,-0.20,0.02),Vector3(0.13,0.31,0.18),m.dark,Vector3(-7,0,0))
 _box(p,"Grip",Vector3(0,-0.19,0.28),Vector3(0.13,0.27,0.13),m.polymer,Vector3(-13,0,0))
 _box(p,"TopRail",Vector3(0,0.115,-0.10),Vector3(0.11,0.035,0.62),m.dark)
 _box(p,"BayonetSpine",Vector3(0,-0.015,-1.14),Vector3(0.045,0.055,0.48),m.blade)
 _box(p,"BayonetTip",Vector3(0,-0.015,-1.40),Vector3(0.025,0.035,0.16),m.blade,Vector3(0,0,0))
 _box(p,"FrontSight",Vector3(0,0.12,-0.91),Vector3(0.05,0.07,0.05),m.hazard)

static func _mat(color:Color,metallic:float,roughness:float)->StandardMaterial3D:
 var mat:=StandardMaterial3D.new();mat.albedo_color=color;mat.metallic=metallic;mat.roughness=roughness;return mat

static func _box(parent:Node3D,node_name:String,pos:Vector3,size:Vector3,mat:Material,rotation:=Vector3.ZERO)->void:
 var n:=MeshInstance3D.new();n.name=node_name;var mesh:=BoxMesh.new();mesh.size=size;n.mesh=mesh;n.material_override=mat;n.position=pos;n.rotation_degrees=rotation;n.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON;parent.add_child(n)

static func _cyl(parent:Node3D,node_name:String,pos:Vector3,radius:float,height:float,mat:Material)->void:
 var n:=MeshInstance3D.new();n.name=node_name;var mesh:=CylinderMesh.new();mesh.top_radius=radius;mesh.bottom_radius=radius;mesh.height=height;mesh.radial_segments=12;n.mesh=mesh;n.material_override=mat;n.position=pos;n.rotation_degrees.x=90.0;n.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON;parent.add_child(n)
