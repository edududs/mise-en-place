"""Contrato compartilhado e efeito de falhas no fan-out."""

from __future__ import annotations

import io
import json
from dataclasses import asdict

import pytest

from mise_en_place.adapters.journals import JsonLinesJournal, MemoryJournal
from mise_en_place.restaurant.observability import CompositeJournal, Event, EventKind


def test_observers_receive_same_events_in_order() -> None:
    memory = MemoryJournal()
    stream = io.StringIO()
    journal = CompositeJournal(memory, JsonLinesJournal(stream))
    events = (Event(EventKind.OPENED, 0, "casa"), Event(EventKind.CLOSED, 1, "casa"))
    for event in events:
        journal.record(event)
    assert memory.events == events
    assert [json.loads(line) for line in stream.getvalue().splitlines()] == [
        asdict(event) for event in events
    ]
    assert not stream.closed


def test_failure_stops_remaining_observers() -> None:
    stream = io.StringIO()
    stream.close()
    memory = MemoryJournal()
    journal = CompositeJournal(JsonLinesJournal(stream), memory)
    with pytest.raises(ValueError, match="closed"):
        journal.record(Event(EventKind.OPENED, 0, "casa"))
    assert memory.events == ()
