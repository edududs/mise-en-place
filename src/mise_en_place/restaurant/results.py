"""Resultado de turno: dados estáveis, sem acesso aos workers pelo consumidor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Measurement:
    scenario: str
    minutes: float
    starter_wait: float
    main_wait: float
    oven_utilization: float
    cook_utilization: float
    waiter_utilization: float
    rounds: int


def utilization(busy: float, minutes: float, capacity: int) -> float:
    """Escala zero serve para testes funcionais, não para medir utilização."""
    denominator = minutes * capacity
    return busy / denominator if denominator else 0.0


# As lições: resultado é fotografia; quem lê não ganha acesso ao estado mutável.
