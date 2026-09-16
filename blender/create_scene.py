"""Build a simple multi-shaft building inside Blender.

Run:
    blender --background --python blender/create_scene.py -- --floors 20 --elevators 4 --save blender/building.blend

Also imported by live_listener.py. Mesh creation uses bpy.data so it works
without a 3D-view context (needed when launching via --python).
"""

from __future__ import annotations

import math

FLOOR_HEIGHT = 3.0
SHAFT_SPACING = 4.5
CAR_HEIGHT = 2.4
CAR_SIZE = 1.8
CAR_COLORS = [
    (0.12, 0.55, 0.98, 1.0),
    (0.98, 0.32, 0.18, 1.0),
    (0.18, 0.78, 0.38, 1.0),
    (0.98, 0.82, 0.12, 1.0),
    (0.72, 0.28, 0.92, 1.0),
    (0.12, 0.82, 0.88, 1.0),
    (0.98, 0.48, 0.12, 1.0),
    (0.55, 0.55, 0.58, 1.0),
    (0.95, 0.45, 0.72, 1.0),
    (0.35, 0.55, 0.25, 1.0),
]


def car_name(elevator_id: int) -> str:
    return f"Elevator_{elevator_id}"


def passenger_name(passenger_id: str) -> str:
    return f"Passenger_{passenger_id}"


def car_z(floor: int) -> float:
    return (floor - 1) * FLOOR_HEIGHT + CAR_HEIGHT / 2.0


def waiting_z(floor: int) -> float:
    return (floor - 1) * FLOOR_HEIGHT + 0.45


def shaft_x(elevator_id: int) -> float:
    return elevator_id * SHAFT_SPACING


def building_center(num_floors: int, num_elevators: int):
    return (
        (num_elevators - 1) * SHAFT_SPACING / 2.0,
        0.0,
        num_floors * FLOOR_HEIGHT / 2.0,
    )


def build_scene(num_floors: int = 20, num_elevators: int = 4) -> None:
    import bpy

    _clear_scene()
    _prefer_layout_workspace()

    cx, _cy, cz = building_center(num_floors, num_elevators)
    width = num_elevators * SHAFT_SPACING + 3.0

    _box(cx, -4.0, cz, width=width, depth=0.25, height=num_floors * FLOOR_HEIGHT + 1.0,
         name="BackWall", color=(0.22, 0.23, 0.26, 1.0))

    for floor in range(1, num_floors + 1):
        z = (floor - 1) * FLOOR_HEIGHT
        _box(cx, 1.8, z, width=width, depth=2.6, height=0.14,
             name=f"Floor_{floor}", color=(0.62, 0.62, 0.66, 1.0))

    for elevator_id in range(num_elevators):
        x = shaft_x(elevator_id)
        _box(x, 0.0, cz, width=0.16, depth=0.16, height=num_floors * FLOOR_HEIGHT,
             name=f"Rail_{elevator_id}", color=(0.05, 0.05, 0.05, 1.0))
        color = CAR_COLORS[elevator_id % len(CAR_COLORS)]
        _box(x, 0.0, car_z(1), width=CAR_SIZE, depth=CAR_SIZE, height=CAR_HEIGHT,
             name=car_name(elevator_id), color=color)

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 35
    camera = bpy.data.objects.new("Camera", cam_data)
    _link(camera)
    camera.location = (cx, -max(22.0, num_floors * 0.85), cz)
    camera.rotation_euler = (math.radians(78), 0.0, 0.0)
    bpy.context.scene.camera = camera

    light_data = bpy.data.lights.new("Sun", type="SUN")
    light_data.energy = 4.0
    light = bpy.data.objects.new("Sun", light_data)
    _link(light)
    light.location = (cx + 8, -12, num_floors * FLOOR_HEIGHT)
    light.rotation_euler = (math.radians(50), 0.0, math.radians(15))

    fill = bpy.data.lights.new("Fill", type="AREA")
    fill.energy = 250
    fill.size = 12
    fill_obj = bpy.data.objects.new("Fill", fill)
    _link(fill_obj)
    fill_obj.location = (cx, -6, cz)

    frame_building(num_floors, num_elevators)


