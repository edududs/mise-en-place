"""Memória e arquivo implementam o mesmo contrato de armazenamento."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ..contracts.results import Measurement
from ..contracts.storage import validate_key


class MemoryResultStore:
    def __init__(self) -> None:
        self._results: dict[str, Measurement] = {}

    def save(self, key: str, result: Measurement) -> None:
        validate_key(key)
        self._results[key] = result

    def load(self, key: str) -> Measurement | None:
        validate_key(key)
        return self._results.get(key)


class StoredResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    result: Measurement


class JsonResultStore:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def save(self, key: str, result: Measurement) -> None:
        validate_key(key)
        payload = StoredResult(result=result).model_dump_json(indent=2)
        self._directory.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self._directory, delete=False
            ) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
            Path(temporary).replace(self._directory / f"{key}.json")
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def load(self, key: str) -> Measurement | None:
        validate_key(key)
        try:
            payload = (self._directory / f"{key}.json").read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        return StoredResult.model_validate_json(payload).result


# As lições: replace evita JSON parcial; não promete transação entre arquivos nem fsync.
