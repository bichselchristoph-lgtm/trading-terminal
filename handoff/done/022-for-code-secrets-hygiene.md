# 022 — done — secrets hygiene: the key is gone, and the test now looks where it was

**Status** RUNNING · **Date** 2026-08-13 · **Type** housekeeping · **Tree** `D:\Dev\momentum`

> **This note needs to be pasted to chat**, and it is now also exported to Drive under 020.
> Neither closes it.

---

## The headline, before anything else

**The task's Part 1 is wrong about where the key was, and the diagnosis it offers for Part 2 is
wrong about why the test missed it. Both were reasonable and both were checkable, so they were
checked rather than acted on.**

- **`D:\Dev\momentum\requirements.txt` never held the key.** Not in the working copy, not in any
  commit. The task calls this occurrence *"committed, which is why this occurrence is the worse
  of the two"*; the file it describes is the **archived** tree's, and even there the key is not
  in history.
- **The key is in no git history at all.** `git log --all -p` across `momentum`,
  `momentum-harness` and `tws_order`: **0 occurrences in each.** The standing constraint *"do
  not rewrite git history"* was therefore never in tension with anything — there is nothing in
  history to rewrite.
- **The failure mode was neither of the two offered.** See below.

---

## Which failure mode it was — the evidence

The task offered two: *never scanned `requirements.txt`* (scope) or *scanned and the pattern did
not match* (matcher). **It was neither. Both were already fixed and both were demonstrably
working.**

**Proof the scope was right.** `test_the_scan_actually_reaches_dependency_manifests` already
asserted `requirements.txt` is scanned, and it passed.

**Proof the matcher was right.** I planted a synthetic key in a `--extra-index-url` line in
`requirements.txt` and ran the suite. It went red on **both** patterns at once:

```
E       AssertionError: possible credential in index url in the tree:
E           requirements.txt:26  [credential in index url]
FAILED tests/test_no_secrets.py::test_no_credentials_in_the_tree[databento api key]
FAILED tests/test_no_secrets.py::test_no_credentials_in_the_tree[credential in index url]
2 failed, 8 passed in 0.44s
```

Reverted immediately; `requirements.txt` back to 0 matches.

### The actual failure mode: a third one, and it is structural

**The scan's ROOT was wrong. The key was outside the repository.**

```python
REPO = Path(__file__).resolve().parents[1]     # D:\Dev\momentum
for p in REPO.rglob("*"): ...
```

The key sat in **`D:\Dev\.claude\settings.local.json`** — the *parent* directory, a **sibling**
of the repo. `D:\Dev` is not a git repo at all. **`rglob` cannot leave `REPO`, so no amount of
widening the scan inside the repo could ever have reached it.** The test was answering *"no
secrets in this repository"* while the question everyone thought it answered was *"no secrets on
this machine."* That substitution is the failure the task itself names, one level up from where
it was looking for it.

It also explains why the module docstring's claim that **`.claude/` is in scope was vacuous**:
`D:\Dev\momentum` has no `.claude/` directory. The clause was true and covered nothing.

---

## Part 1 — every location searched, and every location found

**Scope stated, not implied.** Match pattern `db-[A-Za-z0-9]{20,}` (the key shape) plus
`://[^/@\s]+:[^/@\s]{12,}@` (URL-embedded credentials).

| Searched | Result |
|---|---|
| **All of `D:\Dev`**, recursive, including dotfiles, `.claude/`, `docs/`, every dependency manifest. Excluded `.git`, `.venv`, `__pycache__`, `records/`, `records_truncated/` | **1 file: `D:\Dev\.claude\settings.local.json`, lines 16, 17, 18** |
| `git log --all -p` in `momentum` | **0** |
| `git log --all -p` in `momentum-harness` | **0** |
| `git log --all -p` in `tws_order` | **0** |
| `D:\Dev\momentum\requirements.txt` (working copy and full history) | **0** |
| `D:\Dev\momentum-harness\requirements.txt` (working copy and full history) | **0** |
| `.claude` directories under `D:\Dev` — found two: `D:\Dev\.claude`, `D:\Dev\momentum-harness\.claude` | key in the **first only** |
| `~/.claude/` per subdirectory: `settings.json`, `hooks`, `plans`, `cache`, `downloads`, `sessions`, `shell-snapshots`, `paste-cache`, `backups` | **0 each** |
| `~/.claude/file-history/` | **39 files** |
| `~/.claude/projects/` | **2 files** |
| `~/.claude/history.jsonl` | **1** |

