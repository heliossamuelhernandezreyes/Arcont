import bpy, bmesh, json, math, os, sys
from mathutils import Vector

TRUNK_SIDES = 8
BRANCH_SIDES = 6
TARGET_STRUCTURE_TRIS = 10000
MAX_BRANCHES = 46
MIN_OBSERVATIONS = 2
MIN_BRANCH_PATH_NODES = 3
MIN_HORIZONTAL_SPAN_RATIO = 0.014
MAX_VERTICAL_TO_HORIZONTAL = 2.6
MAX_CONNECTOR_RATIO = 0.14
SECONDARY_MIN_SUPPORT = 24
SECONDARY_MIN_SCORE = 3.4
SECONDARY_MIN_EXTENT_RATIO = 0.026
MAX_AZIMUTH_DEVIATION_DEG = 42.0
MAX_LOCAL_TURN_DEG = 100.0
MIN_RADIAL_PROGRESS_RATIO = 0.004
DUPLICATE_Z_RATIO = 0.022
DUPLICATE_AZIMUTH_DEG = 15.0

# LOD0 structure should read as a living pine rather than a pole with rays.
TRUNK_SEGMENTS = 14
TRUNK_BEND_RATIO = 0.018
TRUNK_TOP_LEAN_RATIO = 0.010
BRANCH_TWIST_DEG = 14.0
BRANCH_SAG_RATIO = 0.013
BRANCH_TIP_VARIATION_RATIO = 0.006
BIFURCATION_SEGMENTS = 2
BIFURCATION_ANGLE_DEG = 31.0
BIFURCATION_UPLIFT = 0.13


def hash01(a, b=0.0, c=0.0):
    x = math.sin(a * 12.9898 + b * 78.233 + c * 37.719) * 43758.5453
    return x - math.floor(x)


def radial(p):
    return math.hypot(p.x, p.y)


def azimuth(p):
    return math.atan2(p.y, p.x)


def angular_distance(a, b):
    d = abs(a - b) % math.tau
    return min(d, math.tau - d)


def rotate_z(v, angle):
    ca, sa = math.cos(angle), math.sin(angle)
    return Vector((v.x * ca - v.y * sa, v.x * sa + v.y * ca, v.z))


def segment_tri_cost(sides):
    return sides * 2 + (sides - 2) * 2


def cylinder_between(start, end, r0, r1, sides, name):
    a, b = Vector(start), Vector(end)
    axis = b - a
    if axis.length < 1e-5:
        return 0
    z = axis.normalized()
    helper = Vector((0, 0, 1))
    if abs(z.dot(helper)) > 0.96:
        helper = Vector((1, 0, 0))
    x = z.cross(helper).normalized()
    y = z.cross(x).normalized()
    verts, faces = [], []
    for i in range(sides):
        ang = math.tau * i / sides
        d = x * math.cos(ang) + y * math.sin(ang)
        verts.extend((a + d * r0, b + d * r1))
    for i in range(sides):
        ni = (i + 1) % sides
        faces.append((2*i, 2*ni, 2*ni+1, 2*i+1))
    faces.append(tuple(2*i for i in range(sides)))
    faces.append(tuple(2*i+1 for i in reversed(range(sides))))
    mesh = bpy.data.meshes.new(name + '_mesh')
    bm = bmesh.new()
    try:
        vs = [bm.verts.new(tuple(v)) for v in verts]
        bm.verts.ensure_lookup_table()
        for face in faces:
            try:
                bm.faces.new([vs[i] for i in face])
            except ValueError:
                pass
        bm.normal_update()
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return segment_tri_cost(sides)


def normalize_branch_path(branch):
    pts = [Vector(p) for p in branch.get('path', [])]
    if len(pts) < MIN_BRANCH_PATH_NODES:
        return []
    if radial(pts[-1]) < radial(pts[0]):
        pts.reverse()
    return pts


