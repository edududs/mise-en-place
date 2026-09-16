"""A entrada configura o meio; a operação não conhece encoding de terminal."""

from __future__ import annotations

import sys
from typing import Protocol, runtime_checkable


@runtime_checkable
class ConfigurableOutput(Protocol):
    def reconfigure(self, *, encoding: str) -> None: ...


def configure_output() -> None:
    if isinstance(sys.stdout, ConfigurableOutput):
        sys.stdout.reconfigure(encoding="utf-8")


# As lições: Windows redirecionado pode usar cp1252; encoding pertence ao adaptador.
