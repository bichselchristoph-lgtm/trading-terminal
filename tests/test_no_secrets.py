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
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

#: Directories that hold no authored text. `.claude/` is NOT among them --
#: excluding it is what let the last key sit unreported.
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}

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


def candidate_files() -> list[Path]:
    out = []
    for p in REPO.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if MANIFEST_NAMES.match(p.name) or p.suffix.lower() in TEXT_SUFFIXES:
            out.append(p)
    return out


ALL_TEXT = [
    (p, p.read_text(encoding="utf-8", errors="ignore"))
    for p in candidate_files()
]


def rel(p: Path) -> str:
    return p.relative_to(REPO).as_posix()


@pytest.mark.parametrize("label,pattern", CREDENTIAL_PATTERNS, ids=[l for l, _ in CREDENTIAL_PATTERNS])
def test_no_credentials_in_the_tree(label: str, pattern: re.Pattern) -> None:
    hits = []
    for path, text in ALL_TEXT:
        if path.name == Path(__file__).name:
            continue  # this file contains the patterns themselves
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


def test_the_key_pattern_matches_a_real_key_shape() -> None:
    """A pattern that matches nothing would make every test above pass."""
    _, pattern = CREDENTIAL_PATTERNS[0]
    assert pattern.search('setx DATABENTO_API_KEY "db-' + "A" * 24 + '"')
    assert pattern.search("--extra-index-url https://u:db-" + "B" * 24 + "@example.com/simple")
    assert not pattern.search("db-short")


def test_the_index_url_pattern_survives_its_own_documentation() -> None:
    """The narrowing above must still catch a real key while ignoring prose that
    merely describes the shape. If a future edit loosens it back, the first of
    these fails; if it tightens too far, the second does."""
    _, pattern = CREDENTIAL_PATTERNS[1]
    assert pattern.search("--extra-index-url https://user:db-" + "C" * 24 + "@example.com/simple")
    assert not pattern.search("a key inside an `--extra-index-url https://user:key@...` line")
