"""A PORTA que o cliente usa para interagir com a casa.

Este é o ponto mais importante da aula 4, e vale ler devagar:

O `Protocol` está declarado **aqui**, no package de quem CONSOME — não no
package do restaurante. Isso inverte a seta de dependência (DIP): a clientela
não depende de uma implementação, ela **declara o que precisa**, e quem serve
tem que se encaixar.

E porque `Protocol` é *estrutural*, o `Restaurante` satisfaz este contrato
**sem herdar de nada e sem importar este arquivo** — ele nem sabe que a
clientela existe. A verificação acontece no único lugar onde os dois se
encontram, o `__main__.py` da aula, e é o type checker que faz. Isto é
hexagonal de graça: porta declarada pelo consumidor, adaptador conferido
estaticamente, zero framework.
"""

from __future__ import annotations

from typing import Protocol

from ..restaurant import Clock, RawOrder
from ..restaurant.dining import Table


class FrontOfHouse(Protocol):
    """O que um cliente precisa de um restaurante. Nada mais que isso."""

    clock: Clock

    async def seat(self, size: int, patience_minutes: float | None = None) -> Table: ...

    async def order(self, raw: RawOrder) -> None: ...

    async def ask_for_bill(self, table: int) -> None: ...

    async def release(self, table: Table) -> None: ...
