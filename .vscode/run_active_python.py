#!/usr/bin/env python3
"""Run the active VS Code Python file as a package module when possible."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def _read_required_path(env_name: str) -> Path:
    raw_value = os.environ.get(env_name, "").strip()
    if not raw_value:
        raise SystemExit(f"Missing VS Code launch environment variable: {env_name}")
    return Path(raw_value).resolve()


def _is_valid_module_part(value: str) -> bool:
    return bool(value) and value.isidentifier()


def _module_name_for_file(active_file: Path, workspace_dir: Path) -> str | None:
    try:
        relative_file = active_file.relative_to(workspace_dir)
    except ValueError:
        return None

    if relative_file.suffix != ".py":
        return None

    parent_parts = relative_file.parent.parts
    if not parent_parts:
        return None

    current_dir = workspace_dir
    for part in parent_parts:
        if not _is_valid_module_part(part):
            return None
        current_dir = current_dir / part
        if not (current_dir / "__init__.py").is_file():
            return None

    stem = relative_file.stem
    if stem == "__init__":
        module_parts = list(parent_parts)
    else:
        if not _is_valid_module_part(stem):
            return None
        module_parts = [*parent_parts, stem]

    return ".".join(module_parts) if module_parts else None


def main() -> None:
    workspace_dir = _read_required_path("VSCODE_WORKSPACE_FOLDER")
    active_file = _read_required_path("VSCODE_ACTIVE_FILE")

    os.chdir(workspace_dir)

    workspace_str = str(workspace_dir)
    if sys.path[0] != workspace_str:
        sys.path.insert(0, workspace_str)

    module_name = _module_name_for_file(active_file, workspace_dir)

    if module_name is not None:
        runpy.run_module(module_name, run_name="__main__", alter_sys=True)
        return

    runpy.run_path(str(active_file), run_name="__main__")


if __name__ == "__main__":
    main()
