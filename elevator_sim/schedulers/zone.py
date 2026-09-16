from __future__ import annotations

import math

from elevator_sim.config import BuildingConfig
from elevator_sim.models import Elevator, Passenger
from elevator_sim.schedulers.nearest_car import pickup_eta


class ZoneScheduler:
    """Each elevator owns a contiguous band of floors (origin-based zoning)."""

    name = "zone"

    def assign(
        self,
        batch: list[Passenger],
        elevators: list[Elevator],
        config: BuildingConfig,
    ) -> dict[str, int]:
        mapping: dict[str, int] = {}
        extra: dict[int, list[Passenger]] = {elevator.id: [] for elevator in elevators}
        zone_size = math.ceil(config.num_floors / config.num_elevators)

        for passenger in batch:
            preferred = min((passenger.source - 1) // zone_size, config.num_elevators - 1)
            ordered = sorted(
                elevators,
                key=lambda elevator: (
                    0 if elevator.id == preferred else 1,
                    0 if elevator.can_serve(passenger.source, passenger.dest) else 1,
                    abs(elevator.id - preferred),
                    pickup_eta(elevator, passenger.source, passenger.dest, extra[elevator.id]),
                ),
            )
            chosen = ordered[0].id
            mapping[passenger.id] = chosen
            extra[chosen].append(passenger)
        return mapping
