# Demo MCP Tools — Community Edition

Seven demonstration tools illustrating the governed-agent execution concept
from the Autonomous Digital Organization Platform.

| Tool | Purpose |
|------|---------|
| `demo_policy_check` | Simulate command policy enforcement |
| `demo_receipt_sign` | Sign an execution receipt (real Ed25519) |
| `demo_receipt_verify` | Verify a receipt Ed25519 signature |
| `demo_model_route` | Check local LLM routing |
| `demo_workspace_jail` | Verify workspace path confinement |
| `demo_audit_log` | Return signed audit-log entries |
| `demo_server_info` | Server metadata: version, public key, crypto |

## Run

```bash
python3 mcp_server.py
```

The server listens on stdin/stdout using the JSON-RPC 2.0 line protocol.
Connect from any MCP-compatible client. See the [MCP specification](https://modelcontextprotocol.io)
for client configuration details.

## Dependencies

- `cryptography>=41.0.0` (Ed25519 signing — RFC 8032)

The server generates a fresh Ed25519 keypair on first run and stores the
private key at `~/.config/agentops/ed25519_private.key` (permissions 0o400).
Every signed receipt includes the public key for external verification.
