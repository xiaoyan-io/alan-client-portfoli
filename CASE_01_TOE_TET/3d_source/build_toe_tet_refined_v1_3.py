"""TOE TET 日式烘焙原料展厅深化模型（工作草案 / 非施工图）。

适用 Blender 5.2。脚本清空当前场景、程序化建模，并导出 GLB。
所有长度单位均为米；入口位于 Y=-3.0 m，后场位于 Y=+3.0 m。
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


CASE_ROOT = Path(__file__).resolve().parent.parent
EXPORT_PATH = CASE_ROOT / "exports" / "TOE_TET_REFINED_V1_3.glb"

ROOM_W = 5.238
ROOM_D = 6.000
ROOM_H = 3.200
AISLE_W = 1.600



def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def material(name, base_color, roughness=0.5, metallic=0.0, transmission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*base_color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    return mat


def cube(name, size, location, mat, bevel=0.0, collection=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    if bevel > 0:
        mod = obj.modifiers.new("Soft_Edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    if collection:
        for old in list(obj.users_collection):
            old.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def cylinder(name, radius, depth, location, mat, vertices=32, collection=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    if collection:
        for old in list(obj.users_collection):
            old.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def text_mesh(body, name, location, rotation=(math.pi / 2, 0, 0), size=0.12, mat=None, extrude=0.005):
    bpy.ops.object.text_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = extrude
    if mat:
        obj.data.materials.append(mat)
    bpy.ops.object.convert(target="MESH")
    return obj


def new_collection(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def build_shelf(code, side, y, width, mats, collection):
    """靠墙高位实木框架货架；150 mm 后侧走线间隙单独保留。"""
    wall_x = side * ROOM_W / 2
    cable_gap = 0.150
    shelf_depth = 0.450
    center_x = wall_x - side * (cable_gap + shelf_depth / 2)
    frame_h = 2.100
    post = 0.045
    oak = mats["oak"]
    for sy in (-1, 1):
        for sx in (-1, 1):
            x = center_x + sx * side * (shelf_depth / 2 - post / 2)
            yy = y + sy * (width / 2 - post / 2)
            cube(f"{code}_POST_{sx}_{sy}", (post, post, frame_h), (x, yy, frame_h / 2), oak, 0.008, collection)
    shelf_levels = (0.20, 0.65, 1.10, 1.55, 2.02)
    for i, z in enumerate(shelf_levels, 1):
        cube(f"{code}_SHELF_{i}", (shelf_depth, width, 0.045), (center_x, y, z), oak, 0.012, collection)
    # 商品尺度参照：不同高度和包装色，打破连续空架的仓储感。
    product_x = center_x - side * 0.04
    for level_index, z in enumerate(shelf_levels[:-1]):
        for item_index, offset in enumerate((-0.25, 0.0, 0.25)):
            if abs(offset) > width * 0.38:
                continue
            item_h = 0.22 + 0.045 * ((level_index + item_index) % 3)
            item_mat = mats["package_cream"] if (level_index + item_index) % 2 == 0 else mats["package_rust"]
            cube(
                f"{code}_PRODUCT_{level_index + 1}_{item_index + 1}",
                (0.16, 0.15, item_h),
                (product_x, y + offset, z + 0.026 + item_h / 2),
                item_mat,
                0.018,
                collection,
            )
    return (wall_x - side * cable_gap, wall_x), (center_x - shelf_depth / 2, center_x + shelf_depth / 2)


def build_step_display(code, x, y, width_y, mats, collection):
    """三层叠落式暖木陈列台，全部位于中央通道外。"""
    tiers = (
        (0.48, width_y, 0.26, x, y, 0.13),
        (0.42, width_y * 0.88, 0.46, x - 0.20, y + 0.02, 0.23),
        (0.36, width_y * 0.72, 0.66, x - 0.38, y + 0.04, 0.33),
    )
    for i, (sx, sy, sz, xx, yy, zz) in enumerate(tiers, 1):
        cube(f"{code}_TIER_{i}", (sx, sy, sz), (xx, yy, zz), mats["oak"], 0.025, collection)


def build_checkout(mats, collection):
    """1.838 × 0.55 × 0.9 m；长边沿进深方向。"""
    length, depth, height = 1.838, 0.550, 0.900
    x = ROOM_W / 2 - 0.10 - depth / 2
    y = -1.67
    cube("CHECKOUT_OAK_CARCASS", (depth - 0.05, length - 0.05, height - 0.06), (x, y, (height - 0.06) / 2), mats["oak"], 0.025, collection)
    cube("CHECKOUT_MICROCEMENT_TOP", (depth, length, 0.06), (x, y, height - 0.03), mats["microcement"], 0.018, collection)
    # 柜门分缝
    for offset in (-0.46, 0.0, 0.46):
        cube("CHECKOUT_CABINET_JOINT", (0.012, 0.008, 0.63), (x - depth / 2 - 0.003, y + offset, 0.43), mats["ink"], 0.002, collection)
    # POS 屏幕、支架与玻璃样品罩
    cube("POS_STAND", (0.06, 0.06, 0.28), (x, y - 0.36, 1.07), mats["black_metal"], 0.008, collection)
    pos = cube("POS_SCREEN", (0.28, 0.06, 0.20), (x, y - 0.36, 1.20), mats["ink"], 0.018, collection)
    pos.rotation_euler.x = math.radians(-12)
    cube("SAMPLE_GLASS_CASE", (0.42, 0.58, 0.28), (x, y + 0.43, 1.07), mats["glass"], 0.012, collection)


def build_track_lighting(x, mats, collection):
    rail_z = 2.85
    cube(f"TRACK_RAIL_{x:+.1f}", (0.055, 5.10, 0.045), (x, 0.05, rail_z), mats["black_metal"], 0.008, collection)
    for idx, y in enumerate((-2.15, -1.08, 0.0, 1.08, 2.15), 1):
        cylinder(f"TRACK_SPOT_{x:+.1f}_{idx}", 0.045, 0.11, (x, y, 2.75), mats["black_metal"], 32, collection)
        bpy.context.object.rotation_euler.y = math.radians(14 if x < 0 else -14)
        light_data = bpy.data.lights.new(f"SPOT_LIGHT_{x:+.1f}_{idx}", type="SPOT")
        light_data.energy = 220.0
        light_data.color = (1.0, 0.78, 0.56)
        light_data.spot_size = math.radians(48)
        light_data.spot_blend = 0.45
        lamp = bpy.data.objects.new(light_data.name, light_data)
        collection.objects.link(lamp)
        lamp.location = (x, y, 2.68)
        target = Vector((0.0 if abs(y) < 0.4 else x * 1.45, y, 0.65))
        lamp.rotation_euler = (target - lamp.location).to_track_quat("-Z", "Y").to_euler()



# V1.3 受控变更：沿用 V1.2 详细家具函数，仅修正 S7 与两处入口。
import hashlib
import json
import sys

CONFIG_PATH = CASE_ROOT / "3d_source" / "toe_tet_v1_3.pipeline.json"
EVIDENCE_DIR = CASE_ROOT / "exports" / "V1_3_EVIDENCE"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box_bounds(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return [[min(v[i] for v in corners) for i in range(3)],
            [max(v[i] for v in corners) for i in range(3)]]


def punch(wall, name, size, center):
    cutter = cube(name + "_CUTTER", size, center, None)
    mod = wall.modifiers.new(name, "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.context.view_layer.objects.active = wall
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def add_camera(name, location, target, lens):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36
    data.clip_start = .05
    data.clip_end = 100
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def build_entrances(cfg, mats, architecture):
    # 门框和开启门扇均不侵占净开口；无门槛。外开90°只是审查姿态，室外扫掠须现场核实。
    d = cfg["doors"]["main"]
    w, h, f = d["clear_width"], d["clear_height"], d["frame"]
    front = cube("WALL_FRONT", (ROOM_W+.2, .1, ROOM_H),
                 (0, -3.05, ROOM_H/2), mats["wall"], .01, architecture)
    punch(front, "BOOL_FRONT_MAIN", (d["rough_width"], .5, d["rough_height"]+.02),
          (0, -3.05, d["rough_height"]/2-.01))
    for sign in (-1, 1):
        x = sign*(w/2+f/2)
        cube(f"MAIN_FRAME_JAMB_{sign}", (f,.1,h), (x,-3.05,h/2), mats["black_metal"], 0, architecture)
        length = w/2+f/2
        cy = -3.05-length/2
        for yy in (-3.05-f/2, -3.05-length+f/2):
            cube(f"MAIN_LEAF_{sign}_STILE_{yy:.3f}", (f,f,h),
                 (x,yy,h/2), mats["black_metal"], .002, architecture)
        for zz in (f/2,h-f/2):
            cube(f"MAIN_LEAF_{sign}_RAIL_{zz:.3f}", (f,length,f),
                 (x,cy,zz), mats["black_metal"], .002, architecture)
        cube(f"MAIN_LEAF_{sign}_GLASS", (.012,length-2*f,h-2*f),
             (x,cy,h/2), mats["glass"], .002, architecture)
        cube(f"MAIN_LEAF_{sign}_HANDLE", (.025,.025,.45),
             (x+sign*.065,-3.05-length+.12,1.05), mats["black_metal"], .008, architecture)
    cube("MAIN_FRAME_HEAD", (w+2*f,.1,f), (0,-3.05,h+f/2),
         mats["black_metal"], 0, architecture)

    d = cfg["doors"]["staff"]
    w, h, f = d["clear_width"], d["clear_height"], d["frame"]
    x, y, _ = d["center_blender"]
    punch(bpy.data.objects["WALL_RIGHT"], "BOOL_RIGHT_STAFF",
          (.5,d["rough_width"],d["rough_height"]+.02),
          (x,y,d["rough_height"]/2-.01))
    for sign in (-1,1):
        cube(f"STAFF_FRAME_JAMB_{sign}", (.1,f,h), (x,y+sign*(w/2+f/2),h/2),
             mats["black_metal"], 0, architecture)
    cube("STAFF_FRAME_HEAD", (.1,w+2*f,f), (x,y,h+f/2),
         mats["black_metal"], 0, architecture)
    leaf_y = y+w/2+f/2
    cube("STAFF_LEAF_OPEN_90", (w+f,f,h), (x+(w+f)/2,leaf_y,h/2),
         mats["wall"], .003, architecture)
    cube("STAFF_HANDLE", (.14,.025,.025), (x+w-.13,leaf_y+.06,1.05),
         mats["black_metal"], .008, architecture)


def group_bounds(prefix):
    objs = [o for o in bpy.context.scene.objects if o.type=="MESH" and o.name.startswith(prefix)]
    boxes = [box_bounds(o) for o in objs]
    return [[min(b[0][i] for b in boxes) for i in range(3)],
            [max(b[1][i] for b in boxes) for i in range(3)]]


def check_geometry(cfg):
    bpy.context.view_layer.update()
    tol = cfg["tolerance"]
    bad = []
    furniture = [o for o in bpy.context.scene.objects if o.type=="MESH" and
                 (o.name.startswith(("P1_","P2_","CHECKOUT_","POS_","SAMPLE_")) or
                  (len(o.name)>2 and o.name[:2] in ["S1","S2","S3","S4","S5","S6","S7"] and o.name[2]=="_"))]
    for obj in furniture:
        lo, hi = box_bounds(obj)
        if lo[0] < .8-tol and hi[0] > -.8+tol:
            bad.append(obj.name+":AISLE")
        if lo[0] < -ROOM_W/2-tol or hi[0]>ROOM_W/2+tol or lo[1]<-3-tol or hi[1]>3+tol:
            bad.append(obj.name+":OUTSIDE")
        # 从中央通道右缘至员工入口的完整横向接近区。
        if hi[0]>.8+tol and lo[0]<2.619-tol and hi[1]>2+tol and lo[1]<2.9-tol:
            bad.append(obj.name+":STAFF_ACCESS")
    assert not bad, bad
    lo, hi = group_bounds("S7_")
    assert abs(lo[1]-1.145)<tol and abs(hi[1]-1.95)<tol
    assert not any(o.name.startswith("REAR_PASSAGE") for o in bpy.data.objects)
    return {"aisle_clear_m":1.6,"staff_access_zone_blender":[[.8,2,0],[2.619,2.9,2.1]],
            "s7_bounds": [lo,hi], "s7_to_staff_clearance_m":2-hi[1],
            "furniture_checked":len(furniture),"violations":bad}


def main():
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert bpy.app.version[:2] == (5,2), bpy.app.version_string
    protected = [CASE_ROOT/"3d_source"/f"build_toe_tet_refined_{v}.py" for v in ["v1","v1_1","v1_2"]]
    protected += [CASE_ROOT/"exports"/f"TOE_TET_REFINED_{v}.glb" for v in ["V1","V1_1","V1_2"]]
    before = {str(p):sha(p) for p in protected}
    reset_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.render.engine = cfg["render"]["engine"]
    if scene.world is None:
        scene.world = bpy.data.worlds.new("WORLD_TOE_TET")
    scene.world.color = (.035,.035,.035)
    mats = {
        "microcement": material("MAT_Microcement_Warm_Grey", (.40,.37,.34), .88),
        "oak": material("MAT_Warm_Oak", (.36,.18,.065), .56),
        "black_metal": material("MAT_Deep_Black_Matte_Metal", (.012,.014,.016), .28,.72),
        "wall": material("MAT_Warm_White_Wall", (.86,.82,.74), .70),
        "ink": material("MAT_Deep_Charcoal", (.018,.022,.024), .42),
        "glass": material("MAT_Clear_Glass", (.73,.88,.90), .12,0,.75),
        "package_cream": material("MAT_Package_Cream", (.74,.57,.35), .72),
        "package_rust": material("MAT_Package_Rust", (.48,.12,.045), .68),
        "paper": material("MAT_Washi_Paper", (.82,.76,.64), .90),
    }
    architecture = new_collection("00_ARCHITECTURE")
    furniture = new_collection("10_FIXED_FURNITURE")
    lighting = new_collection("20_TRACK_LIGHTING")
    cube("FLOOR_MICROCEMENT_5238x6000", (ROOM_W,ROOM_D,.08),(0,0,-.04),mats["microcement"],.012,architecture)
    for side, label in [(-1,"LEFT"),(1,"RIGHT")]:
        cube("WALL_"+label,(.1,ROOM_D,ROOM_H),(side*(ROOM_W/2+.05),0,ROOM_H/2),mats["wall"],.01,architecture)
    cube("WALL_REAR",(ROOM_W+.2,.1,ROOM_H),(0,3.05,ROOM_H/2),mats["wall"],.01,architecture)
    # 从管道配置读取所有货架定位，保留 V1.2 的详细构件和商品。
    for fix in cfg["fixtures"]:
        if fix["kind"] == "shelf":
            y = fix["position"][1]+fix["size"][1]/2-3
            build_shelf(fix["id"],-1 if int(fix["id"][1:])<5 else 1,y,fix["size"][1],mats,furniture)
    for code,y in [("P1",-2.18),("P2",-1.02)]:
        build_step_display(code,-1.16,y,.92,mats,furniture)
    build_checkout(mats,furniture)
    build_entrances(cfg,mats,architecture)
    build_track_lighting(-1.02,mats,lighting)
    build_track_lighting(1.02,mats,lighting)
    add_camera("CAMERA_OVERVIEW",(7.3,-8.2,6.4),(0,.25,1.15),42)
    cam = cfg["camera"]
    scene.camera = add_camera(cam["name"],cam["location"],cam["target"],cam["lens_mm"])
    scene["project_id"] = cfg["project_id"]
    scene["model_version"] = "TOE_TET_REFINED_V1.3"
    scene["model_status"] = cfg["status"]
    scene["main_aisle_clear_m"] = AISLE_W
    scene["working_envelope_m"] = "5.238 x 6.000"
    scene["entrance_topology"] = "FRONT_CENTER_DOUBLE_GLASS + RIGHT_REAR_STAFF; NO_REAR_DOOR"
    checks = check_geometry(cfg)
    # 坐标清单为实际场景逐对象世界包围盒，另附项目左前原点坐标。
    coordinates = []
    for obj in sorted(scene.objects,key=lambda o:o.name):
        lo,hi = box_bounds(obj) if obj.type=="MESH" else (list(obj.location),list(obj.location))
        coordinates.append({"name":obj.name,"type":obj.type,
            "location_blender_m":list(obj.location),
            "bounds_blender_m":[lo,hi],
            "bounds_front_left_m":[[lo[0]+2.619,lo[1]+3,lo[2]],[hi[0]+2.619,hi[1]+3,hi[2]]]})
    EXPORT_PATH.parent.mkdir(parents=True,exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(EXPORT_PATH),export_format="GLB",export_apply=True,
                             export_extras=True,export_cameras=True,export_lights=True)
    assert EXPORT_PATH.stat().st_size>0
    after = {str(p):sha(p) for p in protected}
    assert before == after, "历史版本哈希改变"
    (EVIDENCE_DIR/"coordinates.json").write_text(json.dumps({
        "coordinate_system":cfg["coordinate_system"],"objects":coordinates},ensure_ascii=False,indent=2),encoding="utf-8")
    result = {"status":"ok","blender_version":bpy.app.version_string,"checks":checks,
              "output":str(EXPORT_PATH),"bytes":EXPORT_PATH.stat().st_size,"sha256":sha(EXPORT_PATH),
              "config_sha256":sha(CONFIG_PATH),"protected_before":before,"protected_after":after,
              "protected_unchanged":True,"adjustment":cfg["adjustment"],
              "known_baseline":cfg["known_baseline"],"camera":cfg["camera"]}
    (EVIDENCE_DIR/"build_result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))


if __name__ == "__main__":
    main()

