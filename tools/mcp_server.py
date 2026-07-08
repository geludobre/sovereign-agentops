#!/usr/bin/env python3
"""
Standalone MCP (Model Context Protocol) Governance Server — Community Edition

Provides 6 tools that demonstrate runtime-agnostic governed agent execution:

    demo_policy_check   — real policy enforcement with allow/block/detect
    demo_receipt_sign   — Ed25519-signed execution receipts (real crypto)
    demo_receipt_verify — receipt signature verification
    demo_model_route    — local model routing (ollama / lm-studio)
    demo_workspace_jail — workspace path confinement check
    demo_audit_log      — signed audit-log replay from memory

Protocol: JSON-RPC 2.0 over stdin/stdout (one JSON object per line).
Requires: cryptography>=41.0.0  (pip install cryptography)
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Ed25519 signing (real crypto, not demo)
# ---------------------------------------------------------------------------

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
except ImportError:
    print(
        "Error: 'cryptography' package required.\n"
        "  pip install cryptography>=41.0.0",
        file=sys.stderr,
    )
    sys.exit(1)


def _canonical(obj: Dict[str, Any]) -> bytes:
    """Deterministic JSON — sorted keys, no whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def _load_or_generate_key(key_path: Path) -> Ed25519PrivateKey:
    """Load an existing Ed25519 private key or generate + persist a new one."""
    if key_path.exists():
        raw = key_path.read_bytes()
        if len(raw) == 64:
            return Ed25519PrivateKey.from_private_bytes(raw)
        if len(raw) == 32:
            # Seed-only format (32 bytes) — expand on load.
            return Ed25519PrivateKey.from_private_bytes(raw)
        raise ValueError(f"Invalid key file: {key_path} ({len(raw)} bytes)")

    key_path.parent.mkdir(parents=True, exist_ok=True)
    priv = Ed25519PrivateKey.generate()
    key_path.write_bytes(priv.private_bytes_raw())
    key_path.chmod(0o400)  # keep permissions tight
    return priv


# Key file path — use AGENTOPS_KEY_DIR env var or default
_KEY_DIR = Path(os.environ.get("AGENTOPS_KEY_DIR", Path.home() / ".config" / "agentops"))
_KEY_FILE = _KEY_DIR / "ed25519_private.key"
_PRIV_KEY: Ed25519PrivateKey = _load_or_generate_key(_KEY_FILE)
_PUB_KEY: Ed25519PublicKey = _PRIV_KEY.public_key()
_PUB_KEY_HEX: str = _PUB_KEY.public_bytes_raw().hex()


def _sign(payload: Dict[str, Any]) -> str:
    """Return an Ed25519 signature over the canonical JSON of *payload*.

    Returns a hex-encoded 64-byte Ed25519 signature.
    """
    return _PRIV_KEY.sign(_canonical(payload)).hex()


def _verify(signature: str, payload: Dict[str, Any]) -> bool:
    """Return *True* if *signature* matches *payload* under the server's key."""
    sig_bytes = bytes.fromhex(signature)
    if len(sig_bytes) != 64:
        return False
    try:
        _PUB_KEY.verify(sig_bytes, _canonical(payload))
        return True
    except Exception:
        return False


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

# -- In-memory signed audit log ---------------------------------------------
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
    """Evaluate whether *command* operating on *path* is allowed by policy."""
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
    """Create an Ed25519-signed execution receipt for *action* on *target*."""
    receipt: Dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": str(uuid.uuid4()),
        "workspace_id": "community-demo",
        "actor": "community-user",
        "agent_runtime": "direct-mcp",
        "tool": "demo_receipt_sign",
        "action": action,
        "target": target,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "policy_decision": "signed",
    }

    # Ed25519 hex signature over the canonical receipt (without the signature field)
    sig_hex = _sign(receipt)
    receipt["signature"] = sig_hex

    # Append to in-memory audit log
    _audit_log.append(dict(receipt))

    return {
        "receipt": receipt,
        "signed": True,
        "public_key_hex": _PUB_KEY_HEX,
        "key_path": str(_KEY_FILE),
    }


def _run_receipt_verify(receipt_json: str) -> Dict[str, Any]:
    """Parse and Ed25519-verify a signed receipt from its JSON representation."""
    try:
        data = json.loads(receipt_json)
    except json.JSONDecodeError as exc:
        return {"valid": False, "error": f"Invalid JSON: {exc}"}

    signature = data.pop("signature", None)
    if signature is None:
        return {"valid": False, "error": "No 'signature' field in receipt"}
    if isinstance(signature, str) and signature.startswith("ed25519:"):
        # Support the ed25519:hex format used by the CLI verify tool
        signature = signature[8:]

    is_valid = _verify(signature, data)
    return {
        "valid": is_valid,
        "parsed": data,
        "signature_hex": signature,
        "public_key_hex": _PUB_KEY_HEX,
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

    # Trivial routing heuristic.
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
        "prompt_preview": prompt[:80] + ("\N{HORIZONTAL ELLIPSIS}" if len(prompt) > 80 else ""),
    }


def _run_workspace_jail(path: str, allowed_root: str) -> Dict[str, Any]:
    """Check whether *path* is confined beneath *allowed_root*."""
    abs_path = os.path.abspath(os.path.expanduser(path))
    abs_root = os.path.abspath(os.path.expanduser(allowed_root))

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


def _run_audit_log(limit: int = 5) -> Dict[str, Any]:
    """Return the *limit* most recent entries from the in-memory signed audit log."""
    entries = list(reversed(_audit_log))[:limit]
    return {
        "entries": entries,
        "total_logged": len(_audit_log),
        "returned": len(entries),
        "public_key_hex": _PUB_KEY_HEX,
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
            "Create and sign an execution receipt using Ed25519 (real crypto). "
            "The receipt is recorded in the in-memory audit log and includes "
            "the server's public key for external verification."
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
            "Verify the Ed25519 signature on a previously signed "
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
            "Return recent entries from the in-memory signed audit log. "
            "Entries are added by demo_receipt_sign and include Ed25519 "
            "signatures verifiable with the returned public key."
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
    Tool(
        name="demo_server_info",
        description=(
            "Return server metadata: version, public key, tool count, "
            "and key storage location."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=lambda: {
            "version": "2.0.0",
            "edition": "community",
            "tool_count": len(TOOLS),
            "public_key_hex": _PUB_KEY_HEX,
            "key_path": str(_KEY_FILE),
            "crypto": "Ed25519 (RFC 8032)",
            "protocol": "MCP JSON-RPC 2.0",
        },
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

def _handle_request(req: Any) -> Any:
    """Dispatch a JSON-RPC request and return the response.

    Accepts both single requests (dict) and batch requests (list).
    """
    if isinstance(req, list):
        return [_handle_request(r) for r in req]

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

    Diagnostic messages go to stderr so they do not corrupt the JSON-line
    protocol on stdout.
    """
    tool_names = ", ".join(t.name for t in TOOLS)
    print(
        f"[community-mcp] Ed25519 key: {_KEY_FILE}",
        file=sys.stderr,
    )
    print(
        f"[community-mcp] Public key: {_PUB_KEY_HEX[:16]}...{_PUB_KEY_HEX[-8:]}",
        file=sys.stderr,
    )
    print(
        f"[community-mcp] ready — {len(TOOLS)} tool(s): {tool_names}",
        file=sys.stderr,
    )

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
