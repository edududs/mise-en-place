"""Novo adaptador da aula 17: exporta os mesmos eventos para CSV."""

from __future__ import annotations

import csv
from dataclasses import asdict, fields
from typing import TextIO

from ..restaurant.observability.events import Event


class CsvJournal:
    def __init__(self, stream: TextIO) -> None:
        self._writer = csv.DictWriter(stream, fieldnames=[field.name for field in fields(Event)])
        self._writer.writeheader()

    def record(self, event: Event) -> None:
        self._writer.writerow(asdict(event))


# As lições: novo formato, mesmo contrato; ownership do stream continua com o chamador.
