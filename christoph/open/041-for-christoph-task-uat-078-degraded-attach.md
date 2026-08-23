---
id: c041
title: UAT for 078 — does the screen tell you the attach degraded
type: task
class: product
uat_for: 078
depends: 078
---

# c041 — UAT for 078

**Live, during market hours. Ten minutes. Do not run it before 078 lands.**

## What you are checking

078 does not make the attach faster. **You are checking one thing: when the
fast path fails, does the screen say so.** Before 078, roughly half of AMZN
attaches took over two minutes and the panel gave no sign anything had gone
wrong — it just took longer.

## Steps

1. TWS live, regular hours.
2. Attach **AMZN**. Time it roughly — a watch is fine, this is not a
   measurement task.
3. **Repeat until you get a slow one.** Task 075 saw three in six. If the first
   three are all fast, stop and record that — it is worth knowing.
4. On the slow attach, read the panel while it is filling and again when it
   settles.

## The questions

**A. On the slow attach, did the screen tell you the fast path had failed?**
Yes or no, and copy the exact wording it used.

**B. Could you tell that wording apart from an ordinary partial attach** — some
rows missing because a request came back empty? If the two look the same, that
is a fail even if the wording is present.

**C. On a fast attach, did any degraded wording appear?** It should not. A
warning that shows on the good case has stopped carrying information.

**D. Anything on screen you did not expect** — a new token, a colour, a row
that was not there before. 078 was told to reuse the existing vocabulary and
invent nothing. **If it invented something, that is a finding, not a nicety.**

## What is NOT being checked

**Speed.** The slow attach will still be slow. If that is the thing that
bothers you, it is the right reaction and it is S038's job, not this one's.

Write your answers into this file's copy and retire it the usual way.
