from __future__ import annotations

from dataclasses import dataclass, field


def travel_direction(source: int, dest: int) -> int:
    if dest > source:
        return 1
    if dest < source:
        return -1
    return 0


@dataclass(frozen=True)
class Request:
    time: int
    id: str
    source: int
    dest: int
    name: str = ""
    role: str = "guest"
    icon: str = "user"

    def __post_init__(self) -> None:
        if self.time < 0:
            raise ValueError(f"request {self.id} has negative time")
        if self.source == self.dest:
            raise ValueError(f"request {self.id} has source == dest")
        if self.role not in {"employee", "guest"}:
            object.__setattr__(self, "role", "guest")


@dataclass
class Passenger:
    id: str
    source: int
    dest: int
    request_time: int
    assigned_elevator: int | None = None
    pickup_time: int | None = None
    dropoff_time: int | None = None
    name: str = ""
    role: str = "guest"
    icon: str = "user"

    @property
    def direction(self) -> int:
        return travel_direction(self.source, self.dest)

    @property
    def wait_time(self) -> int | None:
        if self.pickup_time is None:
            return None
        return self.pickup_time - self.request_time

    @property
    def travel_time(self) -> int | None:
        if self.pickup_time is None or self.dropoff_time is None:
            return None
        return self.dropoff_time - self.pickup_time

    @property
    def total_time(self) -> int | None:
        if self.dropoff_time is None:
            return None
        return self.dropoff_time - self.request_time

    @property
    def is_complete(self) -> bool:
        return self.dropoff_time is not None


@dataclass
class Elevator:
    id: int
    floor: int
    capacity: int
    direction: int = 0
    passengers: list[Passenger] = field(default_factory=list)
    pending: list[Passenger] = field(default_factory=list)
    allowed_floors: frozenset[int] | None = None

    @property
    def load(self) -> int:
        return len(self.passengers)

    @property
    def remaining_capacity(self) -> int:
        return self.capacity - self.load

    def can_stop_at(self, floor: int) -> bool:
        return self.allowed_floors is None or floor in self.allowed_floors

    def can_serve(self, source: int, dest: int) -> bool:
        return self.can_stop_at(source) and self.can_stop_at(dest)

    def snapshot(self) -> dict:
        return {
            "id": self.id,
            "floor": self.floor,
            "direction": self.direction,
            "load": self.load,
            "capacity": self.capacity,
            "onboard": [p.id for p in self.passengers],
            "onboard_dests": [p.dest for p in self.passengers],
            "onboard_people": [_person_payload(p) for p in self.passengers],
            "pending_pickups": [
                {"id": p.id, "floor": p.source, "dest": p.dest, **_identity(p)}
                for p in self.pending
            ],
            "allowed_floors": sorted(self.allowed_floors) if self.allowed_floors else None,
        }


def _identity(passenger: Passenger) -> dict:
    return {
        "name": passenger.name or passenger.id,
        "role": passenger.role if passenger.role in {"employee", "guest"} else "guest",
        "icon": passenger.icon or "user",
    }


def _person_payload(passenger: Passenger) -> dict:
    return {
        "id": passenger.id,
        "dest": passenger.dest,
        **_identity(passenger),
    }
