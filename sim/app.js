/* BriefBot Alexa+ web sim — calls the same tool functions as the Python path. */
(function () {
  "use strict";

  var chatEl = document.getElementById("chat");
  var inputEl = document.getElementById("input");
  var jsonEl = document.getElementById("jsonOut");
  var toolsEl = document.getElementById("tools");
  var sendBtn = document.getElementById("sendBtn");
  var clearBtn = document.getElementById("clearBtn");
  var pipelineBtn = document.getElementById("pipelineBtn");
  var samplesEl = document.getElementById("samples");

  var state = {
    lastBrief: null,
    lastProposal: null,
    history: [],
  };

  var SAMPLES = [
    "Need Zapier + Sheets automation for inventory. ASAP. Budget $500-800.",
    "Build a Shopify product sync to Airtable for a small store. Flexible timeline. Zero spend preferred.",
    "We want an n8n workflow that emails a daily sales digest from Google Sheets. Next week.",
  ];

  function addMsg(role, text) {
    var div = document.createElement("div");
    div.className = "msg " + role;
    var who = document.createElement("span");
    who.className = "who";
    who.textContent = role === "user" ? "You" : role === "tool" ? "Tool call" : "BriefBot (Alexa+ sim)";
    div.appendChild(who);
    div.appendChild(document.createTextNode(text));
    chatEl.appendChild(div);
    chatEl.scrollTop = chatEl.scrollHeight;
    state.history.push({ role: role, text: text });
  }

  function setJson(obj) {
    jsonEl.textContent = JSON.stringify(obj, null, 2);
  }

  function renderTools() {
    toolsEl.innerHTML = "";
    BriefBot.TOOL_SPECS.forEach(function (t) {
      var chip = document.createElement("span");
      chip.className = "tool-chip";
      chip.textContent = t.name;
      chip.title = t.description;
      toolsEl.appendChild(chip);
    });
  }

  function renderSamples() {
    samplesEl.innerHTML = "";
    SAMPLES.forEach(function (s) {
      var b = document.createElement("button");
      b.className = "sample";
      b.type = "button";
      b.textContent = s;
      b.addEventListener("click", function () {
        inputEl.value = s;
        inputEl.focus();
      });
      samplesEl.appendChild(b);
    });
  }

  function summarizeProposal(p) {
    if (!p) return "No proposal yet.";
    var lines = [];
    lines.push("Proposal: " + p.title);
    lines.push("Summary: " + p.summary);
    lines.push("Timeline: ~" + p.timeline.total_days_estimate + " days across " + p.timeline.phases.length + " phases.");
    lines.push("Deliverables:");
    p.deliverables.forEach(function (d, i) {
      lines.push("  " + (i + 1) + ". " + d.name + " — " + d.acceptance);
    });
    lines.push("Top risks:");
    p.risks.slice(0, 3).forEach(function (r) {
      lines.push("  [" + r.severity + "/" + r.impact + "] " + r.id + ": " + r.mitigation);
    });
    lines.push("Clarifiers:");
    p.clarifying_questions.slice(0, 4).forEach(function (q) {
      lines.push("  " + q.id + ". " + q.question);
    });
    lines.push("Next: " + p.next_steps.join(" → "));
    return lines.join("\n");
  }

  function callTool(name, args) {
    addMsg("tool", name + "(" + JSON.stringify(args) + ")");
    var result = BriefBot.dispatch(name, args);
    return result;
  }

  function runFullPipeline(text) {
    var parsed = callTool("parse_brief", { brief_text: text });
    if (!parsed.ok) {
      addMsg("agent", "Could not parse brief: " + parsed.error);
      setJson(parsed);
      return;
    }
    state.lastBrief = parsed.brief;
    var drafted = callTool("draft_proposal", { brief: parsed.brief });
    // draft_proposal already embeds risks + clarifiers; still demo the tools explicitly
    var risks = callTool("list_risks", { brief: parsed.brief, proposal: drafted.proposal });
    var qs = callTool("ask_clarifiers", { brief: parsed.brief });
    if (drafted.ok) {
      // keep proposal risks/questions authoritative from draft, but show tool results
      state.lastProposal = drafted.proposal;
      setJson({
        brief: parsed.brief,
        proposal: drafted.proposal,
        list_risks: risks,
        ask_clarifiers: qs,
        tools_called: ["parse_brief", "draft_proposal", "list_risks", "ask_clarifiers"],
      });
      addMsg("agent", summarizeProposal(drafted.proposal));
    } else {
      addMsg("agent", "draft_proposal failed: " + drafted.error);
      setJson(drafted);
    }
  }

  function routeMessage(text) {
    var lower = text.toLowerCase().trim();
    if (lower === "/help" || lower === "help") {
      addMsg(
        "agent",
        "Alexa+ sim commands:\n" +
          "• Paste a freelance brief → I run parse_brief → draft_proposal → list_risks → ask_clarifiers\n" +
          "• /risks — list_risks on last brief\n" +
          "• /questions — ask_clarifiers on last brief\n" +
          "• /parse — parse only\n" +
          "• /proposal — draft from last brief or current text\n" +
          "• /tools — list tool specs\n" +
          "• /clear — reset chat state"
      );
      return;
    }
    if (lower === "/tools") {
      setJson(BriefBot.TOOL_SPECS);
      addMsg("agent", "Tools: " + BriefBot.TOOL_SPECS.map(function (t) { return t.name; }).join(", "));
      return;
    }
    if (lower === "/clear") {
      clearChat();
      return;
    }
    if (lower === "/risks") {
      if (!state.lastBrief) {
        addMsg("agent", "No brief yet. Paste a brief first.");
        return;
      }
      var r = callTool("list_risks", { brief: state.lastBrief, proposal: state.lastProposal });
      setJson(r);
      addMsg("agent", r.ok ? "Found " + r.count + " risks. See JSON panel." : r.error);
      return;
    }
    if (lower === "/questions" || lower === "/clarifiers") {
      if (!state.lastBrief) {
        addMsg("agent", "No brief yet. Paste a brief first.");
        return;
      }
      var q = callTool("ask_clarifiers", { brief: state.lastBrief });
      setJson(q);
      if (q.ok) {
        addMsg(
          "agent",
          q.clarifying_questions
            .map(function (item) {
              return item.id + ". " + item.question;
            })
            .join("\n")
        );
      } else addMsg("agent", q.error);
      return;
    }
    if (lower === "/parse" || lower.startsWith("/parse ")) {
      var body = lower === "/parse" ? "" : text.replace(/^\/parse\s+/i, "");
      if (!body) {
        addMsg("agent", "Usage: /parse <brief text>");
        return;
      }
      var p = callTool("parse_brief", { brief_text: body });
      if (p.ok) state.lastBrief = p.brief;
      setJson(p);
      addMsg("agent", p.ok ? "Parsed: " + p.brief.title + " (urgency=" + p.brief.urgency + ")" : p.error);
      return;
    }
    if (lower === "/proposal" || lower.startsWith("/proposal ")) {
      var rest = lower === "/proposal" ? "" : text.replace(/^\/proposal\s+/i, "");
      if (rest) {
        runFullPipeline(rest);
        return;
      }
      if (!state.lastBrief) {
        addMsg("agent", "No brief yet. Paste a brief or /proposal <text>.");
        return;
      }
      var d = callTool("draft_proposal", { brief: state.lastBrief });
      if (d.ok) {
        state.lastProposal = d.proposal;
        setJson(d);
        addMsg("agent", summarizeProposal(d.proposal));
      } else addMsg("agent", d.error);
      return;
    }
    // Default: treat as brief → full pipeline (agentic Alexa+ style)
    runFullPipeline(text);
  }

  function send() {
    var text = (inputEl.value || "").trim();
    if (!text) return;
    addMsg("user", text);
    inputEl.value = "";
    routeMessage(text);
  }

  function clearChat() {
    chatEl.innerHTML = "";
    state.lastBrief = null;
    state.lastProposal = null;
    state.history = [];
    setJson({ tip: "Paste a brief or pick a sample. Tools run fully offline." });
    addMsg(
      "agent",
      "Hi — I'm BriefBot, a simulated Alexa+ agent.\nPaste a messy client brief and I'll call parse_brief, draft_proposal, list_risks, and ask_clarifiers.\nType /help for commands."
    );
  }

  sendBtn.addEventListener("click", send);
  pipelineBtn.addEventListener("click", function () {
    var text = (inputEl.value || "").trim();
    if (!text) {
      addMsg("agent", "Enter a brief in the box, then Run pipeline.");
      return;
    }
    addMsg("user", text);
    inputEl.value = "";
    runFullPipeline(text);
  });
  clearBtn.addEventListener("click", clearChat);
  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      send();
    }
  });

  renderTools();
  renderSamples();
  clearChat();
})();
