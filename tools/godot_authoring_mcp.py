#!/usr/bin/env python3
"""Dependency-free MCP stdio transport for the same ARCONT authoring API.

Connect one local MCP client. The project adapter remains the only engine writer.
No LLM endpoint or credentials are embedded. stdout contains JSON-RPC only.
"""
import argparse
import json
import sys

if __package__:
    from .godot_authoring_control import OPERATIONS, respond
    from .map_forge_control import decode
else:
    from godot_authoring_control import OPERATIONS, respond
    from map_forge_control import decode

SUPPORTED_PROTOCOLS = ("2024-11-05", "2025-03-26", "2025-06-18")
SCHEMA = {"type": "object", "required": ["protocol_version", "operation"],
          "properties": {"protocol_version": {"const": 1}, "operation": {"enum": list(OPERATIONS)},
                         "document_id": {"type": "string"}, "if_revision": {"type": "string"},
                         "restore_revision": {"type": "string"}, "dry_run": {"type": "boolean", "default": True},
                         "recipe": {"type": "object"}, "patch": {"type": "array"}, "options": {"type": "object"},
                         "scene": {"type": "string"}, "session": {"type": "object"}},
          "additionalProperties": False}


def dispatch(project, message):
    identifier = message.get("id")
    method = message.get("method")
    if identifier is None:
        return None
    if method == "initialize":
        requested = message.get("params", {}).get("protocolVersion")
        result = {"protocolVersion": requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[-1],
                  "capabilities": {"tools": {}}, "serverInfo": {"name": "arcont-godot-authoring", "version": "1.0.0"}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [{"name": "arcont_authoring", "description": "Discover and operate project Godot APIs; author, build, capture, inspect and restore revisions. Playtest accepted scene artifacts through bounded input sessions; inspect both ok and passed. Run capabilities/discover first.", "inputSchema": SCHEMA}]}
    elif method == "tools/call":
        params = message.get("params", {})
        if params.get("name") != "arcont_authoring":
            return {"jsonrpc": "2.0", "id": identifier, "error": {"code": -32602, "message": "unknown tool"}}
        response = respond(project, params.get("arguments"))
        result = {"content": [{"type": "text", "text": json.dumps(response, ensure_ascii=False)}],
                  "isError": not response.get("ok", False)}
    else:
        return {"jsonrpc": "2.0", "id": identifier, "error": {"code": -32601, "message": "method not found"}}
    return {"jsonrpc": "2.0", "id": identifier, "result": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    for line in sys.stdin:
        try:
            message = decode(line)
            if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
                raise ValueError("invalid JSON-RPC request")
            response = dispatch(args.project, message)
        except (ValueError, TypeError, AttributeError) as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
