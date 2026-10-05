"""TOE TET 日式烘焙原料展厅深化模型（工作草案 / 非施工图）。

适用 Blender 5.2。脚本清空当前场景、程序化建模，并导出 GLB。
所有长度单位均为米；入口位于 Y=-3.0 m，后场位于 Y=+3.0 m。
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


CASE_ROOT = Path(__file__).resolve().parent.parent
EXPORT_PATH = CASE_ROOT / "exports" / "TOE_TET_REFINED_V1.glb"

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
    frame_h = 2.250
    post = 0.045
    oak = mats["oak"]
    for sy in (-1, 1):
        for sx in (-1, 1):
            x = center_x + sx * side * (shelf_depth / 2 - post / 2)
            yy = y + sy * (width / 2 - post / 2)
            cube(f"{code}_POST_{sx}_{sy}", (post, post, frame_h), (x, yy, frame_h / 2), oak, 0.008, collection)
    for i, z in enumerate((0.22, 0.72, 1.22, 1.72, 2.18), 1):
        cube(f"{code}_SHELF_{i}", (shelf_depth, width, 0.045), (center_x, y, z), oak, 0.012, collection)
    label_x = center_x - side * (shelf_depth / 2 + 0.012)
    text_mesh(code, f"{code}_LABEL", (label_x, y, 1.95), (math.pi / 2, 0, side * math.pi / 2), 0.13, mats["ink"])
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
    text_mesh(code, f"{code}_LABEL", (x + 0.255, y, 0.285), (math.pi / 2, 0, math.pi / 2), 0.13, mats["ink"])


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
    text_mesh("CHECKOUT + POS", "CHECKOUT_LABEL", (x - depth / 2 - 0.018, y, 0.55), (math.pi / 2, 0, math.pi / 2), 0.105, mats["ink"])


def build_track_lighting(x, mats, collection):
    rail_z = 2.85
    cube(f"TRACK_RAIL_{x:+.1f}", (0.055, 5.10, 0.045), (x, 0.05, rail_z), mats["black_metal"], 0.008, collection)
    for idx, y in enumerate((-2.15, -1.08, 0.0, 1.08, 2.15), 1):
        cylinder(f"TRACK_SPOT_{x:+.1f}_{idx}", 0.075, 0.18, (x, y, 2.70), mats["black_metal"], 32, collection)
        bpy.context.object.rotation_euler.y = math.radians(14 if x < 0 else -14)
        light_data = bpy.data.lights.new(f"SPOT_LIGHT_{x:+.1f}_{idx}", type="SPOT")
        light_data.energy = 220.0
        light_data.color = (1.0, 0.78, 0.56)
        light_data.spot_size = math.radians(48)
        light_data.spot_blend = 0.45
        lamp = bpy.data.objects.new(light_data.name, light_data)
        collection.objects.link(lamp)
        lamp.location = (x, y, 2.62)
        target = Vector((0.0 if abs(y) < 0.4 else x * 1.45, y, 0.65))
        lamp.rotation_euler = (target - lamp.location).to_track_quat("-Z", "Y").to_euler()


def build_scene():
    reset_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.render.engine = "BLENDER_EEVEE"
    scene.world.color = (0.035, 0.035, 0.035)

    mats = {
        "microcement": material("MAT_Microcement_Warm_Grey", (0.46, 0.43, 0.39), 0.82),
        "oak": material("MAT_Warm_Oak", (0.46, 0.25, 0.105), 0.48),
        "black_metal": material("MAT_Deep_Black_Matte_Metal", (0.012, 0.014, 0.016), 0.28, 0.72),
        "wall": material("MAT_Warm_White_Wall", (0.86, 0.82, 0.74), 0.70),
        "ink": material("MAT_Deep_Charcoal", (0.018, 0.022, 0.024), 0.42),
        "glass": material("MAT_Clear_Glass", (0.73, 0.88, 0.90), 0.12, 0.0, 0.75),
        "aisle": material("MAT_Aisle_Clearance_Guide", (0.48, 0.18, 0.04), 0.62),
    }

    architecture = new_collection("00_ARCHITECTURE")
    furniture = new_collection("10_FIXED_FURNITURE")
    lighting = new_collection("20_TRACK_LIGHTING")
    guides = new_collection("90_GUIDES_WORKING_DRAFT")

    # 地坪与围护：前侧保持开放，表达客户入口。
    cube("FLOOR_MICROCEMENT_5238x6000", (ROOM_W, ROOM_D, 0.08), (0, 0, -0.04), mats["microcement"], 0.012, architecture)
    cube("WALL_LEFT", (0.10, ROOM_D, ROOM_H), (-ROOM_W / 2 - 0.05, 0, ROOM_H / 2), mats["wall"], 0.01, architecture)
    cube("WALL_RIGHT", (0.10, ROOM_D, ROOM_H), (ROOM_W / 2 + 0.05, 0, ROOM_H / 2), mats["wall"], 0.01, architecture)
    cube("WALL_REAR", (ROOM_W + 0.20, 0.10, ROOM_H), (0, ROOM_D / 2 + 0.05, ROOM_H / 2), mats["wall"], 0.01, architecture)

    # 1.6 m 中央无障碍主通道：低矮半透明导视面，不作为实际障碍物。
    aisle = cube("GUIDE_MAIN_AISLE_CLEAR_1600", (AISLE_W, ROOM_D - 0.20, 0.004), (0, 0.10, 0.004), mats["aisle"], 0.0, guides)
    aisle.display_type = "WIRE"
    aisle.hide_render = True
    text_mesh("1600 CLEAR MAIN AISLE", "AISLE_LABEL", (0, -2.58, 0.012), (0, 0, 0), 0.105, mats["aisle"])

    # 左右墙架：左 S1-S4，右 S5-S7。
    for code, y in zip(("S1", "S2", "S3", "S4"), (-2.14, -0.72, 0.70, 2.12)):
        build_shelf(code, -1, y, 1.18, mats, furniture)
    for code, y in zip(("S5", "S6", "S7"), (-1.88, 0.02, 1.92)):
        build_shelf(code, 1, y, 1.55, mats, furniture)

    # P1 / P2 位于入口左侧、通道外。
    build_step_display("P1", -1.16, -2.18, 0.92, mats, furniture)
    build_step_display("P2", -1.16, -1.02, 0.92, mats, furniture)
    build_checkout(mats, furniture)

    # 导轨中心线位于主通道两侧。
    build_track_lighting(-1.02, mats, lighting)
    build_track_lighting(1.02, mats, lighting)

    # 工作草案状态牌。
    text_mesh("TOE TET REFINED V1 | WORKING DRAFT | NOT FOR CONSTRUCTION", "STATUS_LABEL", (0, 2.94, 2.82), (math.pi / 2, 0, 0), 0.105, mats["ink"])

    # 自定义属性为 GLB 提供可审计的设计基准。
    scene["project_id"] = "PRJ-2026-TTM-01"
    scene["model_status"] = "WORKING DRAFT / NOT FOR CONSTRUCTION / FIELD VERIFY"
    scene["working_envelope_m"] = "5.238 x 6.000"
    scene["main_aisle_clear_m"] = AISLE_W
    scene["checkout_size_m"] = "1.838 x 0.550 x 0.900"
    scene["shelf_cable_gap_m"] = 0.150

    # 总览相机便于后续打开 .blend 或脚本扩展时复用。
    camera_data = bpy.data.cameras.new("CAMERA_OVERVIEW")
    camera = bpy.data.objects.new("CAMERA_OVERVIEW", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (7.3, -8.2, 6.4)
    camera.rotation_euler = (Vector((0, 0.25, 1.15)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.lens = 42
    scene.camera = camera

    # 尺寸与通道自动校验。
    assert math.isclose(ROOM_W, 5.238, abs_tol=1e-9)
    assert math.isclose(ROOM_D, 6.000, abs_tol=1e-9)
    for obj in furniture.objects:
        if obj.type != "MESH":
            continue
        corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        min_x = min(v.x for v in corners)
        max_x = max(v.x for v in corners)
        if min_x < AISLE_W / 2 and max_x > -AISLE_W / 2:
            raise RuntimeError(f"通道侵占: {obj.name} X=[{min_x:.3f}, {max_x:.3f}]")

    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(EXPORT_PATH),
        export_format="GLB",
        export_apply=True,
        export_extras=True,
        export_cameras=True,
        export_lights=True,
    )
    if not EXPORT_PATH.exists() or EXPORT_PATH.stat().st_size == 0:
        raise RuntimeError(f"GLB 导出失败: {EXPORT_PATH}")
    print(f"TOE_TET_EXPORT_OK={EXPORT_PATH}")
    print(f"TOE_TET_OBJECTS={len(bpy.context.scene.objects)}")
    print(f"TOE_TET_GLB_BYTES={EXPORT_PATH.stat().st_size}")
    print("TOE_TET_AISLE_CLEAR_M=1.600")


if __name__ == "__main__":
    build_scene()

