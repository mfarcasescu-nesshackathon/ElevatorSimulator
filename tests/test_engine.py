from __future__ import annotations

from elevator_sim.config import BuildingConfig
from elevator_sim.models import Passenger, Request
from elevator_sim.schedulers.nearest_car import NearestCarScheduler
from elevator_sim.simulation import PeekingScheduler, run_simulation
from tests.conftest import make_config, req, simulate


def test_one_passenger_travels_one_floor_per_tick():
    result = simulate([req(0, "p", 1, 5)], scheduler=NearestCarScheduler(), num_elevators=1)
    passenger = result.passengers[0]
    assert passenger.pickup_time == 0
    assert passenger.dropoff_time == 4
    assert passenger.wait_time == 0
    assert passenger.travel_time == 4
    assert passenger.total_time == 4
    for previous, current in zip(result.positions, result.positions[1:]):
        assert abs(current[0] - previous[0]) <= 1


def test_ticks_through_gaps_without_peeking():
    wrapper = PeekingScheduler(NearestCarScheduler())
    result = run_simulation(
        [req(0, "early", 1, 3), req(10, "late", 2, 4)],
        make_config(num_elevators=1, num_floors=10),
        scheduler=wrapper,
    )
    assert wrapper.admitted_ids[0] == ["early"]
    assert ["late"] in wrapper.admitted_ids
    assert wrapper.admitted_ids[0] != ["early", "late"]
    assert len(result.positions) >= 11
    late = next(passenger for passenger in result.passengers if passenger.id == "late")
    assert late.request_time == 10
    assert late.pickup_time is not None and late.pickup_time >= 10


def test_capacity_blocks_second_rider():
    requests = [req(0, "first", 1, 8), req(0, "second", 1, 7)]
    result = simulate(requests, num_elevators=1, capacity=1)
    by_id = {passenger.id: passenger for passenger in result.passengers}
    assert by_id["first"].pickup_time == 0
    assert by_id["second"].pickup_time is not None
    assert by_id["second"].pickup_time > by_id["first"].pickup_time


def test_assignment_is_sticky():
    class FlipScheduler:
        name = "flip"

        def __init__(self) -> None:
            self.calls = 0

        def assign(self, batch, elevators, config):
            self.calls += 1
            target = 0 if self.calls == 1 else 1
            return {passenger.id: min(target, len(elevators) - 1) for passenger in batch}

    scheduler = FlipScheduler()
    result = simulate(
        [req(0, "p", 1, 4), req(3, "q", 1, 5)],
        scheduler=scheduler,
        num_elevators=2,
    )
    first = next(passenger for passenger in result.passengers if passenger.id == "p")
    assert first.assigned_elevator == 0
    assert scheduler.calls == 2


def test_all_requests_are_served():
    requests = [
        req(0, "a", 1, 9),
        req(0, "b", 3, 1),
        req(4, "c", 5, 2),
        req(7, "d", 8, 10),
    ]
    result = simulate(requests, num_elevators=2, num_floors=10, capacity=2)
    assert {passenger.id for passenger in result.passengers} == {"a", "b", "c", "d"}
    assert all(passenger.is_complete for passenger in result.passengers)


def test_express_car_is_not_used_for_local_trip():
    config = BuildingConfig(
        num_elevators=2,
        num_floors=20,
        capacity=8,
        express_stops={0: frozenset({1, 10, 20})},
    )
    result = run_simulation(
        [Request(time=0, id="local", source=2, dest=5)],
        config,
        scheduler=NearestCarScheduler(),
    )
    assert result.passengers[0].assigned_elevator == 1


def test_destination_does_not_change():
    result = simulate([req(0, "p", 1, 6)])
    assert result.passengers[0].dest == 6
    assert result.passengers[0].source == 1
