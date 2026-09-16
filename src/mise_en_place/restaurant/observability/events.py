"""O evento: dado PLANO sobre algo que aconteceu.

Regra deste módulo: `Evento` nunca carrega objeto do domínio (`Comanda`,
`Mesa`, `Praca`) — só números e strings. Dois motivos:

1. quem observa não deve poder MEXER em quem é observado;
2. é o que mantém a observabilidade como folha da árvore de imports, sem ciclo.

`momento_min` é o minuto simulado. A formatação em `[HH:MM]` é do `Relogio` —
o evento não sabe a que hora a casa abre.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..menu import Course


class EventKind(StrEnum):
    OPENED = "abriu"
    CLOSED = "fechou"
    ARRIVED = "chegou"
    SEATED = "sentou"
    LEFT_QUEUE = "desistiu"
    CALLED = "chamou"
    ORDERED = "pediu"
    REJECTED = "recusado"
    SERVED = "servido"
    BURNED = "queimou"
    LATE = "atrasou"
    LEFT = "saiu"


GLYPHS: dict[EventKind, str] = {
    EventKind.OPENED: "◆",
    EventKind.CLOSED: "◆",
    EventKind.ARRIVED: "→",
    EventKind.SEATED: "→",
    EventKind.LEFT_QUEUE: "✗",
    EventKind.CALLED: "⏳",
    EventKind.ORDERED: "→",
    EventKind.REJECTED: "!",
    EventKind.SERVED: "✓",
    EventKind.BURNED: "!",
    EventKind.LATE: "!",
    EventKind.LEFT: "←",
}


@dataclass(frozen=True, slots=True)
class Event:
    kind: EventKind
    at_minute: float
    who: str
    detail: str = ""
    course: Course | None = None
    waited: float | None = None
