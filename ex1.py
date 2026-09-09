"""
AULA 1 — Cozinha assíncrona: os fundamentos
===========================================

Rode:  python3 ex1.py

Três cenas, na ordem:
  CENA 1 ... por que async ganha tempo (e o que ele NÃO resolve)
  CENA 2 ... gather x TaskGroup: o prato órfão
  CENA 3 ... a brigada: um balcão de pedidos, N cozinheiros

Analogia-guia (o vocabulário todo da aula):
  event loop ....... o EXPEDIDOR — uma pessoa só; se ela para, o restaurante para
  Task ............. um PEDIDO em andamento
  async def ........ a RECEITA
  await ............ "está no forno, me chama quando terminar"
  asyncio.sleep .... tempo de FORNO (libera o cozinheiro)
  time.sleep ....... o cozinheiro PARADO olhando a panela  ← o pecado
  Queue ............ o BALCÃO de pedidos
  Semaphore ........ as FRITADEIRAS (recurso escasso e compartilhado)
  TaskGroup ........ o TICKET — sai completo ou não sai
  timeout .......... "15 min e o prato não saiu? refaz"

Os tempos estão em segundos para a aula rodar rápido; leia como minutos.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

# ─────────────────────────────────────────────────────────────────────────────
# Constantes nomeadas — nenhum número solto no meio do código.
# O nome é a documentação: `TEMPO_MAXIMO_POR_PRATO_S` explica; `5` não explica.
# ─────────────────────────────────────────────────────────────────────────────
RANDOM_SEED: Final = 7  # serviço reproduzível: a aula sai igual toda vez

RISOTTO_S: Final = 1.2
SALAD_S: Final = 0.6
SIDE_DISH_S: Final = 0.8
SECONDS_UNTIL_BURN: Final = 0.2
WATCH_KITCHEN_S: Final = 1.2  # janela pra ver o órfão terminar

COOKS_ON_SHIFT: Final = 4
FRYERS_AVAILABLE: Final = 3
PASS_SIZE: Final = 20
TABLES_IN_ROOM: Final = 5
TOTAL_ORDERS: Final = 12

DISH_TIMEOUT_S: Final = 3.0
MIN_PREP_S: Final = 0.2
MAX_PREP_S: Final = 0.8
BURN_CHANCE: Final = 0.15


class Dish(StrEnum):
    """O menu como Enum: `pedido.prato == Prato.RISOTO`, nunca `== "risoto"`."""

    RISOTTO = "risoto"
    SALAD = "salada"
    STEAK = "bife"


TODAYS_DISHES: Final[tuple[Dish, ...]] = tuple(Dish)


@dataclass(frozen=True, slots=True)
class Order:
    """Número, mesa e prato viajam JUNTOS — sem primitive obsession.

    `frozen`: um pedido aceito não muda no meio do caminho.
    `slots`: menos memória e acesso mais rápido a atributo.
    """

    number: int
    table: int
    dish: Dish

    def __str__(self) -> str:
        return f"#{self.number:02d} {self.dish} (mesa {self.table})"


class DishBurnedError(Exception):
    """Erro de domínio com nome próprio — quem chama sabe o que tratar."""


# O "como preparar" é um parâmetro, não algo fixo dentro do cozinheiro:
# mechanism (operar a cozinha) separado de policy (a receita).
type Prep = Callable[[str, Order], Awaitable[None]]


# ═════════════════════════════════════════════════════════════════════════════
# CENA 1 — a espera é aproveitável; o esforço não é
# ═════════════════════════════════════════════════════════════════════════════
async def scene_1_waiting_pays_off() -> None:
    print("\n=== CENA 1 — a espera é aproveitável ===")

    async def put_in_the_oven(dish: Dish, seconds: float) -> None:
        print(f"  → {dish} no fogo")
        await asyncio.sleep(seconds)  # ESPERA: o cozinheiro sai de perto
        print(f"  ✓ {dish} pronto")

    started = time.perf_counter()
    await put_in_the_oven(Dish.RISOTTO, RISOTTO_S)
    await put_in_the_oven(Dish.SALAD, SALAD_S)
    print(f"  um de cada vez ......... {time.perf_counter() - started:.1f}s")

    started = time.perf_counter()
    async with asyncio.TaskGroup() as ticket:
        ticket.create_task(put_in_the_oven(Dish.RISOTTO, RISOTTO_S))
        ticket.create_task(put_in_the_oven(Dish.SALAD, SALAD_S))
    print(f"  os dois ao mesmo tempo . {time.perf_counter() - started:.1f}s")

    print("  mesmo cozinheiro, mesma mão: ele só parou de olhar a panela.")
    print("  (se o trabalho fosse SOVAR MASSA — esforço, não espera — não haveria")
    print("   ganho nenhum: pra isso precisa de outra bancada, ou seja, outro core)")


# ═════════════════════════════════════════════════════════════════════════════
# CENA 2 — gather x TaskGroup: quem cancela o irmão?
# ═════════════════════════════════════════════════════════════════════════════
async def scene_2_the_orphan_dish() -> None:
    print("\n=== CENA 2 — gather x TaskGroup ===")

    async def side_dish() -> None:
        try:
            await asyncio.sleep(SIDE_DISH_S)
        except asyncio.CancelledError:
            print("  ✗ guarnição descartada (o ticket foi cancelado)")
            raise  # cancelamento se PROPAGA — nunca se engole
        print("  ✓ guarnição pronta")

    async def main_dish() -> None:
        await asyncio.sleep(SECONDS_UNTIL_BURN)
        raise DishBurnedError("bife queimou")

    print("\n  -- com gather --")
    try:
        await asyncio.gather(side_dish(), main_dish())
    except DishBurnedError as error:
        print(f"  ! erro chega na hora: {error}")
    await asyncio.sleep(WATCH_KITCHEN_S)
    print("  ^ a guarnição ficou pronta DEPOIS do erro: ninguém cancelou. Órfã.")
    print("    o cliente já foi e a cozinha continuou ocupada com o prato dele")

    print("\n  -- com TaskGroup --")
    try:
        async with asyncio.TaskGroup() as ticket:
            ticket.create_task(side_dish())
            ticket.create_task(main_dish())
    except* DishBurnedError as party:
        # ExceptionGroup: o bloco entrega TODOS os erros do ticket, não só o 1º
        print(f"  ! erro chega ao fechar o ticket: {party.exceptions}")
    await asyncio.sleep(WATCH_KITCHEN_S)
    print("  ^ a guarnição foi cancelada junto: nada de órfão, nada de desperdício")


# ═════════════════════════════════════════════════════════════════════════════
# CENA 3 — a brigada: um balcão, N cozinheiros
# ═════════════════════════════════════════════════════════════════════════════
async def prepare_dish(cook: str, order: Order) -> None:
    """POLÍTICA: o que é fazer o prato. Injetada no cozinheiro (tipo `Preparo`)."""
    await asyncio.sleep(random.uniform(MIN_PREP_S, MAX_PREP_S))
    if random.random() < BURN_CHANCE:
        raise DishBurnedError(f"{order} queimou")
    print(f"  ✓ [{cook}] entregou {order}")


async def cook(
    name: str,
    pass_queue: asyncio.Queue[Order],
    prep: Prep,
    fryers: asyncio.Semaphore,
) -> None:
    """MECANISMO: puxar do balcão, cronometrar, tratar erro, encerrar o turno.

    Ele não sabe cozinhar nada — `preparo` vem de fora. Trocar o menu não
    mexe uma linha aqui.
    """
    while True:
        order = await pass_queue.get()  # FORA do try — LIÇÃO 1 no rodapé do arquivo
        try:
            async with asyncio.timeout(DISH_TIMEOUT_S), fryers:
                await prep(name, order)
        except TimeoutError:
            print(f"  ! [{name}] {order} estourou {DISH_TIMEOUT_S}s")
        except DishBurnedError as error:
            # sem este except o cozinheiro MORRE CALADO e a fila nunca mais anda
            print(f"  ! [{name}] {error}")
        finally:
            pass_queue.task_done()  # é isso que faz o `join()` do fim retornar


async def scene_3_the_brigade() -> None:
    print("\n=== CENA 3 — a brigada ===")
    random.seed(RANDOM_SEED)

    pass_queue: asyncio.Queue[Order] = asyncio.Queue(maxsize=PASS_SIZE)
    fryers = asyncio.Semaphore(FRYERS_AVAILABLE)  # do restaurante,
    #                                                            não de cada chef

    async with asyncio.TaskGroup() as shift:
        brigade = [
            shift.create_task(
                cook(f"chef-{number}", pass_queue, prepare_dish, fryers),
                name=f"chef-{number}",
            )
            for number in range(1, COOKS_ON_SHIFT + 1)
        ]

        for number in range(1, TOTAL_ORDERS + 1):
            order = Order(
                number=number,
                table=(number % TABLES_IN_ROOM) + 1,
                dish=random.choice(TODAYS_DISHES),
            )
            await pass_queue.put(order)  # balcão cheio? o garçom ESPERA aqui

        await pass_queue.join()  # espera a cozinha esvaziar
        for task in brigade:
            task.cancel()  # fim do turno: a brigada vai pra casa

    print("  cozinha fechada, brigada liberada")


async def main() -> None:
    await scene_1_waiting_pays_off()
    await scene_2_the_orphan_dish()
    await scene_3_the_brigade()


if __name__ == "__main__":
    asyncio.run(main())
    # Troque por `asyncio.run(main(), debug=True)` e o Python passa a GRITAR
    # sempre que alguma coisa segurar o expedidor por mais de 100ms.
    # É o cronômetro do ticket: use antes de otimizar qualquer coisa.


# ═════════════════════════════════════════════════════════════════════════════
# AS QUATRO LIÇÕES QUE VALEM MAIS QUE O CÓDIGO
#
# 1. `await balcao.get()` fica FORA do `try`.
#    Ao cancelar o cozinheiro, ele quase sempre está parado esperando no `get()`.
#    Se o `get()` estivesse dentro do `try`, o `finally` chamaria `task_done()`
#    para um pedido que nunca existiu → ValueError("task_done() too many times").
#
# 2. `except Exception` NÃO engole cancelamento.
#    `CancelledError` herda de `BaseException`. É de propósito: "fim do turno"
#    não é "prato queimado", e o cozinheiro não pode ignorar a ordem de parar.
#
# 3. `Queue(maxsize=...)` é a decisão mais importante do arquivo.
#    Fila infinita = aceitar 300 pedidos numa cozinha de 4 pessoas: ninguém
#    reclama, ninguém erra, e todo mundo come frio. Com limite, a pressão
#    aparece na PORTA ("hoje a espera é 20 min") em vez de virar prato frio.
#
# 4. `timeout` existe pra que um prato travado não vire um COZINHEIRO travado.
#    Sem ele, um `await` que nunca volta consome uma vaga da brigada pra sempre.
# ═════════════════════════════════════════════════════════════════════════════
