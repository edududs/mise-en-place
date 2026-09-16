"""Entrega local explícita; sem registro global, retries ou transações implícitas."""

from __future__ import annotations

from collections.abc import Callable

from ..contracts.events import RoundServed


class RoundDispatcher:
    def __init__(self, *handlers: Callable[[RoundServed], None]) -> None:
        self._handlers = handlers

    def publish(self, event: RoundServed) -> None:
        for handler in self._handlers:
            handler(event)


# As lições: ordem declarada e fail-fast; falha não desfaz prato já servido.
