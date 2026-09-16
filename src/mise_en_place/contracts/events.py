"""Fato de domínio estruturado, independente de texto e glifos do terminal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .courses import Course


@dataclass(frozen=True, slots=True)
class RoundServed:
    table: int
    course: Course
    item_count: int
    at_minute: float


class RoundPublisher(Protocol):
    def publish(self, event: RoundServed) -> None: ...


# As lições: fato no passado, com dados; não é comando nem texto para parsear.
