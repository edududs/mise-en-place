"""
AULA 4 — O salão vivo (a clientela chega sozinha)
=================================================

Rode:  python3 -m ex4

Esta aula é a aula 3 INTEIRA mais um package novo: `clientela/`. O restaurante
não mudou uma linha — e isso é o resultado que a aula quer provar.

O QUE ENTRA DE NOVO:

1. **Porta declarada pelo consumidor.** `clientela/portas.py` define o
   `Protocol Atendimento`: o que um cliente precisa de um restaurante. O
   `Restaurante` satisfaz esse contrato **sem herdar de nada e sem importar a
   clientela** — ele nem sabe que ela existe. A conferência acontece na função
   `_confirmar_porta` abaixo, e quem confere é o `mypy`.

2. **Chegadas de Poisson.** Um gerador síncrono e puro produz os instantes; um
   async generator dorme até cada um e entrega o grupo, consumido com
   `contextlib.aclosing`.

3. **Produtores independentes.** Cada grupo é uma Task própria com jornada
   própria. Ninguém coordena ninguém: a disputa por mesa, garçom e estação
   emerge da concorrência.

4. **Drink como task paralela.** Dentro do jantar de cada mesa há um
   `TaskGroup` com a refeição e as rodadas de bebida correndo juntas — e a
   bebida pendente é cancelada quando a comida acaba.

5. **Desistência na porta.** `asyncio.timeout` com a paciência do perfil: o
   grupo que espera demais vai embora, e isso aparece no relatório.
"""

from __future__ import annotations

import asyncio
import random
from collections import Counter
from contextlib import aclosing
from typing import Final

from .guests import Party, party_stream
from .guests.arrivals import MAX_SEED
from .guests.ports import FrontOfHouse
from .restaurant import SIMULATED_MINUTE_S, Clock, Restaurant

SERVICE_SEED: Final = 7
REPORT_WIDTH: Final = 78


def _confirm_port(casa: Restaurant) -> FrontOfHouse:
    """A prova estática do DIP, e ela custa uma linha.

    Se um dia o `Restaurante` mudar a assinatura de `pedir`, o erro aparece
    AQUI — no único ponto do sistema em que a porta e o adaptador se encontram.
    Nenhum dos dois arquivos importa o outro; o type checker faz a costura.
    """
    return casa


async def main() -> None:
    clock = Clock(minute_s=SIMULATED_MINUTE_S)
    # UM mestre, e cada consumidor recebe um gerador FILHO. O `random.seed()`
    # global seria uma segunda fonte de verdade: qualquer módulo que chamasse
    # `random.*` roubaria números da sequência e a aula sairia diferente.
    master = random.Random(SERVICE_SEED)
    casa = Restaurant(clock, rng=random.Random(master.randrange(MAX_SEED)))

    parties: list[Party] = []
    async with casa:
        _confirm_port(casa)
        async with asyncio.TaskGroup() as service:
            # `aclosing` garante que o `finally` do gerador de chegadas rode na
            # hora — e não quando o coletor de lixo lembrar.
            async with aclosing(party_stream(clock, master)) as arrivals:
                async for party in arrivals:
                    parties.append(party)
                    service.create_task(party.dine(casa), name=f"grupo-{party.number}")

    print("\n" + "═" * REPORT_WIDTH)
    for row in casa.report():
        print(row)

    styles = Counter(party.profile.style for party in parties)
    print("perfis        " + " · ".join(f"{style} {n}" for style, n in styles.items()))
    complaints = sum(1 for party in parties if party.complained)
    print(
        f"clientela     {len(parties)} grupos chegaram · "
        f"{sum(1 for g in parties if g.gave_up)} desistiram · "
        f"{complaints} reclamaram de item perdido"
    )
    print("═" * REPORT_WIDTH)


if __name__ == "__main__":
    asyncio.run(main())
