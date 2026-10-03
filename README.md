# BriefBot (Alexa+ track) — Amazon Developer Hackathon

**Offline MVP** that turns a messy freelance/job brief into a scoped proposal using MCP-style tools:

| Tool | Purpose |
| --- | --- |
| `parse_brief` | Extract platforms, integrations, urgency, constraints |
| `draft_proposal` | Deterministic proposal JSON (schema `schema/proposal.schema.json`) |
| `list_risks` | Risk register with severity / impact / mitigation |
| `ask_clarifiers` | Clarifying questions to lock scope |

**Track:** Alexa+ (no device). Uses a **web-simulated Alexa+ chat** plus an optional **stdlib MCP JSON-RPC stub**. Rule/template engine first — **no paid LLM, no AWS credits, $0 to run**.

Entrant: **Souren Das** · Devpost account email `sourendas0@gmail.com` (already joined — do not re-join).

---

## Quick start (web sim)

From this folder:

```bash
python3 cli.py serve-sim --port 8765
```

Open **http://127.0.0.1:8765/sim/**

Or open `sim/index.html` via any static server that serves the contest root (so `../tools/briefbot_tools.js` resolves). Double-opening the HTML file via `file://` may block the relative script on some browsers — prefer `serve-sim`.

Paste a brief (or click a sample) → the agent calls all four tools and shows a human summary + JSON.

---

## CLI (Python, stdlib only)

```bash
python3 cli.py tools
python3 cli.py pipeline -f samples/inventory_brief.txt
python3 cli.py parse "Need n8n + Sheets daily digest. Next week."
python3 cli.py risks -f samples/shopify_brief.txt
python3 cli.py clarifiers -f samples/inventory_brief.txt
python3 cli.py dispatch draft_proposal --args '{"brief_text":"Zapier inventory ASAP"}'
```

---

## Optional MCP stub (stdlib HTTP)

Lightweight JSON-RPC surface (not the full `mcp` SDK). Good enough to demo `tools/list` + `tools/call` offline:

```bash
python3 mcp_server_stub.py 8766
```

```bash
curl -s http://127.0.0.1:8766/tools | python3 -m json.tool
curl -s http://127.0.0.1:8766/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"parse_brief","arguments":{"brief_text":"Need Zapier + Sheets for inventory ASAP"}}}' \
  | python3 -m json.tool
```

### Full FastMCP later (optional, still free/local)

If you later `pip install mcp uvicorn` on a machine with network, you can wrap the same `tools/briefbot_tools.py` functions in FastMCP Streamable HTTP (spec ≥ 2025-11-25). **Not required for this MVP.** Do not request AWS credits for that.

Optional HF rewrite stub exists as `BriefBot.rewriteWithHfStub` in JS (no-op offline without a key).

---

## Layout

```
.
  README.md
  LICENSE
  schema/proposal.schema.json
  tools/briefbot_tools.py   # Pure Python tools
  tools/briefbot_tools.js   # Same tools for the browser sim
  sim/index.html            # Alexa+ web sim
  sim/app.js
  sim/styles.css
  samples/*.txt
  cli.py
  mcp_server_stub.py
```

---

## Proposal schema

`draft_proposal` emits JSON matching `schema/proposal.schema.json` (`version: "1.0"`): title, summary, deliverables, timeline phases, scope in/out, assumptions, risks, clarifying_questions, next_steps, optional price_band.

---

## Demo script (for ≤3 min video — later)

1. Start `python3 cli.py serve-sim`
2. Open the sim → paste inventory brief
3. Show tool calls in the chat + JSON panel
4. Optionally show `curl` against `mcp_server_stub.py` `/tools`
5. Point at `tools/briefbot_tools.py` in the editor

---

## License

MIT — https://github.com/Sourendas/briefbot

## Zero spend

No npm install, no pip install, no AWS, no paid APIs. Python 3 + browser only.