def apply_tick(state: dict) -> None:
    import bpy

    num_elevators = int(state.get("num_elevators", 0))
    num_floors = int(state.get("num_floors", 0))
    if num_elevators and num_floors and car_name(0) not in bpy.data.objects:
        build_scene(num_floors, num_elevators)

    for elevator in state.get("elevators", []):
        obj = bpy.data.objects.get(car_name(int(elevator["id"])))
        if obj is None:
            continue
        obj.location.z = car_z(int(elevator["floor"]))

    live_ids = set()
    for waiting in state.get("waiting", []):
        name = passenger_name(str(waiting["id"]))
        live_ids.add(name)
        assigned = waiting.get("elevator") or 0
        x = shaft_x(int(assigned)) + 1.3
        z = waiting_z(int(waiting["floor"]))
        obj = bpy.data.objects.get(name)
        if obj is None:
            obj = _marker(name, x, 1.5, z, color=(1.0, 0.85, 0.15, 1.0))
        obj.location = (x, 1.5, z)

    prefix = "Passenger_"
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefix) and obj.name not in live_ids:
            bpy.data.objects.remove(obj, do_unlink=True)


def frame_building(num_floors: int, num_elevators: int) -> None:
    import bpy
    from mathutils import Euler

    cx, _cy, cz = building_center(num_floors, num_elevators)
    distance = max(28.0, num_floors * FLOOR_HEIGHT * 1.15, num_elevators * 8.0)
    windows = list(bpy.context.window_manager.windows)
    for window in windows:
        if window.workspace and window.workspace.name != "Layout":
            layout = bpy.data.workspaces.get("Layout")
            if layout is not None:
                window.workspace = layout
        for area in window.screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            r3d = space.region_3d
            space.shading.type = "SOLID"
            space.shading.light = "STUDIO"
            space.shading.color_type = "OBJECT"
            space.shading.show_xray = False
            space.overlay.show_floor = True
            space.overlay.show_axis_x = False
            space.overlay.show_axis_y = False
            r3d.view_perspective = "PERSP"
            r3d.view_location = (cx, 0.0, cz)
            r3d.view_distance = distance
            r3d.view_rotation = Euler((math.radians(72), 0.0, math.radians(18))).to_quaternion()
            for region in area.regions:
                if region.type != "WINDOW":
                    continue
                try:
                    with bpy.context.temp_override(window=window, area=area, region=region, space_data=space):
                        bpy.ops.view3d.view_all(center=True)
                except Exception:
                    pass
            area.tag_redraw()


def _prefer_layout_workspace() -> None:
    import bpy

    layout = bpy.data.workspaces.get("Layout")
    if layout is None:
        return
    for window in bpy.context.window_manager.windows:
        window.workspace = layout


def _clear_scene() -> None:
    import bpy

    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)
    for camera in list(bpy.data.cameras):
        bpy.data.cameras.remove(camera)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)
    for curve in list(bpy.data.curves):
        bpy.data.curves.remove(curve)


def _link(obj) -> None:
    import bpy

    collection = bpy.context.scene.collection
    if obj.name not in collection.objects:
        collection.objects.link(obj)


def _set_color(obj, color) -> None:
    import bpy

    obj.color = color
    material = bpy.data.materials.new(name=f"{obj.name}_Mat")
    material.use_nodes = True
    tree = material.node_tree
    principled = next((node for node in tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if principled is not None and "Base Color" in principled.inputs:
        principled.inputs["Base Color"].default_value = color
        if "Roughness" in principled.inputs:
            principled.inputs["Roughness"].default_value = 0.35
    obj.data.materials.clear()
    obj.data.materials.append(material)


def _box(x, y, z, width, depth, height, name, color=None):
    import bpy

    hx, hy, hz = width / 2.0, depth / 2.0, height / 2.0
    verts = [
        (-hx, -hy, -hz),
        (hx, -hy, -hz),
        (hx, hy, -hz),
        (-hx, hy, -hz),
        (-hx, -hy, hz),
        (hx, -hy, hz),
        (hx, hy, hz),
        (-hx, hy, hz),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (1, 2, 6, 5),
        (0, 3, 7, 4),
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    _link(obj)
    obj.location = (x, y, z)
    if color is not None:
        _set_color(obj, color)
    return obj


def _marker(name, x, y, z, color):
    return _box(x, y, z, width=0.55, depth=0.55, height=0.55, name=name, color=color)


def _cli() -> None:
    import argparse
    import sys

    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--floors", type=int, default=20)
    parser.add_argument("--elevators", type=int, default=4)
    parser.add_argument("--save", default="")
    args = parser.parse_args(argv)
    build_scene(args.floors, args.elevators)
    if args.save:
        import bpy

        bpy.ops.wm.save_as_mainfile(filepath=args.save)


if __name__ == "__main__":
    _cli()
