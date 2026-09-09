"""
AULA 3 — O restaurante completo (determinístico)
================================================

Rode:  python3 -m ex3

O que muda em relação ao ex2: **a unidade de trabalho deixa de ser o pedido e
passa a ser a comanda de uma mesa**, que tem cursos com dependência temporal
entre si — a entrada sai primeiro, o principal só depois que a mesa comeu — e
os drinks correm por fora, no bar.

Este arquivo é só o COMPOSITION ROOT da aula: ele monta o package
`ex3/restaurante/` e escreve o roteiro das mesas na mão. A aula inteira é a
PASTA — `python3 -m ex3` executa este `__main__.py`.
Zero aleatoriedade no comportamento —
é a aula 4 que traz a clientela viva.

AS TRÊS PERGUNTAS QUE ESTA AULA RESPONDE:

1. Quem manda na SEQUÊNCIA dos cursos?
   A mesa. `await` **é** a máquina de estados: o estado mora no program counter
   da coroutine. Veja `mesa_roteirizada()` — a sequência se lê de cima pra baixo.
   O orquestrador não sabe o que é curso; se soubesse (um `if curso == PRINCIPAL`
   no despacho), a cozinha passaria a conhecer política de salão.

2. Quem manda na ORDEM entre mesas?
   O orquestrador, por EDF: `(prazo, curso, índice, sequência)`. Prazo absoluto
   e estático ⇒ starvation-free por construção. Ver `servico/praca.py`.

3. Por que o drink chega enquanto o risoto ainda está no fogo?
   Porque o bar é outra PRAÇA: fila própria, estações próprias, brigada própria.
   Não existe um `if curso == DRINK` em lugar nenhum do código.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Final

from .restaurant import (
    SIMULATED_MINUTE_S,
    Clock,
    Course,
    DishBurnedError,
    InvalidOrderError,
    RawOrder,
    Restaurant,
)

SERVICE_SEED: Final = 7
REPORT_WIDTH: Final = 78


@dataclass(frozen=True, slots=True)
class Script:
    """O que uma mesa faz, escrito à mão. Nada aleatório nesta aula."""

    arrives_at_minute: float
    size: int
    starter: tuple[str, ...]
    main: tuple[str, ...]
    drinks: tuple[str, ...] = ()
    dessert: tuple[str, ...] = ()
    eat_starter_minutes: float = 8.0
    eat_main_minutes: float = 14.0


# Os literais ficam aqui de propósito: num `dataclass` congelado o nome do campo
# já nomeia o número (`comer_entrada_min=8.0`), e transformar cada tempo em
# constante `Final` pioraria a leitura sem ganhar nada.
SCRIPTS: Final[tuple[Script, ...]] = (
    Script(
        0.0,
        2,
        ("bruschetta",),
        ("risoto de funghi", "salmão grelhado"),
        drinks=("caipirinha", "chopp"),
        dessert=("petit gâteau",),
    ),
    Script(
        3.0,
        4,
        ("carpaccio", "sopa do dia"),
        ("bife com fritas", "frango assado"),
        drinks=("chopp", "chopp"),
    ),
    Script(
        6.0,
        2,
        ("sopa do dia",),
        ("massa carbonara",),
        drinks=("suco de laranja",),
        dessert=("pudim",),
    ),
    Script(
        9.0,
        6,
        ("bruschetta", "carpaccio"),
        ("bife com fritas", "massa carbonara", "risoto de funghi"),
        drinks=("água com gás", "caipirinha"),
    ),
    Script(12.0, 2, ("carpaccio",), ("salmão grelhado",), drinks=("chopp",)),
)


@dataclass(slots=True)
class Complaints:
    """Um contador simples — existe porque `return` não pode sair de um `except*`."""

    lost: list[str] = field(default_factory=list)


async def serve(casa: Restaurant, raw: RawOrder, complaints: Complaints) -> None:
    """Pede uma rodada e sobrevive a um item perdido.

    ARMADILHA DE SINTAXE que vale a aula: `return`, `break` e `continue` são
    PROIBIDOS dentro de um bloco `except*` (é SyntaxError, não erro em runtime).
    O motivo é que o bloco pode rodar várias vezes, uma por tipo de exceção do
    grupo — então "sair da função" não teria significado único. Por isso o
    resultado sai por uma variável/objeto, e não por `return` lá dentro.

    E é `except*` (não `except`) porque a rodada é um `TaskGroup`: o erro chega
    embalado num `ExceptionGroup`, mesmo quando é um só.
    """
    try:
        await casa.order(raw)
    except* DishBurnedError as party:
        for error in party.exceptions:
            complaints.lost.append(str(error))


async def scripted_table(casa: Restaurant, script: Script, complaints: Complaints) -> None:
    """A sequência da mesa, de cima pra baixo. É esta função a máquina de estados."""
    await casa.clock.wait(script.arrives_at_minute)
    table = await casa.seat(script.size)
    try:
        await serve(
            casa,
            RawOrder(table.number, Course.STARTER, script.starter, script.size),
            complaints,
        )

        # AQUI está o coração da aula: enquanto a mesa COME a entrada, o drink
        # vem do bar em paralelo — e a cozinha segue produzindo pra todo mundo.
        async with asyncio.TaskGroup() as while_eating:
            if script.drinks:
                while_eating.create_task(
                    serve(
                        casa,
                        RawOrder(table.number, Course.DRINK, script.drinks, script.size),
                        complaints,
                    ),
                    name=f"drink-mesa{table.number}",
                )
            while_eating.create_task(
                casa.clock.wait(script.eat_starter_minutes),
                name=f"comendo-mesa{table.number}",
            )

        await serve(
            casa,
            RawOrder(table.number, Course.MAIN, script.main, script.size),
            complaints,
        )
        await casa.clock.wait(script.eat_main_minutes)

        if script.dessert:
            await serve(
                casa,
                RawOrder(table.number, Course.DESSERT, script.dessert, script.size),
                complaints,
            )

        await casa.ask_for_bill(table.number)
    finally:
        # `finally` não é enfeite: se a mesa for cancelada no meio, a mesa física
        # tem que voltar pro salão — senão o restaurante "perde" uma mesa.
        await casa.release(table)


async def boundary_scene(casa: Restaurant) -> None:
    """O validador recusando na porta: é aqui que a fronteira ganha valor."""
    print("\n--- a fronteira recusa (e explica o motivo) ---")
    invalid_orders = (
        RawOrder(1, Course.MAIN, ("polenta frita",)),
        RawOrder(1, Course.MAIN, ("chopp",)),
        RawOrder(1, Course.STARTER, ()),
    )
    for raw in invalid_orders:
        try:
            await casa.order(raw)
        except InvalidOrderError as error:
            print(f"    {type(error).__name__}: {error}")


async def main() -> None:
    clock = Clock(minute_s=SIMULATED_MINUTE_S)
    rng = random.Random(SERVICE_SEED)
    complaints = Complaints()

    async with Restaurant(clock, rng=rng) as casa:
        await boundary_scene(casa)
        print("\n--- o serviço ---")
        async with asyncio.TaskGroup() as arrivals:
            for number, script in enumerate(SCRIPTS, start=1):
                arrivals.create_task(
                    scripted_table(casa, script, complaints), name=f"roteiro-{number}"
                )

    print("\n" + "═" * REPORT_WIDTH)
    for row in casa.report():
        print(row)
    if complaints.lost:
        print(f"perdidos      {len(complaints.lost)}: {'; '.join(complaints.lost)}")
    print("═" * REPORT_WIDTH)


if __name__ == "__main__":
    asyncio.run(main())
