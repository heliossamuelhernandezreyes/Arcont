import bpy, bmesh, json, math, os, sys
from mathutils import Vector

TARGET_FOLIAGE_TRIS = 14400
TARGET_POINTS = 2400
SPRITE_TRIS_PER_POINT = 2
MESH_POINTS = 1200
MESH_TRIS_PER_POINT = 8  # two tetrahedral needle clusters
POSITION_JITTER = 0.055
SPRITE_LENGTH_MIN = 0.18
SPRITE_LENGTH_MAX = 0.36
SPRITE_WIDTH_MIN = 0.08
SPRITE_WIDTH_MAX = 0.16
NEEDLE_LENGTH_MIN = 0.11
NEEDLE_LENGTH_MAX = 0.24
NEEDLE_BASE_MIN = 0.012
NEEDLE_BASE_MAX = 0.028

UV_VARIANTS = (
    (0.03, 0.08, 0.70, 0.92),
    (0.30, 0.08, 0.97, 0.92),
    (0.12, 0.02, 0.88, 0.72),
    (0.12, 0.28, 0.88, 0.98),
    (0.02, 0.02, 0.98, 0.98),
)


def hash01(a, b=0.0, c=0.0):
    x = math.sin(a * 12.9898 + b * 78.233 + c * 37.719) * 43758.5453
    return x - math.floor(x)


def local_frame(direction):
    along = direction.normalized() if direction.length > 1e-6 else Vector((1, 0, 0))
    side = along.cross(Vector((0, 0, 1)))
    if side.length < 1e-5:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(along)
    if up.length < 1e-5:
        up = Vector((0, 0, 1))
    up.normalize()
    return along, side, up


