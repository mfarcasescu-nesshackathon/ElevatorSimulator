from elevator_sim.config import BuildingConfig
from elevator_sim.models import Request
from elevator_sim.simulation import run_simulation


def make_config(**overrides) -> BuildingConfig:
    values = {"num_elevators": 2, "num_floors": 10, "capacity": 4}
    values.update(overrides)
    return BuildingConfig(**values)


def req(time: int, ident: str, source: int, dest: int) -> Request:
    return Request(time=time, id=ident, source=source, dest=dest)


def simulate(requests, scheduler=None, **config_kwargs):
    return run_simulation(requests, make_config(**config_kwargs), scheduler=scheduler)
