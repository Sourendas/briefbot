#!/usr/bin/env python3
"""BriefBot rule/template tools — offline, zero API keys.

Tools:
  parse_brief, draft_proposal, list_risks, ask_clarifiers

Designed for Alexa+ MCP or web-sim agents. Pure stdlib.
"""

from __future__ import annotations

import json
import re
from typing import Any

SCHEMA_VERSION = "1.0"

# Keyword → normalized tag maps (deterministic)
_PLATFORM_PATTERNS = [
    (r"\bshopify\b", "Shopify"),
    (r"\bwordpress\b|\bwp\b", "WordPress"),
    (r"\bwebflow\b", "Webflow"),
    (r"\bnotion\b", "Notion"),
    (r"\bairtable\b", "Airtable"),
    (r"\bgoogle\s*sheets?\b|\bsheets?\b", "Google Sheets"),
    (r"\bexcel\b|\bxlsx\b", "Excel"),
    (r"\bslack\b", "Slack"),
    (r"\bdiscord\b", "Discord"),
    (r"\bwhatsapp\b", "WhatsApp"),
    (r"\btelegram\b", "Telegram"),
    (r"\bemail\b|\bgmail\b|\boutlook\b", "Email"),
    (r"\bfigma\b", "Figma"),
    (r"\bgithub\b", "GitHub"),
    (r"\baws\b|\blambda\b", "AWS"),
    (r"\bvercel\b", "Vercel"),
    (r"\bnext\.?js\b", "Next.js"),
    (r"\breact\b", "React"),
    (r"\bpython\b", "Python"),
    (r"\bnode\.?js\b|\bnodejs\b", "Node.js"),
    (r"\bmobile\b|\bios\b|\bandroid\b", "Mobile"),
    (r"\bweb\s*app\b|\bwebsite\b|\blanding\b", "Web"),
]

_INTEGRATION_PATTERNS = [
    (r"\bzapier\b", "Zapier"),
    (r"\bmake\.com\b|\bintegromat\b", "Make"),
    (r"\bn8n\b", "n8n"),
    (r"\bstripe\b", "Stripe"),
    (r"\bpaypal\b", "PayPal"),
    (r"\brazorpay\b", "Razorpay"),
    (r"\bhubspot\b", "HubSpot"),
    (r"\bsalesforce\b", "Salesforce"),
    (r"\bmailchimp\b", "Mailchimp"),
    (r"\btwillio\b|\bsms\b", "Twilio/SMS"),
    (r"\bapi\b|\bwebhook\b", "Custom API/Webhooks"),
    (r"\bopenai\b|\bgpt\b|\bllm\b|\bai\b", "AI/LLM"),
    (r"\bserpapi\b|\bsearch\s*api\b", "Search API"),
]

_URGENCY_PATTERNS = [
    (r"\basap\b|\burgent\b|\bimmediately\b|\btoday\b|\bthis\s*week\b", "high"),
    (r"\bnext\s*week\b|\bsoon\b|\bquick\b|\bfast\b", "medium"),
    (r"\bno\s*rush\b|\bflexible\b|\bwhenever\b|\bexploratory\b", "low"),
]

_BUDGET_PATTERNS = [
    (r"\$\s?(\d[\d,]*)\s*[-–to]+\s*\$?\s?(\d[\d,]*)", "range_usd"),
    (r"₹\s?(\d[\d,]*)\s*[-–to]+\s*₹?\s?(\d[\d,]*)", "range_inr"),
    (r"\bbudget\b.{0,40}?\$\s?(\d[\d,]*)", "mention_usd"),
    (r"\bbudget\b.{0,40}?₹\s?(\d[\d,]*)", "mention_inr"),
    (r"\bfixed\s*price\b|\bflat\s*fee\b", "fixed"),
    (r"\bhourly\b|\bper\s*hour\b", "hourly"),
]

_DELIVERABLE_HINTS = [
    (r"\bautomation\b|\bautomate\b|\bworkflow\b", "Automation workflow"),
    (r"\bdashboard\b|\breport(ing)?\b", "Dashboard / reporting"),
    (r"\bintegration\b|\bconnect\b|\bsync\b", "System integration"),
    (r"\bscraper?\b|\bscraping\b|\bcrawl\b", "Data scraping pipeline"),
    (r"\bchatbot\b|\bbot\b|\bagent\b", "Chatbot / agent"),
    (r"\blanding\b|\bwebsite\b|\bweb\s*page\b", "Landing page / website"),
    (r"\bmvp\b|\bprototype\b|\bproof\s*of\s*concept\b|\bpoc\b", "MVP / prototype"),
    (r"\binventory\b", "Inventory tracking flow"),
    (r"\bproposal\b|\bbrief\b", "Proposal / scoping pack"),
    (r"\bapi\b", "API design / implementation"),
    (r"\bmigration\b|\bimport\b|\bexport\b", "Data migration"),
    (r"\bform\b|\bintake\b", "Intake form + routing"),
]


def _find_tags(text: str, patterns: list[tuple[str, str]]) -> list[str]:
    found: list[str] = []
    lower = text.lower()
    for pat, label in patterns:
        if re.search(pat, lower, re.I) and label not in found:
            found.append(label)
    return found


def _detect_urgency(text: str) -> str:
    lower = text.lower()
    for pat, level in _URGENCY_PATTERNS:
        if re.search(pat, lower, re.I):
            return level
    return "unspecified"


def _detect_budget(text: str) -> dict[str, Any]:
    lower = text.lower()
    for pat, kind in _BUDGET_PATTERNS:
        m = re.search(pat, lower, re.I)
        if m:
            groups = [g.replace(",", "") for g in m.groups() if g]
            return {"signal": kind, "raw_match": m.group(0), "numbers": groups}
    return {"signal": "none", "raw_match": None, "numbers": []}


def _guess_title(text: str, platforms: list[str], integrations: list[str]) -> str:
    first = re.split(r"[.!?\n]", text.strip())[0].strip()
    first = re.sub(r"\s+", " ", first)
    if 12 <= len(first) <= 80:
        return first[:80]
    bits = []
    if integrations:
        bits.append(integrations[0])
    if platforms:
        bits.append("+ " + platforms[0] if bits else platforms[0])
    if not bits:
        bits.append("Freelance scope")
    return (" ".join(bits) + " project").strip()


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def parse_brief(brief_text: str) -> dict[str, Any]:
    """Tool: parse_brief — extract structured fields from a messy brief."""
    if not isinstance(brief_text, str) or not brief_text.strip():
        return {
            "ok": False,
            "error": "brief_text is required (non-empty string)",
            "brief": None,
        }
    text = brief_text.strip()
    platforms = _find_tags(text, _PLATFORM_PATTERNS)
    integrations = _find_tags(text, _INTEGRATION_PATTERNS)
    deliverable_hints = _find_tags(text, _DELIVERABLE_HINTS)
    urgency = _detect_urgency(text)
    budget = _detect_budget(text)
    title = _guess_title(text, platforms, integrations)

    constraints: list[str] = []
    if re.search(r"\bno\s*(paid|spend|budget)\b|\bzero\s*spend\b|\bfree\s*only\b", text, re.I):
        constraints.append("Zero-spend / free-tier tools preferred")
    if re.search(r"\bnda\b|\bconfidential\b", text, re.I):
        constraints.append("Confidential / NDA likely")
    if re.search(r"\bsonly\b|\bsolo\b|\bone\s*dev\b", text, re.I):
        constraints.append("Solo developer engagement")
    if re.search(r"\bmaintain\b|\bongoing\b|\bretainer\b", text, re.I):
        constraints.append("Ongoing maintenance may be expected")

    goal = _sentences(text)[0] if _sentences(text) else text[:160]

    brief = {
        "title": title,
        "client_goal": goal,
        "raw_excerpt": text[:500],
        "platforms": platforms,
        "integrations": integrations,
        "deliverable_hints": deliverable_hints or ["Scoped proposal package"],
        "urgency": urgency,
        "budget": budget,
        "constraints": constraints,
        "word_count": len(text.split()),
    }
    return {"ok": True, "brief": brief}


