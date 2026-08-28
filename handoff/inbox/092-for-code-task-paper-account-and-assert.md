# 092 — `--paper` selects an account, and the terminal asserts it

```
class:    admin
unblocks: S039
depends:  none
touches:  config/, the launch path
```

## Read this first

**If `handoff/inbox/092-for-code-task-paper-account-and-assert.md` exists in your tree and `handoff/done/092-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

## Why

Christoph has a paper account and has ruled that **Read-Only API comes off on paper and stays on for live**. Everything in the manage slice — S039 — transmits, and none of it is reachable until the terminal can be pointed at the paper account with something stronger than a habit.

RISK §8 already says `--paper` is a launch flag with no runtime switch, *"so no order can reach an account other than the one on screen when the terminal started."* **That sentence describes an intention, not a mechanism.** Today nothing reads the account number back from the broker and compares it to anything. This task builds the comparison.

**Rule 17: an instruction names a condition the terminal can check about itself.** `--paper` is a flag someone typed. The connected account number is a fact the terminal can read. This task makes the second one govern.

## What to build

### 1 — Two account keys, and neither defaults

Add to the config domain that owns broker connection:

```yaml
account_live:   null      # set by Christoph, never by a task
account_paper:  null      # set by Christoph, never by a task
```

**Both are null in the tracked file and both refuse when unset.** Christoph supplies the values himself.

**Determine whether the file holding these values is tracked by git, and report what you found.** If it is tracked, the values must move to a gitignored file with the tracked config carrying the key names only, and the loader reading both. **An account number in a repo that pushes to GitHub is a leak, and it is the kind that is invisible until it is not.** Do not guess whether it is tracked — check, and say which.

### 2 — The assert, at startup, before anything can send

On connect, read the account number from the broker. Compare it to the configured value for the mode the terminal was launched in.

| Condition | Behaviour |
|---|---|
| `--paper` and broker account == `account_paper` | Proceed |
| no flag and broker account == `account_live` | Proceed |
| **They differ** | **Refuse to start.** Name both numbers, name which mode was requested |
| **The relevant key is unset** | **Refuse to start.** Name the key. Nothing defaults |
| **The account number cannot be read** | **Refuse to start.** *Cannot read the account* is not *the account matched* — absence is not zero |

**This is a startup refusal and not a runtime display state.** A runtime state would need a panel design that does not exist yet, and a terminal that starts against the wrong account and then says so on a row has already been wrong for however long it took to look.

**It is positional, not procedural.** The check sits in the connect path, so no code path reaches an order without passing it. A check that any caller can skip is a check that some caller will.

### 3 — Measure what paper actually does, rather than trusting the claim

IBKR states that paper behaves as live. **Fills there are simulated, and that is exactly the surface S039's safety argument rests on.** Measure it.

**This part requires TWS running on the paper account, which is Christoph's to start.** If TWS is not reachable, **do part 1 and 2, report part 3 as not run, and stop.** Do not simulate it.

Place a resting LMT far from the market — far enough that it cannot fill — then:

1. **Amend its quantity on the same `orderId`.** Record whether the amend is accepted, and read the `openOrder` echo back field by field.
2. **Amend it to a quantity larger than anything held.** Record whether paper refuses. **This is the one that matters**: if paper accepts it, S039's refused-amend state cannot be reached through the broker and has to be forced in the suite.
3. **Place one order with `outsideRth` set, outside RTH.** Record whether it is accepted and what status it carries. This determines whether the RTH stop-posting limitation is real for our purposes or worked around by a flag.
4. **Cancel everything you placed.** Read the account back and confirm nothing rests.

**Record all four as observations with their raw responses.** Not conclusions — what was sent, what came back.

### 4 — Scratch

`$env:TEMP`, never the repo.

## Exit tests

**Green.**
- The assert passes when the broker account matches the configured one for the launched mode.
- Both keys unset ⇒ refuses, naming the key.

**Refusal — not optional.**
- Broker account differs from configured ⇒ **refuses to start, naming both numbers and the requested mode.** Write this one first and see it red.
- Account unreadable ⇒ refuses, and the message is distinct from the mismatch message. **Two conditions, two renders.**
- **No code path reaches an order without passing the assert**, asserted positionally rather than by calling it and checking.

**UAT (Christoph).** Launch with `--paper` against the paper account and confirm it starts. Launch with `--paper` against the live account and confirm it refuses and names both numbers.

## What is not in this task

**No panel changes. No manage keys. No stop amend in `tws_order`.** Those are S039 and they are blocked on B-149 as well as on this.

**Do not turn Read-Only API off anywhere, and do not write an account number into any file.** Both are Christoph's, by rule 19.

## Closing sequence

Sync, work, verify, export, push. From the main checkout. `CLAUDE.md` carries it.
