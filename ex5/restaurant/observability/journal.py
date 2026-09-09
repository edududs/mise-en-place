"""Para onde os eventos vão. `Diario` é `Protocol`: quem emite não sabe o destino."""

from __future__ import annotations

from typing import Protocol

from ..core.clock import Clock
from .events import GLYPHS, Event

WHO_WIDTH: int = 10


class Journal(Protocol):
    """Um método só (ISP no limite): quem emite evento não pede mais que isso.

    `Protocol` estrutural: o terminal, as métricas e o composto abaixo são
    `Diario` sem herdar de nada e sem importar esta classe. Quem define o
    contrato é quem CONSOME, e a conformidade é verificada pelo type checker.
    """

    def record(self, event: Event) -> None: ...


class TerminalJournal:
    """A narrativa ao vivo, uma linha por evento."""

    def __init__(self, clock: Clock, *, verbose: bool = True) -> None:
        self._clock = clock
        self._verbose = verbose

    def record(self, event: Event) -> None:
        if not self._verbose:  # guard clause: modo medição não polui a saída
            return
        hour = self._clock.time_of(event.at_minute)
        wait = "" if event.waited is None else f" ({event.waited:.0f}min)"
        course = "" if event.course is None else f" {event.course.label}"
        glyph = GLYPHS[event.kind]
        print(
            f"{hour} {event.who:<{WHO_WIDTH}} {glyph} "
            f"{event.kind}{course}: {event.detail}{wait}".rstrip(": ")
        )


class CompositeJournal:
    """Fan-out para vários destinos. Mecanismo puro: nenhuma política aqui."""

    def __init__(self, *sinks: Journal) -> None:
        self._sinks = sinks

    def record(self, event: Event) -> None:
        for sink in self._sinks:
            sink.record(event)
