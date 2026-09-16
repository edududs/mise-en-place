"""Uma meta de turno reage a fatos sem entrar na cozinha."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..contracts.events import RoundServed


@dataclass(slots=True)
class ServiceGoal:
    target: int
    served: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.target <= 0:
            raise ValueError("meta deve ser positiva")

    def on_round_served(self, event: RoundServed) -> None:  # noqa: ARG002
        self.served += 1

    @property
    def achieved(self) -> bool:
        return self.served >= self.target


# As lições: a regra de progressão é do jogo; a cozinha informa o que aconteceu.
