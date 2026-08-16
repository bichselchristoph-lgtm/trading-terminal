# ALLOCATIONS -- one line per task number, append-only, never rewritten

**053 Part 6a.** A record of which numbers have been handed out, so the next one is
READ rather than inferred.

**Not a counter.** A counter is a cached count and can be wrong; **a log can only be
incomplete, and incompleteness shows as a gap.** Reading the last line is an observation
about a record of events, not a claim about a total.

**Append only. Never rewrite a line, never re-sort, never close a gap by renumbering.**
A gap is information: it says a number was skipped or a file was never committed, and
both are worth knowing. Filling it in destroys the evidence and gains nothing.

**Be honest about the limit.** This makes allocation cheap. **It would not have
prevented the 049/050/052/053 reissues**, because the design session was not allocating
-- it believed it was replacing a document, which is a different act with a different
failure mode. See `053` Part 6b.

**Dates are the file timestamp on the machine that seeded this**, not an authored
record of when the number was handed out. They are an observation about the disk. Rows
appended from here on carry the date the task file arrived.

---

| # | date | title | first seen in |
|---|---|---|---|
| `001` | 2026-08-11 | rvol vs trailing | `handoff/done/` |
| `002` | 2026-08-11 | layer2 side split | `handoff/done/` |
| `003` | 2026-08-11 | layer0 frozen live split | `handoff/done/` |
| `004` | 2026-08-11 | watchlist ingestion spec | `handoff/done/` |
| `004a` | 2026-08-11 | ingestion two folder split | `handoff/done/` |
| `005` | 2026-08-11 | regime context | `handoff/inbox/` |
| `006` | 2026-08-11 | ranked watchlist panel | `handoff/inbox/` |
| `007` | 2026-08-11 | watchlist ingestion amendments | `handoff/inbox/` |
| `008a` | 2026-08-11 | ibkr data verification | `handoff/inbox/` |
| `008b` | 2026-08-11 | keepuptodate | `handoff/inbox/` |
| `012` | 2026-08-11 | live qqq tape capture | `handoff/inbox/` |
| `012a` | 2026-08-11 | preopen correction | `handoff/inbox/` |
| `013` | 2026-08-11 | adopt handoff protocol | `handoff/inbox/` |
| `013a` | 2026-08-11 | handoff tree inventory | `handoff/inbox/` |
| `013b` | 2026-08-11 | state reconciliation | `handoff/inbox/` |
| `013c` | 2026-08-11 | resolution d protocol and trees | `handoff/inbox/` |
| `013d` | 2026-08-12 | acceptance is a copy | `handoff/inbox/` |
| `014` | 2026-08-11 | commit staged work | `handoff/inbox/` |
| `015` | 2026-08-12 | uat must exist as a file | `handoff/inbox/` |
| `016` | 2026-08-12 | verification harness and observations ledger | `handoff/inbox/` |
| `017` | 2026-08-12 | active tree gets a remote | `handoff/inbox/` |
| `018` | 2026-08-12 | depth ordering and uat findings | `handoff/inbox/` |
| `019` | 2026-08-12 | qqq tape capture 2026 08 12 | `handoff/inbox/` |
| `020` | 2026-08-13 | drive export of handoff and christoph done | `handoff/inbox/` |
| `021` | 2026-08-13 | keepuptodate at scale | `handoff/inbox/` |
| `022` | 2026-08-13 | secrets hygiene | `handoff/inbox/` |
| `023` | 2026-08-13 | verify writes a file | `handoff/inbox/` |
| `024` | 2026-08-13 | subagent roster | `handoff/inbox/` |
| `025` | 2026-08-13 | regime snapshot sync | `handoff/inbox/` |
| `026` | 2026-08-13 | inbox sync from drive | `handoff/inbox/` |
| `027` | 2026-08-13 | observations ledger catchup | `handoff/inbox/` |
| `028` | 2026-08-13 | prompt sync and two red tests | `handoff/inbox/` |
| `029` | 2026-08-13 | the app has no entry point | `handoff/inbox/` |
| `030` | 2026-08-13 | regime prompt v1.8 full text | `handoff/inbox/` |
| `031` | 2026-08-13 | two sessions one tree | `handoff/inbox/` |
| `032` | 2026-08-13 | attach is unreachable from the tui | `handoff/inbox/` |
| `033` | 2026-08-13 | the admin tax has a test | `handoff/inbox/` |
| `034` | 2026-08-13 | wire the broker into main | `handoff/inbox/` |
| `035` | 2026-08-14 | pdl and atr14 | `handoff/inbox/` |
| `035a` | 2026-08-13 | adr is rth atr is eth | `handoff/inbox/` |
| `036` | 2026-08-13 | every indicator declares its session | `handoff/inbox/` |
| `037` | 2026-08-14 | drive export stopped | `handoff/inbox/` |
| `038` | 2026-08-14 | sessions levels units windows | `handoff/inbox/` |
| `039` | 2026-08-15 | risk and trade classification | `handoff/inbox/` |
| `040` | 2026-08-15 | readonly stop and accounting probe | `handoff/inbox/` |
| `041` | 2026-08-15 | thirteen levels are rth | `handoff/inbox/` |
| `042` | 2026-08-15 | four deltas | `handoff/inbox/` |
| `043` | 2026-08-15 | third pair and two instruments | `handoff/inbox/` |
| `044` | 2026-08-15 | colour links and boundaries | `handoff/inbox/` |
| `045` | 2026-08-15 | workflow engine | `handoff/inbox/` |
| `046` | 2026-08-15 | permission policy | `handoff/inbox/` |
| `048` | 2026-08-15 | the ask audit | `handoff/inbox/` |
| `049` | 2026-08-15 | validate the owned corpus | `handoff/inbox/` |
| `050` | 2026-08-15 | the tape window | `handoff/inbox/` |
| `051` | 2026-08-15 | the basis audit | `handoff/inbox/` |
| `052` | 2026-08-16 | product spec pointer | `handoff/inbox/` |
| `053` | 2026-08-16 | ledger ruling and verify export | `handoff/inbox/` |

---

## Seeded 2026-08-16 under `053` Part 6a

Sources: `handoff/inbox/`, `handoff/done/`, `handoff/accepted/`, and `git log` over
`handoff/`. **57 numbers recorded, range 001-053.**

### Numbers that appear more than once

**None.** Every number names one task. Thirteen numbers carry two FILENAMES -- `004`,
`018`, `020`, `037`, `038`, `039`, `041`, `042`, `043`, `044`, `045`, `046`, `052` --
but that is the naming convention, not a collision: a done-note drops the
`for-code-task-` prefix its task file carries. **Checked rather than assumed**, because
a filename difference is exactly what a real duplicate would also look like.

### Numbers that do not appear at all

**`009`, `010`, `011`, `047`.** Recorded, not closed.

`047` sits inside the current working range and is the one worth a look: `046` and
`048` both exist, so a number was skipped or a file was written and never committed.
`009`-`011` fall in the early `H`/`M`/`S`-prefixed era when several numbering schemes
were in use at once, and are far likelier to be scheme artifacts than lost work.

**Neither is resolved here.** A gap is reported, never filled -- filling it would
manufacture a record of an allocation nobody made.