def ask_clarifiers(brief: dict[str, Any] | str | None = None, brief_text: str | None = None) -> dict[str, Any]:
    """Tool: ask_clarifiers — generate clarifying questions from a brief."""
    parsed = _coerce_brief(brief, brief_text)
    if not parsed["ok"]:
        return parsed
    b = parsed["brief"]
    qs: list[dict[str, str]] = []

    def add(qid: str, question: str, why: str) -> None:
        qs.append({"id": qid, "question": question, "why": why})

    if b["budget"]["signal"] == "none":
        add("Q1", "What is the target budget range and currency?", "Pricing and phase cut lines depend on budget.")
    if b["urgency"] == "unspecified":
        add("Q2", "What is the hard deadline or preferred go-live date?", "Timeline and phase length need an anchor.")
    if not b["platforms"]:
        add("Q3", "Which systems or platforms must the solution run on?", "Delivery stack and acceptance tests hang on this.")
    if not b["integrations"]:
        add("Q4", "Which tools should be connected (e.g. Zapier, Sheets, Shopify)?", "Integration list drives scope and risk.")
    add("Q5", "Who are the end users and how many will use this in week one?", "UX and scale assumptions affect design.")
    add("Q6", "What does 'done' look like — demo, production deploy, or handoff docs?", "Acceptance criteria must be explicit.")
    if "Inventory tracking flow" in b["deliverable_hints"]:
        add("Q7", "Where does inventory data live today, and how often must it sync?", "Sync cadence and source of truth are common failure points.")
    if any(x in b["integrations"] for x in ("Zapier", "Make", "n8n")):
        add("Q8", "Is a no-code automation host already paid for, or should we stay on free tiers?", "Tooling limits change architecture.")
    if len(qs) > 6:
        qs = qs[:6]
    return {"ok": True, "clarifying_questions": qs, "count": len(qs)}


def list_risks(brief: dict[str, Any] | str | None = None, brief_text: str | None = None, proposal: dict[str, Any] | None = None) -> dict[str, Any]:
    """Tool: list_risks — structured risk register from brief (and optional proposal)."""
    parsed = _coerce_brief(brief, brief_text)
    if not parsed["ok"]:
        return parsed
    b = parsed["brief"]
    risks: list[dict[str, str]] = []

    def add(rid: str, severity: str, impact: str, mitigation: str) -> None:
        risks.append({"id": rid, "severity": severity, "impact": impact, "mitigation": mitigation})

    add(
        "R1",
        "high" if b["word_count"] < 40 else "medium",
        "high",
        "Run ask_clarifiers and lock acceptance criteria before coding.",
    )
    if b["budget"]["signal"] == "none":
        add("R2", "medium", "high", "Agree a price band and out-of-scope list in writing.")
    if b["urgency"] == "high":
        add("R3", "high", "medium", "Cut to an MVP slice; defer nice-to-haves to phase 2.")
    if any(x in b["integrations"] for x in ("Zapier", "Make", "n8n")):
        add("R4", "medium", "medium", "Document trigger/action limits and add retry + dead-letter notes.")
    if "Custom API/Webhooks" in b["integrations"] or "AI/LLM" in b["integrations"]:
        add("R5", "medium", "high", "Confirm auth, rate limits, and data retention before build.")
    if "Shopify" in b["platforms"]:
        add("R6", "low", "medium", "Use Shopify Partner test store; avoid production writes until UAT.")
    if "Zero-spend / free-tier tools preferred" in b["constraints"]:
        add("R7", "medium", "medium", "Design for free tiers; flag upgrade walls early in the proposal.")
    if proposal and isinstance(proposal, dict):
        days = proposal.get("timeline", {}).get("total_days_estimate")
        if isinstance(days, int) and days <= 5 and b["urgency"] == "high":
            add("R8", "high", "high", "Buffer at least one contingency day or reduce deliverables.")
    if len(risks) < 3:
        add("R9", "low", "medium", "Schedule a mid-project check-in to catch scope drift.")
    return {"ok": True, "risks": risks, "count": len(risks)}


