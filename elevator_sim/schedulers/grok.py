from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from elevator_sim.config import BuildingConfig
from elevator_sim.models import Elevator, Passenger
from elevator_sim.schedulers.nearest_car import NearestCarScheduler

DEFAULT_GROK_MODEL = "grok-4-fast"
DEFAULT_GROK_URL = "https://api.x.ai/v1/chat/completions"


class GrokScheduler:
    """Assign an entire same-timestamp batch with one Grok API call."""

    name = "grok"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
        fallback: NearestCarScheduler | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("XAI_API_KEY", "")
        self.model = model or os.environ.get("GROK_MODEL", DEFAULT_GROK_MODEL)
        self.timeout_seconds = timeout_seconds
        self.fallback = fallback or NearestCarScheduler()
        self.last_error: str | None = None
        self.api_calls = 0
        self.fallback_calls = 0

    def assign(
        self,
        batch: list[Passenger],
        elevators: list[Elevator],
        config: BuildingConfig,
    ) -> dict[str, int]:
        fallback_map = self.fallback.assign(batch, elevators, config)
        if not batch:
            return {}
        if not self.api_key:
            self.last_error = "XAI_API_KEY is not set"
            self.fallback_calls += 1
            return fallback_map

        try:
            payload = self._complete(batch, elevators, config)
            mapping = self._validate(payload, batch, elevators, config, fallback_map)
            self.api_calls += 1
            self.last_error = None
            return mapping
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, KeyError) as exc:
            self.last_error = str(exc)
            self.fallback_calls += 1
            return fallback_map

    def _complete(
        self,
        batch: list[Passenger],
        elevators: list[Elevator],
        config: BuildingConfig,
    ) -> dict:
        body = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a destination-dispatch elevator controller. "
                        "Assign every new passenger in the batch to exactly one elevator. "
                        "Minimize wait_time + travel_time. Honor capacity, direction, and "
                        "express stop constraints. Never leave a passenger unassigned. "
                        "Reply with JSON only: "
                        '{"assignments": {"passenger_id": elevator_id, ...}}'
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(self._state_payload(batch, elevators, config)),
                },
            ],
        }
        request = urllib.request.Request(
            os.environ.get("GROK_API_URL", DEFAULT_GROK_URL),
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
        content = raw["choices"][0]["message"]["content"]
        return _parse_json_content(content)

    def _state_payload(
        self,
        batch: list[Passenger],
        elevators: list[Elevator],
        config: BuildingConfig,
    ) -> dict:
        return {
            "building": {
                "num_floors": config.num_floors,
                "num_elevators": config.num_elevators,
                "capacity": config.capacity,
            },
            "elevators": [elevator.snapshot() for elevator in elevators],
            "new_requests": [
                {
                    "id": passenger.id,
                    "source": passenger.source,
                    "dest": passenger.dest,
                    "direction": passenger.direction,
                }
                for passenger in batch
            ],
        }

    def _validate(
        self,
        payload: dict,
        batch: list[Passenger],
        elevators: list[Elevator],
        config: BuildingConfig,
        fallback_map: dict[str, int],
    ) -> dict[str, int]:
        assignments = payload.get("assignments", payload)
        if not isinstance(assignments, dict):
            raise ValueError("Grok response is missing assignments")

        valid_ids = {elevator.id for elevator in elevators}
        mapping: dict[str, int] = {}
        used_fallback = False
        for passenger in batch:
            raw = assignments.get(passenger.id, assignments.get(str(passenger.id)))
            try:
                elevator_id = int(raw)
            except (TypeError, ValueError):
                elevator_id = fallback_map[passenger.id]
                used_fallback = True
            if elevator_id not in valid_ids:
                elevator_id = fallback_map[passenger.id]
                used_fallback = True
            elif not config.can_serve(elevator_id, passenger.source, passenger.dest):
                elevator_id = fallback_map[passenger.id]
                used_fallback = True
            mapping[passenger.id] = elevator_id
        if used_fallback:
            self.fallback_calls += 1
        return mapping


def _parse_json_content(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)
