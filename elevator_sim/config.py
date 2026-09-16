from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BuildingConfig:
    """Configurable building: elevator count, floors, capacity, optional express cars."""

    num_elevators: int = 4
    num_floors: int = 20
    capacity: int = 8
    # elevator_id -> floors that car may stop at. Missing id means every floor.
    express_stops: dict[int, frozenset[int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 1 <= self.num_elevators <= 10:
            raise ValueError("num_elevators must be between 1 and 10")
        if self.num_floors < 2:
            raise ValueError("num_floors must be at least 2")
        if self.capacity < 1:
            raise ValueError("capacity must be at least 1")
        stops = {
            elevator_id: frozenset(floors)
            for elevator_id, floors in self.express_stops.items()
        }
        object.__setattr__(self, "express_stops", stops)
        for elevator_id, floors in self.express_stops.items():
            if elevator_id < 0 or elevator_id >= self.num_elevators:
                raise ValueError(f"express elevator id {elevator_id} is out of range")
            if not floors:
                raise ValueError(f"express elevator {elevator_id} has no stop floors")
            for floor in floors:
                if not 1 <= floor <= self.num_floors:
                    raise ValueError(
                        f"express elevator {elevator_id} stop {floor} is out of range"
                    )

    def allowed_floors(self, elevator_id: int) -> frozenset[int] | None:
        """None means the car may stop at every floor."""
        return self.express_stops.get(elevator_id)

    def can_serve(self, elevator_id: int, source: int, dest: int) -> bool:
        allowed = self.allowed_floors(elevator_id)
        if allowed is None:
            return True
        return source in allowed and dest in allowed


def parse_express_flag(value: str, num_floors: int) -> tuple[int, frozenset[int]]:
    """Parse `elevator_id:1,10,20` into (id, floors). Use `all` for every floor."""
    if ":" not in value:
        raise ValueError("express spec must look like 0:1,10,20,30")
    raw_id, raw_floors = value.split(":", 1)
    elevator_id = int(raw_id)
    if raw_floors.strip().lower() == "all":
        floors = frozenset(range(1, num_floors + 1))
    else:
        floors = frozenset(int(part.strip()) for part in raw_floors.split(",") if part.strip())
    return elevator_id, floors