def clean_outward_path(branch, height):
    pts = normalize_branch_path(branch)
    if len(pts) < MIN_BRANCH_PATH_NODES:
        return []
    farthest = max(pts, key=radial)
    dominant = azimuth(farthest)
    max_dev = math.radians(MAX_AZIMUTH_DEVIATION_DEG)
    candidates = [p.copy() for p in pts if angular_distance(azimuth(p), dominant) <= max_dev]
    if len(candidates) < 2:
        return []
    candidates.sort(key=radial)
    min_progress = height * MIN_RADIAL_PROGRESS_RATIO
    kept = [candidates[0]]
    for p in candidates[1:]:
        if radial(p) > radial(kept[-1]) + min_progress:
            kept.append(p)
    if len(kept) < 2:
        return []
    filtered = [kept[0]]
    max_turn = math.radians(MAX_LOCAL_TURN_DEG)
    for i in range(1, len(kept)-1):
        a = kept[i] - filtered[-1]
        b = kept[i+1] - kept[i]
        a2, b2 = Vector((a.x,a.y,0)), Vector((b.x,b.y,0))
        if a2.length > 1e-5 and b2.length > 1e-5 and a2.angle(b2) > max_turn:
            continue
        filtered.append(kept[i])
    filtered.append(kept[-1])
    if len(filtered) >= 3:
        smoothed = [filtered[0].copy()]
        for i in range(1, len(filtered)-1):
            smoothed.append(filtered[i-1]*0.18 + filtered[i]*0.64 + filtered[i+1]*0.18)
        smoothed.append(filtered[-1].copy())
        filtered = smoothed
    return filtered


def branch_metrics(branch, height):
    pts = clean_outward_path(branch, height)
    if len(pts) < 2:
        return None
    horizontal = vertical = 0.0
    for a,b in zip(pts,pts[1:]):
        d = b-a
        horizontal += math.hypot(d.x,d.y)
        vertical += abs(d.z)
    return {
        'radial_span': radial(pts[-1])-radial(pts[0]),
        'verticality': vertical/max(horizontal,height*0.001),
    }


def branch_is_plausible(branch, height, secondary=False):
    m = branch_metrics(branch,height)
    if not m or m['radial_span'] < height*MIN_HORIZONTAL_SPAN_RATIO or m['verticality'] > MAX_VERTICAL_TO_HORIZONTAL:
        return False
    if secondary:
        return (branch.get('support',0) >= SECONDARY_MIN_SUPPORT and
                branch.get('score',0.0) >= SECONDARY_MIN_SCORE and
                branch.get('extent',0.0) >= height*SECONDARY_MIN_EXTENT_RATIO)
    return branch.get('observations',1) >= MIN_OBSERVATIONS


def trunk_radius_at_t(height, t):
    # Slight basal flare, then a smoother pine taper.
    base = 0.0195 if t < 0.12 else 0.0180
    return height * (base*(1.0-t) + 0.0048*t)


def trunk_center_at_t(height, zmin, zmax, t, seed):
    # Unlike the previous symmetric bend, this does not return to the axis at the top.
    # The compound low-frequency arc plus mild persistent lean makes the silhouette visibly organic.
    phase = seed * math.tau
    envelope = math.sin(math.pi * t)
    arc = height * TRUNK_BEND_RATIO * envelope
    lean = height * TRUNK_TOP_LEAN_RATIO * (t ** 1.45)
    lean_dir = phase * 0.73 + 0.55
    x = (arc * (0.70*math.sin(math.pi*t*1.08 + phase) + 0.30*math.sin(math.pi*t*2.15 + phase*0.41))
         + lean*math.cos(lean_dir))
    y = (arc * (0.64*math.cos(math.pi*t*0.92 + phase*0.69) + 0.36*math.sin(math.pi*t*2.35 + phase*1.13))
         + lean*math.sin(lean_dir))
    z = zmin + (zmax-zmin)*t
    return Vector((x,y,z))


def trunk_center_at_z(height,zmin,zmax,z,seed):
    t = max(0.0,min(1.0,(z-zmin)/max(1e-5,zmax-zmin)))
    return trunk_center_at_t(height,zmin,zmax,t,seed), trunk_radius_at_t(height,t)


def build_curved_trunk(variant,xoff,seed):
    h,zmin,zmax = variant['height'],variant['zmin'],variant['zmax']
    centers=[]
    for i in range(TRUNK_SEGMENTS+1):
        p=trunk_center_at_t(h,zmin,zmax,i/float(TRUNK_SEGMENTS),seed)
        p.x += xoff
        centers.append(p)
    actual=0
    for i in range(TRUNK_SEGMENTS):
        t0=i/float(TRUNK_SEGMENTS); t1=(i+1)/float(TRUNK_SEGMENTS)
        actual += cylinder_between(centers[i],centers[i+1],trunk_radius_at_t(h,t0),trunk_radius_at_t(h,t1),TRUNK_SIDES,f"{variant['name']}_trunk_{i:02d}")
    return actual


