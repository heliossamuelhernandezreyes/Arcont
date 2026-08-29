extends Node3D

# ART-PASS-11: settlement structure authored as thin terrain-following ribbons,
# not visible BoxMesh plates. ForestTerrainRelief remains the collision owner.

var terrain: Node
var sidewalk_material: StandardMaterial3D
var curb_material: StandardMaterial3D
var driveway_material: StandardMaterial3D
var verge_material: StandardMaterial3D

func _ready() -> void:
 call_deferred("_build")

func _build() -> void:
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 if terrain == null or not terrain.has_method("get_height_at"):
  return
 sidewalk_material = _make_material(Color(0.245,0.245,0.225),0.98)
 curb_material = _make_material(Color(0.165,0.17,0.16),1.0)
 driveway_material = _make_material(Color(0.125,0.105,0.078),1.0)
 verge_material = _make_material(Color(0.105,0.125,0.060),0.99)
 _build_core_edges()
 _build_driveways()
 _build_verges()
 set_meta("map_contract","VILLAGE-URBAN-STRUCTURE-V2")
 set_meta("visual_status","IMPLEMENTED_PENDING_CAPTURE_REVIEW")
 set_meta("collision_owner","ForestTerrainRelief")
 set_meta("representation","terrain_sampled_surface_ribbons")
 set_meta("mobile_validation","PENDING")

func _make_material(color: Color, roughness: float) -> StandardMaterial3D:
 var material := StandardMaterial3D.new()
 material.albedo_color = color
 material.roughness = roughness
 return material

func _build_core_edges() -> void:
 _ribbon("CivicWalkWest",Vector3(-7.2,0,23.0),Vector3(0,0,1),29.0,2.0,sidewalk_material,0.026)
 _ribbon("CivicWalkEast",Vector3(7.2,0,23.0),Vector3(0,0,1),29.0,2.0,sidewalk_material,0.026)
 _ribbon("CivicCrossing",Vector3(0,0,10.5),Vector3(1,0,0),12.2,2.3,sidewalk_material,0.030)
 _ribbon("CurbWestCore",Vector3(-5.8,0,23.0),Vector3(0,0,1),31.0,0.24,curb_material,0.040)
 _ribbon("CurbEastCore",Vector3(5.8,0,23.0),Vector3(0,0,1),31.0,0.24,curb_material,0.040)

func _build_driveways() -> void:
 var parcels: Array[Dictionary] = VillageUrbanPlan.parcels()
 for parcel: Dictionary in parcels:
  var center: Vector3 = parcel.get("center",Vector3.ZERO)
  var front: String = String(parcel.get("front","east"))
  var parcel_id: String = String(parcel.get("id","parcel"))
  var direction := Vector3(1,0,0)
  if front == "west": direction = Vector3(-1,0,0)
  elif front == "north": direction = Vector3(0,0,-1)
  elif front == "south": direction = Vector3(0,0,1)
  var drive_center := center + direction * 5.0
  _ribbon("%s_Driveway" % parcel_id,drive_center,direction,6.5,2.6,driveway_material,0.022)

func _build_verges() -> void:
 _ribbon("SouthVergeWest",Vector3(-10.8,0,50),Vector3(0,0,1),31.0,4.4,verge_material,0.014)
 _ribbon("SouthVergeEast",Vector3(10.8,0,50),Vector3(0,0,1),31.0,4.4,verge_material,0.014)
 _ribbon("NorthVergeWest",Vector3(-10.2,0,-30),Vector3(0,0,1),30.0,4.0,verge_material,0.014)
 _ribbon("NorthVergeEast",Vector3(10.2,0,-30),Vector3(0,0,1),30.0,4.0,verge_material,0.014)

func _ribbon(name_text: String, center: Vector3, direction: Vector3, length: float, width: float, material: Material, y_offset: float) -> void:
 var forward := direction.normalized()
 var right := Vector3(-forward.z,0,forward.x)
 var steps: int = maxi(2,ceili(length / 1.8))
 var st := SurfaceTool.new()
 st.begin(Mesh.PRIMITIVE_TRIANGLES)
 for i: int in range(steps):
  var t0 := float(i) / float(steps) - 0.5
  var t1 := float(i + 1) / float(steps) - 0.5
  var a_center := center + forward * (t0 * length)
  var b_center := center + forward * (t1 * length)
  var a_l := _sample(a_center - right * width * 0.5,y_offset)
  var a_r := _sample(a_center + right * width * 0.5,y_offset)
  var b_l := _sample(b_center - right * width * 0.5,y_offset)
  var b_r := _sample(b_center + right * width * 0.5,y_offset)
  _tri(st,a_l,a_r,b_r)
  _tri(st,a_l,b_r,b_l)
 st.generate_normals()
 var mesh := st.commit()
 if mesh == null:
  return
 var node := MeshInstance3D.new()
 node.name = name_text
 node.mesh = mesh
 node.material_override = material
 node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 node.visibility_range_end = 150.0
 node.visibility_range_end_margin = 8.0
 node.set_meta("art_layer","urban_structure")
 node.set_meta("terrain_grounded",true)
 node.set_meta("visual_only",true)
 node.set_meta("terrain_sample_source","ForestTerrainRelief.get_height_at")
 add_child(node)

func _sample(point: Vector3, offset: float) -> Vector3:
 return Vector3(point.x,_height(point.x,point.z)+offset,point.z)

func _tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3) -> void:
 st.set_uv(Vector2(a.x,a.z)*0.16); st.add_vertex(a)
 st.set_uv(Vector2(b.x,b.z)*0.16); st.add_vertex(b)
 st.set_uv(Vector2(c.x,c.z)*0.16); st.add_vertex(c)

func _height(x: float, z: float) -> float:
 return float(terrain.call("get_height_at",x,z))
