"""O relógio do restaurante — fonte única do tempo.

REGRA DO CURSO: nenhum outro módulo chama `asyncio.sleep`. Só o `Relogio`.

Por quê: o fator de escala (quanto vale um minuto simulado) é UM fato. Se cada
módulo dormisse por conta própria, mudar a velocidade da aula significaria caçar
`sleep` espalhado — e um deles ficaria pra trás. Com o relógio injetado:

    Relogio(minuto_s=0.05)   # aula normal: a noite roda em segundos
    Relogio(minuto_s=0.20)   # demonstração ao vivo, dá pra narrar
    Relogio(minuto_s=0.0)    # teste: a noite inteira em milissegundos

E os logs saem no relógio do restaurante (`[20:14]`), não em segundos:
"[20:14] mesa 3 pediu a entrada" conta uma história; "7.42s" não conta nada.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Final

SIMULATED_MINUTE_S: Final = 0.05
OPENING_HOUR: Final = 19
MINUTES_PER_HOUR: Final = 60


@dataclass(frozen=True, slots=True)
class Clock:
    """Converte minutos simulados em espera real e em hora de parede."""

    minute_s: float = SIMULATED_MINUTE_S
    started_at_s: float = field(default_factory=time.perf_counter)

    def minutes(self) -> float:
        """Quantos minutos simulados já se passaram desde a abertura."""
        return self.minutes_from(time.perf_counter() - self.started_at_s)

    def minutes_from(self, real_seconds: float) -> float:
        """Traduz segundos de parede em minutos simulados."""
        if not self.minute_s:  # guard clause: modo teste, o tempo não passa
            return 0.0
        return real_seconds / self.minute_s

    def deadline_s(self, minutes: float | None) -> float | None:
        """Prazo real em segundos para `asyncio.timeout`, ou `None` = sem limite.

        Centraliza uma pegadinha: em modo teste (`minuto_s=0`) todo prazo viraria
        `timeout(0)` e expiraria na hora. `None` é a forma explícita de
        "não expira", e essa tradução mora num lugar só.
        """
        if minutes is None:
            return None
        return minutes * self.minute_s or None

    async def wait(self, minutes: float) -> None:
        """A ÚNICA espera do sistema. `asyncio.sleep(0)` ainda cede o expedidor."""
        await asyncio.sleep(minutes * self.minute_s)

    def now(self) -> str:
        """`[20:14]` — a hora no relógio da parede do restaurante."""
        return self.time_of(self.minutes())

    def time_of(self, minutes: float) -> str:
        """Formata qualquer minuto simulado como hora de parede.

        Existe pra que o `Evento` guarde só o número (`momento_min`) e a
        formatação continue morando num lugar só — quem sabe que a casa abre
        às 19h é o relógio, não quem imprime.
        """
        total = int(minutes)
        hour = OPENING_HOUR + total // MINUTES_PER_HOUR
        return f"[{hour:02d}:{total % MINUTES_PER_HOUR:02d}]"
