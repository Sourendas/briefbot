# BriefBot — ≤3 min demo shot list (no login)

Record on the machine that already has this folder. Zero spend. Do not show any `.env` or API key (this demo has none).

Public repo https://github.com/Sourendas/briefbot tools restored on GitHub as of 2026-10-03 ~21:04 IST: full `tools/briefbot_tools.py` (~19KB) and `tools/briefbot_tools.js` (~18KB) on `main` (no stubs). Local copies in this folder match. Demo still needs no `.env` or API keys.

## Setup (10s, off camera or first frame)

```bash
cd /workspace/money-ops/contests/amazon-dev
python3 cli.py serve-sim --port 8765
```

Browser: http://127.0.0.1:8765/sim/

## Shots

1. **0:00–0:20** Title card in the page header: BriefBot, Alexa+ web sim, offline, four tools. Say: messy freelance brief in, scoped proposal out, no paid model.
2. **0:20–1:10** Click the inventory sample (Zapier + Google Sheets + Slack, ASAP, budget). Hit **Run pipeline**. Show the chat summary.
3. **1:10–2:00** Point at the right panel: `parse_brief`, `draft_proposal`, `list_risks`, `ask_clarifiers`, and the proposal JSON (platforms, urgency, risks).
4. **2:00–2:30** Optional terminal cut: `python3 cli.py pipeline -f samples/inventory_brief.txt` so judges see the same tools outside the browser.
5. **2:30–2:50** One line of product feedback: the sim is a stand-in for Alexa+; tools are deterministic on purpose so the demo does not need AWS credits.

## Still not this step

- YouTube upload (needs sourendas0@gmail.com)
- Devpost submit form
