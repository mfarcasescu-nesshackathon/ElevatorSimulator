from elevator_sim.schedulers.grok import GrokScheduler
from elevator_sim.schedulers.nearest_car import NearestCarScheduler
from elevator_sim.schedulers.round_robin import RoundRobinScheduler
from elevator_sim.schedulers.zone import ZoneScheduler

SCHEDULER_NAMES = ("nearest", "round_robin", "zone", "grok")


def get_scheduler(name: str):
    key = name.strip().lower().replace("-", "_")
    if key == "nearest":
        return NearestCarScheduler()
    if key == "round_robin":
        return RoundRobinScheduler()
    if key == "zone":
        return ZoneScheduler()
    if key == "grok":
        return GrokScheduler()
    raise ValueError(f"unknown scheduler {name!r}; choose from {', '.join(SCHEDULER_NAMES)}")
