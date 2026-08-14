---
id: 015
title: Attach the terminal to QQQ — does it work for a person
status: OPEN
type: EXTERNAL
owner: christoph
blocks: [S011-sizing-risk-and-limits]
---

# 015 — Attach QQQ, and tell me what you actually need on screen

**This is the acceptance `013` was meant to be.** `013` asked you to check the context block
against your charts and could not be performed — there was no way to attach, and then no way to
see most of what attaching produced. **This one is scoped to what the program can actually do
today.**

**The numbers are deliberately not the subject.** `PDL` and `ATR14` are known wrong and `036`
fixes them; fourteen of twenty-six rows cannot be seen at all (`OBS-042`). **Checking values
today would mostly produce "cannot check", which is how `013` failed.**

**What is being tested is the program, as a person meets it.** Answer in this file, then copy it
to `christoph/done/`.

---

## Before you start

```powershell
cd D:\Dev\momentum
C:\venvs\trading\Scripts\python.exe -m live.tui.app
```

TWS running, window at 209 × 54. **`021` may still be capturing on `client 121`; this connects
on `client 7` and the two do not interfere.**

---

## 1. It starts, and HEALTH tells the truth

Look at the HEALTH panel before touching anything.

- Does it say `connected · client 7 · read-only`? **yes**
- Does anything on that panel look wrong or unclear? **yes**
**
1 What does risk open R mean? R of trades still open? If so, will there be an R closed, for closed positions?
2 what does lag 69s mean in ATTACHED panel.
3 ATTACHED Panels says QQQ attached 14:46 and right below as of 14:45 lag .... I don't understand why we have a time difference. 
4 IBKR IP:Port redundant. Remove. Already in HEALTH PANEL. 
5 ADR used is missing unit. Expected $ ...Same for room up.
6 20 sessions excl. today is too much information. Should move into a config or definitions and a command such as /config or /definitions displays these settings. If a setting changes, the terminal should say what has changed and its definition. But we can have the plumming now and build config and warning later. In the user_guide.txt of the trading terminal we can spell out that before using you must review the config and definitions. 
7 Remove ADR$, ADR used, and room up. Replace ADR% with ADR% avail. And ADR $ avg $y. (not on screen just commenting: This allows me to check if I am within my tradebook trading symbols with ADR$ lager than $x.)    
I don't have a playbook based on ADR% room up. Having it on the screen may incurrage me to brake rules. Such as taking a trade because I believe I have enough room left. 
8 Display unit on the right side of indicator without whitespace ADR$, not ADR $
9 HEALTH panel needs connected for MH:MM:SS: visually changing every second. last seen may cover this in the spec? Positive confirmation that we are still connected. If nothing changes something may have failed and disconnected silently. allows me a quick visual cross check.
10 HEALTH panels needs IBKR ping SS:MSMS last: timestamp (time to reach IBRK; refreshes every 10 seconds). Gives me indication of the viability to get information and fills quickly.
11 What happens if we are connected to 5 of 5 tickers and I want to connect to a new one? First in, first out. Lets say I connected QQQ,AMZN, AMD, META, APPL, then I connect to SPXC. QQQ will be dropped. SPXC takes last position,5. Next out would be AMZN and so on. 
**
---

## 2. Attach QQQ

Press `a`, type `QQQ`, press enter.

- How long between enter and the panel filling? **quite long, about 13seconds. Should take a second or two.**
- Did anything flicker, jump, or redraw in a way you noticed? **no**
- Is it obvious *that* it worked, without reading the values? **yes**
**requires CLS, clear screen, otherwise see ##3**
---

## 3. Attach something that does not exist

Press `a`, type `ZZZZQQ`, enter.

- What does it say? **nothing as far as I can tell. Fail silently**
- Does the terminal stay up and usable? **yes**
- **Could you tell from the screen alone what went wrong?** **no**
**
No obvious failure. Still appears to be attached to QQQs.

below the text of ATTACHED extracted from a screenshot
since 14:40 +

