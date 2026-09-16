"""Verifica dependências reais, incluindo imports relativos e pacotes intermediários."""

from __future__ import annotations

import ast
from importlib.util import resolve_name
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "mise_en_place"
FORBIDDEN = {
    "contracts": {
        "restaurant",
        "adapters",
        "application",
        "bootstrap",
        "configuration",
        "ai",
        "game",
        "guests",
    },
    "application": {"restaurant", "adapters", "bootstrap", "configuration", "ai", "game", "guests"},
    "ai": {"restaurant", "adapters", "application", "bootstrap", "configuration", "game", "guests"},
    "game": {"restaurant", "adapters", "application", "bootstrap", "configuration", "ai", "guests"},
    "restaurant": {"adapters", "application", "bootstrap", "configuration", "ai", "game", "guests"},
}
EXTERNAL = {"pydantic", "fastapi", "django", "sqlalchemy"}


def violations(source: str, module: str, boundary: str) -> list[str]:
    package = module.rsplit(".", 1)[0]
    imports: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            name = "." * node.level + (node.module or "")
            resolved = resolve_name(name, package) if node.level else name
            imports.append(resolved)
            imports.extend(f"{resolved}.{alias.name}" for alias in node.names)
    rejected: list[str] = []
    for name in imports:
        parts = name.split(".")
        if parts[0] in EXTERNAL or (
            len(parts) > 1 and parts[0] == "mise_en_place" and parts[1] in FORBIDDEN[boundary]
        ):
            rejected.append(name)
    return rejected


@pytest.mark.parametrize("boundary", list(FORBIDDEN))
def test_boundaries(boundary: str) -> None:
    for path in (PACKAGE / boundary).rglob("*.py"):
        relative = path.relative_to(PACKAGE).with_suffix("")
        module = "mise_en_place." + ".".join(relative.parts)
        assert not violations(path.read_text(encoding="utf-8"), module, boundary), path


def test_guard_detects_deliberate_violation() -> None:
    assert violations("from ..adapters import storage", "mise_en_place.ai.policy", "ai")
    assert violations("import pydantic", "mise_en_place.contracts.models", "contracts")


# As lições: arquitetura precisa de uma verificação que falhe quando sua regra é quebrada.
