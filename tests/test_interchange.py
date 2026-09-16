"""Doze combinações reais de demanda, observação e armazenamento."""

from __future__ import annotations

import asyncio
import csv
import io
import random
from collections.abc import Callable
from pathlib import Path

import pytest

from mise_en_place.adapters.csv_journal import CsvJournal
from mise_en_place.adapters.demand import ScriptedDemand
from mise_en_place.adapters.journals import JsonLinesJournal, MemoryJournal
from mise_en_place.adapters.storage import JsonResultStore, MemoryResultStore
from mise_en_place.ai.scaffold import PlannedDemand
from mise_en_place.application.archive import archive
from mise_en_place.application.events import RoundDispatcher
from mise_en_place.application.run_shift import RunShift, execute
from mise_en_place.bootstrap import build_restaurant
from mise_en_place.contracts.ports import DemandSource
from mise_en_place.contracts.storage import ResultStore
from mise_en_place.demo import DemonstrationPlanner
from mise_en_place.game.goals import ServiceGoal
from mise_en_place.restaurant import Clock, Course, Event, EventKind, Journal, RawOrder


def memory_journal() -> Journal:
    return MemoryJournal()


def json_journal() -> Journal:
    return JsonLinesJournal(io.StringIO())


def csv_journal() -> Journal:
    return CsvJournal(io.StringIO())


@pytest.mark.parametrize("journal_factory", [memory_journal, json_journal, csv_journal])
@pytest.mark.parametrize("planned", [False, True])
@pytest.mark.parametrize("persistent", [False, True])
async def test_interchange(
    journal_factory: Callable[[], Journal],
    *,
    planned: bool,
    persistent: bool,
    tmp_path: Path,
) -> None:
    before = asyncio.all_tasks()
    goal = ServiceGoal(target=1)
    house = build_restaurant(
        Clock(minute_s=0),
        rng=random.Random(7),
        journal=journal_factory(),
        publisher=RoundDispatcher(goal.on_round_served),
    )
    demand: DemandSource = (
        PlannedDemand(DemonstrationPlanner())
        if planned
        else ScriptedDemand((RawOrder(1, Course.DRINK, ("água com gás",)),))
    )
    async with asyncio.timeout(2):
        result = await execute(RunShift("combinação"), house, demand)
    store: ResultStore = JsonResultStore(tmp_path) if persistent else MemoryResultStore()
    archive("turno", result, store)
    assert store.load("turno") == result
    assert result.rounds == 1
    assert goal.achieved
    assert not (asyncio.all_tasks() - before)


def test_csv_preserves_delimiters_unicode_and_order() -> None:
    stream = io.StringIO(newline="")
    journal = CsvJournal(stream)
    journal.record(Event(EventKind.OPENED, 0, "casa", 'olá, "mesa"'))
    journal.record(Event(EventKind.CLOSED, 1, "casa"))
    rows = list(csv.DictReader(io.StringIO(stream.getvalue())))
    assert [row["kind"] for row in rows] == ["abriu", "fechou"]
    assert rows[0]["detail"] == 'olá, "mesa"'
    assert not stream.closed
