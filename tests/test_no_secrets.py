"""No credential is in the tree, and the scan looks where the last one hid.

M001 §0b.2: the predecessor's version of this test passed only because it never
looked in the right places. A live Databento key sat in a working-tree
`requirements.txt` and in `.claude/settings.local.json`, and the scan covered
neither. Two changes, both deliberate:

1. **Scan `.claude/`, every `requirements*.txt`, and every dependency-manifest
   format.** A dependency manifest is exactly where people paste setup commands,
   and `--extra-index-url https://user:key@host/simple` is a credential in a
   place no assignment-syntax scanner looks.
2. **Match on the key's SHAPE (`db-` prefix), not on assignment syntax.** The old
   pattern wanted `KEY = "..."`. A key inside a URL, a `setx` line, or a YAML
   value all evade that and all leak the same secret.

022 added the third change, and it is the one that actually mattered:

3. **Scan the `.claude/` of every ANCESTOR of the repo, not only the repo.** Both
   changes above were already in place on 2026-08-13 and the scan still passed
   while a live Databento key sat in `<parent>/.claude/settings.local.json` — a
   SIBLING of this repo, one directory up, in a directory that is not a git repo
   at all. **The scope was wrong in a way no amount of widening INSIDE the repo
   could fix**, because `REPO.rglob` cannot leave `REPO`. Neither of the two
   failure modes anyone predicted; see `handoff/done/022-*.md`.

   **This makes the suite stop being a pure property of the tree**, deliberately.
   `git checkout` can no longer make it green. The way to green on an adjacent
   hit is to rotate the key and remove it from a file no repo owns.

024 added the fourth, and it is the first time this test has had to cover a
`.claude/` path that is **tracked**:

4. **`.claude/agents/` is now committed** — the subagent roster, four `.md`
   files, at a path Claude Code forces. Every previous rule here was written
   about a `.claude/` that could never be in the repository, so *"the fix is do
   not commit this"* was never the right remedy for a `.claude/` hit and now
   sometimes is.

   **The walk already reached it** — `.claude` is deliberately absent from
   `SKIP_DIRS` and `.md` is in `TEXT_SUFFIXES` — so nothing had to be widened.
   **What was missing is teeth**, and this file has been caught by that exact
   gap before: `test_dot_claude_is_not_skipped` exists because the docstring's
   claim to scan `.claude/` was **vacuous**, this repo having had no `.claude/`
   directory at all. It is no longer vacuous, and
   `test_the_walk_reaches_a_planted_key_in_the_roster` is what makes that
   checkable rather than asserted.

   **`test_claude_config_is_not_tracked` is narrowed, not deleted** — see its
   docstring. It went red the moment the roster was committed, which is the guard
   working, and the wrong response to that red was to remove it.
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

#: The RESOLVED path of this file, not its bare name. Keyed on `path.name` the
#: self-skip matched *any* file called `test_no_secrets.py` in *any* scanned
#: root -- including a copy sitting in an adjacent `.claude` or a drop folder,
#: which would then be exempt from the scan for having the right filename.
SELF = Path(__file__).resolve()

#: Directories that hold no authored text. `.claude/` is NOT among them --
#: excluding it is what let the last key sit unreported.
#:
#: `records` and `records_truncated` hold CAPTURED MARKET DATA, never authored
#: text. **The predecessor's version skipped both; that was dropped when this
#: test was rewritten for this tree under M001, and the defect was invisible
#: until something large landed there.** Once `012`'s QQQ capture filled
#: `records/tape/` with 1.8 GB of depth JSONL, the credential scan read every
#: byte of it on every run and the suite went from 1.4 s to ~128 s.
#:
#: **This narrows WHERE, never WHAT.** `records/` is gitignored and never
#: committed, so scanning it for committed secrets answers a question nobody
#: asked. The suffix list is untouched, there is no size cap and no sampling --
#: a size cap would silently stop scanning a large file that IS tracked, which
#: is the failure this test exists to catch.
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules",
             "records", "records_truncated"}

#: Extensions worth reading as text.
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".yaml", ".yml", ".json", ".ini", ".cfg", ".toml",
    ".ps1", ".sh", ".bat", ".env", ".jsonl", ".local", "",
}

#: Dependency manifests are scanned regardless of suffix or location.
MANIFEST_NAMES = re.compile(
    r"^(requirements.*\.txt|Pipfile|Pipfile\.lock|pyproject\.toml|setup\.cfg|setup\.py|"
    r"poetry\.lock|constraints.*\.txt|environment\.ya?ml|pip\.conf|\.npmrc)$", re.I)

CREDENTIAL_PATTERNS = [
    # Shape, not syntax. Catches a bare key, a `setx` line, and a key embedded in
    # an --extra-index-url. The old pattern required an assignment and missed all three.
    ("databento api key", re.compile(r"\bdb-[A-Za-z0-9]{20,}")),
    # The secret segment must be at least 12 characters. This is a DELIBERATE
    # narrowing with a stated blind spot, not a widened exclusion list.
    #
    # Without it the pattern fires on prose that describes the shape --
    # `--extra-index-url https://user:key@...` in a comment, and the same phrase
    # inside carried evidence that must never be edited. Excluding those by path
    # would blind the scan to a real key sitting in a handoff file, which is
    # worse than the false positive.
    #
    # BLIND SPOT, stated rather than discovered: a real credential shorter than
    # 12 characters in an index URL is not caught here. Databento keys are 24+,
    # and the `db-` shape pattern above catches those anywhere, including inside
    # a URL, regardless of length.
    ("credential in index url",
     re.compile(r"(?:--(?:extra-)?index-url)\s+\S*://[^\s/:]+:[^\s/@]{12,}@")),
    ("aws access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

IDENTIFIER_PATTERNS = [
    # Not a secret, but it names the account in batch-download URLs, so rotating
    # the key does not retire it.
    ("databento user id", re.compile(r"\bDATABENTO_USER\b\s*[=:\"' ]+\s*\S")),
]


#: Adjacent credential surfaces, by leaf name. **Two of these are FILES, not
#: directories**, and that distinction cost a real gap: the first version of
#: `existing_roots` gated on `is_dir()`, so `.claude.json` -- a real Claude Code
#: config location that can hold credentials -- was outside the scan while the
#: test was named "adjacent surfaces". The scope was one directory name.
ADJACENT_LEAVES = (".claude", ".claude.json", ".mcp.json")


def candidate_roots() -> list[tuple[str, Path]]:
    """Every root this scan is SUPPOSED to cover, whether present or not.

    The rule: `REPO` itself, plus `<ancestor>/.claude` for every ancestor of
    `REPO`. **Derived from `REPO.parents` — no path is written down here.** On
    `D:\\Dev\\momentum` that yields `D:\\Dev\\.claude` and `D:\\.claude`; on
    `/home/u/src/momentum` it yields `/home/u/src/.claude` and `/.claude`. Two
    `exists()` calls that normally find nothing.

    **Not an exclusion list and it cannot grow into one**, which is the same
    derivation idiom `tests/test_export_scope_is_derived.py` uses for the same
    reason. `test_the_root_list_is_derived_and_not_enumerated` holds it there.

    THE ONE NARROWING, STATED. The user's home `.claude` is excluded: it is
    per-user and shared with every project rather than adjacent to this repo, it
    holds session transcripts of arbitrary pasted text so the shape patterns
    would fire on prose, and it is gigabytes — the exact runtime failure
    `records/` already caused once. **Blind spot: a key in the user-level
    `.claude` is not caught by this suite.** Recorded as OBS-020.
    """
    home = Path.home().resolve()
    roots = [("repo", REPO)]
    for ancestor in REPO.parents:
        if ancestor.resolve() == home:
            continue
        label = ancestor.name or ancestor.anchor.replace("\\", "").replace("/", "")
        for leaf in ADJACENT_LEAVES:
            roots.append((f"{label or 'root'}/{leaf}", ancestor / leaf))
    return roots


def existing_roots() -> list[tuple[str, Path]]:
    """The subset actually present here.

    Two filters, and the second is the one that was wrong first time:

    1. **Deduped by `resolve()`** so the same surface reached by two names is
       read once.
    2. **Dropped if it resolves INSIDE the repo.** The original only compared
       roots to each other, which does not catch a junction — if
       `<parent>/.claude` points at `<REPO>/.claude`, its `resolve()` is not
       equal to any other root, so both survived and every hit was reported
       twice: once in-tree and once to the adjacent test, **whose remedy text
       says "this file is in no repository"** for a file that is committed.
    """
    repo = REPO.resolve()
    out, seen = [], set()
    for label, path in candidate_roots():
        if not path.exists():
            continue
        key = path.resolve()
        if key in seen:
            continue
        if key != repo and repo in key.parents:
            continue  # already covered by the repo walk; see docstring
        seen.add(key)
        out.append((label, path))
    return out


def candidate_files(root: Path) -> list[Path]:
    # A root may be a FILE (`.claude.json`), not only a directory. Returned
    # unconditionally in that case: it was named as a credential surface, so
    # filtering it by suffix here would silently drop the thing we came for.
    if root.is_file():
        return [root]
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if MANIFEST_NAMES.match(p.name) or p.suffix.lower() in TEXT_SUFFIXES:
            out.append(p)
    return out


def read_texts(roots: list[tuple[str, Path]]) -> list[tuple[Path, str]]:
    out = []
    for _label, root in roots:
        for p in candidate_files(root):
            out.append((p, p.read_text(encoding="utf-8", errors="ignore")))
    return out


ALL_TEXT = read_texts(existing_roots())


def in_repo(p: Path) -> bool:
    return REPO in p.parents


def rel(p: Path) -> str:
    """Repo-relative where possible, absolute otherwise.

    **It must not raise on an out-of-tree path.** Before 022 every scanned file
    was under `REPO` by construction; now some are deliberately not, and a
    `ValueError` here would crash the scan rather than report the hit."""
    try:
        return p.relative_to(REPO).as_posix()
    except ValueError:
        return p.as_posix()


def coverage_report() -> list[str]:
    """One line per CANDIDATE root — present or absent — for the pytest header.

    **A skip would render as a bare `s`**, and invisibility is the thing this
    file exists to prevent. `pytest.ini` already refuses `-q` on the grounds
    that the report header carries load-bearing caveats, so this is the repo's
    designated channel for exactly this. **A blind spot that prints on every
    run is a stated blind spot.**"""
    present = {p.resolve() for _l, p in existing_roots()}
    lines = ["credential scan roots:"]
    for label, path in candidate_roots():
        if path.exists() and path.resolve() in present:
            n = len(candidate_files(path))
            lines.append(f"  PRESENT  {label:<24} {path}  ({n} files read)")
        else:
            lines.append(f"  ABSENT   {label:<24} {path}")
    # ASCII only. The header is printed by a Windows console whose encoding
    # mangles an em dash into a replacement character, and a caveat that renders
    # as a mojibake box is a caveat people stop reading.
    lines.append("  NOT COVERED: the user-level ~/.claude - see OBS-020")
    return lines


@pytest.mark.parametrize("label,pattern", CREDENTIAL_PATTERNS, ids=[l for l, _ in CREDENTIAL_PATTERNS])
def test_no_credentials_in_the_tree(label: str, pattern: re.Pattern) -> None:
    hits = []
    for path, text in ALL_TEXT:
        if path.resolve() == SELF:
            continue  # this file contains the patterns themselves
        if not in_repo(path):
            continue  # adjacent surfaces have their own test and their own remedy
        for m in pattern.finditer(text):
            line = text[: m.start()].count("\n") + 1
            hits.append(f"{rel(path)}:{line}  [{label}]")
    assert not hits, (
        f"possible {label} in the tree:\n  " + "\n  ".join(hits) +
        "\n\nRead credentials from the environment instead:\n"
        "  key = os.environ['DATABENTO_API_KEY']\n"
        "and never pass one on a command line, where it lands in process listings "
        "and shell history."
    )


@pytest.mark.parametrize("label,pattern", CREDENTIAL_PATTERNS, ids=[l for l, _ in CREDENTIAL_PATTERNS])
def test_no_credentials_on_adjacent_surfaces(label: str, pattern: re.Pattern) -> None:
    """A separate test with a separate remedy, deliberately.

    **The fix for a hit here is not "do not commit this".** These files are in no
    repository — `git checkout` cannot make this green and neither can
    `.gitignore`. The fix is to rotate the credential and remove it from a file
    nobody's version control owns. A reader must be able to tell from the test id
    alone whether red means *the tree* or *the machine*.
    """
    hits = []
    for path, text in ALL_TEXT:
        if path.resolve() == SELF or in_repo(path):
            continue
        for m in pattern.finditer(text):
            line = text[: m.start()].count("\n") + 1
            hits.append(f"{rel(path)}:{line}  [{label}]")
    assert not hits, (
        f"possible {label} on a credential surface ADJACENT to this repo:\n  "
        + "\n  ".join(hits) +
        "\n\nThis file is in no repository, so no git operation fixes it and this "
        "test\ncannot be made green by editing the tree. Rotate the credential, "
        "then remove\nit from the file. Every other rule in a Claude settings file "
        "reads the key from\nthe user environment -- an inline one is the anomaly, "
        "not the pattern."
    )


@pytest.mark.parametrize("label,pattern", IDENTIFIER_PATTERNS, ids=[l for l, _ in IDENTIFIER_PATTERNS])
def test_no_account_identifiers(label: str, pattern: re.Pattern) -> None:
    # Marked in-tree vs adjacent, because the two need different remedies and
    # this test reports both. The credential patterns split into two separate
    # test functions; a single identifier pattern carries the distinction in the
    # hit string instead, rather than adding a fourth near-identical test.
    hits = [f"{rel(p)}{'' if in_repo(p) else '  (ADJACENT - in no repository)'}"
            for p, t in ALL_TEXT
            if p.resolve() != SELF and pattern.search(t)]
    assert not hits, (
        f"{label} present in {hits}. Even without the key this identifies the account "
        "in batch-download URLs, so rotating the key does not retire it."
    )


def test_no_claude_config_file_is_tracked() -> None:
    """**No `.json` under `.claude/` is committed, at any depth.** M001 §6.

    **This test used to assert that `.claude/` was empty of tracked files, and
    that assertion was correct until 024.** The subagent roster is now committed
    at `.claude/agents/*.md` — a path Claude Code forces — so the old form went
    red on four markdown files that hold no credential and never could.

    **It is narrowed rather than deleted, and the distinction is the whole
    point.** What M001 §6 is actually protecting is the *config* surface: the
    predecessor's `.claude/settings.local.json` held a live Databento key, and
    JSON under `.claude/` is where a key sits. A markdown agent definition is a
    different kind of file, and it is scanned for keys like everything else by
    the tests above.

    **This is deliberately NOT the same assertion as
    `tests/test_claude_dir_stays_ignored.py::test_only_the_roster_is_tracked_under_claude`**,
    which owns the scope rule — *only `agents/*.md` may be tracked*. This one
    owns the credential rule — *no config file is tracked* — and would still fire
    if the scope rule were relaxed to admit some new non-JSON config format that
    somebody then wrote a key into. Two rules, two files, stated so neither is
    read as a duplicate of the other and quietly removed.
    """
    import subprocess
    tracked = subprocess.run(["git", "ls-files", "--", ".claude"], cwd=REPO,
                             capture_output=True, text=True, check=True).stdout.split()
    configs = [p for p in tracked if p.lower().endswith((".json", ".yaml", ".yml", ".env"))]
    assert not configs, (
        f"config files are tracked under .claude/: {configs}\n\n"
        "That is the shape that held a live Databento key in the predecessor tree. "
        ".gitignore\ndoes not untrack a file already in the index -- use `git rm "
        "--cached`, and if it ever\nheld a credential, rotate it: it is in the "
        "history and on the remote.")


def test_the_walk_reaches_a_planted_key_in_the_roster(tmp_path: Path) -> None:
    """**Teeth for the newly-tracked path.** 024.

    `.claude/agents/` is the first `.claude/` location whose contents get
    committed and pushed, so a key pasted into an agent definition would leave
    the machine. The walk reaches it today because `.claude` is not in
    `SKIP_DIRS` and `.md` is in `TEXT_SUFFIXES` — **but nothing asserted that**,
    and this file's own history is the argument for why that matters:
    `test_dot_claude_is_not_skipped` had to be written because the module
    docstring's claim to cover `.claude/` was true-sounding and untested.

    Mirrors `test_the_walk_actually_reads_a_claude_settings_file`. The key is
    synthetic and assembled from fragments so this file does not contain the
    shape it searches for.
    """
    agents = tmp_path / ".claude" / "agents"
    agents.mkdir(parents=True)
    planted = agents / "reviewer.md"
    planted.write_text(
        "---\nname: reviewer\ntools: Read\n---\nRun it with DATABENTO_API_KEY="
        + "db-" + "Y" * 24 + "\n", encoding="utf-8")

    reached = candidate_files(tmp_path)
    assert planted in reached, (
        f"the walk did not reach {planted}. `.md` is in TEXT_SUFFIXES and no "
        "SKIP_DIRS entry covers `.claude`, so if this fails the roster is a "
        "committed, pushed directory that the credential scan does not read.")

    _, pattern = CREDENTIAL_PATTERNS[0]
    assert pattern.search(planted.read_text(encoding="utf-8"))


def test_the_real_roster_is_actually_scanned() -> None:
    """The non-vacuous half. The test above proves the walk *can* reach an agent
    definition in a temp directory; this proves it *did* reach the ones in this
    repo, which is the claim that matters.

    **Conditional on the roster existing**, because on a checkout made before 024
    it does not — and asserting coverage of an absent directory would be the
    vacuous-claim failure again, inverted.
    """
    roster = REPO / ".claude" / "agents"
    if not roster.is_dir():
        pytest.skip("no .claude/agents/ in this checkout -- the roster is 024's")
    scanned = {p.resolve() for p, _ in ALL_TEXT}
    definitions = {p.resolve() for p in roster.glob("*.md")}
    assert definitions, f"{roster} exists but holds no .md definitions"
    missed = sorted(str(p) for p in definitions - scanned)
    assert not missed, (
        f"these committed agent definitions were NOT read by the credential "
        f"scan: {missed}\nThey are tracked and pushed, so a key in one leaves the "
        "machine.")


def test_the_scan_actually_reaches_dependency_manifests() -> None:
    """The old test passed because it never looked here. Prove this one does --
    otherwise a green run means nothing."""
    scanned = {rel(p) for p, _ in ALL_TEXT}
    assert "requirements.txt" in scanned, (
        "requirements.txt was not scanned. That is the exact blind spot this test was "
        "rewritten to close -- a green run without it is meaningless."
    )


def test_the_records_skip_narrows_where_and_not_what() -> None:
    """016 part 2 -- the skip must not become a hiding place.

    `records/` is excluded because it holds captured market data and is
    gitignored, so a committed secret cannot be there. **The suffix list must
    stay untouched and no size cap may appear**: a cap would silently stop
    scanning a large file that IS tracked, which is the failure mode this test
    exists to catch, and it would look identical to a clean run.
    """
    assert ".jsonl" in TEXT_SUFFIXES, (
        "the .jsonl suffix was dropped. The fix for the runtime was to narrow "
        "WHERE the scan looks, not WHAT it reads -- a tracked .jsonl anywhere "
        "else in the tree must still be scanned.")
    # Checked against the SCANNING FUNCTIONS, not against this file. An earlier
    # version searched the whole module and failed on its own list of banned
    # words -- the same self-reference trap as the `6 of 9` check and the legacy
    # path check. The rule is positional: look only where a cap could actually
    # be applied.
    #
    # 022 WIDENED THE INSPECTED SURFACE, which strengthens this rather than
    # weakening it: the walk is now four functions, and a size cap added in
    # `read_texts` would otherwise evade the guard entirely. **The banned-token
    # list is byte-identical** -- narrowing WHAT is still forbidden; only where
    # the guard looks has widened.
    scan = "".join(inspect.getsource(f) for f in
                   (candidate_roots, existing_roots, candidate_files, read_texts, rel))
    for banned in ("st_size", "MAX_BYTES", "islice"):
        assert banned not in scan, (
            f"a size cap or sample ({banned!r}) appeared in the file walk. A cap "
            "silently stops scanning a large TRACKED file and looks identical to "
            "a clean run.")

    # THE FOURTH TOKEN WAS DEAD. It read `read_text(encoding="utf-8")[:` and
    # could never match: `read_texts` calls `read_text(encoding="utf-8",
    # errors="ignore")`, so the literal never appears -- while the cap somebody
    # would actually write, `read_text(..., errors="ignore")[:65536]`, matched
    # none of the four and landed unguarded in the exact function the widening
    # was introduced to protect. A pattern, not a literal, because the argument
    # list is what varies.
    sliced = re.search(r"read_text\([^)]*\)\s*\[", scan)
    assert not sliced, (
        f"a slice was applied to a read_text call in the file walk: "
        f"{sliced.group(0)!r}. That is a size cap in the form that evades a "
        "literal token list -- it silently stops scanning a large TRACKED file "
        "and looks identical to a clean run.")


def test_the_key_pattern_matches_a_real_key_shape() -> None:
    """A pattern that matches nothing would make every test above pass."""
    _, pattern = CREDENTIAL_PATTERNS[0]
    assert pattern.search('setx DATABENTO_API_KEY "db-' + "A" * 24 + '"')
    assert pattern.search("--extra-index-url https://u:db-" + "B" * 24 + "@example.com/simple")
    assert not pattern.search("db-short")


def test_the_root_list_is_derived_and_not_enumerated() -> None:
    """The root list must come from `REPO.parents`, never from a written path.

    A hard-coded `D:\\Dev\\.claude` would work on exactly one machine and would
    be the same class of defect as the bug it fixes: a scan whose scope is a
    list somebody has to remember to extend."""
    # CODE ONLY, docstring and comments stripped via ast. The first version of
    # this test read the raw source and failed on its own documentation -- the
    # docstring of `candidate_roots` names `D:\\Dev\\.claude` as a worked
    # example, which is exactly the kind of explanation this project wants
    # written down. **A guard that forbids naming a path in prose would push the
    # reasoning out of the file to keep itself green**, which is a worse trade
    # than the guard is worth.
    import ast
    import textwrap

    fn = ast.parse(textwrap.dedent(inspect.getsource(candidate_roots))).body[0]
    if (fn.body and isinstance(fn.body[0], ast.Expr)
            and isinstance(getattr(fn.body[0], "value", None), ast.Constant)
            and isinstance(fn.body[0].value.value, str)):
        fn.body = fn.body[1:]
    code = ast.unparse(fn)

    assert "REPO.parents" in code, (
        "the root list is no longer derived from REPO.parents. If it has become "
        "an enumerated list of paths, it works on one machine and silently "
        "covers nothing anywhere else.")
    for literal in ("D:/", "D:\\", "chbic", "/Dev/", "momentum"):
        assert literal not in code, (
            f"a machine-specific literal {literal!r} appeared in the root "
            "derivation CODE. Derive the roots; do not list them.")


def test_the_parent_directory_claude_is_a_candidate_root() -> None:
    """**This is the test that carries the 022 guarantee**, and it fails on a
    clean clone on any machine if the ancestor walk is deleted — it asserts what
    the scan is SUPPOSED to cover, not what happens to exist here."""
    labels = [label for label, _ in candidate_roots()]
    paths = [p for _, p in candidate_roots()]
    assert ("repo", REPO) == (labels[0], paths[0])

    # CONDITIONED, because the derivation genuinely cannot deliver this when the
    # repo is a DIRECT CHILD of the user home: there `REPO.parent` IS home, and
    # home is the declared blind spot. Asserting it unconditionally would fail on
    # a `~/momentum` layout for reasons having nothing to do with a key -- and
    # would assert a guarantee the code only provides when the repo sits two or
    # more levels below home. **The blind spot is asserted instead of the
    # coverage**, so neither branch is silent.
    if REPO.parent.resolve() == Path.home().resolve():
        assert REPO.parent / ".claude" not in paths, (
            "the repo is a direct child of the user home, so its only adjacent "
            "surface is ~/.claude -- the documented blind spot (OBS-020). It must "
            "not appear as a root here, and this layout is NOT covered.")
    else:
        assert REPO.parent / ".claude" in paths, (
            f"{REPO.parent / '.claude'} is not a candidate root. A live key sat there "
            "on 2026-08-13 while this suite was green, because rglob cannot leave REPO.")

    assert Path.home() / ".claude" not in paths, (
        "the user-level ~/.claude became a scan root. It is gigabytes of session "
        "transcripts holding arbitrary pasted text -- the shape patterns fire on "
        "prose there, and a scanner people learn to ignore is worse than none. "
        "Its exclusion is OBS-020, not an oversight.")


def test_the_walk_actually_reads_a_claude_settings_file(tmp_path: Path) -> None:
    """End-to-end teeth: a planted key in a `.claude/settings.local.json` must be
    both REACHED by the walk and MATCHED by the pattern.

    The two existing pattern tests prove the regex fires on a string. **Neither
    proves the walk ever hands it that string** — and reaching the file was the
    entire defect. The key below is synthetic and assembled from fragments so
    this file does not contain the shape it searches for."""
    cfg = tmp_path / ".claude"
    cfg.mkdir()
    planted = cfg / "settings.local.json"
    planted.write_text(
        '{"permissions": {"allow": ["Bash(DATABENTO_API_KEY=' + "db-" + "Z" * 24
        + ' python x.py)"]}}', encoding="utf-8")

    reached = candidate_files(tmp_path)
    assert planted in reached, (
        f"the walk did not reach {planted}. .json is in TEXT_SUFFIXES and no "
        "SKIP_DIRS entry covers .claude, so if this fails the walk itself is broken.")

    _, pattern = CREDENTIAL_PATTERNS[0]
    assert pattern.search(planted.read_text(encoding="utf-8"))


def test_every_root_is_derived_from_an_ancestor() -> None:
    """The BEHAVIOURAL derivation check, and the reason there are two.

    `test_the_root_list_is_derived_and_not_enumerated` reads the source, and a
    source check is evadable: `Path("D:") / "Dev" / ".claude"` contains no path
    separator in any single literal and slips past every banned token while
    `REPO.parents` still appears elsewhere in the function. **This one cannot be
    evaded, because it checks what the function RETURNS**: every root is either
    `REPO` itself or a named leaf sitting directly in an ancestor of `REPO`.
    """
    ancestors = set(REPO.parents)
    for label, path in candidate_roots():
        if path == REPO:
            continue
        assert path.parent in ancestors, (
            f"root {label} -> {path} is not adjacent to any ancestor of {REPO}. "
            "Roots are derived from REPO.parents; a root from anywhere else is "
            "an enumerated path and works on exactly one machine.")
        assert path.name in ADJACENT_LEAVES, (
            f"root {label} -> {path} has a leaf name outside ADJACENT_LEAVES.")


def test_the_adjacent_branch_is_not_silently_empty() -> None:
    """**The teeth the adjacent scan was missing**, and its absence was the same
    defect one layer out.

    The in-tree side has `test_the_scan_actually_reaches_dependency_manifests`,
    which fails if `requirements.txt` was never read. The adjacent side had no
    equivalent: delete `<parent>/.claude` and all tests still passed while only a
    header line changed. *Green because it never looked* is exactly what this
    file exists to end, so it must not be reachable for the branch that was
    added to end it.

    The assertion is conditional on a root existing, because on a machine with no
    adjacent surface an empty branch is the truth. **What it forbids is the
    combination: a root that exists, and nothing read from it.**
    """
    adjacent_roots = [(l, p) for l, p in existing_roots() if p.resolve() != REPO.resolve()]
    routed = [p for p, _t in ALL_TEXT if not in_repo(p)]

    if not adjacent_roots:
        assert not routed, (
            f"no adjacent root exists, yet {len(routed)} out-of-repo files were "
            "routed to the adjacent test. The routing and the root list disagree.")
        pytest.skip("no adjacent credential surface on this machine "
                    "-- the report header states this on every run")

    assert routed, (
        f"adjacent roots exist ({[l for l, _ in adjacent_roots]}) but ZERO files "
        "reached the adjacent test. It is passing vacuously: a key in any of them "
        "would not be reported. Check existing_roots(), read_texts() and in_repo()."
    )


def test_dot_claude_is_not_skipped() -> None:
    """The module docstring claims `.claude/` is in scope. Before 022 that claim
    was **vacuous** — this repo has no `.claude/` directory at all, so nothing
    tested it and it would have stayed true-sounding if someone added the skip."""
    assert ".claude" not in SKIP_DIRS


def test_the_index_url_pattern_survives_its_own_documentation() -> None:
    """The narrowing above must still catch a real key while ignoring prose that
    merely describes the shape. If a future edit loosens it back, the first of
    these fails; if it tightens too far, the second does."""
    _, pattern = CREDENTIAL_PATTERNS[1]
    assert pattern.search("--extra-index-url https://user:db-" + "C" * 24 + "@example.com/simple")
    assert not pattern.search("a key inside an `--extra-index-url https://user:key@...` line")
