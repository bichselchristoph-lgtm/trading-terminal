"""The subagent roster's restrictions are enforced, not requested. 024.

**A roster whose restrictions are not asserted is a roster of suggestions.**
Someone will add `Edit` to the reviewer *"just for this one fix"*, and the fix
will look obvious in the moment — that is the whole reason this file exists, and
it was seen red against exactly that edit before being accepted.

**The point is the restriction, not the role name.** A reviewer *told* not to
edit will eventually edit. **A reviewer with no `Edit` tool cannot.** Same
construction as everywhere else in this tree: `Advisory` has no field a consumer
can act on, `size_for()` cannot accept a rule, the symbol process does not import
the staging module. `SPEC.md` §4.2a — **the defect is made unrepresentable rather
than forbidden in prose**, because prose is what this project has repeatedly
learned does not hold.

----

**What this file can and cannot enforce, stated up front because the difference
is the finding.**

`tools:` is a whitelist, so a missing tool is a real capability the agent does
not have. **But `Bash` is write-capable**, and the reviewer has it — it cannot
run the suite otherwise, and a reviewer that cannot reproduce a defect is
guessing. So *"the reviewer cannot modify the tree"* is **true of `Write` and
`Edit` and false of `Bash`**, and this file asserts the first and requires the
second to be **written down as a known hole** rather than left implied by a tool
list that looks airtight.

That is `024`'s own rule applied to `024`: *a prohibition an agent could violate
is a request*, and where it cannot be expressed as a missing tool it must say
plainly that it is a convention and therefore weaker.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
ROSTER = REPO / ".claude" / "agents"

#: 024: **four agents, and resist adding more.** Every agent is a context
#: boundary and a place for information to be lost in translation. A roster that
#: grows past what the work needs makes handoffs, not throughput.
EXPECTED = {"architect", "implementer", "reviewer", "test-author"}

#: Tools that create or change a file **through the tool layer**. `Bash` is
#: deliberately NOT here — see `test_bash_is_write_capable_and_the_roster_says_so`,
#: which exists so that this exclusion is a stated position rather than an
#: oversight somebody has to notice.
WRITE_TOOLS = {"Write", "Edit", "NotebookEdit", "MultiEdit"}

#: The agents whose value depends on being unable to write.
READ_ONLY = {"architect", "reviewer"}


def definitions() -> dict[str, tuple[dict, str]]:
    """Parse every `.claude/agents/*.md` into (frontmatter, body).

    Deliberately a small hand-rolled parser rather than a YAML dependency: the
    frontmatter is four scalar keys, and a parse failure here must name the file
    rather than raise from inside a library.
    """
    out = {}
    for path in sorted(ROSTER.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", text, re.S)
        assert m, (
            f"{path.name} has no YAML frontmatter block. Claude Code reads the "
            "agent's tool list from that block; without it the agent inherits "
            "EVERY tool, silently.")
        fm = {}
        for line in m.group(1).splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
        out[path.stem] = (fm, m.group(2))
    return out


def tools_of(fm: dict) -> list[str]:
    return [t.strip() for t in fm.get("tools", "").split(",") if t.strip()]


@pytest.fixture(scope="module")
def roster() -> dict[str, tuple[dict, str]]:
    assert ROSTER.is_dir(), (
        f"{ROSTER} does not exist. The roster is 024 and it must be COMMITTED -- "
        "an uncommitted restriction is absent from every clone.")
    return definitions()


# ---- the roster exists and is the size it was designed to be ----------------


def test_the_four_agents_exist(roster) -> None:
    assert set(roster) == EXPECTED, (
        f"roster is {sorted(roster)}, expected {sorted(EXPECTED)}.\n"
        "024: four agents, and resist adding more -- every agent is a context "
        "boundary\nand a place for information to be lost in translation. Adding "
        "one is a decision,\nso it changes this test.")


# ---- the restriction itself --------------------------------------------------


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_every_agent_declares_its_tools_explicitly(name, roster) -> None:
    """**Do not omit the field and inherit everything.**

    An inherited toolset is the same as no restriction, and it will be inherited
    *silently* — the agent works, does everything asked, and the roster's entire
    mechanism is absent with nothing to show it.
    """
    fm, _body = roster[name]
    assert "tools" in fm and fm["tools"].strip(), (
        f"{name}.md does not declare `tools:`. An agent with no tools field "
        "INHERITS EVERY TOOL,\nwhich is the same as no restriction -- and it "
        "inherits them silently, so nothing\nlooks wrong. This is the one failure "
        "the roster cannot survive.")


@pytest.mark.parametrize("name", sorted(READ_ONLY))
def test_the_read_only_agents_have_no_write_tool(name, roster) -> None:
    """**The assertion 024 exists for.** Seen red with `Edit` added to
    `reviewer` before this file was accepted."""
    tools = tools_of(roster[name][0])
    offenders = sorted(set(tools) & WRITE_TOOLS)
    assert not offenders, (
        f"{name} declares {offenders}, and its whole value is that it cannot.\n\n"
        f"A reviewer that fixes stops reporting, and its fixes are unreviewed by "
        f"construction.\nAn architect that can write will write, and then the plan "
        f"is post-hoc narration of\ncode that already exists.\n\n"
        f"If a fix is needed, it goes to the implementer. Do not add the tool.")


def test_the_implementer_is_the_only_agent_that_can_write(roster) -> None:
    """One writer makes *"who changed this"* answerable without a transcript."""
    writers = sorted(n for n, (fm, _) in roster.items()
                     if set(tools_of(fm)) & {"Write", "Edit"} and n != "test-author")
    assert writers == ["implementer"], (
        f"agents with write access: {writers}. Only `implementer` may have it "
        "(and `test-author`,\nwhich is excluded here and asserted separately "
        "below, because its write access is\nreal and only its SCOPE is a "
        "convention).")


def test_the_architect_cannot_run_commands_at_all(roster) -> None:
    """024 says *no mutating `Bash`* for the architect. There is no such thing as
    a non-mutating `Bash` grant, so it gets no `Bash` — the only form of that
    restriction a tool list can actually express."""
    assert "Bash" not in tools_of(roster["architect"][0]), (
        "architect declares Bash. 024 says 'no mutating Bash', and a tool list "
        "cannot grant\nBash conditionally -- so the restriction is either no Bash "
        "or no restriction.")


# ---- the honesty requirement: prohibitions must match the tools --------------


def test_bash_is_write_capable_and_the_roster_says_so(roster) -> None:
    """**A prohibition an agent could violate is a request** — `016` part 7,
    `020` Refusal A.

    The reviewer holds `Bash`, so *"it cannot modify the tree"* is false as
    stated: `echo > file` is one keystroke away. That trade was made knowingly —
    a reviewer that cannot run the suite is guessing — but it **must be written
    down in the definition itself**, not left for a reader to infer from a tool
    list that looks airtight.
    """
    fm, body = roster["reviewer"]
    assert "Bash" in tools_of(fm), (
        "the reviewer no longer has Bash. If that was deliberate, this test and "
        "the\n'hole in your own tool list' section of reviewer.md both change -- "
        "the hole would\nbe closed and should stop being advertised.")
    low = body.lower()
    assert "convention" in low, (
        "reviewer.md does not use the word 'convention'. Every prohibition it "
        "cannot enforce\nmust be labelled as one, or it sits beside the enforced "
        "ones borrowing their authority.")
    assert "bash" in low and ("hole" in low or "write" in low), (
        "reviewer.md does not state that its Bash grant is a residual write "
        "path.\nThe tool list reads as airtight and is not.")


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_every_unenforceable_prohibition_is_labelled(name, roster) -> None:
    """Each definition's *may not* list must be satisfied by its tool list — and
    where it cannot be, it must **say so in words**.

    Checked structurally: any definition that claims a restriction it cannot
    enforce has to contain the word `convention`. `architect` is the one agent
    whose restrictions are fully expressible, so it is exempt and that exemption
    is itself the assertion — if the architect ever gains `Bash` or `Write`, this
    stops being true and `test_the_architect_cannot_run_commands_at_all` fires.
    """
    fm, body = roster[name]
    if name == "architect":
        assert not (set(tools_of(fm)) & (WRITE_TOOLS | {"Bash"})), (
            "architect gained a mutating tool, so its restrictions are no longer "
            "fully enforced\nby its tool list and it now needs the 'convention' "
            "labelling every other agent has.")
        return
    assert "convention" in body.lower(), (
        f"{name}.md states restrictions its tool list cannot enforce and never "
        f"uses the word\n'convention'. 024: where a prohibition cannot be "
        f"expressed as a missing tool, say\nplainly that it is a convention and "
        f"therefore weaker -- rather than letting it sit\nnext to the enforced "
        f"ones and borrow their authority.")


# ---- the roster is committed, or it is nothing -------------------------------


def test_the_roster_is_tracked(roster) -> None:
    """**An uncommitted restriction is absent from every clone**, and nothing
    goes red to say so. This is why `.gitignore` has a narrow exception at all —
    see `tests/test_claude_dir_stays_ignored.py`."""
    import subprocess
    tracked = set(subprocess.run(
        ["git", "ls-files", "--", ".claude/agents"], cwd=REPO,
        capture_output=True, text=True, check=True).stdout.split())
    missing = sorted(f".claude/agents/{n}.md" for n in roster
                     if f".claude/agents/{n}.md" not in tracked)
    assert not missing, (
        f"these agent definitions are not tracked: {missing}\n"
        ".claude/ is ignored except for this exact path. If git refuses to add "
        "them, the\nnegation in .gitignore is wrong -- not the roster.")


def test_the_check_can_actually_fail(roster) -> None:
    """A test that cannot fail proves nothing. Confirm the write-tool detection
    would catch the edit somebody will actually make."""
    assert "Edit" in WRITE_TOOLS
    pretend = dict(roster["reviewer"][0], tools="Read, Grep, Glob, Bash, Edit")
    assert set(tools_of(pretend)) & WRITE_TOOLS == {"Edit"}
