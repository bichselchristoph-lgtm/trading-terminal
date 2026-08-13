---
id: 022
title: Remove the Databento key from the tree, and fix the test that missed it twice
status: READY
blocks: []
type: housekeeping
owner: claude-code
---

# 022 — Secrets hygiene: remove the key, and repair the test that did not catch it

**The urgent part is done. Christoph rotated the Databento key on 2026-08-10**, so the
exposed credential is dead and the copies in git history are inert. **Nothing here is a
race.**

**What remains is the part that matters more.** This is the **second** time a live Databento
key has been found in cleartext in this repo, and **`test_no_secrets.py` passed on both
occasions.** A secrets test that goes green while a live key sits in a committed file is
worse than no test — **it manufactures confidence.** It answers *"no secrets in the files I
scan"*, which is a different question from *"no secrets"*, and that substitution is the
failure this project keeps having in other forms.

---

## Standing constraints

- **Do not rewrite git history.** The key is rotated, so the historical copies are worthless.
  Rewriting is disruptive, breaks every clone, and **cannot recall what has already been
  fetched.** Rotation was the fix; this is cleanup.
- **Do not print the key** — not in output, not in a commit message, not in the done-note.
  Refer to it by location.
- **Do not commit a replacement value.** The environment is the only place it lives.

---

## Part 1 — Remove the live key from the working tree

Two known locations. **Search for others rather than assuming these are all.**

1. **`D:\Dev\momentum\requirements.txt`** — committed, which is why this occurrence is the
   worse of the two. **Note the likely form**: a key embedded in an
   `--extra-index-url https://user:key@…` line rather than a bare assignment. That shape is
   invisible to a matcher looking for `KEY=`, and it is probably why the test missed it.
2. **`D:\Dev\.claude\settings.local.json`** — three allow-rules. Every other rule in that
   file already reads the key from the user environment, so **these three are the anomaly,
   not the pattern.**

**Replace both with an environment read.** Then **grep the whole active tree** — including
dotfiles, `.claude/`, every dependency manifest, notebooks, and `docs/` — for the key's
distinctive prefix. **Report what you searched, not only what you found**; a search whose
scope is unstated cannot be trusted by the next reader.

---

## Part 2 — Repair `test_no_secrets.py`

**Establish the failure before fixing it.** There are two possibilities and they need
different fixes:

- **It never scanned `requirements.txt`** ⇒ the scope is wrong.
- **It scanned and the pattern did not match** ⇒ the matcher is wrong.

**Say which it was.** Guessing here would repeat the defect at one remove.

Then:

1. **Widen the scope** to `.claude/`, all dependency manifests (`requirements*.txt`,
   `pyproject.toml`, `Pipfile`, `setup.cfg`, lock files), and dotfiles. **The current scope
   demonstrably excluded at least one committed file.**
2. **Match on credential shape, not on assignment syntax.** Databento's key prefix, plus the
   URL-embedded-credential form `://[^/@\\s]+:[^/@\\s]+@`. **A matcher keyed to `NAME=value`
   is exactly what an index URL walks past.**
3. **Prove it fails before you accept that it passes.** Add a fixture containing a
   **synthetic** key of the right shape in an index-URL line, in a manifest, and confirm the
   test goes red. **A test never seen failing is a test whose green means nothing** — and
   that is precisely the situation this task exists to end.

---

## Done when

- The live key appears nowhere in the working tree, and the search scope is written down.
- `test_no_secrets.py` **fails against the synthetic fixture** and **passes on the cleaned
  tree** — in that order, both demonstrated.
- The done-note states **which of the two failure modes** it was.

---

## Deliverable

`handoff/done/022-for-code-secrets-hygiene.md`. It must contain:

1. **Which failure mode** the old test had, with the evidence.
2. **Every location searched** and every location found — scope stated, not implied.
3. **The fixture test going red**, quoted, before the cleaned tree goes green.
4. **What you could not do**, and why. Empty is suspicious.

**A note that says "removed the key and the test passes" is a failed handoff**, because it
is exactly what could have been written on both previous occasions.
