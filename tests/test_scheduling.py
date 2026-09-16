"""Políticas exercitadas na fila real, inclusive empate."""

from __future__ import annotations

import pytest

from mise_en_place.restaurant import Clock, Section, Station
from mise_en_place.restaurant.menu import MENU
from mise_en_place.restaurant.orders import OrderItem
from mise_en_place.restaurant.service.line import Line
from mise_en_place.restaurant.service.policies import POLICIES, SchedulingMode


@pytest.mark.parametrize(
    ("mode", "expected"), [(SchedulingMode.EDF, (2, 3, 1)), (SchedulingMode.FIFO, (1, 2, 3))]
)
async def test_real_queue_obeys_policy(mode: SchedulingMode, expected: tuple[int, ...]) -> None:
    line = Line(Section.KITCHEN, Clock(minute_s=0), slots={Station.OVEN: 1}, policy=POLICIES[mode])
    futures = [
        await line.enqueue(OrderItem(table, MENU["bruschetta"], index=0), deadline=deadline)
        for table, deadline in ((1, 20), (2, 10), (3, 10))
    ]
    order: list[int] = []
    for _ in futures:
        order.append((await line.next_dispatch()).item.table)
        line.complete()
    await line.drain()
    line.close()
    for future in futures:
        future.cancel()
    assert tuple(order) == expected
