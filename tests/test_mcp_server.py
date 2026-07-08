"""Tests for the Sovereign AgentOps Community Edition MCP governance server."""
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from tools import mcp_server


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolated_key_dir():
    """Use a temp key directory so tests don't clobber the real key."""
    tmp = Path(tempfile.mkdtemp())
    with patch("tools.mcp_server._KEY_DIR", tmp):
        with patch("tools.mcp_server._KEY_FILE", tmp / "ed25519_private.key"):
            # Re-initialize the module-level key with a fresh one
            mcp_server._PRIV_KEY = mcp_server._load_or_generate_key(tmp / "ed25519_private.key")
            mcp_server._PUB_KEY = mcp_server._PRIV_KEY.public_key()
            mcp_server._PUB_KEY_HEX = mcp_server._PUB_KEY.public_bytes_raw().hex()
            # Clear audit log
            mcp_server._audit_log.clear()
            yield
    shutil.rmtree(tmp, ignore_errors=True)


def call_tool(tool_name: str, **kwargs) -> dict:
    """Helper: invoke an MCP tool handler directly and return the result dict."""
    tool = mcp_server._TOOL_MAP.get(tool_name)
    assert tool is not None, f"Tool {tool_name!r} not found"
    return tool.handler(**kwargs)


# ---------------------------------------------------------------------------
# Server info
# ---------------------------------------------------------------------------

def test_server_info():
    result = call_tool("demo_server_info")
    assert result["version"] == "2.0.0"
    assert result["edition"] == "community"
    assert len(result["public_key_hex"]) == 64  # 32 bytes = 64 hex chars


# ---------------------------------------------------------------------------
# Server info (no-arg handler with lambda)
# ---------------------------------------------------------------------------

def test_server_info_keys():
    result = call_tool("demo_server_info")
    assert "public_key_hex" in result
    assert "key_path" in result


# ---------------------------------------------------------------------------
# Policy check
# ---------------------------------------------------------------------------

def test_policy_check_allowed():
    result = call_tool("demo_policy_check", command="git push origin main", path="/workspace/repo")
    assert result["allowed"] is True
    assert "pass all policy checks" in result["reason"]


def test_policy_check_blocked_sudo():
    result = call_tool("demo_policy_check", command="sudo rm -rf /etc", path="/etc")
    assert result["allowed"] is False
    assert "sudo" in result["reason"].lower()


def test_policy_check_blocked_rm_rf():
    result = call_tool("demo_policy_check", command="rm -rf /", path="/")
    assert result["allowed"] is False
    assert "rm -rf /" in result["reason"]


def test_policy_check_path_traversal():
    result = call_tool("demo_policy_check", command="cat", path="/workspace/../../etc/shadow")
    assert result["allowed"] is False
    assert "traversal" in result["reason"].lower()


def test_policy_check_fork_bomb():
    result = call_tool("demo_policy_check", command=":(){ :|:& };:", path="/tmp")
    assert result["allowed"] is False
    assert "dangerous" in result["reason"].lower()


# ---------------------------------------------------------------------------
# Receipt signing
# ---------------------------------------------------------------------------

def test_receipt_sign_returns_signed():
    result = call_tool("demo_receipt_sign", action="deploy", target="web-app")

    assert result["signed"] is True
    assert "receipt" in result
    assert "public_key_hex" in result

    receipt = result["receipt"]
    assert receipt["schema_version"] == "1.0"
    assert receipt["action"] == "deploy"
    assert receipt["target"] == "web-app"
    assert "signature" in receipt
    assert receipt["workspace_id"] == "community-demo"


def test_receipt_sign_adds_to_audit_log():
    mcp_server._audit_log.clear()
    call_tool("demo_receipt_sign", action="test", target="audit-entry")

    log_result = call_tool("demo_audit_log", limit=10)
    assert log_result["total_logged"] >= 1
    assert any(e["action"] == "test" and e["target"] == "audit-entry" for e in log_result["entries"])


# ---------------------------------------------------------------------------
# Receipt verification
# ---------------------------------------------------------------------------

def test_receipt_verify_valid():
    signed = call_tool("demo_receipt_sign", action="verify-me", target="test")
    receipt_json = json.dumps(signed["receipt"])

    result = call_tool("demo_receipt_verify", receipt_json=receipt_json)
    assert result["valid"] is True
    assert result["public_key_hex"] == mcp_server._PUB_KEY_HEX
    assert result["parsed"]["action"] == "verify-me"


def test_receipt_verify_invalid_signature():
    receipt = {
        "action": "deploy",
        "target": "hacked",
        "signature": "00" * 64,  # junk signature
    }
    result = call_tool("demo_receipt_verify", receipt_json=json.dumps(receipt))
    assert result["valid"] is False


