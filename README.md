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

Or open `sim/index.html` via any static server that serves the contest root (so `../tools/briefbot_tools.js` resolves). Prefer `serve-sim` over `file://`.

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

---

## Layout

```
briefbot/
  README.md
  LICENSE
  schema/proposal.schema.json
  tools/briefbot_tools.py
  tools/briefbot_tools.js
  sim/index.html
  sim/app.js
  sim/styles.css
  samples/*.txt
  cli.py
  mcp_server_stub.py
```

## License

MIT

## Zero spend

No npm install, no pip install, no AWS, no paid APIs. Python 3 + browser only.
