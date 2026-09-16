"""Dados que atravessam a fronteira entre demanda e atendimento."""

from __future__ import annotations

from dataclasses import dataclass

from .courses import Course


@dataclass(frozen=True, slots=True)
class RawOrder:
    table: int
    course: Course
    items: tuple[str, ...]
    size: int = 1


@dataclass(frozen=True, slots=True)
class Table:
    number: int
    capacity: int

    def __str__(self) -> str:
        return f"mesa {self.number}"


# As lições: compartilhar vocabulário não é compartilhar o mecanismo da cozinha.
