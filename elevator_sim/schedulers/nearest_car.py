from __future__ import annotations

from elevator_sim.config import BuildingConfig
from elevator_sim.models import Elevator, Passenger, travel_direction


def pickup_eta(
    elevator: Elevator,
    source: int,
    dest: int,
    extra_pending: list[Passenger],
) -> float:
    """Heuristic time until this car could pick up a passenger at `source`."""
    if not elevator.can_serve(source, dest):
        return float("inf")

    passenger_dir = travel_direction(source, dest)
    pending = list(elevator.pending) + extra_pending
    load_pressure = elevator.load + len(pending)
    penalty = 20.0 if load_pressure >= elevator.capacity else 0.5 * load_pressure

    if elevator.direction == 0:
        return abs(elevator.floor - source) + penalty

    same_way = (
        elevator.direction == passenger_dir
        and (
            (elevator.direction == 1 and source >= elevator.floor)
            or (elevator.direction == -1 and source <= elevator.floor)
        )
    )
    if same_way:
        return abs(elevator.floor - source) + penalty

    committed = [elevator.floor]
    committed.extend(p.dest for p in elevator.passengers)
    committed.extend(p.source for p in pending)
    if elevator.direction == 1:
        turnaround = max(committed)
        return (turnaround - elevator.floor) + abs(turnaround - source) + penalty
    turnaround = min(committed)
    return (elevator.floor - turnaround) + abs(source - turnaround) + penalty


def assign_by_cost(
    batch: list[Passenger],
    elevators: list[Elevator],
    cost_fn,
) -> dict[str, int]:
    mapping: dict[str, int] = {}
    extra: dict[int, list[Passenger]] = {elevator.id: [] for elevator in elevators}

    for passenger in batch:
        best_id: int | None = None
        best_cost = float("inf")
        for elevator in elevators:
            cost = cost_fn(elevator, passenger, extra[elevator.id])
            if cost < best_cost:
                best_cost = cost
                best_id = elevator.id
        if best_id is None:
            best_id = min(elevators, key=lambda item: abs(item.floor - passenger.source)).id
        mapping[passenger.id] = best_id
        extra[best_id].append(passenger)
    return mapping


class NearestCarScheduler:
    name = "nearest"

    def assign(
        self,
        batch: list[Passenger],
        elevators: list[Elevator],
        config: BuildingConfig,
    ) -> dict[str, int]:
        del config

        def cost(elevator: Elevator, passenger: Passenger, extra_pending: list[Passenger]) -> float:
            return pickup_eta(elevator, passenger.source, passenger.dest, extra_pending)

        return assign_by_cost(batch, elevators, cost)
