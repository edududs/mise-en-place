"""Observadores substituíveis: memória e stream JSONL."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TextIO

from ..restaurant.observability.events import Event


class MemoryJournal:
    def __init__(self) -> None:
        self._events: list[Event] = []

    @property
    def events(self) -> tuple[Event, ...]:
        return tuple(self._events)

    def record(self, event: Event) -> None:
        self._events.append(event)


class JsonLinesJournal:
    """O chamador abre e fecha o stream. Escrita síncrona; erro propaga."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream

    def record(self, event: Event) -> None:
        self._stream.write(json.dumps(asdict(event), ensure_ascii=False, allow_nan=False) + "\n")


# As lições: contrato inclui ordem, ownership e falha; I/O síncrono tem custo no loop.
