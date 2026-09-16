"""Trocar observadores revelou a obrigação de fechar mesmo se observação falhar."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass

import pytest

from mise_en_place.adapters.demand import ScriptedDemand
from mise_en_place.adapters.journals import MemoryJournal
from mise_en_place.application.run_shift import RunShift, execute
from mise_en_place.bootstrap import build_restaurant
from mise_en_place.contracts.ports import FrontOfHouse
from mise_en_place.restaurant import Clock, Event, EventKind


@dataclass
class FailingJournal:
    when: EventKind

    def record(self, event: Event) -> None:
        if event.kind is self.when:
            raise OSError("stream indisponível")


@pytest.mark.parametrize("when", [EventKind.OPENED, EventKind.CLOSED])
async def test_observer_failure_does_not_leak_tasks(when: EventKind) -> None:
    before = asyncio.all_tasks()
    house = build_restaurant(Clock(minute_s=0), rng=random.Random(7), journal=FailingJournal(when))
    with pytest.raises(ExceptionGroup) as caught:
        async with asyncio.timeout(2):
            await execute(RunShift("falha"), house, ScriptedDemand(()))
    matched, _ = caught.value.split(OSError)
    assert matched is not None
    assert not house.is_open
    assert not (asyncio.all_tasks() - before)


class CancelledDemand:
    async def run(self, house: FrontOfHouse) -> None:  # noqa: ARG002
        raise asyncio.CancelledError


async def test_cancellation_closes_workers() -> None:
    before = asyncio.all_tasks()
    house = build_restaurant(Clock(minute_s=0), rng=random.Random(7), journal=MemoryJournal())
    with pytest.raises(asyncio.CancelledError):
        await execute(RunShift("cancelado"), house, CancelledDemand())
    assert not house.is_open
    assert not (asyncio.all_tasks() - before)


async def test_operation_is_single_use() -> None:
    house = build_restaurant(Clock(minute_s=0), rng=random.Random(7), journal=MemoryJournal())
    await execute(RunShift("primeiro"), house, ScriptedDemand(()))
    with pytest.raises(RuntimeError, match="único turno"):
        await execute(RunShift("segundo"), house, ScriptedDemand(()))
