"""Session-level fixture that enforces zero BOV imports in library source."""
from __future__ import annotations

import ast
import pathlib

import pytest

SRC = pathlib.Path(__file__).parent.parent / "src" / "agentic_debate"


def _collect_imports(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text())
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


@pytest.fixture(scope="session", autouse=True)
def assert_no_bov_imports() -> None:
    violations: list[str] = []
    for py_file in SRC.rglob("*.py"):
        for module in _collect_imports(py_file):
            if module.startswith("bov_agentic_runtime"):
                violations.append(
                    f"{py_file.relative_to(SRC)}: imports {module}"
                )
    if violations:
        pytest.fail(
            "Library source imports host adapter:\n" + "\n".join(violations)
        )
