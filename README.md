# Sovereign AgentOps — Community Edition

**Runtime-agnostic governed agent execution — demo and evaluation edition**

![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Version](https://img.shields.io/badge/version-2.0.0-lightgrey)
![Build](https://img.shields.io/badge/build-passing-brightgreen)

## What is this?

A standalone demonstration server for the **governed MCP execution layer** concept.
It provides 7 MCP tools that showcase policy enforcement, Ed25519-signed execution
receipts, workspace path jailing, and local model routing — with **real
cryptography**, not simulations.

The full **Enterprise platform** (98 MCP tools, 455+ endpoints, 91+ web UI tabs,
constitutional governance, service catalogue, compliance automation, fleet
command, agent-owned assets, digital twin simulation, and autonomous incident
resolution) is available under a commercial license.

## Quickstart

```bash
# 1. Install dependencies
pip install cryptography>=41.0.0

# 2. Run the MCP governance server (JSON-RPC over stdio)
python3 tools/mcp_server.py
```

In another terminal, send it commands:

```bash
# List available tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 tools/mcp_server.py

# Check if a command is allowed by policy
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"demo_policy_check","arguments":{"command":"git push origin main","path":"/workspace/repo"}}}' | python3 tools/mcp_server.py

# Sign an execution receipt with real Ed25519
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"demo_receipt_sign","arguments":{"action":"deploy","target":"web-app"}}}' | python3 tools/mcp_server.py
```

## Docker

```bash
docker compose up --build
```

The server runs in stdio mode inside the container. Send commands via stdin:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | docker exec -i agentops-demo python3 tools/mcp_server.py
```

## Tools

| Tool | Description |
|------|-------------|
| `demo_policy_check` | Evaluate whether a command + path is allowed/blocked by policy |
| `demo_receipt_sign` | Create an Ed25519-signed execution receipt |
| `demo_receipt_verify` | Verify a receipt's Ed25519 signature |
| `demo_model_route` | Show which local LLM endpoint would handle a prompt |
| `demo_workspace_jail` | Check whether a path is confined within a workspace root |
| `demo_audit_log` | Return recent entries from the in-memory signed audit log |
| `demo_server_info` | Server metadata: version, public key, crypto backend |

## Receipt Verification

Every signed receipt includes the server's Ed25519 public key. Use the included
CLI tool to verify:

```bash
# The server prints its public key on startup (stderr) and in every signed receipt
python3 cli/receipt-verify.py --verify path/to/receipt.json
```

The server generates a fresh Ed25519 keypair on first run, stored at
`~/.config/agentops/ed25519_private.key` (permissions `0o400`).

## Why Sovereign AgentOps?

Teams adopting AI coding agents in regulated environments need to control what
commands agents can run, audit every action with cryptographic proof, and operate
entirely offline. This community edition demonstrates the concept with real crypto
and real policy enforcement — the Enterprise platform delivers the full production
stack.

## Feature Comparison

| Feature | Community | Enterprise |
|---------|-----------|------------|
| Policy enforcement (allow/block/detect) | 7 demo tools | **Full production stack** |
| Ed25519-signed execution receipts | Yes | Yes |
| Receipt verification CLI | Yes | Yes |
| Workspace path jail | Demo | Full enforcement |
| Model routing heuristic | Demo | 15+ provider routing |
| Signed audit log | In-memory | SQLite hash-chain |
| **MCP tools** | 7 demo tools | **98 tools (93 static + 5 plugins)** |
| **Constitutional governance** | No | 6-layer (Cortex, Policy, Autonomy, Memory, Federation) |
| **Web UI** | No | 91+ tabs (Flask + SocketIO) |
| **PostgreSQL / Redis persistence** | No | Yes |
| **Agent orchestration** | No | Capability registry, message bus, DAG |
| **Service catalogue** | No | Auto-discovery, health, SLA |
| **Observability hub** | No | LLM tracing, SLOs, cost analytics |
| **Compliance automation (SOC2/HIPAA/PCI)** | No | Weighted scoring, PDF reports, SoD |
| **Fleet command** | No | Multi-instance, heartbeat, treaty-gated |
| **Agent-owned assets** | No | Token/data/compute/artifact/credential |
| **Digital twin simulator** | No | What-if analysis, scenario sim |
| **Autonomous incident resolution** | No | ML diagnosis, auto-resolve, pattern learning |
| **Self-negotiating treaties** | No | 6 treaty types, dual-signed |
| SSO (SAML/OIDC) | No | Yes |
| RBAC custom roles | No | Yes |
| High-availability cluster | No | Yes |
| Commercial license | Apache 2.0 | Enterprise EULA |

## Documentation

- [Architecture Overview](docs/architecture.md) — governance layer design
- [Security Model](docs/security-model.md) — defense-in-depth architecture
- [Contributing Guide](CONTRIBUTING.md) — how to contribute
- [Changelog](CHANGELOG.md) — release history

## License

Community Edition is open source under Apache 2.0 with an Enterprise Edition
exclusion clause. See [LICENSE.community](LICENSE.community) for details.

Enterprise Edition features require a commercial license from FinBridge.

---

Built on the MCP protocol. Governance, not lock-in.
