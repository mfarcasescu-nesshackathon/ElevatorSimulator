from __future__ import annotations

from elevator_sim.config import BuildingConfig
from elevator_sim.models import Elevator, Passenger


class RoundRobinScheduler:
    name = "round_robin"

    def __init__(self) -> None:
        self._next = 0

    def assign(
        self,
        batch: list[Passenger],
        elevators: list[Elevator],
        config: BuildingConfig,
    ) -> dict[str, int]:
        del config
        mapping: dict[str, int] = {}
        count = len(elevators)
        for passenger in batch:
            assigned: int | None = None
            for offset in range(count):
                elevator = elevators[(self._next + offset) % count]
                if elevator.can_serve(passenger.source, passenger.dest):
                    assigned = elevator.id
                    self._next = (elevator.id + 1) % count
                    break
            if assigned is None:
                assigned = elevators[self._next % count].id
                self._next = (self._next + 1) % count
            mapping[passenger.id] = assigned
        return mapping
