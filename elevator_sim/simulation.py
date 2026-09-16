from __future__ import annotations

from dataclasses import dataclass, field

from elevator_sim.config import BuildingConfig
from elevator_sim.models import Elevator, Passenger, Request
from elevator_sim.schedulers.base import Scheduler
from elevator_sim.schedulers.nearest_car import NearestCarScheduler


@dataclass
class SimulationResult:
    config: BuildingConfig
    scheduler_name: str
    positions: list[list[int]]
    passengers: list[Passenger]
    ticks: int
    extra: dict = field(default_factory=dict)
    snapshots: list[dict] = field(default_factory=list)


class PeekingScheduler:
    """Wraps a scheduler and records every admitted batch for tests."""

    def __init__(self, inner: Scheduler) -> None:
        self.inner = inner
        self.admitted_ids: list[list[str]] = []

    @property
    def name(self) -> str:
        return self.inner.name

    def assign(
        self,
        batch: list[Passenger],
        elevators: list[Elevator],
        config: BuildingConfig,
    ) -> dict[str, int]:
        self.admitted_ids.append([passenger.id for passenger in batch])
        return self.inner.assign(batch, elevators, config)


def run_simulation(
    requests: list[Request],
    config: BuildingConfig,
    scheduler: Scheduler | None = None,
    publisher=None,
    max_ticks: int | None = None,
) -> SimulationResult:
    scheduler = scheduler or NearestCarScheduler()
    elevators = [
        Elevator(
            id=index,
            floor=1,
            capacity=config.capacity,
            allowed_floors=config.allowed_floors(index),
        )
        for index in range(config.num_elevators)
    ]
    pending_requests = sorted(requests, key=lambda item: (item.time, item.id))
    _validate_requests(pending_requests, config)

    admitted: dict[str, Passenger] = {}
    completed: list[Passenger] = []
    positions: list[list[int]] = []
    snapshots: list[dict] = []
    time = 0
    limit = max_ticks if max_ticks is not None else _default_max_ticks(pending_requests, config)

    while time <= limit:
        positions.append([elevator.floor for elevator in elevators])
        if publisher is not None:
            publisher.publish(_tick_state(time, config, elevators, admitted, completed, done=False))

        batch = _admit(pending_requests, time, admitted, config)
        if batch:
            mapping = scheduler.assign(batch, elevators, config)
            _apply_assignments(batch, mapping, elevators, config)

        for elevator in elevators:
            _alight(elevator, time, completed)
            _board(elevator, time)
            elevator.direction = _choose_direction(elevator, config.num_floors)
            _board(elevator, time)

        unfinished = any(
            passenger.dropoff_time is None for passenger in admitted.values()
        )
        done = not pending_requests and not unfinished
        snapshots.append(_tick_state(time, config, elevators, admitted, completed, done=done))
        if done:
            if publisher is not None:
                publisher.publish(snapshots[-1])
            break

        for elevator in elevators:
            _move(elevator, config.num_floors)
        time += 1
    else:
        raise RuntimeError(
            f"simulation exceeded {limit} ticks without serving all passengers"
        )

    return SimulationResult(
        config=config,
        scheduler_name=getattr(scheduler, "name", "unknown"),
        positions=positions,
        passengers=sorted(completed, key=lambda passenger: passenger.id),
        ticks=time,
        extra={"admitted": len(admitted)},
        snapshots=snapshots,
    )


def _validate_requests(requests: list[Request], config: BuildingConfig) -> None:
    seen: set[str] = set()
    for request in requests:
        if request.id in seen:
            raise ValueError(f"duplicate passenger id {request.id}")
        seen.add(request.id)
        if not 1 <= request.source <= config.num_floors:
            raise ValueError(f"{request.id} source {request.source} is out of range")
        if not 1 <= request.dest <= config.num_floors:
            raise ValueError(f"{request.id} dest {request.dest} is out of range")


def _default_max_ticks(requests: list[Request], config: BuildingConfig) -> int:
    last_request = max((request.time for request in requests), default=0)
    return last_request + max(len(requests), 1) * config.num_floors * 4 + 100


def _admit(
    pending_requests: list[Request],
    time: int,
    admitted: dict[str, Passenger],
    config: BuildingConfig,
) -> list[Passenger]:
    del config
    batch: list[Passenger] = []
    while pending_requests and pending_requests[0].time == time:
        request = pending_requests.pop(0)
        passenger = Passenger(
            id=request.id,
            source=request.source,
            dest=request.dest,
            request_time=request.time,
            name=request.name or request.id,
            role=request.role,
            icon=request.icon,
        )
        admitted[passenger.id] = passenger
        batch.append(passenger)
    return batch


