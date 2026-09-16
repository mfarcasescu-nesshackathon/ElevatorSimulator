from __future__ import annotations

import random

from elevator_sim.config import BuildingConfig
from elevator_sim.models import Request

EMPLOYEES = [
    "Ava Chen",
    "Marcus Webb",
    "Priya Nair",
    "Elena Rossi",
    "Noah Okonkwo",
    "Sofia Alvarez",
    "Jonah Park",
    "Leila Haddad",
    "Owen Brooks",
    "Maya Patel",
    "Chris Nguyen",
    "Hannah Berg",
    "Diego Santos",
    "Amelia Shaw",
    "Kenji Mori",
]
GUESTS = [
    "Jordan Hale",
    "Samira Cole",
    "Theo Brandt",
    "Nina Volkov",
    "Riley Quinn",
    "Luca Moretti",
    "Harper Dane",
    "Yves Moreau",
    "Imani Brooks",
    "Felix Ortega",
]
EMPLOYEE_ICONS = ("briefcase", "badge", "laptop", "user")
GUEST_ICONS = ("star", "coffee", "camera", "gift")


def generate_demand(
    config: BuildingConfig,
    passenger_count: int = 24,
    seed: int = 1,
) -> list[Request]:
    """Lobby-biased destination-dispatch demand for the web configurator."""
    if passenger_count < 1:
        raise ValueError("passenger_count must be at least 1")
    rng = random.Random(seed)
    requests: list[Request] = []
    time = 0
    used_names: set[str] = set()
    for index in range(passenger_count):
        roll = rng.random()
        if roll < 0.45:
            source = 1
            dest = rng.randint(2, config.num_floors)
        elif roll < 0.75:
            source = rng.randint(2, config.num_floors)
            dest = 1
        else:
            source = rng.randint(1, config.num_floors)
            dest = rng.randint(1, config.num_floors)
            while dest == source:
                dest = rng.randint(1, config.num_floors)
        if index > 0 and rng.random() > 0.35:
            time += rng.randint(1, 3)
        is_employee = rng.random() < 0.7
        pool = EMPLOYEES if is_employee else GUESTS
        icons = EMPLOYEE_ICONS if is_employee else GUEST_ICONS
        name = pool[index % len(pool)]
        suffix = 2
        unique = name
        while unique in used_names:
            unique = f"{name} {suffix}"
            suffix += 1
        used_names.add(unique)
        requests.append(
            Request(
                time=time,
                id=f"p{index + 1:03d}",
                source=source,
                dest=dest,
                name=unique,
                role="employee" if is_employee else "guest",
                icon=icons[index % len(icons)],
            )
        )
    return requests