**Not searched, and named rather than left implicit:** `.venv` site-packages (third-party, and
the two shape hits there are a numpy `RECORD` sha256 and pyarrow's own S3 test fixtures — both
verified false positives), `records/` and `records_truncated/` (captured market data, gitignored,
never committed), the Windows registry, and environment variables themselves.

### What was changed

**`D:\Dev\.claude\settings.local.json`: three allow-rules removed, 108 → 105.** JSON re-parsed
after the edit to confirm it is still valid. The removal was **line-based, not a JSON
round-trip**, so the other 105 rules are byte-identical.

**Removed rather than rewritten, and the task's own words are the reason:** *"Every other rule in
that file already reads the key from the user environment, so these three are the anomaly, not
the pattern."* Deleting the anomalies restores the pattern. Rewriting them as env-reads would
have meant inventing a *new* permission grant to replace a dead one — permission rules are
patterns, and a broader pattern is a widening, not a fix. The env-read form the task asks for
**already exists** in that file, many times over, as
`PowerShell($env:DATABENTO_API_KEY = [Environment]::GetEnvironmentVariable('DATABENTO_API_KEY','User'); ...)`.

**After the change: `D:\Dev` contains 0 files matching the key shape.**

### What I could NOT do, and why — "empty is suspicious"

**The key remains in cleartext in 42 machine-local Claude Code files** — 39 under
`~/.claude/file-history/`, 2 session transcripts under `~/.claude/projects/`, and
`~/.claude/history.jsonl`. **I did not delete them.**

Not an oversight and not laziness: `file-history/` is what backs Claude Code's undo, and
`projects/` is the session record. Deleting either destroys tooling state and history to remove a
**rotated, dead** credential — **which is the same trade the task already refuses for git
history, for the same reason.** Rotation was the fix. **This is Christoph's call and it is
recorded as OBS-019.** Say the word and I will purge them.

**Also not done:** an audit of the other 105 permission rules. One of them contains an entire
pasted paragraph of design prose captured into what should be a `Bash(grep …)` pattern — a
permission rule can silently hold arbitrary text, and nobody reads a 105-entry allow list. That
is **OBS-021**, and widening 022's scope to chase it silently is the failure this project keeps
naming.

---

## Part 2 — the repair

`REPO` stays the primary root; **the scan now also covers `<ancestor>/.claude` for every ancestor
of the repo**, derived from `REPO.parents`, never enumerated.

| Added | What it does |
|---|---|
| `candidate_roots()` | `REPO`, plus `<ancestor>/.claude` per ancestor, **excluding the user home**. Two `exists()` calls that normally find nothing. |
| `existing_roots()` | The subset present here, deduped by `resolve()` so a junction cannot double-report. |
| `candidate_files(root)` / `read_texts(roots)` | The old walk, parameterised by root. |
| `in_repo()` / tolerant `rel()` | Splits in-tree from adjacent hits. **`rel()` must no longer raise on an out-of-tree path** — a `ValueError` there would crash the scan instead of reporting the hit. |
| `test_no_credentials_on_adjacent_surfaces` | **Separate test, separate remedy.** The fix for an adjacent hit is *rotate and remove from a file no repo owns*, not *do not commit this*. A reader must be able to tell from the test id whether red means the tree or the machine. |
| `test_the_parent_directory_claude_is_a_candidate_root` | **This carries the guarantee.** It asserts what the scan is *supposed* to cover, so it fails on a clean clone on any machine if the ancestor walk is deleted. |
| `test_the_root_list_is_derived_and_not_enumerated` | Parses the function with `ast`, strips the docstring, and forbids machine-specific literals **in the code**. |
| `test_the_walk_actually_reads_a_claude_settings_file` | End-to-end teeth in `tmp_path`. |
| `test_dot_claude_is_not_skipped` | The docstring's claim was vacuous; now it is checked. |
| `tests/conftest.py` | Prints the root coverage in the **pytest report header**. |

**The consequence, stated because it is a real cost:** the suite is no longer a pure property of
the tree. **`git checkout` can no longer make it green**, and neither can `.gitignore`. On an
adjacent hit the only route to green is rotating the credential and removing it. That is the
point — the hermetic alternative preserves exactly the blindness that caused this.

