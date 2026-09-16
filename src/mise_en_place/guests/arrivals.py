"""Quem chega, e quando. A "IA" da porta da rua.

Duas camadas de propósito:

* `instantes_de_chegada` é um gerador SÍNCRONO e puro — só produz números.
  Não dorme, não conhece asyncio, não conhece restaurante. Dá pra testar a
  distribuição sem event loop (e é o que a trilha de testes vai fazer).
* `noite` é um async generator: ele dorme até a próxima chegada e ENTREGA o
  grupo. Fonte preguiçosa, 1 produtor → 1 consumidor: é exatamente o caso em
  que gerador é a peça certa. Para fan-out (N consumidores) seria `Queue` —
  dois `async for` no mesmo async generator dão `RuntimeError`.

Por que Poisson e não intervalo uniforme: o intervalo uniforme esconde a
RAJADA, e é a rajada que satura o garçom. Chegada aleatória de verdade tem
intervalo exponencial — com semente, continua reproduzível.
"""

from __future__ import annotations

import random
from collections.abc import AsyncGenerator, Iterator
from typing import Final

from ..restaurant import Clock
from .party import Party
from .profiles import random_profile

ARRIVAL_RATE_PER_MINUTE: Final = 1 / 6.0  # ~1 grupo a cada 6 minutos
ARRIVAL_WINDOW_MINUTES: Final = 60.0  # a porta fica aberta uma hora
MAX_SEED: Final = 2**32


def arrival_times(
    rng: random.Random,
    *,
    rate_per_minute: float = ARRIVAL_RATE_PER_MINUTE,
    until_minute: float = ARRIVAL_WINDOW_MINUTES,
) -> Iterator[float]:
    """Processo de Poisson: o INTERVALO entre chegadas é exponencial."""
    at = 0.0
    while True:
        at += rng.expovariate(rate_per_minute)
        if at > until_minute:  # guard clause: fechou a porta
            return
        yield at


def random_party(number: int, master: random.Random) -> Party:
    """Cada grupo leva um `Random` PRÓPRIO, derivado do mestre.

    Não é preciosismo: com asyncio a ordem de entrelaçamento pode variar entre
    máquinas, e num `Random` compartilhado isso mudaria a ordem dos sorteios —
    a aula sairia diferente. Com um gerador por grupo, a história de cada mesa
    é estável independente do escalonamento.
    """
    rng = random.Random(master.randrange(MAX_SEED))
    profile = random_profile(rng)
    return Party(
        number=number,
        size=rng.randint(*profile.size),
        profile=profile,
        rng=rng,
    )


async def party_stream(
    clock: Clock,
    master: random.Random,
    *,
    until_minute: float = ARRIVAL_WINDOW_MINUTES,
) -> AsyncGenerator[Party]:
    """Dorme até cada chegada e entrega o grupo. Consumir com `aclosing`.

    LIÇÃO DE TIPAGEM: o retorno é `AsyncGenerator`, não `AsyncIterator`. Os dois
    funcionam no `async for`, mas só o `AsyncGenerator` declara `aclose()` — e é
    isso que o `contextlib.aclosing` exige. `AsyncIterator` é o tipo certo pro
    PARÂMETRO de quem só consome (ISP: não peça o que não vai usar).
    """
    previous_minute = 0.0
    try:
        for number, at_minute in enumerate(
            arrival_times(master, until_minute=until_minute), start=1
        ):
            await clock.wait(at_minute - previous_minute)
            previous_minute = at_minute
            yield random_party(number, master)
    finally:
        # ARMADILHA: sem `contextlib.aclosing` no consumidor, um `break` no
        # `async for` NÃO roda este `finally` na hora — ele só sai quando o GC
        # lembrar. Se aqui houvesse liberação de recurso, o recurso ficaria preso.
        pass  # A fonte nao escolhe mais o terminal como destino.
