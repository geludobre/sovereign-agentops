#!/usr/bin/env python3
"""
Minimal MCP (Model Context Protocol) Demo Server — Community Edition

Provides 6 demonstration tools that illustrate the governed-agent concept:
    demo_policy_check   — simulated command policy enforcement
    demo_receipt_sign   — Ed25519-style execution receipt signing
    demo_receipt_verify — receipt signature verification
    demo_model_route    — local model routing (ollama / lm-studio)
    demo_workspace_jail — workspace path confinement check
    demo_audit_log      — simulated audit-log replay

Protocol: JSON-RPC 2.0 over stdin/stdout (one JSON object per line).
No external dependencies — Python 3.10+ stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Minimal Ed25519-style signing (demonstration only — NOT production crypto)
# ---------------------------------------------------------------------------

_SIGNING_KEY = hashlib.sha256(b"demo-community-edition-seed-2026").hexdigest()[:64]


def _demo_sign(payload: Dict[str, Any]) -> str:
    """Return a deterministic hex signature over the canonical JSON of *payload*."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(
        hashlib.sha256(canonical.encode()).hexdigest().encode()
        + _SIGNING_KEY.encode()
    ).hexdigest()


def _demo_verify(signature: str, payload: Dict[str, Any]) -> bool:
    """Return *True* if *signature* matches *payload* under the demo key."""
    return _demo_sign(payload) == signature


# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------

@dataclass
class Tool:
    """Descriptor for a single MCP tool."""

    name: str
    description: str
    parameters: Dict[str, Any]
    handler: callable

    def definition(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.parameters,
        }


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

# -- Simulated audit log (appended by demo_receipt_sign) ----------------
_audit_log: List[Dict[str, Any]] = []

_DANGEROUS_PATTERNS = (
    "sudo", "rm -rf /", "mkfs.", ":(){ :|:& };:",  # fork bomb
    "> /dev/sda", "dd if=", "chmod 777 /",
)

_BLOCKED_COMMANDS_PREFIXES = (
    "sudo", "su ", "chown", "chmod 777", "passwd",
    "/etc/shadow", "reboot", "shutdown", "init ",
)


def _run_policy_check(command: str, path: str) -> Dict[str, Any]:
    """Simulate policy evaluation for *command* operating on *path*."""
    command_lower = command.strip().lower()

    for pattern in _DANGEROUS_PATTERNS:
        if pattern in command_lower:
            return {
                "allowed": False,
                "reason": f"Command contains dangerous pattern: {pattern!r}",
                "command": command,
                "path": path,
            }

    for prefix in _BLOCKED_COMMANDS_PREFIXES:
        if command_lower.startswith(prefix):
            return {
                "allowed": False,
                "reason": f"Command prefix {prefix!r} is blocked by policy",
                "command": command,
                "path": path,
            }

    if ".." in path.split("/"):
        return {
            "allowed": False,
            "reason": "Path traversal detected (contains '..')",
            "command": command,
            "path": path,
        }

    return {
        "allowed": True,
        "reason": "Command and path pass all policy checks",
        "command": command,
        "path": path,
    }


def _run_receipt_sign(action: str, target: str) -> Dict[str, Any]:
    """Create a signed execution receipt for *action* on *target*."""
    receipt: Dict[str, Any] = {
        "receipt_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "action": action,
        "target": target,
        "status": "simulated",
    }
    receipt["signature"] = _demo_sign(receipt)

    # Append to the in-memory audit log.
    _audit_log.append(dict(receipt))

    return {"receipt": receipt, "signed": True}


def _run_receipt_verify(receipt_json: str) -> Dict[str, Any]:
    """Parse and verify a signed receipt from its JSON representation."""
    try:
        data = json.loads(receipt_json)
    except json.JSONDecodeError as exc:
        return {"valid": False, "error": f"Invalid JSON: {exc}"}

    signature = data.pop("signature", None)
    if signature is None:
        return {"valid": False, "error": "No 'signature' field in receipt"}

    is_valid = _demo_verify(signature, data)
    return {
        "valid": is_valid,
        "parsed": data,
        "signature": signature,
    }


def _run_model_route(prompt: str, provider: str) -> Dict[str, Any]:
    """Determine which local model endpoint would handle *prompt*."""
    prompt_lower = prompt.lower()
    model_map = {
        "ollama": {
            "endpoint": "http://localhost:11434/api/generate",
            "model": "llama3.1:latest",
        },
        "lm-studio": {
            "endpoint": "http://localhost:1234/v1/chat/completions",
            "model": "gemma-4-12b-it",
        },
    }

    cfg = model_map.get(provider)
    if cfg is None:
        return {
            "error": f"Unknown provider {provider!r}; expected ollama or lm-studio",
        }

    # Simulate a trivial routing heuristic.
    if len(prompt_lower.split()) > 50:
        routed_model = f"{cfg['model']}-longctx"
    elif any(kw in prompt_lower for kw in ("analyze", "audit", "explain", "review")):
        routed_model = f"{cfg['model']}-reasoning"
    else:
        routed_model = cfg["model"]

    return {
        "provider": provider,
        "endpoint": cfg["endpoint"],
        "base_model": cfg["model"],
        "routed_model": routed_model,
        "prompt_preview": prompt[:80] + ("…" if len(prompt) > 80 else ""),
    }


