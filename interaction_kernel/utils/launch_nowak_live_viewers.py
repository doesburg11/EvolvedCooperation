#!/usr/bin/env python3
"""Launch live viewers for Nowak mechanism packages from one menu.

Run from repo root:
  ./.conda/bin/python -m interaction_kernel.utils.launch_nowak_live_viewers
"""

from __future__ import annotations

from typing import Callable

from direct_reciprocity.direct_reciprocity_pygame_ui import main as direct_main
from group_selection.group_selection_pygame_ui import main as group_main
from indirect_reciprocity.indirect_reciprocity_pygame_ui import main as indirect_main
from kin_selection.kin_selection_pygame_ui import main as kin_main
from network_reciprocity.network_reciprocity_pygame_ui import main as network_main

VIEWERS: list[tuple[str, Callable[[], None]]] = [
    ("kin_selection", kin_main),
    ("network_reciprocity", network_main),
    ("direct_reciprocity", direct_main),
    ("indirect_reciprocity", indirect_main),
    ("group_selection", group_main),
]


def _show_menu() -> None:
    print("Nowak live viewer launcher")
    print("Choose one viewer:\n")
    for i, (name, _) in enumerate(VIEWERS, start=1):
        print(f"  {i}. {name}")
    print("  a. run all sequentially")
    print("  q. quit")


def _run_one(index: int) -> None:
    name, entrypoint = VIEWERS[index]
    print(f"[launch_nowak_live_viewers] starting {name}")
    entrypoint()


def main() -> None:
    while True:
        _show_menu()
        choice = input("selection: ").strip().lower()

        if choice in {"q", "quit", "exit"}:
            print("[launch_nowak_live_viewers] exiting")
            return

        if choice in {"a", "all"}:
            for i in range(len(VIEWERS)):
                _run_one(i)
            return

        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(VIEWERS):
                _run_one(index)
                return

        print("Invalid selection. Please choose a listed option.\n")


if __name__ == "__main__":
    main()
