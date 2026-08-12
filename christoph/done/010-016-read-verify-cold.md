# 010 · UAT — read `verify.ps1` cold

**Task** 016
**Status** RUNNING · **Owner** Christoph only · **Blocks** 016 reaching DONE
**Written** 2026-08-12 by the design session

---

## 1. Why this exists

**You carry machine-to-machine traffic you cannot check.** A done-note says 179 hashes verified
and a suite passed; you can see that the note arrived and that all of it arrived, and nothing
more.

Today that limit bit. Three documents gave three different test counts for one tree — `015` said
104 tests, `012` said 104, `016` was written believing 126, and it was actually 128. **None of
them was lying. There was simply no way to check.**

`verify.ps1` is the fix: four facts, printed raw, **with no opinion attached.** It does not say
"all good". It says what is true and stops.

---

## 2. What to do

```powershell
cd D:\Dev\momentum
.\verify.ps1
```

Read the output **without asking anyone what it means.**

---

## 3. The one question

> **Could I tell, from this output alone, whether a done-note's claims were true?**

That is the whole criterion. Not whether it is pretty, and not whether the numbers are good.

The four facts it prints:

| # | fact | what a note might claim about it |
|---|---|---|
| 1 | the pytest summary line | "the suite passed" |
| 2 | `git status --short` | "committed" |
| 3 | `HEAD` | "at commit X" |
| 4 | evidence re-hash | "179 rows verified" |

**Fact 4 is deliberately not the test suite's own code.** If the test that checks the hashes had
a bug, it and the suite would agree with each other and both be wrong. This walks the manifest
independently.

---

## 4. Record your answer here

**A · Could you tell whether the four facts matched a note's claims, without asking?**

- [ ] yes
- [x ] no — and what was unclear: `___| 2 | `git status --short` | "committed" |
| 3 | `HEAD` | "at commit X" |
| 4 | evidence re-hash | "179 rows verified" |No idea what to do with this information other than that the tests passed. which is valuable_____________________________`_____________________________`

**B · Did anything in the output need explaining before it meant anything to you?**
Name the exact line, because a fact you cannot read is not a fact you have:

`________________________________________________`

**C · Is anything missing that you would want before agreeing a task is done?**

`________________________________________________`

**D · The suite now runs in about 2.5 seconds, down from 128.**
Did `verify.ps1` finish fast enough that you would actually run it every time?

- [x ] yes
- [ ] no

**E · Anything unexpected.** Free text:

`________________________________________________`

---

Signed `_Christoph_______________` Date/time `_________August 12, 2026 2:35pm_______`

*Once signed, copy this file to `christoph/done/`, verify it is byte-identical, then remove it
from `christoph/open/`.*

---

## 5. Two things this UAT does not ask

**Whether the numbers are good.** They are what they are. `verify.ps1`'s value is that it has no
view about them — the reading belongs to the design session, and a script that graded itself
would be the thing being fixed.

**Whether `verify.ps1` is correct.** It reports on the repo; nothing reports on it. **If it ever
printed a comfortable falsehood, nothing here would catch it.** Stated so it is known rather
than assumed away.
