"""Live / replay Blender client for the elevator simulator.

Live:
    blender --factory-startup --python blender/live_listener.py -- --port 8765 --floors 8 --elevators 2

Replay a finished run (no TCP needed):
    blender --factory-startup --python blender/live_listener.py -- --replay outputs/positions.csv --delay 0.25
"""

from __future__ import annotations

import csv
import json
import queue
import socket
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from create_scene import apply_tick, build_scene, frame_building  # noqa: E402


def parse_args(argv: list[str] | None = None):
    import argparse

    raw = argv if argv is not None else sys.argv
    if "--" in raw:
        raw = raw[raw.index("--") + 1 :]
    parser = argparse.ArgumentParser(description="Elevator visualization for Blender")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--floors", type=int, default=20)
    parser.add_argument("--elevators", type=int, default=4)
    parser.add_argument("--replay", default="", help="positions.csv from a completed run")
    parser.add_argument("--delay", type=float, default=0.25, help="Seconds per replay tick")
    parser.add_argument("--loop", action="store_true", help="Loop the replay")
    return parser.parse_args(raw)


def reader_thread(host: str, port: int, incoming: queue.Queue, stop: threading.Event) -> None:
    sock = None
    last_error = "could not connect"
    deadline = 90.0
    started = time.time()
    while not stop.is_set() and (time.time() - started) < deadline:
        try:
            sock = socket.create_connection((host, port), timeout=2)
            break
        except OSError as exc:
            last_error = str(exc)
            time.sleep(0.4)
    if sock is None:
        incoming.put({"type": "error", "message": last_error})
        return
    sock.settimeout(0.5)
    buffer = ""
    incoming.put({"type": "connected"})
    try:
        while not stop.is_set():
            try:
                chunk = sock.recv(4096)
            except TimeoutError:
                continue
            except OSError as exc:
                incoming.put({"type": "error", "message": str(exc)})
                break
            if not chunk:
                incoming.put({"type": "closed"})
                break
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                incoming.put(json.loads(line))
    finally:
        try:
            sock.close()
        except OSError:
            pass


def load_replay(path: str) -> tuple[int, int, list[list[int]]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        elevator_cols = [name for name in header[1:] if name.startswith("e")]
        rows: list[list[int]] = []
        for row in reader:
            if not row:
                continue
            rows.append([int(value) for value in row[1 : 1 + len(elevator_cols)]])
    num_elevators = len(elevator_cols)
    num_floors = max(max(row) for row in rows) if rows else 2
    return num_floors, num_elevators, rows


def replay_states(rows: list[list[int]], num_floors: int, num_elevators: int):
    for index, floors in enumerate(rows):
        yield {
            "type": "tick",
            "t": index,
            "done": index == len(rows) - 1,
            "num_floors": num_floors,
            "num_elevators": num_elevators,
            "elevators": [
                {"id": elevator_id, "floor": floor}
                for elevator_id, floor in enumerate(floors)
            ],
            "waiting": [],
        }


def _redraw() -> None:
    import bpy

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _hide_splash() -> None:
    import bpy

    try:
        bpy.context.preferences.view.show_splash = False
    except Exception:
        pass


def start_live(host: str, port: int, num_floors: int, num_elevators: int) -> None:
    import bpy

    incoming: queue.Queue = queue.Queue()
    stop = threading.Event()
    build_scene(num_floors, num_elevators)
    frame_building(num_floors, num_elevators)

    thread = threading.Thread(
        target=reader_thread,
        args=(host, port, incoming, stop),
        daemon=True,
    )
    thread.start()
    print(f"Elevator listener connecting to {host}:{port}", flush=True)

    def poll() -> float | None:
        while True:
            try:
                message = incoming.get_nowait()
            except queue.Empty:
                break
            kind = message.get("type")
            if kind == "error":
                print(f"listener error: {message.get('message')}", flush=True)
            elif kind == "connected":
                print("connected to simulator", flush=True)
            elif kind == "hello":
                build_scene(int(message["num_floors"]), int(message["num_elevators"]))
                frame_building(int(message["num_floors"]), int(message["num_elevators"]))
            elif kind == "tick":
                apply_tick(message)
                if message.get("done"):
                    print("simulation complete", flush=True)
            elif kind == "closed":
                print("simulator disconnected", flush=True)
        _redraw()
        return 0.05

    bpy.app.timers.register(poll, first_interval=0.05, persistent=True)


def start_replay(path: str, delay: float, loop: bool) -> None:
    import bpy

    num_floors, num_elevators, rows = load_replay(path)
    build_scene(num_floors, num_elevators)
    frame_building(num_floors, num_elevators)
    states = list(replay_states(rows, num_floors, num_elevators))
    index = {"value": 0}
    print(f"Replaying {path} ({len(states)} ticks, {num_elevators} cars, {num_floors} floors)", flush=True)

    def poll() -> float | None:
        if not states:
            return None
        apply_tick(states[index["value"]])
        _redraw()
        index["value"] += 1
        if index["value"] >= len(states):
            if loop:
                index["value"] = 0
            else:
                print("replay complete", flush=True)
                return None
        return delay

    bpy.app.timers.register(poll, first_interval=0.4, persistent=True)


def main() -> None:
    args = parse_args()
    try:
        import bpy
    except ImportError as exc:
        raise SystemExit(
            "This script must be launched from Blender, e.g.\n"
            "  blender --factory-startup --python blender/live_listener.py -- --replay outputs/positions.csv"
        ) from exc

    _hide_splash()

    def _boot() -> None:
        if args.replay:
            start_replay(args.replay, args.delay, args.loop)
        else:
            start_live(args.host, args.port, args.floors, args.elevators)

    bpy.app.timers.register(_boot, first_interval=0.5)


if __name__ == "__main__":
    main()