IBKR 127.0.0.1:7496 . as of 14:39 . lag 77s
0/5 slots used
absent - tape not opened by S010 - no tape componen ...
1.63 . 20 sessions, excl. today
11.83 . 20 sessions, excl. today
20 sessions, excl. today
20 sessions, excl. today
. 20 sessions, excl. today
. Wilder RMA, n=14, 59 true ranges
10-day SMA / ADR $
. 20-day SMA / ADR $
50-day SMA / ADR $
. bar-derived . 18,119, 366 sh . 640 min . 2 ...
18,119,366.00 . 640 min from 2026-08-13 04:00:00
0.86 . 14:39 . 20d median
- (no sector mapping)

- (no trades today)
- (no positions)
2 of 2 . end

daily limit - (no account snapshot)

+- ATTACHED
QQQ attached 14:40
from
slot
tape
ADR%
ADR $
ADR used
room up
room down 19.41
ATR14
ext 10
ext 20
ext 50
VWAP
cum vol
RVOL
RVOL_rel
+- RISK
day P&L
open R

64.05
4.25

13.14
1.39
2.57
1.65
730.84

not transmitted +

Then press `a`, `QQQ`, enter again.
**

- Does it recover cleanly? **no**
**
1 All panels are displayed twice.
2 The screen refreshes which is a good visual inicator that something happened. It was faster than the first attach but still too long for taking trades quickly. Time updated in attached.
**
---

## 4. Escape

Press `a`, then escape without typing.

- Does it close cleanly and leave the attachment alone? **yes / no —**

---

## 5. THE QUESTION THAT MATTERS MOST

**The context block computes 26 rows. The panel shows 12. You can see:*no*

```
from · slot · tape · ADR% · ADR $ · ADR used · room up · room down ·
ATR14 · ext 10 · ext 20
```
no room down. however we should not display this anyways. see 7 in ##1 above


**Hidden below the fold:*no*

```
ext 50 · VWAP · cum vol · RVOL · RVOL_rel · PDH · PDL · PMH · PML ·
ORH · ORL · 52wH · 52wL · round
```

no indication that there is as a below the fold. doesn't say N of Y displayed. The full below the list appeared after resizing the window. This happened after ##3 -> Then press `a`, `QQQ`, enter again. Not 

**Do not tell me to add a scrollbar.** Tell me what you need:

**a) Which rows do you look at before taking a trade?
** 
Price
ADR% used ADR$ (in same row)
RVOL_rel RVOL_avg Cum vol (one line)
VWAP at+\- recenable band,above,or below followed by $Current_price 
tape

>/< HOD (daily)
>/< LOD (daily)

>/< PDH
>/< PDO
>/< PDL
>/< PDC (prior day close, new requirement)

>/< PMH
>/< PML

>/< ORH 5
>/< ORH 15

>/< ATHO(all time higopenw requirement)

>/< MoMC(prior month close)
>/< MoMO(prior month open)
>/< MoMH (prior month high)
>/< MoML(prior month low)

>/< PWC (prior week ..)
>/< PWO
>/< PWH
>/< PWL

>/< 52wH

Two Rows. One row for greater > list all indicators wich meet condition in ordered by indicator time decay starting with pre market ending with montly, 52 week, ATH
one row for less than.

Considering weaken my principle of explicitly stating any state on screen because it becomes visually overhelming. For longs only indicators meeeting greater than. For shorts reversed. Once trade direction is indicated. Before show all. If hiding some display x of y. 
 
Generate two screen mocks with two different sorting mechanism one orderd by state, greater or smaller than, then list oll indicators meeting requirement in one row in logical order. Two rows total one for greater and one for smaller than. Example > PDH,PDL,ATH. 
Second mockup list of each indicator, one in each row with >/< ORH
Likely will triage some out because of the amount of information. 
**

**b) Which of the 26 do you never need on screen?** 
**
ext 10, 20, 50 (MAs)
ext 9, 21 (EMAs, new requiement for trade data collection)
ADR $
room up
room down
ATR14
**

**c) Is 12 rows enough if they were the right 12?** **yes**

**d) Would you rather the panel were taller and something else smaller?** no**—**

**This decides whether the fix is scrolling, choosing, or re-laying-out the whole tile** — three
very different amounts of work, and only you can pick.
**Choosing in config — cannot be abitrary, triage down to make fit; risk this may not be viable once having done some trading and we need to introduce scrolling. however the principle of having to much info is less is important and I am leaning towards holding to it.**

