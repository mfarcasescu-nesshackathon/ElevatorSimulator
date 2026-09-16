"""Build a simple multi-shaft building inside Blender.

Run:
    blender --background --python blender/create_scene.py -- --floors 20 --elevators 4 --save blender/building.blend

Also imported by live_listener.py.
"""

from __future__ import annotations

FLOOR_HEIGHT = 3.0
SHAFT_SPACING = 4.0
CAR_HEIGHT = 2.4
CAR_SIZE = 1.6


def car_name(elevator_id: int) -> str:
    return f"Elevator_{elevator_id}"


def passenger_name(passenger_id: str) -> str:
    return f"Passenger_{passenger_id}"


def car_z(floor: int) -> float:
    return (floor - 1) * FLOOR_HEIGHT + CAR_HEIGHT / 2.0


def waiting_z(floor: int) -> float:
    return (floor - 1) * FLOOR_HEIGHT + 0.35


def shaft_x(elevator_id: int) -> float:
    return elevator_id * SHAFT_SPACING


def build_scene(num_floors: int = 20, num_elevators: int = 4) -> None:
    import bpy

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for collection in list(bpy.data.collections):
        if collection.name not in bpy.context.scene.collection.children:
            continue

    _box((num_elevators * SHAFT_SPACING) / 2.0 - SHAFT_SPACING / 2.0, -3.5, num_floors * FLOOR_HEIGHT / 2.0,
         width=num_elevators * SHAFT_SPACING + 2.0, depth=0.3, height=num_floors * FLOOR_HEIGHT,
         name="BackWall")

    for floor in range(1, num_floors + 1):
        z = (floor - 1) * FLOOR_HEIGHT
        slab = _box(
            (num_elevators * SHAFT_SPACING) / 2.0 - SHAFT_SPACING / 2.0,
            1.6,
            z,
            width=num_elevators * SHAFT_SPACING + 1.5,
            depth=2.2,
            height=0.12,
            name=f"Floor_{floor}",
        )
        slab.location.z = z

    for elevator_id in range(num_elevators):
        x = shaft_x(elevator_id)
        rail = _box(x, 0.0, num_floors * FLOOR_HEIGHT / 2.0, width=0.15, depth=0.15,
                    height=num_floors * FLOOR_HEIGHT, name=f"Rail_{elevator_id}")
        rail.location.z = num_floors * FLOOR_HEIGHT / 2.0
        car = _box(x, 0.0, car_z(1), width=CAR_SIZE, depth=CAR_SIZE, height=CAR_HEIGHT,
                   name=car_name(elevator_id), color=(0.15, 0.55, 0.9, 1.0))
        car.location.z = car_z(1)

    camera = bpy.data.objects.get("Camera")
    if camera is None:
        bpy.ops.object.camera_add()
        camera = bpy.context.object
        camera.name = "Camera"
    camera.location = (num_elevators * SHAFT_SPACING * 0.45, -max(18.0, num_floors * 0.55), num_floors * FLOOR_HEIGHT * 0.45)
    camera.rotation_euler = (1.1, 0.0, 0.15)
    bpy.context.scene.camera = camera

    if "Sun" not in bpy.data.objects:
        bpy.ops.object.light_add(type="SUN", location=(5, -8, num_floors * FLOOR_HEIGHT))


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
        obj = bpy.data.objects.get(name)
        assigned = waiting.get("elevator") or 0
        x = shaft_x(int(assigned)) + 1.15
        z = waiting_z(int(waiting["floor"]))
        if obj is None:
            obj = _icosphere(name, x, 1.3, z)
        obj.location = (x, 1.3, z)

    prefix = "Passenger_"
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefix) and obj.name not in live_ids:
            bpy.data.objects.remove(obj, do_unlink=True)


def _box(x, y, z, width, depth, height, name, color=None):
    import bpy

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (width, depth, height)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if color is not None:
        material = bpy.data.materials.new(name=f"{name}_Mat")
        material.diffuse_color = color
        obj.data.materials.append(material)
    return obj


def _icosphere(name, x, y, z):
    import bpy

    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.22, location=(x, y, z))
    obj = bpy.context.object
    obj.name = name
    material = bpy.data.materials.new(name=f"{name}_Mat")
    material.diffuse_color = (0.95, 0.75, 0.2, 1.0)
    obj.data.materials.append(material)
    return obj


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
