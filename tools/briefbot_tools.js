/**
 * BriefBot rule/template tools — offline, zero API keys.
 * Mirror of briefbot_tools.py for the Alexa+ web sim (GitHub Pages-ready).
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    root.BriefBot = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var SCHEMA_VERSION = "1.0";

  var PLATFORM_PATTERNS = [
    [/\bshopify\b/i, "Shopify"],
    [/\bwordpress\b|\bwp\b/i, "WordPress"],
    [/\bwebflow\b/i, "Webflow"],
    [/\bnotion\b/i, "Notion"],
    [/\bairtable\b/i, "Airtable"],
    [/\bgoogle\s*sheets?\b|\bsheets?\b/i, "Google Sheets"],
    [/\bexcel\b|\bxlsx\b/i, "Excel"],
    [/\bslack\b/i, "Slack"],
    [/\bdiscord\b/i, "Discord"],
    [/\bwhatsapp\b/i, "WhatsApp"],
    [/\btelegram\b/i, "Telegram"],
    [/\bemail\b|\bgmail\b|\boutlook\b/i, "Email"],
    [/\bfigma\b/i, "Figma"],
    [/\bgithub\b/i, "GitHub"],
    [/\baws\b|\blambda\b/i, "AWS"],
    [/\bvercel\b/i, "Vercel"],
    [/\bnext\.?js\b/i, "Next.js"],
    [/\breact\b/i, "React"],
    [/\bpython\b/i, "Python"],
    [/\bnode\.?js\b|\bnodejs\b/i, "Node.js"],
    [/\bmobile\b|\bios\b|\bandroid\b/i, "Mobile"],
    [/\bweb\s*app\b|\bwebsite\b|\blanding\b/i, "Web"],
  ];

  var INTEGRATION_PATTERNS = [
    [/\bzapier\b/i, "Zapier"],
    [/\bmake\.com\b|\bintegromat\b/i, "Make"],
    [/\bn8n\b/i, "n8n"],
    [/\bstripe\b/i, "Stripe"],
    [/\bpaypal\b/i, "PayPal"],
    [/\brazorpay\b/i, "Razorpay"],
    [/\bhubspot\b/i, "HubSpot"],
    [/\bsalesforce\b/i, "Salesforce"],
    [/\bmailchimp\b/i, "Mailchimp"],
    [/\btwilio\b|\bsms\b/i, "Twilio/SMS"],
    [/\bapi\b|\bwebhook\b/i, "Custom API/Webhooks"],
    [/\bopenai\b|\bgpt\b|\bllm\b|\bai\b/i, "AI/LLM"],
    [/\bserpapi\b|\bsearch\s*api\b/i, "Search API"],
  ];

  var URGENCY_PATTERNS = [
    [/\basap\b|\burgent\b|\bimmediately\b|\btoday\b|\bthis\s*week\b/i, "high"],
    [/\bnext\s*week\b|\bsoon\b|\bquick\b|\bfast\b/i, "medium"],
    [/\bno\s*rush\b|\bflexible\b|\bwhenever\b|\bexploratory\b/i, "low"],
  ];

  var DELIVERABLE_HINTS = [
    [/\bautomation\b|\bautomate\b|\bworkflow\b/i, "Automation workflow"],
    [/\bdashboard\b|\breport(ing)?\b/i, "Dashboard / reporting"],
    [/\bintegration\b|\bconnect\b|\bsync\b/i, "System integration"],
    [/\bscraper?\b|\bscraping\b|\bcrawl\b/i, "Data scraping pipeline"],
    [/\bchatbot\b|\bbot\b|\bagent\b/i, "Chatbot / agent"],
    [/\blanding\b|\bwebsite\b|\bweb\s*page\b/i, "Landing page / website"],
    [/\bmvp\b|\bprototype\b|\bproof\s*of\s*concept\b|\bpoc\b/i, "MVP / prototype"],
    [/\binventory\b/i, "Inventory tracking flow"],
    [/\bproposal\b|\bbrief\b/i, "Proposal / scoping pack"],
    [/\bapi\b/i, "API design / implementation"],
    [/\bmigration\b|\bimport\b|\bexport\b/i, "Data migration"],
    [/\bform\b|\bintake\b/i, "Intake form + routing"],
  ];

  function findTags(text, patterns) {
    var found = [];
    for (var i = 0; i < patterns.length; i++) {
      var pat = patterns[i][0];
      var label = patterns[i][1];
      pat.lastIndex = 0;
      if (pat.test(text) && found.indexOf(label) === -1) found.push(label);
    }
    return found;
  }

  function detectUrgency(text) {
    for (var i = 0; i < URGENCY_PATTERNS.length; i++) {
      URGENCY_PATTERNS[i][0].lastIndex = 0;
      if (URGENCY_PATTERNS[i][0].test(text)) return URGENCY_PATTERNS[i][1];
    }
    return "unspecified";
  }

  function detectBudget(text) {
    var lower = text.toLowerCase();
    var rangeUsd = /\$\s?(\d[\d,]*)\s*[-–to]+\s*\$?\s?(\d[\d,]*)/i.exec(lower);
    if (rangeUsd) {
      return {
        signal: "range_usd",
        raw_match: rangeUsd[0],
        numbers: [rangeUsd[1].replace(/,/g, ""), rangeUsd[2].replace(/,/g, "")],
      };
    }
    var rangeInr = /₹\s?(\d[\d,]*)\s*[-–to]+\s*₹?\s?(\d[\d,]*)/i.exec(lower);
    if (rangeInr) {
      return {
        signal: "range_inr",
        raw_match: rangeInr[0],
        numbers: [rangeInr[1].replace(/,/g, ""), rangeInr[2].replace(/,/g, "")],
      };
    }
    var mUsd = /budget.{0,40}?\$\s?(\d[\d,]*)/i.exec(lower);
    if (mUsd) {
      return { signal: "mention_usd", raw_match: mUsd[0], numbers: [mUsd[1].replace(/,/g, "")] };
    }
    var mInr = /budget.{0,40}?₹\s?(\d[\d,]*)/i.exec(lower);
    if (mInr) {
      return { signal: "mention_inr", raw_match: mInr[0], numbers: [mInr[1].replace(/,/g, "")] };
    }
    if (/\bfixed\s*price\b|\bflat\s*fee\b/i.test(lower)) {
      return { signal: "fixed", raw_match: "fixed", numbers: [] };
    }
    if (/\bhourly\b|\bper\s*hour\b/i.test(lower)) {
      return { signal: "hourly", raw_match: "hourly", numbers: [] };
    }
    return { signal: "none", raw_match: null, numbers: [] };
  }

  function sentences(text) {
    return text
      .split(/(?<=[.!?])\s+|\n+/)
      .map(function (p) {
        return p.trim();
      })
      .filter(Boolean);
  }

  function guessTitle(text, platforms, integrations) {
    var first = text.trim().split(/[.!?\n]/)[0].replace(/\s+/g, " ").trim();
    if (first.length >= 12 && first.length <= 80) return first.slice(0, 80);
    var bits = [];
    if (integrations.length) bits.push(integrations[0]);
    if (platforms.length) bits.push(bits.length ? "+ " + platforms[0] : platforms[0]);
    if (!bits.length) bits.push("Freelance scope");
    return (bits.join(" ") + " project").trim();
  }

  function parseBrief(briefText) {
    if (typeof briefText !== "string" || !briefText.trim()) {
      return { ok: false, error: "brief_text is required (non-empty string)", brief: null };
    }
    var text = briefText.trim();
    var platforms = findTags(text, PLATFORM_PATTERNS);
    var integrations = findTags(text, INTEGRATION_PATTERNS);
    var deliverableHints = findTags(text, DELIVERABLE_HINTS);
    var urgency = detectUrgency(text);
    var budget = detectBudget(text);
    var title = guessTitle(text, platforms, integrations);
    var constraints = [];
    if (/\bno\s*(paid|spend|budget)\b|\bzero\s*spend\b|\bfree\s*only\b/i.test(text)) {
      constraints.push("Zero-spend / free-tier tools preferred");
    }
    if (/\bnda\b|\bconfidential\b/i.test(text)) constraints.push("Confidential / NDA likely");
    if (/\bsonly\b|\bsolo\b|\bone\s*dev\b/i.test(text)) constraints.push("Solo developer engagement");
    if (/\bmaintain\b|\bongoing\b|\bretainer\b/i.test(text)) {
      constraints.push("Ongoing maintenance may be expected");
    }
    var sents = sentences(text);
    var goal = sents.length ? sents[0] : text.slice(0, 160);
    return {
      ok: true,
      brief: {
        title: title,
        client_goal: goal,
        raw_excerpt: text.slice(0, 500),
        platforms: platforms,
        integrations: integrations,
        deliverable_hints: deliverableHints.length ? deliverableHints : ["Scoped proposal package"],
        urgency: urgency,
        budget: budget,
        constraints: constraints,
        word_count: text.split(/\s+/).filter(Boolean).length,
      },
    };
  }

  function coerceBrief(brief, briefText) {
    if (brief && typeof brief === "object" && brief.client_goal) return { ok: true, brief: brief };
    if (brief && typeof brief === "object" && brief.brief) return { ok: true, brief: brief.brief };
    var text = null;
    if (typeof brief === "string" && brief.trim()) text = brief;
    else if (typeof briefText === "string" && briefText.trim()) text = briefText;
    if (text) return parseBrief(text);
    return { ok: false, error: "Provide brief object or brief_text string", brief: null };
  }

  function askClarifiers(brief, briefText) {
    var parsed = coerceBrief(brief, briefText);
    if (!parsed.ok) return parsed;
    var b = parsed.brief;
    var qs = [];
    function add(id, question, why) {
      qs.push({ id: id, question: question, why: why });
    }
    if (b.budget.signal === "none") {
      add("Q1", "What is the target budget range and currency?", "Pricing and phase cut lines depend on budget.");
    }
    if (b.urgency === "unspecified") {
      add("Q2", "What is the hard deadline or preferred go-live date?", "Timeline and phase length need an anchor.");
    }
    if (!b.platforms.length) {
      add("Q3", "Which systems or platforms must the solution run on?", "Delivery stack and acceptance tests hang on this.");
    }
    if (!b.integrations.length) {
      add("Q4", "Which tools should be connected (e.g. Zapier, Sheets, Shopify)?", "Integration list drives scope and risk.");
    }
    add("Q5", "Who are the end users and how many will use this in week one?", "UX and scale assumptions affect design.");
    add("Q6", "What does 'done' look like — demo, production deploy, or handoff docs?", "Acceptance criteria must be explicit.");
    if (b.deliverable_hints.indexOf("Inventory tracking flow") !== -1) {
      add("Q7", "Where does inventory data live today, and how often must it sync?", "Sync cadence and source of truth are common failure points.");
    }
    if (["Zapier", "Make", "n8n"].some(function (x) { return b.integrations.indexOf(x) !== -1; })) {
      add("Q8", "Is a no-code automation host already paid for, or should we stay on free tiers?", "Tooling limits change architecture.");
    }
    if (qs.length > 6) qs = qs.slice(0, 6);
    return { ok: true, clarifying_questions: qs, count: qs.length };
  }

  function listRisks(brief, briefText, proposal) {
    var parsed = coerceBrief(brief, briefText);
    if (!parsed.ok) return parsed;
    var b = parsed.brief;
    var risks = [];
    function add(id, severity, impact, mitigation) {
      risks.push({ id: id, severity: severity, impact: impact, mitigation: mitigation });
    }
    add(
      "R1",
      b.word_count < 40 ? "high" : "medium",
      "high",
      "Run ask_clarifiers and lock acceptance criteria before coding."
    );
    if (b.budget.signal === "none") {
      add("R2", "medium", "high", "Agree a price band and out-of-scope list in writing.");
    }
    if (b.urgency === "high") {
      add("R3", "high", "medium", "Cut to an MVP slice; defer nice-to-haves to phase 2.");
    }
    if (["Zapier", "Make", "n8n"].some(function (x) { return b.integrations.indexOf(x) !== -1; })) {
      add("R4", "medium", "medium", "Document trigger/action limits and add retry + dead-letter notes.");
    }
    if (b.integrations.indexOf("Custom API/Webhooks") !== -1 || b.integrations.indexOf("AI/LLM") !== -1) {
      add("R5", "medium", "high", "Confirm auth, rate limits, and data retention before build.");
    }
    if (b.platforms.indexOf("Shopify") !== -1) {
      add("R6", "low", "medium", "Use Shopify Partner test store; avoid production writes until UAT.");
    }
    if (b.constraints.indexOf("Zero-spend / free-tier tools preferred") !== -1) {
      add("R7", "medium", "medium", "Design for free tiers; flag upgrade walls early in the proposal.");
    }
    if (proposal && proposal.timeline && typeof proposal.timeline.total_days_estimate === "number") {
      if (proposal.timeline.total_days_estimate <= 5 && b.urgency === "high") {
        add("R8", "high", "high", "Buffer at least one contingency day or reduce deliverables.");
      }
    }
    if (risks.length < 3) {
      add("R9", "low", "medium", "Schedule a mid-project check-in to catch scope drift.");
    }
    return { ok: true, risks: risks, count: risks.length };
  }

  function draftProposal(brief, briefText) {
    var parsed = coerceBrief(brief, briefText);
    if (!parsed.ok) return parsed;
    var b = parsed.brief;
    var risks = listRisks(b).risks;
    var clarifiers = askClarifiers(b).clarifying_questions;
    var platforms = b.platforms.length ? b.platforms.slice() : ["Web"];
    var integrations = b.integrations.slice();
    var hints = b.deliverable_hints.slice();
    var deliverables = [];
    for (var i = 0; i < Math.min(4, hints.length); i++) {
      deliverables.push({
        name: hints[i],
        description: "Implement and demo '" + hints[i] + "' aligned to the client goal.",
        acceptance: "Stakeholder can walk through '" + hints[i] + "' end-to-end on a test account.",
      });
    }
    deliverables.push({
      name: "Handoff pack",
      description: "Short README, credentials map (placeholders), and next-step backlog.",
      acceptance: "Client can redeploy or rerun the happy path from the README alone.",
    });
    var base = 5 + 2 * integrations.length + (b.urgency === "high" ? 2 : 0);
    if (b.urgency === "low") base += 3;
    var discovery = Math.max(1, Math.floor(base / 5));
    var build = Math.max(3, base - discovery - 2);
    var uat = 2;
    var phases = [
      {
        name: "Discovery & scope lock",
        days: discovery,
        outcomes: ["Clarifiers answered", "Acceptance criteria signed off"],
      },
      {
        name: "Build MVP",
        days: build,
        outcomes: deliverables.slice(0, -1).map(function (d) { return d.name; }),
      },
      {
        name: "UAT & handoff",
        days: uat,
        outcomes: ["Bugfixes from UAT", "Handoff pack delivered"],
      },
    ];
    var totalDays = phases.reduce(function (s, p) { return s + p.days; }, 0);
    var scopeIn = [
      "Primary platforms: " + platforms.join(", "),
      "Happy-path automation or feature flow with test data",
      "Written proposal artifacts (this JSON + human summary)",
    ];
    if (integrations.length) scopeIn.push("Integrations: " + integrations.join(", "));
    var scopeOut = [
      "Production SLA / 24-7 on-call",
      "Custom mobile native apps (unless explicitly listed)",
      "Paid third-party upgrades or ad spend",
      "Legal / tax / compliance filings",
    ];
    var assumptions = [
      "Client provides timely access to accounts and sample data.",
      "One primary stakeholder for decisions.",
      "Work stays on free/local tooling unless client supplies licenses.",
    ].concat(b.constraints);
    var summaryBits = [b.client_goal];
    if (integrations.length) summaryBits.push("Uses " + integrations.slice(0, 3).join(", ") + ".");
    var proposal = {
      version: SCHEMA_VERSION,
      title: b.title,
      summary: summaryBits.join(" "),
      client_goal: b.client_goal,
      platforms: platforms,
      integrations: integrations,
      deliverables: deliverables,
      timeline: { total_days_estimate: totalDays, phases: phases },
      scope_in: scopeIn,
      scope_out: scopeOut,
      assumptions: assumptions,
      risks: risks,
      clarifying_questions: clarifiers,
      next_steps: [
        "Answer clarifying questions",
        "Confirm budget band and deadline",
        "Approve MVP slice, then start Discovery phase",
      ],
      meta: {
        generator: "BriefBot rule-engine",
        urgency: b.urgency,
        source_word_count: b.word_count,
      },
    };
    var nums = b.budget.numbers || [];
    if (b.budget.signal.indexOf("range") === 0 && nums.length >= 2) {
      proposal.price_band = {
        currency: b.budget.signal.indexOf("usd") !== -1 ? "USD" : "INR",
        low: parseFloat(nums[0]),
        high: parseFloat(nums[1]),
        note: "Taken from brief; not a quote until clarifiers close.",
      };
    } else if (b.budget.signal.indexOf("mention") === 0 && nums.length) {
      var n = parseFloat(nums[0]);
      proposal.price_band = {
        currency: b.budget.signal.indexOf("usd") !== -1 ? "USD" : "INR",
        low: n * 0.8,
        high: n * 1.2,
        note: "Inferred band around a single budget mention.",
      };
    }
    return { ok: true, proposal: proposal };
  }

  var TOOL_SPECS = [
    {
      name: "parse_brief",
      description: "Parse a messy freelance/job brief into structured fields.",
      parameters: { type: "object", required: ["brief_text"], properties: { brief_text: { type: "string" } } },
    },
    {
      name: "draft_proposal",
      description: "Draft a scoped proposal JSON from a brief.",
      parameters: { type: "object", properties: { brief_text: { type: "string" }, brief: { type: "object" } } },
    },
    {
      name: "list_risks",
      description: "List project risks with severity, impact, and mitigation.",
      parameters: {
        type: "object",
        properties: { brief_text: { type: "string" }, brief: { type: "object" }, proposal: { type: "object" } },
      },
    },
    {
      name: "ask_clarifiers",
      description: "Generate clarifying questions to tighten scope.",
      parameters: { type: "object", properties: { brief_text: { type: "string" }, brief: { type: "object" } } },
    },
  ];

  function dispatch(toolName, args) {
    args = args || {};
    if (toolName === "parse_brief") return parseBrief(args.brief_text || "");
    if (toolName === "draft_proposal") return draftProposal(args.brief, args.brief_text);
    if (toolName === "list_risks") return listRisks(args.brief, args.brief_text, args.proposal);
    if (toolName === "ask_clarifiers") return askClarifiers(args.brief, args.brief_text);
    return { ok: false, error: "Unknown tool: " + toolName };
  }

  function runPipeline(briefText) {
    var parsed = parseBrief(briefText);
    if (!parsed.ok) return parsed;
    var drafted = draftProposal(parsed.brief);
    return {
      ok: true,
      brief: parsed.brief,
      proposal: drafted.proposal,
      tools_called: ["parse_brief", "draft_proposal", "list_risks", "ask_clarifiers"],
    };
  }

  /** Optional stub: free HF inference later. Offline no-op unless window.BRIEFBOT_HF_TOKEN set. */
  function rewriteWithHfStub(text) {
    return Promise.resolve({
      ok: false,
      skipped: true,
      reason: "HF stub disabled offline (no key). Rule engine output used instead.",
      text: text,
    });
  }

  return {
    SCHEMA_VERSION: SCHEMA_VERSION,
    TOOL_SPECS: TOOL_SPECS,
    parse_brief: parseBrief,
    draft_proposal: draftProposal,
    list_risks: listRisks,
    ask_clarifiers: askClarifiers,
    dispatch: dispatch,
    runPipeline: runPipeline,
    rewriteWithHfStub: rewriteWithHfStub,
  };
});
