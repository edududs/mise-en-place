"""Demonstração finita: IA scaffold → operação → evento → meta e arquivo."""

from __future__ import annotations

import asyncio
import io
import random
from collections.abc import Iterable

from .adapters.console import configure_output
from .adapters.csv_journal import CsvJournal
from .adapters.storage import MemoryResultStore
from .ai.scaffold import PlannedDemand
from .application.archive import archive
from .application.events import RoundDispatcher
from .application.run_shift import RunShift, execute
from .bootstrap import build_restaurant
from .contracts.courses import Course
from .contracts.models import RawOrder
from .game.goals import ServiceGoal
from .restaurant.core.clock import Clock


class DemonstrationPlanner:
    def plan(self) -> Iterable[RawOrder]:
        return (RawOrder(1, Course.DRINK, ("água com gás",)),)


async def main() -> None:
    configure_output()
    goal = ServiceGoal(target=1)
    stream = io.StringIO()
    house = build_restaurant(
        Clock(minute_s=0),
        rng=random.Random(7),
        journal=CsvJournal(stream),
        publisher=RoundDispatcher(goal.on_round_served),
    )
    result = await execute(RunShift("integração"), house, PlannedDemand(DemonstrationPlanner()))
    store = MemoryResultStore()
    archive("demo", result, store)
    print(stream.getvalue())
    print(
        f"Rodadas: {result.rounds}; meta atingida: {goal.achieved}; salvo: {store.load('demo') == result}"
    )


if __name__ == "__main__":
    asyncio.run(main())

# As lições: o scaffold planeja, a operação valida, o jogo reage e adapters traduzem.
