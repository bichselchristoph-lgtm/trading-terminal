"""`python -m live.tui` — the package entry point. 029.

**Two lines, deliberately.** Everything the launch actually does lives in
`live.tui.app.main`, which `-m live.tui.app` also reaches. A launcher that did
its own config loading here would be a **second place where configuration
lives**, and the two would drift the moment one of them was fixed — the
project's oldest pattern, applied to its newest file.

There is no argument parsing because there is nothing to parse: one command, no
flags, no defaults acquired at the boundary (`SPEC.md` §4.4).
"""
from __future__ import annotations

from .app import main

raise SystemExit(main())
