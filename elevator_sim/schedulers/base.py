from __future__ import annotations

from typing import Protocol

from elevator_sim.config import BuildingConfig
from elevator_sim.models import Elevator, Passenger


class Scheduler(Protocol):
    name: str

    def assign(
        self,
        batch: list[Passenger],
        elevators: list[Elevator],
        config: BuildingConfig,
    ) -> dict[str, int]:
        """Assign every passenger in the current-time batch to an elevator id.

        Must not inspect requests that have not been admitted yet. Destination
        is sticky after this mapping is applied by the engine.
        """
        ...