def shape_branch_path(branch,height,zmin,zmax,seed,branch_index):
    pts=clean_outward_path(branch,height)
    if len(pts)<2:
        return [],0.0
    root=pts[0]
    center,trunk_r=trunk_center_at_z(height,zmin,zmax,root.z,seed)
    outward=Vector((root.x,root.y,0))
    if outward.length<1e-5: outward=Vector((1,0,0))
    outward.normalize()
    trunk_root=center+outward*trunk_r
    connector=(root-trunk_root).length
    if connector>height*MAX_CONNECTOR_RATIO:
        return [],connector
    raw=[trunk_root]
    if connector>height*0.004:
        mid=trunk_root.lerp(root,0.52); mid.z += min(height*0.003,connector*0.05); raw.append(mid)
    raw.extend(pts)

    # Preserve the source-guided route while adding pine-like weight, torsion and asymmetry.
    shaped=[]
    n=max(1,len(raw)-1)
    twist_sign=-1.0 if hash01(branch_index,seed,height)<0.5 else 1.0
    twist_total=math.radians(BRANCH_TWIST_DEG*(0.55+0.70*hash01(branch_index+17,seed,height)))*twist_sign
    sag=height*BRANCH_SAG_RATIO*(0.55+0.75*hash01(branch_index+31,seed,height))
    tip_variation=height*BRANCH_TIP_VARIATION_RATIO*(hash01(branch_index+47,seed,height)-0.5)*2.0
    root_xy=Vector((trunk_root.x,trunk_root.y,0))
    for i,p in enumerate(raw):
        t=i/float(n)
        q=p.copy()
        if i>0:
            rel=Vector((q.x-root_xy.x,q.y-root_xy.y,0))
            rel=rotate_z(rel,twist_total*(t**1.35))
            q.x=root_xy.x+rel.x; q.y=root_xy.y+rel.y
            q.z -= sag*math.sin(math.pi*min(1.0,t))*((0.25+0.75*t))
            q.z += tip_variation*(t**2.2)
        shaped.append(q)
    return shaped,connector


def branch_priority(b):
    obs=b.get('observations',1); extent=b.get('extent',0.0); score=b.get('score',0.0); support=b.get('support',0)
    return score*max(0.25,extent)*math.log2(1.0+obs)*(1.0+min(0.30,math.log2(1.0+support)*0.03))


def branch_signature(branch,height):
    pts=clean_outward_path(branch,height)
    if len(pts)<2: return None
    return pts[0].z,azimuth(pts[-1]),radial(pts[-1])


def is_duplicate_branch(branch,selected,height):
    sig=branch_signature(branch,height)
    if sig is None: return True
    z,az,reach=sig
    for other in selected:
        osig=branch_signature(other,height)
        if osig is None: continue
        oz,oaz,oreach=osig
        if abs(z-oz)<=height*DUPLICATE_Z_RATIO and angular_distance(az,oaz)<=math.radians(DUPLICATE_AZIMUTH_DEG) and abs(reach-oreach)<=height*0.10:
            return True
    return False


def estimate_branch_tris(branch,height):
    pts=clean_outward_path(branch,height)
    return max(0,len(pts)+1)*segment_tri_cost(BRANCH_SIDES)


def select_branches(variant,trunk_tris):
    height=variant['height']
    primary=[b for b in variant.get('branches',[]) if branch_is_plausible(b,height,False)]
    secondary=[b for b in variant.get('branches',[]) if b.get('observations',1)<MIN_OBSERVATIONS and branch_is_plausible(b,height,True)]
    primary.sort(key=branch_priority,reverse=True); secondary.sort(key=branch_priority,reverse=True)
    selected=[]; used=trunk_tris; ps=ss=dup=0
    # Reserve room for bifurcations rather than spending all 10k on long primary cylinders.
    branch_budget=int(TARGET_STRUCTURE_TRIS*0.78)
    for pool,is_secondary in ((primary,False),(secondary,True)):
        for branch in pool:
            if is_duplicate_branch(branch,selected,height): dup+=1; continue
            cost=estimate_branch_tris(branch,height)
            if cost<=0 or used+cost>branch_budget: continue
            selected.append(branch); used+=cost
            if is_secondary: ss+=1
            else: ps+=1
            if len(selected)>=MAX_BRANCHES: break
        if len(selected)>=MAX_BRANCHES: break
    return selected,used,len(primary),len(secondary),ps,ss,dup


