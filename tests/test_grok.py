from __future__ import annotations

import json
from unittest.mock import patch

from elevator_sim.config import BuildingConfig
from elevator_sim.models import Elevator, Passenger
from elevator_sim.schedulers.grok import GrokScheduler


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _batch():
    return [Passenger(id="passenger1", source=1, dest=8, request_time=0)]


def _elevators():
    config = BuildingConfig(num_elevators=2, num_floors=10, capacity=4)
    elevators = [Elevator(id=0, floor=1, capacity=4), Elevator(id=1, floor=4, capacity=4)]
    return elevators, config


def test_grok_parses_batch_assignments():
    elevators, config = _elevators()
    scheduler = GrokScheduler(api_key="test-key")
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({"assignments": {"passenger1": 1}}),
                }
            }
        ]
    }
    with patch("elevator_sim.schedulers.grok.urllib.request.urlopen", return_value=_FakeResponse(payload)):
        mapping = scheduler.assign(_batch(), elevators, config)
    assert mapping == {"passenger1": 1}
    assert scheduler.api_calls == 1
    assert scheduler.fallback_calls == 0


def test_grok_falls_back_without_key():
    elevators, config = _elevators()
    scheduler = GrokScheduler(api_key="")
    mapping = scheduler.assign(_batch(), elevators, config)
    assert mapping["passenger1"] in {0, 1}
    assert scheduler.fallback_calls == 1
    assert scheduler.api_calls == 0


def test_grok_falls_back_on_invalid_elevator():
    elevators, config = _elevators()
    scheduler = GrokScheduler(api_key="test-key")
    payload = {
        "choices": [
            {"message": {"content": json.dumps({"assignments": {"passenger1": 99}})}}
        ]
    }
    with patch("elevator_sim.schedulers.grok.urllib.request.urlopen", return_value=_FakeResponse(payload)):
        mapping = scheduler.assign(_batch(), elevators, config)
    assert mapping["passenger1"] in {0, 1}
    assert scheduler.fallback_calls == 1


def test_grok_strips_markdown_fence():
    elevators, config = _elevators()
    scheduler = GrokScheduler(api_key="test-key")
    fenced = "```json\n" + json.dumps({"assignments": {"passenger1": 0}}) + "\n```"
    payload = {"choices": [{"message": {"content": fenced}}]}
    with patch("elevator_sim.schedulers.grok.urllib.request.urlopen", return_value=_FakeResponse(payload)):
        mapping = scheduler.assign(_batch(), elevators, config)
    assert mapping == {"passenger1": 0}