def _apply_assignments(
    batch: list[Passenger],
    mapping: dict[str, int],
    elevators: list[Elevator],
    config: BuildingConfig,
) -> None:
    by_id = {elevator.id: elevator for elevator in elevators}
    for passenger in batch:
        if passenger.assigned_elevator is not None:
            continue
        servable = [
            elevator.id
            for elevator in elevators
            if elevator.can_serve(passenger.source, passenger.dest)
        ]
        if not servable:
            raise ValueError(
                f"{passenger.id} cannot be served by any elevator "
                f"(source={passenger.source}, dest={passenger.dest})"
            )
        raw = mapping.get(passenger.id)
        if raw not in by_id or not config.can_serve(raw, passenger.source, passenger.dest):
            raw = servable[0]
        passenger.assigned_elevator = raw
        by_id[raw].pending.append(passenger)


def _alight(elevator: Elevator, time: int, completed: list[Passenger]) -> None:
    staying: list[Passenger] = []
    for passenger in elevator.passengers:
        if passenger.dest == elevator.floor:
            passenger.dropoff_time = time
            completed.append(passenger)
        else:
            staying.append(passenger)
    elevator.passengers = staying


def _board(elevator: Elevator, time: int) -> None:
    still_pending: list[Passenger] = []
    for passenger in elevator.pending:
        if passenger.source != elevator.floor:
            still_pending.append(passenger)
            continue
        if not elevator.can_stop_at(elevator.floor):
            still_pending.append(passenger)
            continue
        if elevator.remaining_capacity <= 0:
            still_pending.append(passenger)
            continue
        if elevator.direction != 0 and passenger.direction != elevator.direction:
            still_pending.append(passenger)
            continue
        if elevator.direction == 0:
            elevator.direction = passenger.direction
        passenger.pickup_time = time
        elevator.passengers.append(passenger)
    elevator.pending = still_pending


def _stops_in_direction(elevator: Elevator, direction: int) -> bool:
    if direction == 1:
        if any(passenger.dest > elevator.floor for passenger in elevator.passengers):
            return True
        return any(
            passenger.source > elevator.floor and passenger.direction == 1
            for passenger in elevator.pending
        )
    if direction == -1:
        if any(passenger.dest < elevator.floor for passenger in elevator.passengers):
            return True
        return any(
            passenger.source < elevator.floor and passenger.direction == -1
            for passenger in elevator.pending
        )
    return False


def _choose_direction(elevator: Elevator, num_floors: int) -> int:
    del num_floors
    current = elevator.direction
    if current != 0 and _stops_in_direction(elevator, current):
        return current
    if current != 0 and _stops_in_direction(elevator, -current):
        return -current
    if _stops_in_direction(elevator, 1):
        return 1
    if _stops_in_direction(elevator, -1):
        return -1
    if elevator.pending:
        nearest = min(elevator.pending, key=lambda passenger: abs(passenger.source - elevator.floor))
        if nearest.source > elevator.floor:
            return 1
        if nearest.source < elevator.floor:
            return -1
        return nearest.direction
    return 0


def _move(elevator: Elevator, num_floors: int) -> None:
    if elevator.direction == 1 and elevator.floor < num_floors:
        elevator.floor += 1
    elif elevator.direction == -1 and elevator.floor > 1:
        elevator.floor -= 1
    elif elevator.direction == 1 and elevator.floor >= num_floors:
        elevator.direction = -1 if _stops_in_direction(elevator, -1) else 0
        if elevator.direction == -1 and elevator.floor > 1:
            elevator.floor -= 1
    elif elevator.direction == -1 and elevator.floor <= 1:
        elevator.direction = 1 if _stops_in_direction(elevator, 1) else 0
        if elevator.direction == 1 and elevator.floor < num_floors:
            elevator.floor += 1


def _tick_state(
    time: int,
    config: BuildingConfig,
    elevators: list[Elevator],
    admitted: dict[str, Passenger],
    completed: list[Passenger],
    done: bool,
) -> dict:
    waiting = [
        {
            "id": passenger.id,
            "floor": passenger.source,
            "dest": passenger.dest,
            "elevator": passenger.assigned_elevator,
            "request_time": passenger.request_time,
            "is_new": passenger.request_time == time,
            "name": passenger.name or passenger.id,
            "role": passenger.role,
            "icon": passenger.icon,
        }
        for passenger in admitted.values()
        if passenger.pickup_time is None
    ]
    return {
        "type": "tick",
        "t": time,
        "done": done,
        "num_floors": config.num_floors,
        "num_elevators": config.num_elevators,
        "capacity": config.capacity,
        "elevators": [elevator.snapshot() for elevator in elevators],
        "waiting": waiting,
        "completed": [passenger.id for passenger in completed],
    }
