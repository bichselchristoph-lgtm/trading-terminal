"""Report-header wiring. 022.

`tests/test_no_secrets.py` scans credential surfaces that are NOT inside this
repository — the `.claude/` of each ancestor directory — because on 2026-08-13 a
live key sat in one of them while the suite was green.

**Those roots may or may not exist on a given machine, and a `pytest.skip` would
render as a bare `s`.** Invisibility is precisely the failure that file exists to
prevent: a scan that quietly covers nothing looks exactly like a scan that found
nothing. So the coverage is printed in the report header on **every** run, green
or red, listing each candidate root as PRESENT or ABSENT.

`pytest.ini` already refuses `-q` on the stated grounds that the header carries
load-bearing caveats. This is that channel.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


def pytest_report_header() -> list[str]:
    # Loaded BY PATH. `tests/` is not a package -- it has no `__init__.py`, by
    # design, so `import tests.test_no_secrets` raises ModuleNotFoundError and
    # takes the whole session down as an INTERNALERROR before a single test runs.
    #
    # WRAPPED, and that is not defensive habit. A header is a reporting aid; if
    # it can abort the run, a cosmetic edit to it can silently disable the entire
    # suite -- strictly worse than the invisibility it exists to fix. On failure
    # it says so in the header and the tests still run.
    try:
        path = Path(__file__).parent / "test_no_secrets.py"
        spec = importlib.util.spec_from_file_location("_no_secrets_header", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.coverage_report()
    except Exception as exc:  # noqa: BLE001 -- see above
        return [f"credential scan roots: CANNOT COMPUTE ({type(exc).__name__}: {exc})"]
