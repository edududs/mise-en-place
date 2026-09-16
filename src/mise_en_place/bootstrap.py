"""A montagem conhece implementações; atendimento recebe colaboradores prontos."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence

from .restaurant.core.clock import Clock
from .restaurant.dining import DINING_ROOM, Seating, Table, WaitStaff
from .restaurant.layout import (
    BAR_STATIONS,
    BARTENDERS_ON_SHIFT,
    COOKS_ON_SHIFT,
    KITCHEN_STATIONS,
    WAITER_NAMES,
    WAITERS_ON_SHIFT,
)
from .restaurant.menu import Section, Station
from .restaurant.observability import CompositeJournal, Journal, Metrics, TerminalJournal
from .restaurant.restaurant import Restaurant
from .restaurant.service import Line, Preparer
from .restaurant.service.policies import POLICIES, SchedulingMode


def build_restaurant(
    clock: Clock,
    *,
    rng: random.Random,
    journal: Journal | None = None,
    cooks: int = COOKS_ON_SHIFT,
    bartenders: int = BARTENDERS_ON_SHIFT,
    waiters: int = WAITERS_ON_SHIFT,
    seating: Sequence[Table] = DINING_ROOM,
    kitchen_slots: Mapping[Station, int] = KITCHEN_STATIONS,
    bar_slots: Mapping[Station, int] = BAR_STATIONS,
    scheduling: SchedulingMode = SchedulingMode.EDF,
) -> Restaurant:
    metrics = Metrics()
    observers = CompositeJournal(
        journal if journal is not None else TerminalJournal(clock), metrics
    )
    lines = {
        Section.KITCHEN: Line(
            Section.KITCHEN, clock, slots=kitchen_slots, policy=POLICIES[scheduling]
        ),
        Section.BAR: Line(Section.BAR, clock, slots=bar_slots, policy=POLICIES[scheduling]),
    }
    brigade = tuple(
        Preparer(f"{label}-{number}", line=lines[section], clock=clock, journal=observers, rng=rng)
        for section, count, label in (
            (Section.KITCHEN, cooks, "chef"),
            (Section.BAR, bartenders, "barman"),
        )
        for number in range(1, count + 1)
    )
    return Restaurant(
        clock,
        seating=Seating(seating),
        wait_staff=WaitStaff(clock, count=waiters, names=WAITER_NAMES),
        lines=lines,
        brigade=brigade,
        journal=observers,
        metrics=metrics,
        oven_slots=kitchen_slots.get(Station.OVEN, 0),
    )


# As lições: composição explícita; sem service locator; uma mudança de montagem tem um dono.
