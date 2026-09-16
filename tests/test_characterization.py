"""Comportamentos observáveis da aula 5, antes das refatorações."""

from __future__ import annotations

import asyncio
import random

import pytest

from mise_en_place.restaurant import Clock, Course, Event, EventKind, RawOrder, Restaurant
from mise_en_place.restaurant.core.errors import EmptyRoundError, RestaurantClosedError
from mise_en_place.restaurant.menu import MENU, Section, Station
from mise_en_place.restaurant.orders import OrderItem, Validator
from mise_en_place.restaurant.service.line import Line


class RecordingJournal:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def record(self, event: Event) -> None:
        self.events.append(event)


async def test_serves_round_and_closes_workers() -> None:
    journal = RecordingJournal()
    house = Restaurant(Clock(minute_s=0), rng=random.Random(7), journal=journal)
    async with asyncio.timeout(2):
        async with house:
            await house.order(RawOrder(table=1, course=Course.DRINK, items=("água com gás",)))
    kinds = [event.kind for event in journal.events]
    assert kinds[0] == EventKind.OPENED
    assert EventKind.SERVED in kinds
    assert kinds[-1] == EventKind.CLOSED
    assert not house.is_open
    assert house.metrics.served == 1


async def test_closed_house_rejects_order() -> None:
    house = Restaurant(Clock(minute_s=0), rng=random.Random(7))
    with pytest.raises(RestaurantClosedError):
        await house.order(RawOrder(table=1, course=Course.DRINK, items=("chopp",)))


def test_empty_round_is_rejected() -> None:
    with pytest.raises(EmptyRoundError):
        Validator(Clock()).validate(RawOrder(table=1, course=Course.STARTER, items=()))


async def test_queue_orders_deadlines_and_drains() -> None:
    line = Line(Section.KITCHEN, Clock(minute_s=0), slots={Station.OVEN: 1})
    recipe = MENU["bruschetta"]
    late = await line.enqueue(OrderItem(table=1, recipe=recipe, index=0), deadline=20)
    early = await line.enqueue(OrderItem(table=2, recipe=recipe, index=0), deadline=10)
    assert (await line.next_dispatch()).item.table == 2
    line.complete()
    assert (await line.next_dispatch()).item.table == 1
    line.complete()
    await line.drain()
    late.cancel()
    early.cancel()
    line.close()
    with pytest.raises(asyncio.QueueShutDown):
        await line.next_dispatch()


# As lições: proteger efeitos observáveis; não fixar timestamps nem ordem incidental.
