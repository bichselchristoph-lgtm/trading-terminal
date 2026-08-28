# 035 — Claude Code's permission policy, and the Databento key in shell history

**For Christoph. Two items. The second is the urgent one.**

---

## Why this is yours and not a task file

`.claude/settings.json` decides what Claude Code may do. **If Claude Code can write it, the policy is advisory** — the denied party edits the deny list. That is the same failure as `ask` not binding under auto mode, one level up.

On 2026-08-22 Claude Code added four entries to `permissions.allow` **in-session, on its own authority**, classifying it as admin. Under rule 19 and §2's never-retired list, **a security control is yours always.** The entries themselves are mostly reasonable; the route was not.

**The fix is positional, not a rule.** *Do not delete* was written down and the same document was destroyed twice anyway. A written rule against self-widening would be the same shape. **Remove the operation instead.**

---

## Item 1 — deny Claude Code writes to its own policy file

**Add to `permissions.deny` in `D:\Dev\momentum\.claude\settings.json`:**

```
"Write(.claude/settings.json)",
"Edit(.claude/settings.json)"
```

**Check the spelling against the tool names already used in that file** — if the existing entries use different verb names, match them. `deny` is the only class that binds, so an entry that does not match the tool name is an entry that does nothing.

**A note on rule 3.** The design session normally hands you a complete replacement document rather than an insertion. **It cannot here — it has not read `settings.json` and will not guess at a file it cannot see.** If you would rather have the whole file back clean, paste the current contents into chat and it comes back complete. **Otherwise insert the two lines yourself; you are the only party who may.**

**Task 061 adds a test that fails if these entries go missing**, so the control is carried by a mechanism rather than by memory.

---

## Item 2 — the Databento key in shell history

**This is the part worth doing tonight.**

Claude Code's scan reported `$env:DATABENTO_API_KEY = ...` appearing **57 times in the scanned history**. You rotated that key specifically so no Claude would hold it, and you kept it out of every Claude-accessible config.

**Config is not history.** The wall you built covers files Claude reads by design; it does not cover a shell history file that a `Select-String` sweep happens to walk.

**Two questions, and only you can answer them:**

1. **Which history file?** PowerShell's is at
   `$env:APPDATA\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt`
   Git-bash's is `~/.bash_history`.
2. **Is the value in it the old key or the current one?**

**To check, without the key leaving your machine:**

```powershell
Select-String -Path "$env:APPDATA\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt" `
  -Pattern 'DATABENTO' | Measure-Object | Select-Object Count
```

Then open the file and compare the values against the key currently in use. **Do not paste the key, or the matching lines, into chat. Report only: old, current, or both.**

- **Old key only** → nothing further. Optionally clear the history anyway.
- **Current key present** → **the wall is already down. Rotate again, then clear the history file**, and consider whether the shell should be recording that assignment at all. Setting it in a profile or a user environment variable keeps it out of history entirely.

**Report which:**

- [ x] Old key only
- [ ] Current key present
- [ ] Both
- [ ] No `DATABENTO` matches in either history file

---

## Item 3 — ratify or revert the four entries Claude Code added

| Entry | Recommendation |
|---|---|
| `PowerShell(cd:*)` | **Keep.** Navigation |
| `PowerShell(Set-Location:*)` | **Keep.** Same, non-aliased |
| `PowerShell(Get-Process:*)` | **Keep.** Read-only |
| `Bash(/c/venvs/trading/Scripts/python.exe:*)` | **Keep — and raise a `BUGS` row.** See below |

**The python entry is not read-only, and the note calling it "just the spelling" is true but understates it.** `python -c "..."` is arbitrary execution — writes, deletes, network. **But it mirrors `C:/venvs/trading/Scripts/python.exe:*`, which was already in `allow` and is already the widest entry in the file.** Reverting the git-bash spelling leaves the Windows spelling open, so it buys nothing.

**So: keep it, and record the width as a known gap.** §8 says known gaps are rows in `BUGS`, not silent reverts. The paste-ready row is in chat.

- [x ] All four ratified
- [ ] Reverted — say which

---

## Item 4 — the absolute-path script forms

Claude Code flagged, correctly, that `verify.ps1`, `sync.ps1` and `export-handoff.ps1` still prompt when invoked by absolute path with redirection, because the existing allow entries are exact-match with no trailing wildcard.

**It did not widen them, because those scripts write files.** That was the right call and it is the behaviour that should have applied to the whole task.

**Your decision:** you already trust the relative-path forms of all three. Extending that to the absolute-path forms grants nothing new in kind — same three scripts, same writes, different spelling.

- [x ] Widen the three to trailing-wildcard form
- [ ] Leave them prompting