def add_bifurcations(branch_pts,h,bi,actual,variant_name):
    if len(branch_pts)<4: return actual,0
    created=0
    for fi,frac in enumerate((0.52,0.70,0.84)):
        cost=BIFURCATION_SEGMENTS*segment_tri_cost(BRANCH_SIDES)
        if actual+cost>TARGET_STRUCTURE_TRIS: break
        idx=min(len(branch_pts)-2,max(1,int((len(branch_pts)-1)*frac)))
        root=branch_pts[idx]
        tangent=branch_pts[min(len(branch_pts)-1,idx+1)]-branch_pts[max(0,idx-1)]
        if tangent.length<1e-5: continue
        tangent.normalize()
        sign=-1.0 if hash01(bi,fi,h)<0.5 else 1.0
        angle=math.radians(BIFURCATION_ANGLE_DEG*(0.72+0.52*hash01(bi+13,fi,h)))*sign
        direction=rotate_z(tangent,angle)
        direction.z += BIFURCATION_UPLIFT*(0.45+0.90*hash01(bi+29,fi,h))
        direction.normalize()
        total_len=h*(0.018+0.026*hash01(bi+43,fi,h))
        mid=root+direction*(total_len*0.55)
        bend=rotate_z(direction,angle*(0.18+0.24*hash01(bi+59,fi,h)))
        bend.z += (hash01(bi+71,fi,h)-0.42)*0.13; bend.normalize()
        tip=mid+bend*(total_len*0.45)
        base_r=h*(0.00090+0.00042*hash01(bi+83,fi,h))
        actual += cylinder_between(root,mid,base_r,base_r*0.64,BRANCH_SIDES,f"{variant_name}_b{bi:02d}_fork{fi}_0")
        actual += cylinder_between(mid,tip,base_r*0.64,h*0.00044,BRANCH_SIDES,f"{variant_name}_b{bi:02d}_fork{fi}_1")
        created+=1
    return actual,created


def build_variant(variant,xoff):
    h,zmin,zmax=variant['height'],variant['zmin'],variant['zmax']
    seed=hash01(len(variant['name']),h,zmin)
    trunk_tris=build_curved_trunk(variant,xoff,seed)
    selected,estimated,pc,sc,ps,ss,dup=select_branches(variant,trunk_tris)
    actual=trunk_tris; connected=rejected=0; max_connector=0.0; bifurcations=0; selected_ids=[]
    for bi,branch in enumerate(selected):
        pts,connector=shape_branch_path(branch,h,zmin,zmax,seed,bi)
        if not pts: rejected+=1; continue
        for p in pts: p.x += xoff
        connected+=1; max_connector=max(max_connector,connector); selected_ids.append(branch.get('id'))
        base=h*(0.0048*(1.0-min(0.85,branch.get('t',0.5))*0.50))
        seg_count=max(1,len(pts)-1)
        for si in range(seg_count):
            cost=segment_tri_cost(BRANCH_SIDES)
            if actual+cost>TARGET_STRUCTURE_TRIS: break
            f0=1.0-0.76*(si/seg_count); f1=1.0-0.76*((si+1)/seg_count)
            actual += cylinder_between(pts[si],pts[si+1],max(h*0.0010,base*f0),max(h*0.00062,base*f1),BRANCH_SIDES,f"{variant['name']}_b{bi:02d}_s{si:02d}")
        actual,made=add_bifurcations(pts,h,bi,actual,variant['name']); bifurcations+=made
    return {
        'name':variant['name'],'height':h,'primary_candidates':pc,'secondary_candidates':sc,
        'primary_selected':ps,'secondary_selected':ss,'selected_branches':len(selected),
        'connected_branches':connected,'rejected_detached':rejected,'duplicate_rejected':dup,
        'max_connector':max_connector,'estimated_tris':estimated,'actual_tris':actual,
        'selected_ids':selected_ids,'bifurcations':bifurcations,'trunk_segments':TRUNK_SEGMENTS,
        'trunk_bend_ratio':TRUNK_BEND_RATIO,'branch_twist_deg':BRANCH_TWIST_DEG,'branch_sag_ratio':BRANCH_SAG_RATIO,
        'mean_observations':sum(b.get('observations',1) for b in selected)/max(1,len(selected)),
    }


