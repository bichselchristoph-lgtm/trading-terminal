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
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

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
        roots.append((f"{label or 'root'}/.claude", ancestor / ".claude"))
    return roots


def existing_roots() -> list[tuple[str, Path]]:
    """The subset actually present here, deduped by `resolve()` so a junction
    pointing into the tree cannot produce a doubled report."""
    out, seen = [], set()
    for label, path in candidate_roots():
        if not path.is_dir():
            continue
        key = path.resolve()
        if key in seen:
            continue
        seen.add(key)
        out.append((label, path))
    return out


def candidate_files(root: Path) -> list[Path]:
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
        if path.is_dir() and path.resolve() in present:
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
        if path.name == Path(__file__).name:
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
        if path.name == Path(__file__).name or in_repo(path):
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
    hits = [rel(p) for p, t in ALL_TEXT
            if p.name != Path(__file__).name and pattern.search(t)]
    assert not hits, (
        f"{label} present in {hits}. Even without the key this identifies the account "
        "in batch-download URLs, so rotating the key does not retire it."
    )


def test_claude_config_is_not_tracked() -> None:
    """`.claude/` must never be committed -- M001 §6. The predecessor's held a key."""
    import subprocess
    tracked = subprocess.run(["git", "ls-files", ".claude"], cwd=REPO,
                             capture_output=True, text=True, check=True).stdout.strip()
    assert not tracked, f".claude/ is tracked: {tracked.splitlines()}. It must never be committed."


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
    for banned in ("st_size", "MAX_BYTES", "islice", "read_text(encoding=\"utf-8\")[:"):
        assert banned not in scan, (
            f"a size cap or sample ({banned!r}) appeared in the file walk. A cap "
            "silently stops scanning a large TRACKED file and looks identical to "
            "a clean run.")


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
