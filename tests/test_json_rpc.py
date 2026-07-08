"""Tests for the JSON-RPC 2.0 protocol layer of the MCP server."""
import json

from tools import mcp_server
from tools.mcp_server import _handle_request, _json_rpc_error, _json_rpc_result


class TestJsonRpcHelpers:
    def test_result_format(self):
        resp = _json_rpc_result(42, {"ok": True})
        assert resp == {"jsonrpc": "2.0", "id": 42, "result": {"ok": True}}

    def test_error_format(self):
        resp = _json_rpc_error(1, -32601, "Not found")
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 1
        assert resp["error"]["code"] == -32601
        assert resp["error"]["message"] == "Not found"

    def test_error_with_data(self):
        resp = _json_rpc_error(None, -1, "msg", {"detail": "x"})
        assert resp["error"]["data"] == {"detail": "x"}


class TestJsonRpcDispatch:
    def test_list_tools(self):
        resp = _handle_request({"id": 1, "method": "tools/list", "params": {}})
        assert "result" in resp
        assert "tools" in resp["result"]
        tool_names = [t["name"] for t in resp["result"]["tools"]]
        assert "demo_policy_check" in tool_names
        assert "demo_receipt_sign" in tool_names
        assert "demo_server_info" in tool_names

    def test_tools_call_unknown_tool(self):
        resp = _handle_request({
            "id": 1,
            "method": "tools/call",
            "params": {"name": "nonexistent", "arguments": {}},
        })
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_tools_call_missing_required(self):
        resp = _handle_request({
            "id": 1,
            "method": "tools/call",
            "params": {"name": "demo_policy_check", "arguments": {}},
        })
        assert "error" in resp
        assert resp["error"]["code"] == -32602
        assert "Missing required" in resp["error"]["message"]

    def test_unknown_method(self):
        resp = _handle_request({"id": 1, "method": "unknown", "params": {}})
        assert "error" in resp
        assert "Method not found" in resp["error"]["message"]

    def test_tools_call_valid(self):
        resp = _handle_request({
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "demo_policy_check",
                "arguments": {"command": "git push", "path": "/workspace"},
            },
        })
        assert "result" in resp
        result_data = json.loads(resp["result"]["content"][0]["text"])
        assert result_data["allowed"] is True

    def test_batch_request(self):
        resp = _handle_request([
            {"id": 1, "method": "tools/list", "params": {}},
            {"id": 2, "method": "unknown", "params": {}},
        ])
        assert isinstance(resp, list)
        assert len(resp) == 2
        assert "result" in resp[0]
        assert "error" in resp[1]