def make_material():
    mat=bpy.data.materials.new('structural_debug'); mat.diffuse_color=(0.22,0.13,0.06,1.0)
    for obj in bpy.context.scene.objects:
        if obj.type=='MESH': obj.data.materials.append(mat)


def setup_camera_and_light(variants):
    max_h=max(v['height'] for v in variants)
    total_span=sum(v['height']*0.72 for v in variants[:-1])+variants[-1]['height']*0.5
    cam_data=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cam_data)
    bpy.context.collection.objects.link(cam); bpy.context.scene.camera=cam
    target=Vector((total_span*0.42,0,max_h*0.50)); cam.location=(target.x,-max_h*2.4,target.z)
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=max_h*1.18
    light_data=bpy.data.lights.new('Sun','SUN'); light_data.energy=3.0
    light=bpy.data.objects.new('Sun',light_data); bpy.context.collection.objects.link(light); light.rotation_euler=(math.radians(35),math.radians(-20),math.radians(30))
    scene=bpy.context.scene; world=scene.world or bpy.data.worlds.new('ArcontStructuralPreviewWorld'); scene.world=world
    world.use_nodes=False; world.color=(0.08,0.08,0.08)


def render_png(path):
    scene=bpy.context.scene
    try: scene.render.engine='BLENDER_EEVEE_NEXT'
    except TypeError: scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=1400; scene.render.resolution_y=900; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.filepath=path; scene.render.film_transparent=False
    bpy.ops.render.render(write_still=True)


def main():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(argv)!=4:
        raise SystemExit('usage: blender --background --python build_pine_structural_lod0_experiment.py -- skeleton.json out.glb out.json out.png')
    src,out_glb,out_json,out_png=argv
    data=json.load(open(src,'r',encoding='utf-8')); variants=data['variants']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    reports=[]; xoff=0.0
    for variant in variants:
        reports.append(build_variant(variant,xoff)); xoff += variant['height']*0.72
    make_material(); os.makedirs(os.path.dirname(out_glb) or '.',exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out_glb,export_format='GLB')
    setup_camera_and_light(variants); render_png(out_png)
    report={
        'target_structure_tris':TARGET_STRUCTURE_TRIS,'max_branches':MAX_BRANCHES,
        'architecture':'asymmetric_curved_trunk_plus_source_guided_sagged_twisted_branches_plus_budgeted_bifurcations',
        'trunk_segments':TRUNK_SEGMENTS,'trunk_bend_ratio':TRUNK_BEND_RATIO,'trunk_top_lean_ratio':TRUNK_TOP_LEAN_RATIO,
        'branch_twist_deg':BRANCH_TWIST_DEG,'branch_sag_ratio':BRANCH_SAG_RATIO,
        'filters':{'max_azimuth_deviation_deg':MAX_AZIMUTH_DEVIATION_DEG,'max_local_turn_deg':MAX_LOCAL_TURN_DEG,
                   'min_radial_progress_ratio':MIN_RADIAL_PROGRESS_RATIO,'duplicate_z_ratio':DUPLICATE_Z_RATIO,
                   'duplicate_azimuth_deg':DUPLICATE_AZIMUTH_DEG},
        'variants':reports,
    }
    with open(out_json,'w',encoding='utf-8') as f: json.dump(report,f,indent=2)
    for r in reports:
        print(f"ARCONT_PINE_STRUCTURAL_EXPERIMENT={r['name']} connected={r['connected_branches']} primary={r['primary_selected']} secondary={r['secondary_selected']} candidates={r['primary_candidates']}+{r['secondary_candidates']} tris={r['actual_tris']} bifurcations={r['bifurcations']} duplicates={r['duplicate_rejected']} rejected_detached={r['rejected_detached']} max_connector={r['max_connector']:.3f} mean_obs={r['mean_observations']:.2f}")
    print('ARCONT_PINE_STRUCTURAL_PREVIEW=',out_png)
    print('ARCONT_PINE_STRUCTURAL_GLB=',out_glb)


if __name__=='__main__':
    main()
