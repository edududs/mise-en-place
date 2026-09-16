"""Arquivar resultados acontece depois de encerrar o turno."""

from __future__ import annotations

from ..contracts.results import Measurement
from ..contracts.storage import ResultStore


def archive(key: str, result: Measurement, store: ResultStore) -> None:
    store.save(key, result)


# As lições: a aplicação depende da porta; filesystem é escolha da montagem.
