from __future__ import annotations

from elevator_sim.io import observations, summarize_passengers
from elevator_sim.simulation import SimulationResult


def result_to_json(result: SimulationResult) -> dict:
    summary = summarize_passengers(result.passengers)
    return {
        "scheduler": result.scheduler_name,
        "config": {
            "num_elevators": result.config.num_elevators,
            "num_floors": result.config.num_floors,
            "capacity": result.config.capacity,
        },
        "ticks": result.ticks,
        "positions": result.positions,
        "snapshots": result.snapshots,
        "stats": summary,
        "observations": observations(result),
        "passengers": [
            {
                "id": passenger.id,
                "name": passenger.name or passenger.id,
                "role": passenger.role,
                "icon": passenger.icon,
                "source": passenger.source,
                "dest": passenger.dest,
                "request_time": passenger.request_time,
                "assigned_elevator": passenger.assigned_elevator,
                "wait_time": passenger.wait_time,
                "travel_time": passenger.travel_time,
                "total_time": passenger.total_time,
            }
            for passenger in result.passengers
        ],
    }