def draft_proposal(brief: dict[str, Any] | str | None = None, brief_text: str | None = None) -> dict[str, Any]:
    """Tool: draft_proposal — emit a schema-shaped proposal (deterministic)."""
    parsed = _coerce_brief(brief, brief_text)
    if not parsed["ok"]:
        return parsed
    b = parsed["brief"]
    risks = list_risks(brief=b)["risks"]
    clarifiers = ask_clarifiers(brief=b)["clarifying_questions"]

    platforms = b["platforms"] or ["Web"]
    integrations = b["integrations"]
    hints = b["deliverable_hints"]

    deliverables = []
    for i, hint in enumerate(hints[:4], start=1):
        deliverables.append(
            {
                "name": hint,
                "description": f"Implement and demo '{hint}' aligned to the client goal.",
                "acceptance": f"Stakeholder can walk through '{hint}' end-to-end on a test account.",
            }
        )
    deliverables.append(
        {
            "name": "Handoff pack",
            "description": "Short README, credentials map (placeholders), and next-step backlog.",
            "acceptance": "Client can redeploy or rerun the happy path from the README alone.",
        }
    )

    # Timeline heuristics
    base = 5 + 2 * len(integrations) + (2 if b["urgency"] == "high" else 0)
    if b["urgency"] == "low":
        base += 3
    discovery = max(1, base // 5)
    build = max(3, base - discovery - 2)
    uat = 2
    phases = [
        {
            "name": "Discovery & scope lock",
            "days": discovery,
            "outcomes": ["Clarifiers answered", "Acceptance criteria signed off"],
        },
        {
            "name": "Build MVP",
            "days": build,
            "outcomes": [d["name"] for d in deliverables[:-1]],
        },
        {
            "name": "UAT & handoff",
            "days": uat,
            "outcomes": ["Bugfixes from UAT", "Handoff pack delivered"],
        },
    ]
    total_days = sum(p["days"] for p in phases)

    scope_in = [
        f"Primary platforms: {', '.join(platforms)}",
        "Happy-path automation or feature flow with test data",
        "Written proposal artifacts (this JSON + human summary)",
    ]
    if integrations:
        scope_in.append("Integrations: " + ", ".join(integrations))

    scope_out = [
        "Production SLA / 24-7 on-call",
        "Custom mobile native apps (unless explicitly listed)",
        "Paid third-party upgrades or ad spend",
        "Legal / tax / compliance filings",
    ]

    assumptions = [
        "Client provides timely access to accounts and sample data.",
        "One primary stakeholder for decisions.",
        "Work stays on free/local tooling unless client supplies licenses.",
    ]
    assumptions.extend(b["constraints"])

    summary_bits = [b["client_goal"]]
    if integrations:
        summary_bits.append("Uses " + ", ".join(integrations[:3]) + ".")
    summary = " ".join(summary_bits)

    price_band = None
    nums = b["budget"].get("numbers") or []
    if b["budget"]["signal"].startswith("range") and len(nums) >= 2:
        cur = "USD" if "usd" in b["budget"]["signal"] else "INR"
        price_band = {
            "currency": cur,
            "low": float(nums[0]),
            "high": float(nums[1]),
            "note": "Taken from brief; not a quote until clarifiers close.",
        }
    elif b["budget"]["signal"].startswith("mention") and nums:
        cur = "USD" if "usd" in b["budget"]["signal"] else "INR"
        n = float(nums[0])
        price_band = {
            "currency": cur,
            "low": n * 0.8,
            "high": n * 1.2,
            "note": "Inferred band around a single budget mention.",
        }

    proposal: dict[str, Any] = {
        "version": SCHEMA_VERSION,
        "title": b["title"],
        "summary": summary,
        "client_goal": b["client_goal"],
        "platforms": platforms,
        "integrations": integrations,
        "deliverables": deliverables,
        "timeline": {"total_days_estimate": total_days, "phases": phases},
        "scope_in": scope_in,
        "scope_out": scope_out,
        "assumptions": assumptions,
        "risks": risks,
        "clarifying_questions": clarifiers,
        "next_steps": [
            "Answer clarifying questions",
            "Confirm budget band and deadline",
            "Approve MVP slice, then start Discovery phase",
        ],
        "meta": {
            "generator": "BriefBot rule-engine",
            "urgency": b["urgency"],
            "source_word_count": b["word_count"],
        },
    }
    if price_band:
        proposal["price_band"] = price_band

    return {"ok": True, "proposal": proposal}


def _coerce_brief(brief: dict[str, Any] | str | None, brief_text: str | None) -> dict[str, Any]:
    if isinstance(brief, dict) and brief.get("client_goal"):
        return {"ok": True, "brief": brief}
    if isinstance(brief, dict) and brief.get("brief"):
        return {"ok": True, "brief": brief["brief"]}
    text = None
    if isinstance(brief, str) and brief.strip():
        text = brief
    elif isinstance(brief_text, str) and brief_text.strip():
        text = brief_text
    if text:
        return parse_brief(text)
    return {"ok": False, "error": "Provide brief object or brief_text string", "brief": None}


TOOL_SPECS = [
    {
        "name": "parse_brief",
        "description": "Parse a messy freelance/job brief into structured fields (platforms, integrations, urgency, constraints).",
        "parameters": {
            "type": "object",
            "required": ["brief_text"],
            "properties": {
                "brief_text": {"type": "string", "description": "Raw client brief text"}
            },
        },
    },
    {
        "name": "draft_proposal",
        "description": "Draft a scoped proposal JSON (deliverables, timeline, risks, clarifiers) from a brief.",
        "parameters": {
            "type": "object",
            "properties": {
                "brief_text": {"type": "string"},
                "brief": {"type": "object", "description": "Output of parse_brief"},
            },
        },
    },
    {
        "name": "list_risks",
        "description": "List project risks with severity, impact, and mitigation.",
        "parameters": {
            "type": "object",
            "properties": {
                "brief_text": {"type": "string"},
                "brief": {"type": "object"},
                "proposal": {"type": "object"},
            },
        },
    },
    {
        "name": "ask_clarifiers",
        "description": "Generate clarifying questions to tighten scope before build.",
        "parameters": {
            "type": "object",
            "properties": {
                "brief_text": {"type": "string"},
                "brief": {"type": "object"},
            },
        },
    },
]


def dispatch(tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dispatch a tool call by name (MCP / sim bridge)."""
    arguments = arguments or {}
    if tool_name == "parse_brief":
        return parse_brief(arguments.get("brief_text", ""))
    if tool_name == "draft_proposal":
        return draft_proposal(brief=arguments.get("brief"), brief_text=arguments.get("brief_text"))
    if tool_name == "list_risks":
        return list_risks(
            brief=arguments.get("brief"),
            brief_text=arguments.get("brief_text"),
            proposal=arguments.get("proposal"),
        )
    if tool_name == "ask_clarifiers":
        return ask_clarifiers(brief=arguments.get("brief"), brief_text=arguments.get("brief_text"))
    return {"ok": False, "error": f"Unknown tool: {tool_name}"}


def run_pipeline(brief_text: str) -> dict[str, Any]:
    """Convenience: parse → proposal (includes risks + clarifiers)."""
    parsed = parse_brief(brief_text)
    if not parsed["ok"]:
        return parsed
    drafted = draft_proposal(brief=parsed["brief"])
    return {
        "ok": True,
        "brief": parsed["brief"],
        "proposal": drafted.get("proposal"),
        "tools_called": ["parse_brief", "draft_proposal", "list_risks", "ask_clarifiers"],
    }


if __name__ == "__main__":
    import sys

    sample = (
        sys.stdin.read().strip()
        if not sys.stdin.isatty()
        else "Need Zapier + Sheets automation for inventory. ASAP. Budget $500-800."
    )
    print(json.dumps(run_pipeline(sample), indent=2))