### Why a header and not a `pytest.skip`

The adjacent roots may not exist on another machine. **A skip renders as a bare `s`**, and
invisibility is the precise failure `test_no_secrets.py` exists to prevent — a scan that quietly
covers nothing looks identical to one that found nothing. `pytest.ini` already refuses `-q` on
the grounds that the header carries load-bearing caveats, so the header is this repo's designated
channel. Every run now prints:

```
credential scan roots:
  PRESENT  repo                     D:\Dev\momentum  (172 files read)
  PRESENT  Dev/.claude              D:\Dev\.claude  (1 files read)
  ABSENT   D:/.claude               D:\.claude
  NOT COVERED: the user-level ~/.claude - see OBS-020
```

**A blind spot that prints on every run is a stated blind spot.**

The header is wrapped in `try/except` — not defensive habit. A header is a reporting aid; if it
can abort the session, a cosmetic edit to it silently disables the entire suite, which is worse
than the invisibility it fixes. **It already did exactly that once**: `from tests.test_no_secrets
import …` raised `ModuleNotFoundError` (there is no `tests/__init__.py`, deliberately) and took
the run down as an `INTERNALERROR` before a single test collected. It now loads by path.

---

## The fixture going red, before the tree goes green — in that order

**The demonstration that matters.** A synthetic key planted in the **parent's** `.claude`, which
is the surface the old scope could never reach:

```
E       AssertionError: possible databento api key on a credential surface ADJACENT to this repo:
E           D:/Dev/.claude/settings.local.json:109  [databento api key]
E
E       This file is in no repository, so no git operation fixes it and this test
E       cannot be made green by editing the tree. Rotate the credential, then remove
E       it from the file.
FAILED tests/test_no_secrets.py::test_no_credentials_on_adjacent_surfaces[databento api key]
1 failed, 17 passed in 0.69s
```

Reverted; allow-rules confirmed restored at **105**, key shape **0**. Then clean:
**`18 passed in 0.48s`** for `test_no_secrets.py`.

**Both plants were synthetic and neither was ever committed.** The real key appears nowhere in
this note, in any commit message, or in any command output — everything above was filtered
through a redacting `sed` before it was read.

---

## The suite

| When | Result |
|---|---|
| Before 022 | **190 passed, 1 failed** (020's UAT gate) |
| After 022 | **197 passed, 2 failed** |

Seven net new tests. **Neither failure is 022's code**, and neither is fixable from this side:

1. **`test_uat_has_a_file`** — 020's, unchanged. Needs `christoph/open/NNN-020-*.md` from chat.
2. **`test_handoff_state_declared`** — **new, and not caused by this task.** Four task files
   arrived carrying YAML frontmatter `status: READY` and no `**Status**` header:
   `021`, `022`, `023`, `024`. **`READY` is not one of the five states**
   (`WRITTEN | HANDED OFF | RUNNING | REVIEWED | DONE`), and the key is `**Status**`, not
   frontmatter. The test says plainly *"Christoph holds the state — if it is not known, ask
   rather than assume."* **So I did not add one.** Four files at once is protocol drift on the
   authoring side, not four accidents.

**`023-for-code-verify-writes-a-file.md` and `024-for-code-subagent-roster.md` arrived mid-task**
and are unread. `021` is also unstarted.

---

## Exit criteria

| Criterion | Result |
|---|---|
| Live key appears nowhere in the working tree | **Met.** 0 matches across all of `D:\Dev`. |
| Search scope written down | **Met.** Table above, including what was *not* searched. |
| Test fails against the synthetic fixture, then passes on the cleaned tree, in that order | **Met, twice** — once in `requirements.txt`, once on the adjacent surface. |
| Done-note states which failure mode | **Met.** Neither of the two offered; the root was outside the repo. |
| **UAT** | **None.** 022 owes no UAT — every criterion is machine-checkable and was checked. |

## Ledger

**OBS-019** (residual copies in machine-local caches, Christoph's decision), **OBS-020** (the
user-level `~/.claude` is deliberately unscanned — the stated blind spot), **OBS-021** (a
permission rule holding a pasted paragraph). All `OPEN`, review-by 2026-11-13.

## The export

Ran after the commit. `HEAD` recorded in the manifests; see `verify.ps1` section 5.
