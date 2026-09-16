"""Executar um turno é uma intenção acionável por CLI, script ou teste."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..guests.ports import FrontOfHouse
from ..restaurant.restaurant import Restaurant
from ..restaurant.results import Measurement


class DemandSource(Protocol):
    async def run(self, house: FrontOfHouse) -> None:
        """Produz trabalho finito; só retorna após terminar os clientes que iniciou."""
        ...


@dataclass(frozen=True, slots=True)
class RunShift:
    name: str


async def execute(request: RunShift, house: Restaurant, demand: DemandSource) -> Measurement:
    async with house:
        await demand.run(house)
    return house.measurement(request.name)


# As lições: um caso de uso pode ser função; não precisa de classe com um único método.