---

## 6. Anything else

**What surprised you? What did you reach for that was not there?
**
On attach, fill UI when data arrives, don't wait until all data is available. Show what you have. This will give me visual confirmation that attaching is in progress and progresssing. it may also give me important information on a trade even if incomplete. ATTACHED, and TAPE having priority over other panels.

Pipeline
1 Rename regimen to health. regime lives outside of terminal.
2 rank should be part of watchlist, ordered by rank ascending. ATTACHED should show grade as well. this covers attaching a ticker not in watchlist. 
3 Select, size, stage, submit needs review. Most likely combine in a single window called TRADE. May include manage as well. If collapsed into on TRADE panel, we build in slices not everthing at once. Stage first, followed by manage, then submit.  

RISK panel:
Discovered a critical gap in my requirements.
1 Risk needs to be tracked in Rs (R:R Risk:Reward), and number of daily and monthly trades allowed.  
2 Monetary values are not on the screen with the exception of Daily limit. P&L as monetary $ ammount for data collection. Seeing dollars made and lost encourages overtrading and/or revenge trading. 
3 Daily and monthly limit is fixed in config file. It does not change with the NLV. At least not in the initial versions. Later, we may layer on a rules engine which will manage how risk changes over time. Risk should not change daily. It should change after N days won, and get reduced when Y days lost in sequence vs in a month or week. Again, keep this as a requirement for later version. Again, initially we use the defaults in the config we already decided on. 
4 Risk measures are calculated in R. Daily,and monthly R, hitting limits disconnects the terminal closes with Appropriate message. On reconnect it will automatically connect to my paper trading account.I should continue to be able to practice trading and the use of the terminal. 
Just not with my live account.   
6 The safety layer of max loss in % and value remains in the config, and will lead to terminal closing / live account lockout if for some reason the P&L for day or month are overrun. Paper trading allowed. Appropriate message and/or disconnect, or console closin
7 When reaching max trades, trerminal will allow to manage any other open trades, other functionality will disconnect. Future version not core. 

Risk panel parameters: 
1 Account LIVE vs paper *lastfouraccountdigits (live in capital intentiually)
2 R today +/-R; Examples: R today -1R (lost money);Rs today +4R  (made money)
3 Trades left count_lost_trades_today/max_loosing_trades_today. Examples: Trades 0/2 (no loosers yet). Trades 1/2 (one remaining) Trades 2/2 (Terminal freezes and exits with error. Max winning trades set in config to 2. Max total trades per day is a config value initially set to 3. 
4 Trades monthly count_lost_trades_month/max_montly_trades. Behaves same as day counter if maxed. 

Trades panel (future versions)
1 Needs to measure and display time it took to get order filled and slippage in $.rounded to two cents. 

SIZING panel
1 remove 1R; replace with R size and replace with qualifier of position sizing measured against 1, full position,  0.25 (high risk day etc). Future version, not core. 
2 Move above R size to RISK panel. 
3 Don't think we need a sizing panel at all. The trade of an particular symbol will decide how many shares to buy. This will fall into TRADES panel. 

HISTORY
not a panel. click a /history lists all history of attached symbols and attach time timestamp of todays session. Survives terminal restart. Ordered by descending by time attached.  Not core, later version. 

HEALTH
1. confirming current behavior as expected. IF TWS is not up display as is today. Requires me to start TWS kill and reconnect terminal. Remark for later conideration async poll for connection and attach once availble.

PANEL SLOT lengs
All parameter values in a panel need to aligh neetly. Parameter names may be shortened. Therefore we need to define a max lenght each row can have and then trim the parameter name starting with the last letter.

sources   IBKR 127.0.0.1:7496
            — (connection refused - nothing is listening)
  last seen — (nothing seen)
  frames/ticks  — (no ticks received)
  4 of 4 · end
  
  
DISPLAY ISSUESE
started terminal again after bringing up TWS, now all panels displayed twice again. Each disconnect, switching of symbols need a CLS.  
 
**
---

## Return

**Answers in this file, then copy to `christoph/done/`.** No Claude writes to `christoph/`.

**Section 5 is the deliverable.** Everything above it is a smoke test; section 5 is the design
input, and nothing else in the project can produce it.