"""Nome de funcionário não é seu papel na medição."""

from __future__ import annotations

import random

import pytest

from mise_en_place.restaurant import Clock, Restaurant, Section


def test_renaming_cook_preserves_role() -> None:
    house = Restaurant(Clock(minute_s=1), rng=random.Random(7))
    cook = next(p for p in house.brigade if p.section is Section.KITCHEN)
    cook.name = "Maria"
    cook.busy_minutes = 2.0
    result = house.measurement("teste")
    assert result.cook_utilization * result.minutes == pytest.approx(2 / 3)


def test_zero_clock_returns_finite_measurement() -> None:
    result = Restaurant(Clock(minute_s=0), rng=random.Random(7)).measurement("teste")
    assert result.cook_utilization == 0
    assert result.rounds == 0
