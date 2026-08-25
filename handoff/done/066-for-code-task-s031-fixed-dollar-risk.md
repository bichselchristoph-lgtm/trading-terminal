---
task: 066
title: "S031: size from a fixed dollar risk"
type: task
class: product
story: S031
epic: 7
owner: claude-code
repo: D:\Dev\tws_order
depends: none
touches: tws_order sizing module, tws_order CLI, tws_order tests
bugs:
  - id: B-041
    action: close
    status: "Closed. --risk-usd sizes from a fixed dollar risk figure, Decimal end to end (compute_sizing_from_risk_usd, tws_order/sizing.py), mutually exclusive with --risk-pct, refused when neither is given. See Part A below for the exact design and why the existing 37 tests needed zero changes."
---

**Status** RUNNING

# 066 — S031: size from a fixed dollar risk

**This note needs to be pasted to chat.**

---

## 0. Where the work is

**All of it in `D:\Dev\tws_order`, a separate git repo. Nothing in `D:\Dev\momentum` changed** except this note, `verify.ps1`'s own output, and the sync files other concurrent sessions had already touched before this task began (left exactly as found, per every prior task's own discipline).

**Two disjoint subagents, as §2 asked for** — Part A (the sizing module + CLI) and Part B (the secrets test), launched in parallel, neither committing. This session reviewed both diffs in full, ran the suite independently (not trusting either agent's own "it passed" report), did one more red/green pass of its own via `git stash`, then made the single commit both parts share.

---

## Part A — `--risk-usd`

### The design decision that needed resolving before implementation, stated because it is the one genuinely interpretive call in this task

Criterion 3 reads *"Given neither flag, Then it refuses and names the missing choice — nothing defaults."* Read literally and applied inside `resolve_config()`, that would refuse **every** invocation of `--show-config`, `--cancel`, and any submit with no risk flag at all — because `resolve_config()` today always resolves `risk_pct` to *something* (CLI, then config file, then the built-in default of 0.5%), and two existing tests (`test_cli_overrides_config_which_overrides_builtin_default`, `test_config_file_values_take_precedence_over_builtin`) pin exactly that resolving-with-no-CLI-flag behaviour as correct. §7 also requires **"tws_order's existing 37 tests still pass"** — those two among them.

**Resolution: `resolve_config()` is untouched — it still always resolves a `risk_pct`, exactly as before, for any command.** The new refusal (criteria 2 and 3) lives in `cmd_submit()` instead, in the same place `--symbol`'s own required-ness already lives (`if not resolved.symbol: ... return 2`, never inside `resolve_config()`) — because required-ness is a property of *which command is running*, and `--show-config`/`--cancel` never need a risk figure at all. Two new fields carry what `cmd_submit()` needs to judge this that `resolved.risk_pct` alone cannot: `risk_usd: Optional[Decimal]` (parsed/validated, CLI-only) and `risk_pct_given_on_cli: bool` (`args.risk_pct is not None` — distinct from `resolved.risk_pct`, which is never `None`).

The observable result satisfies criterion 3 exactly as stated: `provision_order.py --symbol NVDA` with neither flag now refuses at the CLI, naming both flags, even though `resolved.risk_pct` still silently holds `0.5` internally — it is simply never reached by the sizing call in that path. **Zero existing tests needed modification.** This was checked, not assumed: grepped every test file for `risk_pct`/`compute_sizing`/`print_success` before writing anything, confirmed no test exercises a full `cmd_submit()` success path or `output.print_success` directly (so the `risk_pct: float` → `risk_basis: str` rename there was also safe), and reran the untouched 37 alongside every new test at the end.

### What changed

- **`tws_order/sizing.py`** — new `compute_sizing_from_risk_usd(risk_usd: Decimal, entry_price: float, stop_price: float) -> SizingResult`. Decimal end to end for the subtraction/division that actually matter: `Decimal(str(entry_price))`/`Decimal(str(stop_price))` — **never `Decimal(x)` directly**, which would just encode the float's own binary imprecision into a Decimal — so `stop_distance` is exact for any two decimal-representable prices. `compute_sizing()`'s existing float path is byte-identical to before; it is a different, deliberately-preserved defect (see the existing `test_basic_sizing_matches_spec_example`'s own docstring: `71.20 - 70.50` in float floors to 139 shares, "not a bug"). Same class as B-031 (a float subtraction landing a hair off zero, in a different module's R-multiple classification) — this is where `tws_order`'s own sizing arithmetic gets the Decimal treatment for the path this story adds. `shares = int(risk_usd // stop_distance)` — Decimal floor division, both operands always positive by the time this runs — never rounds up.
- **`tws_order/config.py`** — `ResolvedConfig` gains `risk_usd: Optional[Decimal]` and `risk_pct_given_on_cli: bool`. `resolve_config()` parses `args.risk_usd` (a raw string — `type=str` on the CLI flag, not `float`, so a malformed value can be echoed back verbatim) into a `Decimal`, refusing with the exact received value on a parse failure or a non-positive value (criterion 4). **Never reads a `risk_usd` key from the YAML config file or `BUILT_IN_DEFAULTS`** — "1R is received, never read": confirmed by a new test (`test_risk_usd_is_never_read_from_config_file`) that `BUILT_IN_DEFAULTS["risk"]` carries no such key.
- **`tws_order/cli.py`** — `--risk-usd` added to the parser. `cmd_submit()` gains the two refusals (criteria 2, 3) as the very first check after `--symbol`, **before** `_print_resolved_warnings()` — placed there deliberately so a doomed both-flags request never first prints an irrelevant "risk_pct clamped to 2.0%" warning about a figure it's about to refuse to use. The sizing call branches on `resolved.risk_usd is not None`. `output.print_success`'s `risk_pct: float` parameter became `risk_basis: str` (`"fixed $ risk"` vs `f"{resolved.risk_pct:.2f}% NLV"`, computed once at the call site) — the old signature would have printed a bogus, unused percentage figure next to a dollar-sized order.
- **Tests** — 14 new, across `tests/test_sizing.py` (5), `tests/test_config.py` (6), `tests/test_cli.py` (3). The Decimal-precision test is built from the SAME price pair (`71.20`/`70.50`) the existing float test uses — `Decimal("71.20") - Decimal("70.50")` is exactly `Decimal("0.70")`, so `floor(98.00 / 0.70)` is unambiguously 140, asserted directly against 140, with a comment cross-referencing the float path's 139 on the identical inputs. Every one of the five acceptance criteria has its own test; round-down-never-up gets its own on an inexact division ($100.03 / $3.00 → 33, not 34).

---

## Part B — the secrets test this repo never had

`tests/test_no_secrets.py` (new, this repo's first), `tests/conftest.py` (report-header wiring — the coverage report would otherwise be invisible under `-q`), `pytest.ini` (new — `addopts = --strict-markers`, deliberately **not** `-q`, for the same reason).

**Adapted from `D:\Dev\momentum\tests\test_no_secrets.py`, intent kept, patterns re-derived rather than copied** — read in full first, per §4's own instruction. Where it does NOT transfer cleanly, found and stated in the new file's own module docstring: momentum's `db-[A-Za-z0-9]{20,}` Databento-key pattern is shape-correct for what it protects, but `tws_order` has no Databento dependency at all, so reusing it here would produce a scan that can only ever pass — vacuous coverage wearing the shape of real coverage, which is precisely what got two real Databento keys past momentum's own earlier version, just arrived at from the opposite direction. Replaced with AWS-access-key and private-key-block patterns (plausible leaks for any Python project, regardless of vendor), plus the same 12-character-floor credential-in-index-url pattern.

**What transfers directly and was not skipped:** `D:\Dev\tws_order` and `D:\Dev\momentum` share the identical parent, `D:\Dev` — so the ancestor-`.claude`-adjacent-surface gap that took momentum three rewrites to actually close (`022`) is the exact same gap here. **`D:\Dev\.claude\settings.local.json` is real and present on this machine today**, confirmed scanned (the coverage header shows `PRESENT Dev/.claude D:\Dev\.claude (1 files read)`, visible in `verify.ps1`'s §10 output above) and clean.

**Teeth, not just plumbing**: planted-fixture tests prove the walk actually reaches a synthetic key in a `tmp_path`-based `.claude/settings.local.json` and in a `Pipfile.lock` (chosen specifically because `.lock` is outside `TEXT_SUFFIXES`, so this only passes if the manifest-name routing genuinely fires regardless of extension). A `test_the_adjacent_branch_is_not_silently_empty` guard fails if the real, present `D:\Dev\.claude` root exists but nothing was actually routed to the adjacent-surface test — the "green because it never looked" shape, made unreachable rather than assumed away.

**The required `$env:TEMP` red/green demonstration**, done by hand, reported here rather than left as a permanent script: a realistic fake AWS-key-shaped string was planted in `%TEMP%\tws_order_secrets_probe\.claude\settings.local.json` (outside this repo and every one of its ancestors), the scan's own matching function was pointed at it and fired (RED), the probe directory was deleted and the same function confirmed empty (GREEN), then the real, permanent suite was run against the real tree (19/19 secrets tests passing). No credential-shaped string was ever written inside `D:\Dev\tws_order`, including transiently.

**An incident during that demonstration, disclosed in full and independently re-verified by this session before committing anything:** a `$env:TEMP`-resolution mishap during the manual probe accidentally created garbage-named nested directories **inside `D:\Dev\momentum`** (not `tws_order`) — a tree the Part B agent was explicitly told not to touch. The agent found and removed them itself (`rmdir` on the exact names, after a recursive `rm` was blocked by this session's own sandbox), then reported the incident and its cleanup rather than staying silent. **This session independently re-checked `D:\Dev\momentum` before writing anything further** — `git status --short` and a `Get-ChildItem -Recurse` sweep for directory names containing a newline or colon, both clean; only the two pre-existing, legitimate `wt-probe`/`records\probes` directories matched a loose `*probe*` filter. No trace of the incident remains, nothing from it was ever committed, and `verify.ps1`'s own precondition (`063`'s own "tree was dirty" guard) would have caught a genuine leftover regardless.

---

## §5, confirmed cleared

`verify.ps1` §10 now reports `tws_order`'s path, HEAD and raw suite output — checked directly in `handoff/verify-output.md` after this task's run: HEAD `d8c8388`, `70 passed, 1 warning`, coverage report included verbatim. The instrument existed and was used, not merely trusted to exist.

---

## Tests — full account, both parts

`tws_order` suite: **37 → 70 passed** (14 from Part A, 19 from Part B, 37 pre-existing untouched). Confirmed independently by this session (not merely trusted from either subagent's report):

- Reviewed every diff in full before running anything.
- Ran the full suite myself: `70 passed, 1 warning in 0.81s`.
- Did my own `git stash` of `tws_order/sizing.py`/`config.py`/`cli.py`/`output.py` against the real pre-fix tree and reran: **RED** — `ImportError: cannot import name 'compute_sizing_from_risk_usd'` at collection, `1 error` (test_sizing.py cannot even collect, so nothing in it could run). `git stash pop` restored the fix; reran: **green, 70 passed**, identical to before the stash.
- Part A's own report additionally confirmed each of the 5 acceptance criteria red/green individually via targeted reverts (documented in its own summary, not repeated verbatim here). Part B's own report confirmed three separate injected regressions (skipping `.claude`, bypassing manifest routing, adding a size-cap slice) each caught by a specific new test, then reverted.

---

## What was NOT touched, confirmed

`tws_order/stops.py`, `ibkr.py`, `audit.py`, `state.py`, `orphaned_protection_watcher.py` — untouched. No existing test function in `test_sizing.py`/`test_config.py`/`test_cli.py` was modified, only new functions added. `risk_pct`'s own default/precedence/clamp logic in `config.py` — byte-identical to before. `--cancel`/`cmd_cancel`/`--show-config`/`cmd_show_config` — untouched. No `risk_usd` config-file key anywhere. **Not in this task, confirmed untouched**: S026/S028 (blocked on the dead size-stage mockup), B-032 (`winner_min_r`'s float boundary — `momentum`'s RISK, other repo), B-076 (the ATR floor refit — Christoph's), order placement/transmit/staging (Read-Only API stays on; `--risk-usd` only changes sizing arithmetic, nothing reachable by it can transmit).

---

## UAT

Christoph's own, per §7: size one real setup from a dollar figure and check the share count by hand; confirm giving neither flag refuses rather than picking one. Not performed here.

---

## Closing sequence — §8's, not the usual one

1. **Committed and pushed `D:\Dev\tws_order`** — `d8c8388`, pushed to `origin/main` (`https://github.com/bichselchristoph-lgtm/tws_order.git`).
2. **`verify.ps1` run from this `momentum` checkout** — §10 captured `tws_order`'s HEAD and raw suite output (checked above). Not pasted in full here, per this project's own convention for `verify.ps1` output.
3. **This done-note**, naming the `tws_order` commit hash (`d8c8388`).
4. `export-handoff.ps1`, then push `momentum`, follow.
