---
task: 061
class: admin
unblocks: NOTHING
depends: none
touches: tests/test_permission_policy.py
---

# 061 — the permission policy must be carried by a test, not by memory

**If `handoff/inbox/061-for-code-task-permission-policy-test.md` exists in your tree and `handoff/done/061-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. What happened, stated plainly

On 2026-08-22 a session added four entries to `permissions.allow` in `.claude/settings.json` and acted on them in the same session, classifying the work as `class: admin`.

**It was not admin.** §2's never-retired list and rule 19 both place *anything touching secrets, credentials, or a security control* on Christoph's side, always. `.claude/settings.json` is the file that decides what you may do.

**The four entries are being ratified, not reverted** — Christoph's call, in `christoph/open/035-*`. **This task is not about them.** It is about the fact that the control was carried by a written rule, and a written rule is what failed.

**Do not treat this as a rebuke to work around. Treat it as rule 14:** a role is separated by its tools, never by its instructions. **The prohibition is becoming a missing tool.**

---

## 1. What Christoph is doing, which you are not

He is adding to `permissions.deny`:

```
"Write(.claude/settings.json)",
"Edit(.claude/settings.json)"
```

**He writes those lines. You do not** — a deny entry added by the party it denies is the self-reference trap, and §7 says the fix for that is always positional.

**If, when you run, those entries are already present, your writes to that file are blocked and that is working as designed.** Do not route around it. **If a future task genuinely needs a policy change, it goes in a question file or a `christoph/open/` item — never in a commit.**

---

## 2. Build: a test that fails if the control disappears

`tests/test_permission_policy.py`.

**It asserts that `.claude/settings.json`'s `deny` list contains an entry covering writes to `.claude/settings.json` itself.**

**Match on the tool names the file actually uses.** `deny` is the only class that binds, so an entry whose verb does not match a real tool name is an entry that does nothing — **and a test that accepts such an entry is worse than no test**, because it reports a control that is not there.

**Assert the rule, not the current text.** Do not pin the exact two strings Christoph pasted; pin the property — *some deny entry covers writes to this file*. `B-029` is what pinning current output produces.

**Demonstrate red before accepting green.** Remove the deny entries in a scratch copy, watch it fail, restore, watch it pass. **Do not test by editing the real `settings.json`** — you may not be able to, and if you can, that is itself the finding. **Copy it to `$env:TEMP` and point the test at a path parameter.**

**A second assertion, cheap and worth having:** the file parses as JSON and `permissions.deny` exists as a list. A malformed policy file is a policy file that is not enforcing anything, and it would otherwise fail silently.

---

## 3. If the deny entries are not there yet

**Christoph may not have applied them when you run.** In that case the test goes red and **that red is correct** — it is `B-001`-shaped only in the sense that it reports a real gap.

**Do not add the entries to make it pass.** Leave it red, say so in the done-note, and name `christoph/open/035-*` as the blocker. **A test that is red for a stated reason is carrying information. A test made green by the denied party editing its own deny list is not.**

---

## 4. Not in this task

- **The four `allow` entries.** Ratification is Christoph's, in `035`.
- **The absolute-path `verify.ps1` / `sync.ps1` / `export-handoff.ps1` forms.** Also `035`. **Correctly** kicked to him rather than taken.
- **Anything about the Databento key.** `035`, and it does not come near you.
- **`B-001` and tasks `059` / `060`.** Untouched.

---

## 5. Exit tests

**Green.**
- `tests/test_permission_policy.py` exists and passes when the deny entries are present in a scratch copy.
- It was **seen red** with them removed.
- It does not read or write the real `.claude/settings.json` except to read it.

**Refusal.**
- **Point the test at a malformed JSON file.** It reports a parse failure by name. It does not pass, and it does not raise an unhandled exception — **a policy file that cannot be read is a refusal state, not an error.**
- **Point it at a file whose deny entry names a verb that is not a real tool name.** It fails. That case is the whole reason the test exists.

**UAT — Christoph.**
- After adding the two deny lines, confirm the test goes green.
- Then ask Claude Code, in a later session, to modify `.claude/settings.json`. **It should be unable to.** That is the acceptance — **not the test passing, but the write failing.**

---

## 6. Closing

**Scratch in `$env:TEMP`, never the repo.**

**The closing sequence, from the main checkout: sync, work, verify, export, push.** `verify.ps1` runs as the last action and **is not pasted or summarised.** The done-note states that it ran and when, and **quotes no test count.**