def test_receipt_verify_tampered():
    signed = call_tool("demo_receipt_sign", action="no-tamper", target="test")
    receipt = signed["receipt"]
    receipt["target"] = "tampered"  # change after signing

    result = call_tool("demo_receipt_verify", receipt_json=json.dumps(receipt))
    assert result["valid"] is False


def test_receipt_verify_no_signature():
    receipt = {"action": "deploy", "target": "test"}
    result = call_tool("demo_receipt_verify", receipt_json=json.dumps(receipt))
    assert result["valid"] is False
    assert "No 'signature'" in result["error"]


def test_receipt_verify_malformed_json():
    result = call_tool("demo_receipt_verify", receipt_json="not-json{{{")
    assert result["valid"] is False
    assert "Invalid JSON" in result["error"]


# ---------------------------------------------------------------------------
# Receipt sign produces valid receipt
# ---------------------------------------------------------------------------

def test_signed_receipt_self_verify():
    """A receipt signed by demo_receipt_sign must pass demo_receipt_verify."""
    signed = call_tool("demo_receipt_sign", action="self-test", target="verify")
    receipt_json = json.dumps(signed["receipt"])

    verified = call_tool("demo_receipt_verify", receipt_json=receipt_json)
    assert verified["valid"] is True


# ---------------------------------------------------------------------------
# Model routing
# ---------------------------------------------------------------------------

def test_model_route_ollama():
    result = call_tool("demo_model_route", prompt="Hello world", provider="ollama")
    assert result["provider"] == "ollama"
    assert "localhost:11434" in result["endpoint"]
    assert "llama3.1" in result["base_model"]


def test_model_route_lm_studio():
    result = call_tool("demo_model_route", prompt="Hello world", provider="lm-studio")
    assert result["provider"] == "lm-studio"
    assert "localhost:1234" in result["endpoint"]


def test_model_route_long_prompt():
    long_prompt = "word " * 60
    result = call_tool("demo_model_route", prompt=long_prompt, provider="ollama")
    assert "longctx" in result["routed_model"]


def test_model_route_reasoning_keyword():
    result = call_tool("demo_model_route", prompt="analyze the security audit log", provider="ollama")
    assert "reasoning" in result["routed_model"]


def test_model_route_unknown_provider():
    result = call_tool("demo_model_route", prompt="test", provider="nonexistent")
    assert "error" in result


# ---------------------------------------------------------------------------
# Workspace jail
# ---------------------------------------------------------------------------

def test_workspace_jail_allowed():
    result = call_tool("demo_workspace_jail", path="/workspace/project/src", allowed_root="/workspace")
    assert result["allowed"] is True


def test_workspace_jail_blocked_escape():
    result = call_tool("demo_workspace_jail", path="/etc/shadow", allowed_root="/workspace")
    assert result["allowed"] is False
    assert "escapes" in result["reason"].lower()


def test_workspace_jail_exact_root():
    result = call_tool("demo_workspace_jail", path="/workspace", allowed_root="/workspace")
    assert result["allowed"] is True


def test_workspace_jail_home_expansion():
    result = call_tool("demo_workspace_jail", path="~/test", allowed_root="/home")
    # ~/ expands to /home/dobre/ on this system, which starts with /home
    assert result["allowed"] is True
    assert result["resolved_path"].startswith("/home/")


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def test_audit_log_empty():
    mcp_server._audit_log.clear()
    result = call_tool("demo_audit_log", limit=5)
    assert result["total_logged"] == 0
    assert result["returned"] == 0
    assert result["entries"] == []


def test_audit_log_returns_limit():
    mcp_server._audit_log.clear()
    for i in range(10):
        mcp_server._audit_log.append({"id": i, "msg": f"entry-{i}"})

    result = call_tool("demo_audit_log", limit=3)
    assert result["returned"] == 3
    assert result["total_logged"] == 10
    # Most recent first (reversed)
    assert result["entries"][0]["id"] == 9


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

def test_tool_registry_has_expected_tools():
    expected = {
        "demo_policy_check",
        "demo_receipt_sign",
        "demo_receipt_verify",
        "demo_model_route",
        "demo_workspace_jail",
        "demo_audit_log",
        "demo_server_info",
    }
    registered = set(mcp_server._TOOL_MAP.keys())
    assert expected.issubset(registered), f"Missing: {expected - registered}"


def test_tool_definitions_have_valid_schema():
    for tool in mcp_server.TOOLS:
        defn = tool.definition()
        assert defn["name"]
        assert defn["description"]
        assert "inputSchema" in defn
        schema = defn["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema
