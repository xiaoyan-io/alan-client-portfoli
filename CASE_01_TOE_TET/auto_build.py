import bpy

# 清空默认场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 创建材质函数
def make_mat(name, color, roughness=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

mat_floor = make_mat("Floor_Mat", (0.85, 0.82, 0.75, 1.0), 0.7)
mat_wood = make_mat("Wood_Teak", (0.55, 0.35, 0.17, 1.0), 0.6)
mat_metal = make_mat("Dark_Metal", (0.1, 0.12, 0.15, 1.0), 0.3)
mat_counter = make_mat("Micro_Cement", (0.0, 0.8, 0.9, 1.0), 0.4)

# 1. 地板 (5.238m x 6.0m)
bpy.ops.mesh.primitive_plane_add(size=1)
floor = bpy.context.active_object
floor.name = "Floor"
floor.scale = (5.238, 6.0, 1.0)
floor.data.materials.append(mat_floor)

# 2. 收银台 (CHECKOUT + POS: 1.838m x 0.55m x 0.9m)
bpy.ops.mesh.primitive_cube_add(size=1)
counter = bpy.context.active_object
counter.name = "Checkout_Counter"
counter.scale = (1.838, 0.55, 0.9)
counter.location = (1.9, -0.6, 0.45)
counter.data.materials.append(mat_counter)

# 3. 左侧木质货架 S1 - S4 (深 0.45m x 宽 0.8m x 高 1.8m)
for i in range(4):
    bpy.ops.mesh.primitive_cube_add(size=1)
    shelf = bpy.context.active_object
    shelf.name = f"Shelf_S{i+1}"
    shelf.scale = (0.8, 0.45, 1.8)
    shelf.location = (-2.0, -1.8 + i * 1.05, 0.9)
    shelf.data.materials.append(mat_metal)

# 4. 右侧货架 S5 - S7
for j in range(3):
    bpy.ops.mesh.primitive_cube_add(size=1)
    shelf = bpy.context.active_object
    shelf.name = f"Shelf_S{j+5}"
    shelf.scale = (0.8, 0.45, 1.8)
    shelf.location = (2.0, 0.8 + j * 0.95, 0.9)
    shelf.data.materials.append(mat_metal)

# 5. 原料陈列平台 P1 / P2
for k, name in enumerate(["P1_FLOUR", "P2_INGREDIENTS"]):
    bpy.ops.mesh.primitive_cube_add(size=1)
    plat = bpy.context.active_object
    plat.name = name
    plat.scale = (1.2, 0.55, 0.45)
    plat.location = (-1.1, 2.2 - k * 0.75, 0.225)
    plat.data.materials.append(mat_wood)

# 6. 导出 GLB
out_path = "O:\\ALAN_SYSTEM\\06_PROJECT_CASES\\_WEB_DEPLOY\\CASE_01_TOE_TET\\toe_tet_model.glb"
bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB')
print(">>> TOE TET 3D 模型生成并导出完成！")
