extends Node3D

var terrain: Node
var soil: StandardMaterial3D
var worn: StandardMaterial3D

func _ready() -> void:
 call_deferred("_apply")

func _apply() -> void:
 terrain = get_parent().get_node_or_null("ForestTerrainRelief")
 if terrain == null or not terrain.has_method("get_height_at"):
  return
 soil = _mat(Color(0.075,0.062,0.040),0.99)
 worn = _mat(Color(0.115,0.095,0.060),0.98)
 _hide_surface("VillageApron_ContinuousSurface")
 _hide_surface("VillageSquare_ContinuousSurface")
 _patch("BellTowerForecourt",Vector3(-7,0,23),Vector2(11.0,8.0),worn,0.028)
 _patch("WellPocket",Vector3(7,0,24),Vector2(8.0,7.0),soil,0.026)
 _patch("GeneratorPocket",Vector3(-8,0,29),Vector2(8.5,6.0),soil,0.025)
 _patch("CrossroadsWear",Vector3(0,0,12),Vector2(10.0,6.5),worn,0.024)
 set_meta("art_status","ART-PASS-16-VILLAGE-SURFACE-CLEANUP")
 set_meta("collision_owner","ForestTerrainRelief")

func _hide_surface(surface_name: String) -> void:
 var node := get_parent().get_node_or_null("ContinuousRouteSurfacePass/%s" % surface_name) as GeometryInstance3D
 if node != null:
  node.visible = false

func _patch(name_text: String,center: Vector3,size: Vector2,material: Material,offset: float) -> void:
 var st := SurfaceTool.new()
 st.begin(Mesh.PRIMITIVE_TRIANGLES)
 var hx := size.x*0.5
 var hz := size.y*0.5
 var p := [Vector3(center.x-hx+0.6,0,center.z-hz),Vector3(center.x+hx,0,center.z-hz+0.4),Vector3(center.x+hx-0.5,0,center.z+hz),Vector3(center.x-hx,0,center.z+hz-0.7)]
 for i: int in range(4):
  p[i].y = _height(p[i].x,p[i].z)+offset
 _tri(st,p[0],p[1],p[2])
 _tri(st,p[0],p[2],p[3])
 st.generate_normals()
 var node := MeshInstance3D.new()
 node.name = name_text
 node.mesh = st.commit()
 node.material_override = material
 node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 node.set_meta("art_layer","worn_village_ground")
 node.set_meta("terrain_grounded",true)
 add_child(node)

func _tri(st: SurfaceTool,a: Vector3,b: Vector3,c: Vector3) -> void:
 st.set_uv(Vector2(a.x,a.z)*0.18); st.add_vertex(a)
 st.set_uv(Vector2(b.x,b.z)*0.18); st.add_vertex(b)
 st.set_uv(Vector2(c.x,c.z)*0.18); st.add_vertex(c)

func _height(x: float,z: float) -> float:
 return float(terrain.call("get_height_at",x,z))

func _mat(color: Color,roughness: float) -> StandardMaterial3D:
 var m := StandardMaterial3D.new()
 m.albedo_color = color
 m.roughness = roughness
 return m
