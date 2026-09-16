"""A clientela existente e um roteiro finito acionam a mesma operação."""

from __future__ import annotations

import asyncio
import random
from contextlib import aclosing
from dataclasses import dataclass

from ..guests import party_stream
from ..guests.ports import FrontOfHouse
from ..restaurant.core.clock import Clock
from ..restaurant.orders import RawOrder


@dataclass(frozen=True, slots=True)
class PopulationDemand:
    clock: Clock
    rng: random.Random

    async def run(self, house: FrontOfHouse) -> None:
        async with asyncio.TaskGroup() as service:
            async with aclosing(party_stream(self.clock, self.rng)) as arrivals:
                async for party in arrivals:
                    service.create_task(party.dine(house), name=f"grupo-{party.number}")


@dataclass(frozen=True, slots=True)
class ScriptedDemand:
    """Roteiro de rodadas para integração; não simula a jornada completa das mesas."""

    orders: tuple[RawOrder, ...]

    async def run(self, house: FrontOfHouse) -> None:
        for order in self.orders:
            await house.order(order)


# As lições: fonte de demanda não acessa fila, estação nem worker interno.
