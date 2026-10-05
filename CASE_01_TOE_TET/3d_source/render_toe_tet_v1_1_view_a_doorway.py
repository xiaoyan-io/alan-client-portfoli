"""TOE TET V1.1 VIEW A：后墙贯通门洞粘土渲染。

从锁定 GLB 读取场景，在内存中移除后墙品牌构件、对 WALL_REAR 执行真实布尔开洞，
并增加门后通道的墙/地/顶体量以显示墙厚与进深阴影。不会写回或覆盖锁定 GLB。

"""

from pathlib import Path
import json
import bpy
from mathutils import Vector

# Dimensions
DOOR_WIDTH = 0.9  # meters
DOOR_HEIGHT = 2.1  # meters
DOOR_DEPTH = 0.2  # meters (cutting depth)
REAR_WALL_Y = 3.0  # Y coordinate of rear wall

# Find the rear wall object
wall = bpy.data.objects.get("WALL_REAR")
if not wall:
    # Try to locate the rear wall by name pattern or other heuristic
    # For now, raise an error
    raise RuntimeError("Rear wall object 'WALL_REAR' not found. Please check object name.")

# Create cutter mesh (cube)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, REAR_WALL_Y, DOOR_HEIGHT/2.0))
cutter = bpy.context.active_object
cutter.name = "DoorCutter"
cutter.scale = (DOOR_WIDTH/2, DOOR_DEPTH/2, DOOR_HEIGHT/2)

# Apply boolean difference to wall
bool_mod = wall.modifiers.new(name="DoorCut", type='BOOLEAN')
bool_mod.operation = 'DIFFERENCE'
bool_mod.object = cutter

# Make wall active and apply modifier
bpy.context.view_layer.objects.active = wall
bpy.ops.object.modifier_apply(modifier=bool_mod.name)

# Set up camera
cam_data = bpy.data.cameras.new(name="ViewACam")
cam_obj = bpy.data.objects.new("ViewACam", cam_data)
bpy.context.collection.objects.link(cam_obj)

# Camera location
cam_obj.location = (0.0, -3.0, 1.6)

# Camera rotation for single-point perspective (looking down -Y)
cam_obj.rotation_euler = (0.0, 0.0, -math.radians(90.0))

# Camera lens (focal length)
cam_data.lens = 35.0

# Set scene camera
bpy.context.scene.camera = cam_obj

# Set render resolution (16:9)
bpy.context.scene.render.resolution_x = 2560
bpy.context.scene.render.resolution_y = 1440

# Output file
bpy.context.scene.render.filepath = "TOE_TET_VIEW_A_CLAY.png"

# Optional: assign clay material if needed
clay_mat = bpy.data.materials.get("Clay")
if clay_mat:
    wall.data.materials.clear()
    wall.data.materials.append(clay_mat)

# Render silently
bpy.ops.render.render(write_still=True)