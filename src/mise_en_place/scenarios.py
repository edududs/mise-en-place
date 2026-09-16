"""Cenário interno: a aplicação recebe dados já traduzidos da entrada."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .restaurant.layout import KITCHEN_STATIONS
from .restaurant.menu import Station
from .restaurant.service.policies import SchedulingMode


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    cooks: int = 3
    waiters: int = 3
    kitchen_slots: Mapping[Station, int] = field(default_factory=lambda: dict(KITCHEN_STATIONS))
    scheduling: SchedulingMode = SchedulingMode.EDF


# As lições: configuração externa e dados internos têm responsabilidades distintas.
