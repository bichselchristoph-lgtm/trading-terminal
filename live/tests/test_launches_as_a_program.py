"""The app must start as a **program**, not only as a library. 029.

**What happened.** Christoph ran the `013` UAT:

    PS D:\\Dev\\momentum> C:\\venvs\\trading\\Scripts\\python.exe -m live.tui.app
    PS D:\\Dev\\momentum>

No output, no traceback, prompt returns. `app.py` defined `MomentumApp` and
nothing called `.run()`, so `-m` imported the module, executed the class
definitions, reached the end and exited **0**. 236 tests passed at the time.

**Why the suite did not catch it, which is the more important half.** Every
other test in this folder drives the app through Textual's `run_test()` pilot,
which constructs `MomentumApp` directly and never needs a process entry point.
The suite was asking *does this library behave* while the UAT was asking *does
this program start* — **two different questions about objects that share a
name**, and nothing in the repo knew they were different.

**So this test is a subprocess, and nothing else will do.**

    A test that imports `live.tui.__main__` and asserts it exists is not this
    test. It would pass against an entry point that raises on its first line.

**And `returncode == 0` is not the assertion either — exit 0 IS the bug.** The
broken command exited 0. What this asserts is that the process **reached the
point of rendering**: it drove the app far enough to produce a screen, and that
screen carries the panel titles.

**The mechanism**, stated because the next reader will need to know which of
Textual's several headless routes this uses — installed version is **8.2.8**:

* `TEXTUAL_DRIVER=textual.drivers.headless_driver:HeadlessDriver` — selected by
  environment via `App.get_driver_class`, so **the launcher needs no test-only
  flag**. A `--headless` switch on the entry point would be a second place where
  behaviour lives, and the test would then be exercising the switch.
* `TEXTUAL_SCREENSHOT=1` — Textual's own `App._ready` hook: once the app is
  ready it saves an SVG of the rendered screen and calls `exit()`. The SVG is
  the evidence and the exit is what makes the test terminate.
* `COLUMNS`/`LINES` — the headless driver sizes itself from
  `shutil.get_terminal_size()`, which reads these. 209x54 is the terminal the
  `013` UAT is performed on.

**`TEXTUAL_SCREENSHOT=0` does not work on 8.2.8** and the failure is not
obvious: `timer.py` divides by the interval and raises `ZeroDivisionError` in a
task nobody retrieves, so the app never exits and the test hangs to its timeout.
One second, deliberately.
"""
from __future__ import annotations

import html
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

#: The size the `013` UAT is run at.
UAT_COLS, UAT_ROWS = 209, 54

#: Startup + the one-second screenshot delay, with room for a cold import on a
#: loaded machine. A hang is a failure, not a wait.
LAUNCH_TIMEOUT = 90

#: Every panel `render_panels` places on an empty record. Checking one title
#: would pass against a frame that mounted a single tile and died.
EXPECTED_TITLES = ["WATCHLIST", "ATTACHED", "TAPE", "SIZING", "RISK", "HEALTH",
                   "PIPELINE"]

#: Both commands, and **both are required.** `-m live.tui` is the form worth
#: having; `-m live.tui.app` is the one Christoph has in his shell history and
#: will type again.
COMMANDS = ["live.tui", "live.tui.app"]


def svg_text(svg: Path) -> str:
    """The rendered characters, with the SVG scaffolding removed.

    Textual writes each styled run as its own `<text>` element and pads with
    NO-BREAK SPACE (U+00A0). Both are normalised here so an assertion can be
    written in the words that appear on screen.
    """
    raw = svg.read_text(encoding="utf-8")
    spans = re.findall(r"<text[^>]*>(.*?)</text>", raw, re.S)
    return " ".join(html.unescape(s) for s in spans).replace("\u00a0", " ")


def launch(module: str, out_dir: Path,
           cols: int = UAT_COLS, rows: int = UAT_ROWS) -> tuple[subprocess.CompletedProcess, Path]:
    """Start `python -m <module>` as a real process and return it with its shot."""
    shot = out_dir / f"{module.replace('.', '-')}.svg"
    env = dict(os.environ)
    env.update(
        TEXTUAL_DRIVER="textual.drivers.headless_driver:HeadlessDriver",
        TEXTUAL_SCREENSHOT="1",
        TEXTUAL_SCREENSHOT_LOCATION=str(out_dir),
        TEXTUAL_SCREENSHOT_FILENAME=shot.name,
        COLUMNS=str(cols),
        LINES=str(rows),
        # cwd is set to REPO below; PYTHONPATH makes the import independent of
        # it, so a runner that changes directory does not turn this red for an
        # unrelated reason.
        PYTHONPATH=str(REPO),
        PYTHONIOENCODING="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, "-m", module],
        cwd=REPO, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=LAUNCH_TIMEOUT,
    )
    return proc, shot


@pytest.mark.parametrize("module", COMMANDS)
def test_the_command_reaches_the_point_of_rendering(module: str, tmp_path: Path) -> None:
    """**The one that would have caught it.**

    Ordered so the failure message names the real defect: the missing screen is
    checked BEFORE the exit code, because a silent exit 0 is what this exists to
    catch and `returncode == 0` would pass against it.
    """
    proc, shot = launch(module, tmp_path)

    assert shot.is_file(), (
        f"python -m {module} produced no rendered screen.\n"
        f"  exit code : {proc.returncode}   <- 0 here is the DEFECT, not the pass\n"
        f"  stdout    : {proc.stdout.strip()!r}\n"
        f"  stderr    : {proc.stderr.strip()!r}\n"
        "The module was imported and the process ended without the app ever "
        "running. That is 029: no entry point."
    )

    assert proc.returncode == 0, (
        f"python -m {module} rendered, then exited {proc.returncode}\n{proc.stderr}")

    screen = svg_text(shot)
    missing = [t for t in EXPECTED_TITLES if t not in screen]
    assert not missing, (
        f"python -m {module} started but did not render {missing} at "
        f"{UAT_COLS}x{UAT_ROWS}.\nRendered:\n{screen[:2000]}")


def test_it_starts_with_no_broker_and_says_why_each_panel_is_empty(tmp_path: Path) -> None:
    """SPEC.md 4.2 — *surfaced, not refused*, at the process boundary.

    There is no TWS in this environment and there must not need to be. **A
    launcher that exits when the broker is absent is a refusal the user cannot
    read** — the same defect as the silent exit, moved one line later. The
    panels render and each states its own reason for being empty.
    """
    proc, shot = launch("live.tui", tmp_path)
    # Named, not left to `read_text` raising FileNotFoundError three frames
    # deep. A test whose red is a stack trace about a temp path is a test whose
    # red gets read as a broken test.
    assert shot.is_file(), (
        "python -m live.tui produced no rendered screen with no broker present.\n"
        f"  exit code : {proc.returncode}   <- 0 here is the DEFECT, not the pass\n"
        f"  stderr    : {proc.stderr.strip()!r}")
    screen = svg_text(shot)

    for reason in ["(no watchlist ingested today)", "(no feed connected)",
                   "(no account snapshot)"]:
        assert reason in screen, (
            f"launched with no broker and {reason!r} was not on screen.\n"
            f"Rendered:\n{screen[:2000]}")
