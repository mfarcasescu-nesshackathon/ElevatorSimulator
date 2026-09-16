from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from elevator_sim.config import BuildingConfig
from elevator_sim.demand import generate_demand
from elevator_sim.models import Request
from elevator_sim.schedulers import SCHEDULER_NAMES, get_scheduler
from elevator_sim.serialize import result_to_json
from elevator_sim.simulation import run_simulation

MAX_PASSENGERS = 80


def run_web_server(host: str = "127.0.0.1", port: int = 8766) -> None:
    server = ThreadingHTTPServer((host, port), SimulateHandler)
    print(f"Simulator API at http://{host}:{port}/api/simulate")
    print("POST JSON: elevators, floors, capacity, scheduler, passengers, seed")
    server.serve_forever()


class SimulateHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        print("[api]", self.address_string(), args[0] if args else "")

    def do_OPTIONS(self) -> None:
        self._ok(204)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/health"}:
            self._json(200, {"ok": True, "schedulers": list(SCHEDULER_NAMES)})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/simulate":
            self._json(404, {"error": "not found"})
            return
        try:
            payload = self._read_json()
            result = _run_from_payload(payload)
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
            return
        except Exception as exc:
            self._json(500, {"error": str(exc)})
            return
        self._json(200, result)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _ok(self, status: int) -> None:
        self.send_response(status)
        self._cors()
        self.end_headers()

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def _run_from_payload(payload: dict) -> dict:
    elevators = _int(payload.get("elevators", 4), "elevators", 1, 10)
    floors = _int(payload.get("floors", 20), "floors", 2, 60)
    capacity = _int(payload.get("capacity", 8), "capacity", 1, 20)
    passenger_count = _int(payload.get("passengers", 24), "passengers", 1, MAX_PASSENGERS)
    seed = _int(payload.get("seed", 1), "seed", 0, 1_000_000)
    scheduler_name = str(payload.get("scheduler", "nearest"))
    config = BuildingConfig(num_elevators=elevators, num_floors=floors, capacity=capacity)
    if payload.get("requests"):
        requests = [_request_from_row(row, config) for row in payload["requests"]]
    else:
        requests = generate_demand(config, passenger_count=passenger_count, seed=seed)
    scheduler = get_scheduler(scheduler_name)
    result = run_simulation(requests, config, scheduler=scheduler)
    body = result_to_json(result)
    body["request_count"] = len(requests)
    return body


def _request_from_row(row: dict, config: BuildingConfig) -> Request:
    request = Request(
        time=int(row["time"]),
        id=str(row["id"]),
        source=int(row["source"]),
        dest=int(row["dest"]),
        name=str(row.get("name") or row["id"]),
        role=str(row.get("role") or "guest"),
        icon=str(row.get("icon") or "user"),
    )
    if not 1 <= request.source <= config.num_floors or not 1 <= request.dest <= config.num_floors:
        raise ValueError(f"{request.id} has a floor outside 1..{config.num_floors}")
    return request


def _int(value, name: str, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return number
