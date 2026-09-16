"""Cenário interno: a aplicação recebe dados já traduzidos da entrada."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .restaurant.menu import Station
from .restaurant.restaurant import KITCHEN_STATIONS


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    cooks: int = 3
    waiters: int = 3
    kitchen_slots: Mapping[Station, int] = field(default_factory=lambda: dict(KITCHEN_STATIONS))


# As lições: configuração externa e dados internos têm responsabilidades distintas.
