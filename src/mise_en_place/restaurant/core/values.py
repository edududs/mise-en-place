"""Objetos de valor: unidade e invariantes têm um dono."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Duration:
    minutes: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.minutes) or self.minutes < 0:
            raise ValueError("duração deve ser finita e não negativa")


# As lições: igualdade por valor, unidade explícita e validade em qualquer entrada.
