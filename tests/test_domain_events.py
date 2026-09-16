"""Meta do jogo acompanha operação real; falha local tem semântica explícita."""

from __future__ import annotations

import random

import pytest

from mise_en_place.adapters.demand import ScriptedDemand
from mise_en_place.adapters.journals import MemoryJournal
from mise_en_place.application.events import RoundDispatcher
from mise_en_place.application.run_shift import RunShift, execute
from mise_en_place.bootstrap import build_restaurant
from mise_en_place.contracts.events import RoundServed
from mise_en_place.game.goals import ServiceGoal
from mise_en_place.restaurant import Clock, Course, RawOrder


async def test_goal_reacts_to_real_served_round() -> None:
    goal = ServiceGoal(target=1)
    events: list[RoundServed] = []
    house = build_restaurant(
        Clock(minute_s=0),
        rng=random.Random(7),
        journal=MemoryJournal(),
        publisher=RoundDispatcher(goal.on_round_served, events.append),
    )
    result = await execute(
        RunShift("meta"), house, ScriptedDemand((RawOrder(1, Course.DRINK, ("água com gás",)),))
    )
    assert result.rounds == 1
    assert goal.achieved
    assert events == [RoundServed(1, Course.DRINK, 1, 0)]


def fail(event: RoundServed) -> None:  # noqa: ARG001
    raise RuntimeError("consumidor indisponível")


def test_dispatch_is_ordered_fail_fast_without_rollback() -> None:
    first = ServiceGoal(target=1)
    last = ServiceGoal(target=1)
    dispatcher = RoundDispatcher(first.on_round_served, fail, last.on_round_served)
    with pytest.raises(RuntimeError, match="indisponível"):
        dispatcher.publish(RoundServed(1, Course.DRINK, 1, 0))
    assert first.achieved
    assert not last.achieved
