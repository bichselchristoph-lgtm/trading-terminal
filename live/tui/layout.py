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
class Stage:
    """One of the twelve pipeline stages. S009a part 3.

    Declared here so that **a stage which exists in the spec and not in code is
    distinguishable from a stage that does not exist.** Before this, a component
    absent from the config did not render at all, and Christoph had to ask
    whether there should be an indicator section — the question that proves the
    two were rendering identically.

    Exactly one of `built_by`, `slice`, `human` or `renders` says what this stage
    currently is:

    * `built_by` — a slice has built it.
    * `slice`    — a slice will build it; the badge names it.
    * `human`    — not a slice and never will be. A stage the system does not
                   perform must not render as one it has not performed yet.
    * `renders`  — produced outside the terminal and pointed at from a panel.
                   **`regime` is the only one, and it is not a stage that is
                   coming**: `SPEC.md` §3.2 removes every regime layer from the
                   terminal, so the health panel's pointer is correct and must
                   not become a `NOT BUILT` panel.

    A stage with none of the four renders `[ NOT BUILT ] (slice not assigned)`,
    which is a finding rather than a formatting gap — see `manage`.
    """

    slot: int
    name: str
    built_by: str = ""
    slice: str = ""
    human: bool = False
    renders: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.slot, bool) or not isinstance(self.slot, int):
            raise ValueError(f"{self.name}: slot must be an ordinal int, got {self.slot!r}")
        claims = [bool(self.built_by), bool(self.slice), self.human, bool(self.renders)]
        if sum(claims) > 1:
            raise ValueError(
                f"{self.name}: a stage makes at most ONE claim about its state, got "
                f"built_by={self.built_by!r} slice={self.slice!r} human={self.human} "
                f"renders={self.renders!r}. Two claims render as one badge and the "
                f"other is silently lost.")


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
    def __init__(self, components: list[Component], stages: Optional[list[Stage]] = None):
        self._components = components
        self._stages = stages or []

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
        stages = [Stage(**s) for s in data.get("stages", [])]
        seen_stage: set[int] = set()
        for s in stages:
            if s.slot in seen_stage:
                raise ValueError(f"duplicate stage slot {s.slot} for {s.name}")
            seen_stage.add(s.slot)
        return cls(sorted(comps, key=lambda c: c.slot),
                   sorted(stages, key=lambda s: s.slot))

    @property
    def stages(self) -> list[Stage]:
        """EVERY stage, built or not. There is no `visible_only` for stages —
        an unbuilt stage rendering is the entire point of declaring them."""
        return list(self._stages)

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
