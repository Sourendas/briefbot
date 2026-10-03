#!/usr/bin/env python3
"""BriefBot CLI — offline tool runner (stdlib only).

Examples:
  python3 cli.py pipeline "Need Zapier + Sheets automation for inventory"
  python3 cli.py parse -f samples/inventory_brief.txt
  python3 cli.py tools
  python3 cli.py serve-sim   # static file server for sim/ (port 8765)
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))

from briefbot_tools import (  # noqa: E402
    TOOL_SPECS,
    ask_clarifiers,
    dispatch,
    draft_proposal,
    list_risks,
    parse_brief,
    run_pipeline,
)


def _read_text(args: argparse.Namespace) -> str:
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if args.text:
        return args.text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("Provide brief text, --file, or stdin")


def cmd_tools(_: argparse.Namespace) -> None:
    print(json.dumps(TOOL_SPECS, indent=2))


def cmd_parse(args: argparse.Namespace) -> None:
    print(json.dumps(parse_brief(_read_text(args)), indent=2))


def cmd_proposal(args: argparse.Namespace) -> None:
    print(json.dumps(draft_proposal(brief_text=_read_text(args)), indent=2))


def cmd_risks(args: argparse.Namespace) -> None:
    print(json.dumps(list_risks(brief_text=_read_text(args)), indent=2))


def cmd_clarifiers(args: argparse.Namespace) -> None:
    print(json.dumps(ask_clarifiers(brief_text=_read_text(args)), indent=2))


def cmd_pipeline(args: argparse.Namespace) -> None:
    print(json.dumps(run_pipeline(_read_text(args)), indent=2))


def cmd_dispatch(args: argparse.Namespace) -> None:
    raw = args.args_json or "{}"
    try:
        arguments = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON for --args: {e}") from e
    print(json.dumps(dispatch(args.tool_name, arguments), indent=2))


def cmd_serve_sim(args: argparse.Namespace) -> None:
    port = args.port
    # Serve contest root so ../tools works from sim/index.html

    class RootHandler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(ROOT), **kw)

        def log_message(self, fmt: str, *log_args) -> None:
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % log_args))

    httpd = ThreadingHTTPServer(("127.0.0.1", port), RootHandler)
    url = f"http://127.0.0.1:{port}/sim/"
    print(f"BriefBot sim at {url}", flush=True)
    print("Ctrl+C to stop.", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def main() -> None:
    p = argparse.ArgumentParser(description="BriefBot offline CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("tools", help="List tool specs").set_defaults(func=cmd_tools)

    def add_text_args(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("text", nargs="?", help="Brief text")
        sp.add_argument("-f", "--file", help="Read brief from file")

    for name, func, help_ in [
        ("parse", cmd_parse, "parse_brief"),
        ("proposal", cmd_proposal, "draft_proposal"),
        ("risks", cmd_risks, "list_risks"),
        ("clarifiers", cmd_clarifiers, "ask_clarifiers"),
        ("pipeline", cmd_pipeline, "Full parse→proposal pipeline"),
    ]:
        sp = sub.add_parser(name, help=help_)
        add_text_args(sp)
        sp.set_defaults(func=func)

    spd = sub.add_parser("dispatch", help="Dispatch tool by name")
    spd.add_argument("tool_name")
    spd.add_argument("--args", dest="args_json", default="{}", help="JSON object of arguments")
    spd.set_defaults(func=cmd_dispatch)

    sps = sub.add_parser("serve-sim", help="Serve web sim on localhost")
    sps.add_argument("--port", type=int, default=8765)
    sps.set_defaults(func=cmd_serve_sim)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