def choose_points(points, target):
    if len(points) <= target:
        return list(points)
    weighted = sorted(
        enumerate(points),
        key=lambda kv: (-float(kv[1].get('density', 0.0)), kv[1]['position'][2], math.atan2(kv[1]['position'][1], kv[1]['position'][0])),
    )
    dense_n = min(target // 2, len(weighted))
    chosen = [p for _, p in weighted[:dense_n]]
    remainder = [p for _, p in weighted[dense_n:]]
    need = target - len(chosen)
    if need > 0 and remainder:
        stride = len(remainder) / float(need)
        chosen.extend(remainder[min(len(remainder)-1, int((i + 0.5) * stride))] for i in range(need))
    return chosen[:target]


def add_sprite(bm, uv_layer, center, along, width_axis, length, width, uv_rect, flip_u=False):
    along = along.normalized(); width_axis = width_axis.normalized()
    hl, hw = length * 0.5, width * 0.5
    corners = [
        center - along*hl - width_axis*hw,
        center + along*hl - width_axis*hw,
        center + along*hl + width_axis*hw,
        center - along*hl + width_axis*hw,
    ]
    verts = [bm.verts.new(tuple(v)) for v in corners]
    face = bm.faces.new(verts)
    u0, v0, u1, v1 = uv_rect
    if flip_u: u0, u1 = u1, u0
    for loop, uv in zip(face.loops, ((u0,v0),(u1,v0),(u1,v1),(u0,v1))):
        loop[uv_layer].uv = uv
    return 2


def add_tetra_needle(bm, root, direction, length, base_radius, roll):
    along, side, up = local_frame(direction)
    ca, sa = math.cos(roll), math.sin(roll)
    s = side * ca + up * sa
    u = -side * sa + up * ca
    tip = root + along * length
    b0 = root + s * base_radius
    b1 = root + (-s * 0.5 + u * 0.8660254) * base_radius
    b2 = root + (-s * 0.5 - u * 0.8660254) * base_radius
    v0, v1, v2, vt = [bm.verts.new(tuple(v)) for v in (b0,b1,b2,tip)]
    bm.faces.new((v0,v1,v2))
    bm.faces.new((v0,v1,vt))
    bm.faces.new((v1,v2,vt))
    bm.faces.new((v2,v0,vt))
    return 4


def point_basis(src, i, xoff):
    center = Vector(src['position']); center.x += xoff
    density = max(0.0, min(1.0, float(src.get('density', 0.5))))
    radial = Vector((src['direction'][0], src['direction'][1], 0.0))
    if radial.length < 1e-5: radial = Vector((1,0,0))
    radial.normalize(); tangential = Vector((-radial.y, radial.x, 0.0))
    h0, h1, h2 = hash01(i,1,density), hash01(i,2,density), hash01(i,3,density)
    center += radial * ((h0-.5)*POSITION_JITTER) + tangential * ((h1-.5)*POSITION_JITTER)
    center.z += (h2-.5)*POSITION_JITTER
    direction = (radial*(0.58+0.22*hash01(i,4,density)) + tangential*((hash01(i,5,density)-.5)*0.36) + Vector((0,0,0.08+0.22*(hash01(i,6,density)-.5)))).normalized()
    return center, direction, density


def build_hybrid_foliage(variant, xoff):
    selected = choose_points(variant.get('points', []), TARGET_POINTS)
    sprite_mesh = bpy.data.meshes.new(variant['name'] + '_hybrid_sprites_mesh')
    needle_mesh = bpy.data.meshes.new(variant['name'] + '_hybrid_needles_mesh')
    sbm = bmesh.new(); nbm = bmesh.new(); uv = sbm.loops.layers.uv.new('UVMap')
    sprite_tris = mesh_tris = 0
    records = []
    try:
        for i, src in enumerate(selected):
            center, direction, density = point_basis(src, i, xoff)
            along, side, up = local_frame(direction)
            dense_scale = 0.92 + 0.34*math.sqrt(density)
            length = (SPRITE_LENGTH_MIN + (SPRITE_LENGTH_MAX-SPRITE_LENGTH_MIN)*hash01(i,11,density))*dense_scale
            width = (SPRITE_WIDTH_MIN + (SPRITE_WIDTH_MAX-SPRITE_WIDTH_MIN)*hash01(i,12,density))*dense_scale
            fan = (hash01(i,13,density)-.5)*math.radians(70)
            width_axis = (side*math.cos(fan)+up*math.sin(fan)).normalized()
            uv_i = min(len(UV_VARIANTS)-1, int(hash01(i,14,density)*len(UV_VARIANTS)))
            sprite_tris += add_sprite(sbm, uv, center, along, width_axis, length, width, UV_VARIANTS[uv_i], hash01(i,15,density)>.5)

            has_mesh = i < MESH_POINTS
            if has_mesh:
                needle_len = NEEDLE_LENGTH_MIN + (NEEDLE_LENGTH_MAX-NEEDLE_LENGTH_MIN)*(0.35+0.65*density)
                base = NEEDLE_BASE_MIN + (NEEDLE_BASE_MAX-NEEDLE_BASE_MIN)*(0.25+0.75*density)
                # Two real 3D tetrahedral needle volumes share the exact same source point as the sprite.
                d0 = (along + side*((hash01(i,21,density)-.5)*0.45) + up*((hash01(i,22,density)-.5)*0.30)).normalized()
                d1 = (along + side*((hash01(i,23,density)-.5)*0.55) + up*((hash01(i,24,density)-.5)*0.34)).normalized()
                mesh_tris += add_tetra_needle(nbm, center - along*needle_len*0.18, d0, needle_len, base, hash01(i,25,density)*math.tau)
                mesh_tris += add_tetra_needle(nbm, center + along*needle_len*0.06, d1, needle_len*0.86, base*0.82, hash01(i,26,density)*math.tau)

            records.append({
                'position':[round(center.x,5),round(center.y,5),round(center.z,5)],
                'direction':[round(along.x,5),round(along.y,5),round(along.z,5)],
                'density':round(density,5),'sprite':True,'mesh3d':has_mesh,'uv_variant':uv_i,
            })
        sbm.normal_update(); nbm.normal_update(); sbm.to_mesh(sprite_mesh); nbm.to_mesh(needle_mesh)
    finally:
        sbm.free(); nbm.free()
    sprite_mesh.update(); needle_mesh.update()
    sprite_obj = bpy.data.objects.new(variant['name'] + '_hybrid_sprites', sprite_mesh)
    needle_obj = bpy.data.objects.new(variant['name'] + '_hybrid_needles', needle_mesh)
    bpy.context.collection.objects.link(sprite_obj); bpy.context.collection.objects.link(needle_obj)
    return sprite_obj, needle_obj, {
        'name':variant['name'],'source_points':len(variant.get('points',[])),'hybrid_points':len(selected),
        'sprite_points':len(selected),'mesh3d_points':min(MESH_POINTS,len(selected)),
        'sprite_tris':sprite_tris,'mesh3d_tris':mesh_tris,'total_tris':sprite_tris+mesh_tris,'points':records,
    }


def make_sprite_material(diff_path, alpha_path):
    mat = bpy.data.materials.new('pine_hybrid_sprite_atlas'); mat.use_nodes = True
    if hasattr(mat,'surface_render_method'): mat.surface_render_method='DITHERED'
    elif hasattr(mat,'blend_method'): mat.blend_method='CLIP'
    nodes=mat.node_tree.nodes; links=mat.node_tree.links
    for n in list(nodes): nodes.remove(n)
    out=nodes.new('ShaderNodeOutputMaterial'); bsdf=nodes.new('ShaderNodeBsdfPrincipled')
    tex=nodes.new('ShaderNodeTexImage'); alpha=nodes.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(diff_path); alpha.image=bpy.data.images.load(alpha_path); alpha.image.colorspace_settings.name='Non-Color'
    links.new(tex.outputs['Color'],bsdf.inputs['Base Color']); links.new(alpha.outputs['Color'],bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value=.74; links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    return mat


def make_mesh_material():
    mat=bpy.data.materials.new('pine_hybrid_3d_needles'); mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value=(0.075,0.20,0.055,1.0); bsdf.inputs['Roughness'].default_value=.82
    return mat


def setup_preview(objects):
    coords=[obj.matrix_world@Vector(c) for obj in objects for c in obj.bound_box]
    mins=Vector((min(p.x for p in coords),min(p.y for p in coords),min(p.z for p in coords)))
    maxs=Vector((max(p.x for p in coords),max(p.y for p in coords),max(p.z for p in coords)))
    center=(mins+maxs)*.5; extent=maxs-mins
    cam_data=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cam_data); bpy.context.collection.objects.link(cam); bpy.context.scene.camera=cam
    cam.location=(center.x,center.y-max(extent.z*2.25,extent.x*1.7),center.z); cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO'; cam.data.ortho_scale=max(extent.z*1.18,extent.x/(1500/900)*1.18)
    ld=bpy.data.lights.new('Sun','SUN'); ld.energy=2.3; light=bpy.data.objects.new('Sun',ld); bpy.context.collection.objects.link(light); light.rotation_euler=(math.radians(35),math.radians(-25),math.radians(25))
    world=bpy.context.scene.world or bpy.data.worlds.new('ArcontHybridPineWorld'); bpy.context.scene.world=world; world.use_nodes=False; world.color=(.055,.065,.055)


def render_png(path):
    scene=bpy.context.scene
    try: scene.render.engine='BLENDER_EEVEE_NEXT'
    except TypeError: scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=1500; scene.render.resolution_y=900; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.filepath=path; bpy.ops.render.render(write_still=True)


def main():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(argv)!=7:
        raise SystemExit('usage: blender --background --python build_pine_foliage_lod0_experiment.py -- foliage_volume.json structural.glb twig_diff twig_alpha out.glb out.json out.png')
    volume_path,structural_glb,diff_path,alpha_path,out_glb,out_json,out_png=argv
    volume=json.load(open(volume_path,'r',encoding='utf-8'))
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=structural_glb)
    structural=[o for o in bpy.context.scene.objects if o.type=='MESH']
    sprite_mat=make_sprite_material(diff_path,alpha_path); mesh_mat=make_mesh_material()
    xoff=0.0; stats=[]; foliage=[]
    for variant in volume['variants']:
        sprite_obj,needle_obj,st=build_hybrid_foliage(variant,xoff)
        sprite_obj.data.materials.append(sprite_mat); needle_obj.data.materials.append(mesh_mat)
        foliage.extend((sprite_obj,needle_obj)); stats.append(st); xoff += variant['height']*.72
    os.makedirs(os.path.dirname(out_glb) or '.',exist_ok=True); bpy.ops.export_scene.gltf(filepath=out_glb,export_format='GLB')
    setup_preview(structural+foliage); render_png(out_png)
    payload={
        'representation':'source_volume_hybrid_mesh3d_plus_sprites',
        'source_representation':volume.get('representation'),
        'target_foliage_tris':TARGET_FOLIAGE_TRIS,
        'hybrid_contract':{
            'single_point_map':True,
            'sprite_on_every_point':True,
            'mesh3d_on_dense_half':True,
            'sprite_tris_per_point':SPRITE_TRIS_PER_POINT,
            'mesh3d_tris_per_dense_point':MESH_TRIS_PER_POINT,
        },
        'runtime_intent':'One foliage point map drives two Godot MultiMeshes: textured sprite sprays plus tiny real 3D needle meshes; both share identical transforms/source positions and deterministic per-instance variation.',
        'variants':stats,
    }
    with open(out_json,'w',encoding='utf-8') as f: json.dump(payload,f,indent=2)
    for st in stats:
        print(f"ARCONT_PINE_HYBRID_FOLIAGE={st['name']} points={st['hybrid_points']} sprites={st['sprite_points']} mesh3d={st['mesh3d_points']} sprite_tris={st['sprite_tris']} mesh_tris={st['mesh3d_tris']} total={st['total_tris']}")
    print('ARCONT_PINE_FOLIAGE_PREVIEW=',out_png); print('ARCONT_PINE_FOLIAGE_GLB=',out_glb)

if __name__=='__main__': main()
