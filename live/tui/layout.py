"""`config/layout.yaml` — committed and load-bearing. S009 §4f.

One line per component: `id`, `slot` (an **ordinal, not a boolean**), `visible`,
and a **required `reason` on any change**. The renderer reads it; nothing else
does.

**A hidden component still computes and still writes to the day record.**
Otherwise only visible components accumulate evidence and the inference is
circular — tenet 7, *display is not storage*. Enforced by test, not by comment.

**No auto-reordering, ever.** A system that both measures your preference and
shapes it destroys the measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

REPO = Path(__file__).resolve().parents[2]
LAYOUT_PATH = REPO / "config" / "layout.yaml"


@dataclass
class Component:
    id: str
    slot: int
    visible: bool
    reason: str = ""

    def __post_init__(self) -> None:
        # `slot` is an ordinal. A bool here would silently sort as 0/1 and
        # collapse the ordering the file exists to express.
        if isinstance(self.slot, bool) or not isinstance(self.slot, int):
            raise ValueError(f"{self.id}: slot must be an ordinal int, got {self.slot!r}")


class Layout:
    def __init__(self, components: list[Component]):
        self._components = components

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Layout":
        p = path or LAYOUT_PATH
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        comps = [Component(**c) for c in data.get("components", [])]
        seen: set[int] = set()
        for c in comps:
            if c.slot in seen:
                raise ValueError(f"duplicate slot {c.slot} for {c.id}")
            seen.add(c.slot)
        return cls(sorted(comps, key=lambda c: c.slot))

    @property
    def all(self) -> list[Component]:
        """EVERY component, visible or not.

        This is the list the compute path iterates. `visible_only` is for the
        renderer alone — that separation is the whole of tenet 7.
        """
        return list(self._components)

    @property
    def visible_only(self) -> list[Component]:
        return [c for c in self._components if c.visible]

    def hidden(self) -> list[Component]:
        return [c for c in self._components if not c.visible]
