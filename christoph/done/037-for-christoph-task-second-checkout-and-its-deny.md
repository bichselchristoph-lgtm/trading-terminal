---
task: 037
class: admin
owner: christoph
unblocks: NOTHING
depends: none
---

# 037 — the second Code instance gets its own checkout, and a deny list that binds

**Your decision, 2026-08-23: second clone, B barred from sync and export.** This is the setup. It is yours because it acts outside the repo and because it writes a permission policy — both are permanently on your side.

---

## 0. Order of operations. This part matters more than the rest.

**Do these in order. Steps 1 and 2 are cheap and must happen before step 3.**

| | Step | Who |
|---|---|---|
| **1** | **B commits its own work and stops.** | The B session |
| **2** | **A runs `063`** — the quiet-tree re-verify | The A session |
| **3** | **Create the second clone** | You |
| **4** | **Write its deny file** | You, alone |
| **5** | **Measure that the deny actually binds** | You |

**Why B commits rather than being killed:** it currently holds uncommitted changes to `verify.ps1` and it authored `handoff/inbox/062-*`. Another session's uncommitted work is never discarded — **its author commits it.** Branch or not is B's call; it just has to land in history before the tree goes quiet.

**Why `063` runs before the clone:** it needs the shared tree exactly as it is now, clean. Once B moves to its own clone, the tree that produced `061`'s green no longer exists in the same state.

---

## 1. Create the clone

```
git clone https://github.com/bichselchristoph-lgtm/trading-terminal D:\Dev\momentum-b
```

**Clone from GitHub, not from `D:\Dev\momentum`.** A local clone would set `origin` to the other working copy, and you would have two trees pointing at each other instead of two trees pointing at one remote.

**Do not copy `records/` into it.** Captured tape is gitignored and there is one copy by decision. B does not get a second.

**B works on `b/*` branches and pushes those.** It never pushes to the branch A is on. **That one is a convention, not a control — I cannot express "push only these branches" as a deny pattern, so it is weaker than everything below and you should treat it as weaker.**

---

## 2. The deny file — you write this, nobody else

`D:\Dev\momentum-b\.claude\settings.local.json`

```json
{
  "permissions": {
    "deny": [
      "Bash(*sync.ps1*)",
      "Bash(*export-handoff.ps1*)",
      "Write(//d/Dev/momentum/**)",
      "Edit(//d/Dev/momentum/**)",
      "Write(.claude/settings.local.json)",
      "Edit(.claude/settings.local.json)"
    ]
  }
}
```

**And the mirror, in A's own local file** — `D:\Dev\momentum\.claude\settings.local.json`:

```json
{
  "permissions": {
    "deny": [
      "Write(//d/Dev/momentum-b/**)",
      "Edit(//d/Dev/momentum-b/**)",
      "Write(.claude/settings.local.json)",
      "Edit(.claude/settings.local.json)"
    ]
  }
}
```

**Why the local file and not `.claude/settings.json`:** the tracked one is the same file in both clones, so a deny placed there would bar A from syncing too. The two instances need different policies, which means an untracked per-clone file.

**Why the last two lines in each:** without them, the denied party can edit its own deny list. That is the self-reference trap, and the fix is positional — the file forbids writing itself, and you are the only party who writes it.

**The cross-tree deny is the strong one.** `Write(//d/Dev/momentum/**)` makes B writing into A's tree impossible regardless of what B is told or what it believes. Everything else here is narrower.

---

## 3. Measure that it binds. Do not assume.

**`deny` binds and `ask` does not** was established by measurement, not by reading documentation. Do the same here. Three checks, in B:

1. **Ask B to run `sync.ps1`.** Must be refused.
2. **Ask B to run `export-handoff.ps1`.** Must be refused.
3. **Ask B to write any file under `D:\Dev\momentum\`.** Must be refused.

And one in A:

4. **Ask A to write any file under `D:\Dev\momentum-b\`.** Must be refused.

**If any of the four is allowed, `settings.local.json` is not being honoured** — tell me and I will rewrite this as something that is. **Do not proceed on the assumption that it worked.** A control you believe in and that is not there is worse than no control, because you stop watching.

**Also confirm the file is untracked:** `git status` in B must not list `.claude/settings.local.json`. If it does list it, it will sync into A and both policies collide — tell me.

---

## 4. Two things this does not solve, stated plainly

**B's done-notes will not reach me automatically.** `export-handoff.ps1` is what carries `handoff/done/` to Drive, and B is barred from running it. **B's notes reach me by you pasting them, or after B's branch merges and A exports.** That is a real gap, not an oversight — giving B the exporter would put two copiers on the same Drive folders, which is already producing the `sync-run-record.md` races in `061` §7 and §8.

**Nothing tests the deny file.** `tests/test_permission_policy.py` reads the tracked `.claude/settings.json`; an untracked per-clone file is invisible to the tree and therefore to every test. **So this control is carried by your memory and this document** — which is exactly the shape `061` existed to end. **It needs a follow-up task making `verify.ps1` report, per checkout, whether the local deny file is present.** I will write that once you confirm §3 passed; writing it before then would be specifying a mechanism for a control that may not bind.

---

## 5. Exit test

- Four refusals in §3, observed, not assumed.
- `.claude/settings.local.json` untracked in both clones.
- B running in `D:\Dev\momentum-b`, A in `D:\Dev\momentum`, each reporting its own repo path in `verify.ps1` output — **that line is how a done-note tells us which tree it came from, and it already exists.**

**Tell me which of the four refusals fired and which did not.** If all four fired, say so and I will write the `verify.ps1` follow-up.

Christoph Aug 23  2026, retired. one branch one code instance.