"""TOE TET V1.1 锁定相机与粘土渲染。

只读取锁定 GLB，在内存场景中添加审查相机、粘土材质与审查灯光。
不写回 GLB，不修改建模脚本、空间尺寸或家具拓扑。
"""

from pathlib import Path
import json

import bpy
from mathutils import Vector


CASE_ROOT = Path(__file__).resolve().parent.parent
SOURCE_GLB = CASE_ROOT / "exports" / "TOE_TET_REFINED_V1_1.glb"
OUTPUT_DIR = CASE_ROOT / "renders" / "V1_1_CLAY_LOCKED"

CAMERA_LOCK = (
    {
        "name": "CAM_LOCK_01_ENTRANCE_HERO",
        "file": "TOE_TET_V1_1_CLAY_01_ENTRANCE_HERO.png",
        "location": (0.0, -7.45, 2.20),
        "target": (0.0, 0.35, 1.08),
        "lens_mm": 42.0,
    },
    {
        "name": "CAM_LOCK_02_CENTRAL_AISLE",
        "file": "TOE_TET_V1_1_CLAY_02_CENTRAL_AISLE.png",
        "location": (0.0, -2.68, 1.62),
        "target": (0.0, 2.42, 1.12),
        "lens_mm": 35.0,
    },
    {
        "name": "CAM_LOCK_03_CHECKOUT_DISPLAY",
        "file": "TOE_TET_V1_1_CLAY_03_CHECKOUT_DISPLAY.png",
        "location": (-0.48, -3.70, 1.74),
        "target": (1.94, -1.42, 0.96),
        "lens_mm": 47.0,
    },
)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_clay_material():
    mat = bpy.data.materials.new("MAT_CLAY_WARM_GREY_LOCKED_REVIEW")
    mat.diffuse_color = (0.52, 0.49, 0.45, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.52, 0.49, 0.45, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.82
    bsdf.inputs["Metallic"].default_value = 0.0
    return mat


def add_area_light(name, location, target, energy, size):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = (1.0, 0.93, 0.84)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    point_at(obj, target)
    return obj


def main():
    if not SOURCE_GLB.is_file():
        raise FileNotFoundError(f"锁定 GLB 不存在: {SOURCE_GLB}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE_GLB))
    imported_objects = tuple(bpy.context.scene.objects)
    imported_mesh_count = sum(obj.type == "MESH" for obj in imported_objects)

    # 移除导入场景中的相机和灯光，仅影响本次内存渲染，不写回 GLB。
    for obj in list(bpy.context.scene.objects):
        if obj.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)

    clay = make_clay_material()
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.data.materials.clear()
            obj.data.materials.append(clay)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("WORLD_CLAY_REVIEW")
    scene.world.color = (0.035, 0.035, 0.035)
    scene.view_settings.look = "AgX - Medium High Contrast"

    # 中性审查光：强调比例、遮挡和通道，不追求最终氛围效果。
    add_area_light("CLAY_KEY", (-3.6, -2.8, 5.4), (0.0, 0.2, 1.0), 1050.0, 4.2)
    add_area_light("CLAY_FILL", (3.4, -0.8, 4.2), (0.0, 0.6, 1.0), 720.0, 3.6)
    add_area_light("CLAY_REAR", (0.0, 3.8, 3.8), (0.0, 0.7, 1.0), 620.0, 3.0)

    camera_data = bpy.data.cameras.new("CAMERA_LOCK_DATA")
    camera_data.sensor_width = 36.0
    camera_data.clip_start = 0.05
    camera_data.clip_end = 100.0
    camera = bpy.data.objects.new("CAMERA_LOCK_ACTIVE", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = []
    for spec in CAMERA_LOCK:
        camera.name = spec["name"]
        camera.location = spec["location"]
        camera.data.lens = spec["lens_mm"]
        point_at(camera, spec["target"])
        output_path = OUTPUT_DIR / spec["file"]
        scene.render.filepath = str(output_path)
        bpy.ops.render.render(write_still=True)
        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise RuntimeError(f"渲染输出缺失: {output_path}")
        outputs.append(
            {
                "camera": spec["name"],
                "location": spec["location"],
                "target": spec["target"],
                "lens_mm": spec["lens_mm"],
                "output": str(output_path),
                "bytes": output_path.stat().st_size,
            }
        )

    print(
        json.dumps(
            {
                "status": "ok",
                "source_glb": str(SOURCE_GLB),
                "source_objects": len(imported_objects),
                "source_meshes": imported_mesh_count,
                "camera_lock_count": len(CAMERA_LOCK),
                "resolution": [1600, 1000],
                "outputs": outputs,
                "project_status": "WORKING DRAFT / NOT FOR CONSTRUCTION",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
