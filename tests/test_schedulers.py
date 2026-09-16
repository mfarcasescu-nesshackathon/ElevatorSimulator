from elevator_sim.config import BuildingConfig
from elevator_sim.models import Elevator, Passenger
from elevator_sim.schedulers import get_scheduler
from elevator_sim.schedulers.nearest_car import NearestCarScheduler
from elevator_sim.schedulers.round_robin import RoundRobinScheduler
from elevator_sim.schedulers.zone import ZoneScheduler
from tests.conftest import req, simulate


def _passenger(ident: str, source: int, dest: int) -> Passenger:
    return Passenger(id=ident, source=source, dest=dest, request_time=0)


def _elevators(count: int = 3, floors: int = 20) -> tuple[list[Elevator], BuildingConfig]:
    config = BuildingConfig(num_elevators=count, num_floors=floors, capacity=8)
    elevators = [
        Elevator(id=index, floor=1, capacity=8)
        for index in range(count)
    ]
    return elevators, config


def test_nearest_prefers_closer_car():
    elevators, config = _elevators(2)
    elevators[0].floor = 1
    elevators[1].floor = 10
    mapping = NearestCarScheduler().assign([_passenger("p", 9, 12)], elevators, config)
    assert mapping["p"] == 1


def test_round_robin_cycles():
    elevators, config = _elevators(2)
    scheduler = RoundRobinScheduler()
    first = scheduler.assign([_passenger("a", 1, 4)], elevators, config)
    second = scheduler.assign([_passenger("b", 1, 5)], elevators, config)
    assert first["a"] != second["b"]


def test_zone_uses_origin_band():
    elevators, config = _elevators(2, floors=20)
    mapping = ZoneScheduler().assign(
        [_passenger("low", 2, 3), _passenger("high", 18, 19)],
        elevators,
        config,
    )
    assert mapping["low"] == 0
    assert mapping["high"] == 1


def test_get_scheduler_names():
    assert get_scheduler("nearest").name == "nearest"
    assert get_scheduler("round_robin").name == "round_robin"
    assert get_scheduler("zone").name == "zone"
    assert get_scheduler("grok").name == "grok"


def test_compare_local_algorithms_complete():
    from elevator_sim.compare import compare_schedulers
    from tests.conftest import make_config

    rows = compare_schedulers(
        [req(0, "a", 1, 8), req(0, "b", 1, 6), req(3, "c", 4, 1)],
        make_config(num_elevators=2, num_floors=10),
    )
    names = [name for name, _result, _summary in rows]
    assert names == ["nearest", "round_robin", "zone"]
    for _name, result, summary in rows:
        assert summary["count"] == 3
        assert all(passenger.is_complete for passenger in result.passengers)
