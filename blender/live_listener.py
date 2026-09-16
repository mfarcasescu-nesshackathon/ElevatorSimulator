"""Live Blender client: listen for JSON-line ticks and move elevator cars.

1. Start the simulator with live streaming:
       python -m elevator_sim run --requests samples/small.csv --floors 8 --elevators 2 --live --tick-delay 0.15
2. In another terminal, with Blender on PATH:
       blender --python blender/live_listener.py -- --host 127.0.0.1 --port 8765

Press Esc in the Blender window to stop the listener.
"""

from __future__ import annotations

import json
import queue
import socket
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from create_scene import apply_tick, build_scene  # noqa: E402


def parse_args(argv: list[str] | None = None):
    import argparse

    raw = argv if argv is not None else sys.argv
    if "--" in raw:
        raw = raw[raw.index("--") + 1 :]
    parser = argparse.ArgumentParser(description="Live elevator visualization for Blender")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--floors", type=int, default=20)
    parser.add_argument("--elevators", type=int, default=4)
    return parser.parse_args(raw)


def reader_thread(host: str, port: int, incoming: queue.Queue, stop: threading.Event) -> None:
    try:
        sock = socket.create_connection((host, port), timeout=30)
    except OSError as exc:
        incoming.put({"type": "error", "message": str(exc)})
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
        sock.close()


def register_operator(host: str, port: int, num_floors: int, num_elevators: int):
    import bpy

    incoming: queue.Queue = queue.Queue()
    stop = threading.Event()

    class ElevatorLiveOperator(bpy.types.Operator):
        bl_idname = "wm.elevator_live_listener"
        bl_label = "Elevator Live Listener"

        def modal(self, context, event):
            if event.type == "ESC":
                return self._stop(context, "Cancelled")
            if event.type != "TIMER":
                return {"PASS_THROUGH"}
            while True:
                try:
                    message = incoming.get_nowait()
                except queue.Empty:
                    break
                kind = message.get("type")
                if kind == "error":
                    self.report({"WARNING"}, message.get("message", "socket error"))
                elif kind == "hello":
                    build_scene(int(message["num_floors"]), int(message["num_elevators"]))
                elif kind == "tick":
                    apply_tick(message)
                    if message.get("done"):
                        self.report({"INFO"}, "Simulation complete")
                elif kind == "closed":
                    self.report({"INFO"}, "Simulator disconnected")
            for area in context.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
            return {"PASS_THROUGH"}

        def execute(self, context):
            build_scene(num_floors, num_elevators)
            self._timer = context.window_manager.event_timer_add(0.05, window=context.window)
            context.window_manager.modal_handler_add(self)
            self._thread = threading.Thread(
                target=reader_thread,
                args=(host, port, incoming, stop),
                daemon=True,
            )
            self._thread.start()
            self.report({"INFO"}, f"Connecting to {host}:{port}")
            return {"RUNNING_MODAL"}

        def _stop(self, context, message: str):
            stop.set()
            context.window_manager.event_timer_remove(self._timer)
            self.report({"INFO"}, message)
            return {"CANCELLED"}

    bpy.utils.register_class(ElevatorLiveOperator)
    bpy.ops.wm.elevator_live_listener()


def main() -> None:
    args = parse_args()
    try:
        import bpy  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "This script must be launched from Blender, e.g.\n"
            "  blender --python blender/live_listener.py -- --port 8765"
        ) from exc
    register_operator(args.host, args.port, args.floors, args.elevators)


if __name__ == "__main__":
    main()
