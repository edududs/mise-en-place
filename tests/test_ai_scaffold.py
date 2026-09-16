"""Integração da IA futura: decisões são dados; operação conserva sua autoridade."""

from __future__ import annotations

import random
from collections.abc import Iterable

from mise_en_place.adapters.journals import MemoryJournal
from mise_en_place.ai.scaffold import PlannedDemand
from mise_en_place.application.run_shift import RunShift, execute
from mise_en_place.bootstrap import build_restaurant
from mise_en_place.contracts.courses import Course
from mise_en_place.contracts.models import RawOrder
from mise_en_place.restaurant.core.clock import Clock


class FixedPlanner:
    def plan(self) -> Iterable[RawOrder]:
        return (RawOrder(1, Course.DRINK, ("água com gás",)),)


async def test_planned_demand_uses_real_operation() -> None:
    house = build_restaurant(Clock(minute_s=0), rng=random.Random(7), journal=MemoryJournal())
    result = await execute(RunShift("scaffold"), house, PlannedDemand(FixedPlanner()))
    assert result.rounds == 1
