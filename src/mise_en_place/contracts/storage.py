"""Contrato de resultados concluídos; não armazena estado vivo do runtime."""

from __future__ import annotations

import re
from typing import Protocol

from .results import Measurement


def validate_key(key: str) -> None:
    if re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", key) is None:
        raise ValueError("identificador deve conter 1–80 letras ASCII, números, _ ou -")


class ResultStore(Protocol):
    def save(self, key: str, result: Measurement) -> None:
        """Cria ou substitui um resultado. Erro de I/O propaga."""
        ...

    def load(self, key: str) -> Measurement | None:
        """Ausência retorna None; corrupção levanta ValueError; I/O propaga."""
        ...


# As lições: nomear ausência, sobrescrita e falha faz parte da porta.
