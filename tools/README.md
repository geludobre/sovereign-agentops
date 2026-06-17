# Demo MCP Tools — Community Edition

Six demonstration tools illustrating the governed-agent execution concept
from the Sovereign AgentOps platform.

| Tool | Purpose |
|------|---------|
| `demo_policy_check` | Simulate command policy enforcement |
| `demo_receipt_sign` | Sign an execution receipt (Ed25519-style) |
| `demo_receipt_verify` | Verify a receipt signature |
| `demo_model_route` | Check local LLM routing |
| `demo_workspace_jail` | Verify workspace path confinement |
| `demo_audit_log` | Return simulated audit-log entries |

## Run

```bash
python3 mcp-server.py
```

The server listens on stdin/stdout using the JSON-RPC 2.0 line protocol.
Connect from any MCP-compatible client. See the [MCP specification](https://modelcontextprotocol.io)
for client configuration details.

## No Dependencies

Python 3.10+ stdlib only — no pip install required.