def _run_workspace_jail(path: str, allowed_root: str) -> Dict[str, Any]:
    """Check whether *path* is confined beneath *allowed_root*."""
    import os.path

    abs_path = os.path.abspath(os.path.expanduser(path))
    abs_root = os.path.abspath(os.path.expanduser(allowed_root))

    # The path must be a child (or the same as) the allowed root.
    # Normalise both so trailing slashes don't cause false negatives.
    norm_path = os.path.normpath(abs_path)
    norm_root = os.path.normpath(abs_root)

    if norm_path == norm_root or norm_path.startswith(norm_root + "/"):
        return {
            "allowed": True,
            "resolved_path": norm_path,
            "allowed_root": norm_root,
            "reason": "Path is within the workspace jail",
        }

    return {
        "allowed": False,
        "resolved_path": norm_path,
        "allowed_root": norm_root,
        "reason": "Path escapes the workspace jail",
    }


def _run_audit_log(limit: int) -> Dict[str, Any]:
    """Return the *limit* most recent entries from the in-memory audit log."""
    entries = list(reversed(_audit_log))[:limit]
    return {
        "entries": entries,
        "total_logged": len(_audit_log),
        "returned": len(entries),
    }


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

TOOLS: List[Tool] = [
    Tool(
        name="demo_policy_check",
        description=(
            "Simulate policy enforcement: evaluate whether a command operating "
            "on a given file path would be allowed or blocked, with a reason."
        ),
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to evaluate",
                },
                "path": {
                    "type": "string",
                    "description": "Target file path",
                },
            },
            "required": ["command", "path"],
        },
        handler=_run_policy_check,
    ),
    Tool(
        name="demo_receipt_sign",
        description=(
            "Create and sign an execution receipt for a simulated action. "
            "The receipt is recorded in the in-memory audit log."
        ),
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action performed (e.g. 'deploy', 'delete')",
                },
                "target": {
                    "type": "string",
                    "description": "Target of the action (e.g. 'service-x')",
                },
            },
            "required": ["action", "target"],
        },
        handler=_run_receipt_sign,
    ),
    Tool(
        name="demo_receipt_verify",
        description=(
            "Verify the Ed25519-style signature on a previously signed "
            "execution receipt. Supply the receipt as a JSON string."
        ),
        parameters={
            "type": "object",
            "properties": {
                "receipt_json": {
                    "type": "string",
                    "description": "Full receipt JSON (including the 'signature' field)",
                },
            },
            "required": ["receipt_json"],
        },
        handler=_run_receipt_verify,
    ),
    Tool(
        name="demo_model_route",
        description=(
            "Check which local LLM endpoint and model would handle a prompt "
            "under the current routing configuration."
        ),
        parameters={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Prompt text to route",
                },
                "provider": {
                    "type": "string",
                    "enum": ["ollama", "lm-studio"],
                    "description": "Target inference provider",
                },
            },
            "required": ["prompt", "provider"],
        },
        handler=_run_model_route,
    ),
    Tool(
        name="demo_workspace_jail",
        description=(
            "Verify that a file path is confined beneath a specified workspace "
            "root directory (path-jail enforcement)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to check",
                },
                "allowed_root": {
                    "type": "string",
                    "description": "Allowed workspace root directory",
                },
            },
            "required": ["path", "allowed_root"],
        },
        handler=_run_workspace_jail,
    ),
    Tool(
        name="demo_audit_log",
        description=(
            "Return recent entries from the in-memory audit log. "
            "Entries are added by demo_receipt_sign."
        ),
        parameters={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum number of entries to return",
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": [],
        },
        handler=_run_audit_log,
    ),
]

_TOOL_MAP: Dict[str, Tool] = {t.name: t for t in TOOLS}


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 helpers
# ---------------------------------------------------------------------------

def _json_rpc_error(
    req_id: Optional[Any], code: int, message: str, data: Any = None
) -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 error response."""
    err: Dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }
    if data is not None:
        err["error"]["data"] = data
    return err


def _json_rpc_result(req_id: Optional[Any], result: Any) -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 success response."""
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


# ---------------------------------------------------------------------------
# Request dispatcher
# ---------------------------------------------------------------------------

def _handle_request(req: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a single JSON-RPC request and return the response."""
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "tools/list":
        return _json_rpc_result(req_id, {"tools": [t.definition() for t in TOOLS]})

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        tool = _TOOL_MAP.get(tool_name)
        if tool is None:
            return _json_rpc_error(
                req_id, -32601, f"Tool not found: {tool_name!r}",
            )

        # Validate required parameters.
        required = tool.parameters.get("required", [])
        missing = [k for k in required if k not in arguments]
        if missing:
            return _json_rpc_error(
                req_id,
                -32602,
                f"Missing required parameter(s): {', '.join(missing)}",
            )

        # Provide defaults for optional parameters.
        properties = tool.parameters.get("properties", {})
        for pname, pschema in properties.items():
            if pname not in arguments and "default" in pschema:
                arguments[pname] = pschema["default"]

        try:
            result = tool.handler(**arguments)
        except Exception as exc:
            return _json_rpc_error(
                req_id, -32603, f"Tool execution error: {exc}",
            )

        return _json_rpc_result(
            req_id,
            {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
        )

    return _json_rpc_error(req_id, -32601, f"Method not found: {method!r}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Read JSON-RPC requests from stdin and write responses to stdout.

    The server logs diagnostic messages to stderr so they do not corrupt
    the JSON-line protocol on stdout.
    """
    # Signal readiness (stderr avoids polluting the protocol stream).
    tool_names = ", ".join(t.name for t in TOOLS)
    print(f"[demo-mcp] ready — {len(TOOLS)} tool(s): {tool_names}", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response = _json_rpc_error(
                None, -32700, f"Parse error: {exc}",
            )
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        # Support batch requests (list of requests).
        if isinstance(request, list):
            response = [_handle_request(req) for req in request]
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        response = _handle_request(request)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
