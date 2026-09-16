from elevator_sim.config import BuildingConfig
from elevator_sim.demand import generate_demand
from elevator_sim.schedulers.nearest_car import NearestCarScheduler
from elevator_sim.serialize import result_to_json
from elevator_sim.server import _run_from_payload
from elevator_sim.simulation import run_simulation


def test_generate_demand_respects_floors():
    config = BuildingConfig(num_elevators=3, num_floors=10, capacity=6)
    requests = generate_demand(config, passenger_count=12, seed=2)
    assert len(requests) == 12
    assert all(1 <= item.source <= 10 and 1 <= item.dest <= 10 for item in requests)
    assert all(" " in item.name for item in requests)
    assert all(item.role in {"employee", "guest"} for item in requests)


def test_snapshots_match_ticks():
    config = BuildingConfig(num_elevators=2, num_floors=8, capacity=4)
    requests = generate_demand(config, passenger_count=6, seed=1)
    result = run_simulation(requests, config, scheduler=NearestCarScheduler())
    assert result.snapshots
    assert len(result.snapshots) == len(result.positions)
    assert result.snapshots[-1]["done"] is True
    payload = result_to_json(result)
    assert payload["stats"]["count"] == 6


def test_api_payload_runs():
    payload = _run_from_payload(
        {
            "elevators": 3,
            "floors": 8,
            "capacity": 4,
            "passengers": 8,
            "scheduler": "nearest",
            "seed": 4,
        }
    )
    assert payload["config"]["num_elevators"] == 3
    assert payload["snapshots"][0]["waiting"][0].get("is_new") is True or payload["snapshots"][0]["waiting"] == []
    assert payload["stats"]["count"] == 8
    waiting = next((tick["waiting"] for tick in payload["snapshots"] if tick["waiting"]), [])
    assert waiting[0]["name"]
    assert waiting[0]["role"] in {"employee", "guest"}
