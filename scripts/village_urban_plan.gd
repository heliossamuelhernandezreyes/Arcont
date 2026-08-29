class_name VillageUrbanPlan
extends RefCounted

# Non-visual planning layer. It does not alter runtime composition until a later
# visual pass consumes these parcel anchors and receives screenshot approval.

const PARCEL_SPECS: Array[Dictionary] = [
 {"id":"west_north","center":Vector3(-22.0,0.0,-20.0),"size":Vector2(18.0,18.0),"yaw":16.0,"kind":"family_house","front":"east"},
 {"id":"east_north","center":Vector3(20.0,0.0,-23.0),"size":Vector2(18.0,19.0),"yaw":-18.0,"kind":"family_house","front":"west"},
 {"id":"west_mid","center":Vector3(-25.0,0.0,8.0),"size":Vector2(17.0,18.0),"yaw":-8.0,"kind":"cottage","front":"east"},
 {"id":"east_mid","center":Vector3(24.0,0.0,9.0),"size":Vector2(18.0,18.0),"yaw":12.0,"kind":"cottage","front":"west"},
 {"id":"west_south","center":Vector3(-20.0,0.0,35.0),"size":Vector2(19.0,20.0),"yaw":18.0,"kind":"shop_house","front":"east"},
 {"id":"east_south","center":Vector3(20.0,0.0,34.0),"size":Vector2(19.0,20.0),"yaw":-14.0,"kind":"shop_house","front":"west"},
 {"id":"west_edge","center":Vector3(-37.0,0.0,25.0),"size":Vector2(20.0,23.0),"yaw":80.0,"kind":"edge_homestead","front":"south"},
 {"id":"east_edge","center":Vector3(37.0,0.0,-2.0),"size":Vector2(21.0,22.0),"yaw":96.0,"kind":"service_parcel","front":"north"}
]

const DISTRICT_ANCHORS: Array[Dictionary] = [
 {"id":"civic_square","center":Vector3(0.0,0.0,24.0),"radius":18.0,"role":"civic_commercial"},
 {"id":"stream_crossing","center":Vector3(-4.0,0.0,-35.0),"radius":14.0,"role":"transition_landmark"},
 {"id":"north_entry","center":Vector3(-4.0,0.0,-69.0),"radius":16.0,"role":"arrival"},
 {"id":"south_entry","center":Vector3(-2.0,0.0,70.0),"radius":18.0,"role":"arrival"}
]

static func parcels() -> Array[Dictionary]:
 return PARCEL_SPECS.duplicate(true)

static func anchors() -> Array[Dictionary]:
 return DISTRICT_ANCHORS.duplicate(true)

static func parcel_for_house_index(index: int) -> Dictionary:
 if index < 0 or index >= PARCEL_SPECS.size():
  return {}
 return PARCEL_SPECS[index].duplicate(true)

static func validate_plan() -> PackedStringArray:
 var warnings := PackedStringArray()
 var ids := {}
 for parcel: Dictionary in PARCEL_SPECS:
  var id: String = String(parcel.get("id", ""))
  if id.is_empty():
   warnings.append("parcel_missing_id")
  elif ids.has(id):
   warnings.append("duplicate_parcel_id:%s" % id)
  else:
   ids[id] = true
  var size: Vector2 = parcel.get("size", Vector2.ZERO)
  if size.x < 8.0 or size.y < 8.0:
   warnings.append("parcel_too_small:%s" % id)
  var center: Vector3 = parcel.get("center", Vector3.ZERO)
  if absf(center.x) > 70.0 or absf(center.z) > 90.0:
   warnings.append("parcel_outside_village_core:%s" % id)
 return warnings

static func summary() -> Dictionary:
 var kinds := {}
 for parcel: Dictionary in PARCEL_SPECS:
  var kind: String = String(parcel.get("kind", "unknown"))
  kinds[kind] = int(kinds.get(kind, 0)) + 1
 return {
  "contract":"VILLAGE-URBAN-PLAN-V1",
  "parcel_count":PARCEL_SPECS.size(),
  "district_anchor_count":DISTRICT_ANCHORS.size(),
  "parcel_kinds":kinds,
  "visual_status":"NOT_MOUNTED",
  "visual_acceptance":"PENDING_SCREENSHOT_REVIEW"
 }
