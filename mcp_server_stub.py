#!/usr/bin/env python3
"""Optional MCP-shaped JSON-RPC stub over Streamable-ish HTTP (stdlib only).

This is NOT a full MCP SDK server. It exposes the same four BriefBot tools via
a tiny HTTP endpoint so judges/demo can see tool discovery + calls without
pip-installing `mcp` / FastMCP (keeps zero-spend / offline).

Endpoints:
  GET  /health
  GET  /tools          -> tool list (MCP-like)
  POST /mcp            -> JSON-RPC: tools/list | tools/call

For a real FastMCP Streamable HTTP server later (still free/local):
  pip install mcp uvicorn
  # then swap this stub — do not require AWS credits.
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))

from briefbot_tools import TOOL_SPECS, dispatch  # noqa: E402


def _tools_list() -> list[dict[str, Any]]:
    out = []
    for t in TOOL_SPECS:
        out.append(
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["parameters"],
            }
        )
    return out


def _handle_rpc(body: dict[str, Any]) -> dict[str, Any]:
    method = body.get("method")
    req_id = body.get("id")
    params = body.get("params") or {}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": _tools_list()}}
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        result = dispatch(name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                "structuredContent": result,
                "isError": not result.get("ok", False),
            },
        }
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-11-25",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "briefbot", "version": "0.1.0"},
            },
        }
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: Any, content_type: str = "application/json") -> None:
        data = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, {"ok": True, "service": "briefbot-mcp-stub"})
            return
        if path == "/tools":
            self._send(200, {"tools": _tools_list()})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid json"})
            return
        if path in ("/mcp", "/"):
            self._send(200, _handle_rpc(body))
            return
        self._send(404, {"error": "not found"})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"BriefBot MCP stub on http://127.0.0.1:{port}", flush=True)
    print("  GET  /health  /tools", flush=True)
    print("  POST /mcp     JSON-RPC tools/list | tools/call | initialize", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
