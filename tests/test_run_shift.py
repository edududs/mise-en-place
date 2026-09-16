"""Mesmo caso de uso com entrada roteirizada e observador em memória."""

from __future__ import annotations

import asyncio
import random

import pytest

from mise_en_place.adapters.demand import ScriptedDemand
from mise_en_place.adapters.journals import MemoryJournal
from mise_en_place.application.run_shift import RunShift, execute
from mise_en_place.bootstrap import build_restaurant
from mise_en_place.restaurant import Clock, Course, EventKind, RawOrder
from mise_en_place.restaurant.core.errors import EmptyRoundError


async def test_script_runs_without_terminal(capsys: pytest.CaptureFixture[str]) -> None:
    journal = MemoryJournal()
    house = build_restaurant(Clock(minute_s=0), rng=random.Random(7), journal=journal)
    demand = ScriptedDemand((RawOrder(1, Course.DRINK, ("água com gás",)),))
    async with asyncio.timeout(2):
        result = await execute(RunShift("roteiro"), house, demand)
    assert result.rounds == 1
    assert result.scenario == "roteiro"
    assert journal.events[-1].kind is EventKind.CLOSED
    assert capsys.readouterr().out == ""


async def test_invalid_demand_closes_house() -> None:
    house = build_restaurant(Clock(minute_s=0), rng=random.Random(7), journal=MemoryJournal())
    demand = ScriptedDemand((RawOrder(1, Course.DRINK, ()),))
    with pytest.raises(ExceptionGroup) as caught:
        async with asyncio.timeout(2):
            await execute(RunShift("inválido"), house, demand)
    matched, _ = caught.value.split(EmptyRoundError)
    assert matched is not None
    assert not house.is_open
