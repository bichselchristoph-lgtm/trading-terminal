---
id: 023
title: Does the third Drive pair land, and is christoph/done still locked
status: OPEN
type: EXTERNAL
owner: christoph
closes: 043's UAT row
---

**Status** OPEN

# c023 — the last file you have to copy by hand

**`043` adds a third Drive pair so UAT files reach `christoph/open/` the same way task files reach
`handoff/inbox/`.** After this you stop copying them.

**Two minutes. The second half matters more than the first.**

---

## 1 — does it land

Drop any small `.md` into the Drive folder `momentum-inbox-christoph`. Wait for the sync folder to
catch up, then run the inbound copier.

| | |
|---|---|
| Did it report the file **by name**? | yes / no |
| Did it land in `christoph/open/`? | yes / no |
| Run it again — does it say `0 new · up to date`? | yes / no |

**The second run matters.** `0 new · up to date` and `0 new · source unreachable` were the same
sentence until recently, and the same defect on the inbound leg is what `043` Part 2 fixes.

---

## 2 — is `christoph/done/` still locked

**This is the half worth doing carefully.** The rule changed for `open/` only.

| | |
|---|---|
| Is there a Drive folder that writes to `christoph/done/`? | **should be no** |
| Does `config/sync.yaml` name `christoph/done/` as any destination? | **should be no** |
| Did anything appear in `christoph/done/` that you did not put there? | **should be no** |

**Any yes is a defect and a stop.** `christoph/done/` is your answers, and nothing writes into it by
any channel.

---

## 3 — the deliberate conflict

Put a file with the **same name but different content** into `momentum-inbox-christoph` as one
already in `christoph/open/`. Run the sync.

| | |
|---|---|
| Did it **refuse** rather than overwrite? | yes / no |
| Did it say which file and stop? | yes / no |

**An overwrite here would silently replace a UAT you may already be part-way through.** A refusal is
the correct behaviour.

---

## Afterwards

Delete your test files from both the Drive folder and `christoph/open/`.

Save into `christoph/done/023-third-drive-pair.md` — the filled-in file. Then tell chat.

**If step 3 overwrote instead of refusing, say so first and loudly.** That one is not a detail.
