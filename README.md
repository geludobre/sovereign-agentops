# Sovereign AgentOps -- Community Edition

Runtime-agnostic governed agent execution for regulated engineering teams

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Version](https://img.shields.io/badge/version-1.1.0-lightgrey)

## Architecture

```
  +-------------------------------------------------------------+
  |                   AGENT RUNTIMES                            |
  |  +----------+  +---------+  +-----------+  +--------------+  |
  |  |Claude    |  |OpenCode |  |Direct MCP |  |Workflow      |  |
  |  |Code      |  |         |  |Clients    |  |Engine        |  |
  +----+--------+--+----+----+--+-----+-----+--+------+-------+--+
       |               |           |                |
       +-------+-------+----------+----------------+
               |        GOVERNANCE LAYER
  +------------v------------------------------------------+
  | MCP Protocol (60 tools)                               |
  | +------------------+  +-----------------------------+ |
  | | Policy Enforcer  |  | Execution Receipt Engine    | |
  | | (allow/block/    |  | (Ed25519-signed, hash-chain | |
  | |  jail/detect)    |  |  linked, SQLite-backed)     | |
  | +------------------+  +-----------------------------+ |
  +------------------------+------------------------------+
                           |
  +------------------------v------------------------------+
  |             SELF-HOSTED INFRASTRUCTURE                 |
  |  +--------+ +-------+ +-------+ +------+ +---------+  |
  |  |Postgres| |Redis  | |Ollama | |LM    | |Web UI   |  |
  |  |        | |       | |(local | |Studio| |(38 tabs,|  |
  |  |        | |       | | LLM)  | |(local| | SocketIO)|  |
  |  |        | |       | |      | | LLM) | |         |  |
  |  +--------+ +-------+ +-------+ +------+ +---------+  |
  |  +--------------------------------------------------+  |
  |  | Nginx Reverse Proxy (HTTPS, port 443)             |  |
  |  | Unified API Gateway (port 8080)                   |  |
  |  +--------------------------------------------------+  |
  +---------------------------------------------------------+
```

## Quickstart

```bash
# 1. Start all services
docker compose up -d

# 2. Verify the control plane is running
curl https://localhost/api/health

# 3. Apply a governance policy -- block dangerous commands
curl -X POST https://localhost/api/policy \
  -H "Content-Type: application/json" \
  -d '{"action": "block", "pattern": "sudo", "scope": "global"}'

# 4. Run a command through the governed layer --
#    the policy enforcer intercepts and blocks it automatically.

# 5. Verify an execution receipt
curl https://localhost/api/receipts/verify \
  -H "Content-Type: application/json" \
  -d '{"receipt_id": "<receipt-id-from-last-execution>"}'
```

## Why Sovereign AgentOps?

Teams adopting AI coding agents in regulated environments face a fundamental gap: every major agent platform assumes cloud-managed execution with opaque governance. When you need to control what commands agents can run, audit every action with cryptographic proof, and operate entirely offline, the cloud-first model breaks down.

Sovereign AgentOps fills that gap by providing:

- **Runtime-agnostic governance.** Policy enforcement and signed receipts work identically whether agents run via Claude Code, OpenCode, a direct MCP client, or a batch workflow engine. No runtime is privileged.
- **Local-first infrastructure.** PostgreSQL, Redis, local LLMs (Ollama, LM Studio), and the web control panel all run on your hardware. No data leaves your network.
- **Cryptographic audit.** Every agent action produces an Ed25519-signed receipt in a hash-chain, forming a tamper-evident audit trail.
- **Multi-provider AI routing.** Route requests across 15+ model providers with local fallback -- choose your cost, latency, and privacy tradeoffs per workload.

## Feature Comparison

| Feature | Community | Enterprise |
|---------|-----------|------------|
| MCP governance layer (policy enforcement) | Yes | Yes |
| Ed25519-signed execution receipts | Yes | Yes |
| Receipt chain verification | Yes | Yes |
| All 4 agent runtimes | Yes | Yes |
| 60 MCP tools | Yes | Yes |
| Web UI control panel (38 tabs) | Yes | Yes |
| Local LLM integration (Ollama, LM Studio) | Yes | Yes |
| Multi-provider AI routing | Yes | Yes |
| 28/28 multi-runtime proof matrix | Yes | Yes |
| Single sign-on (SAML/OIDC) | No | Yes |
| LDAP directory integration | No | Yes |
| Audit log export (Splunk, Datadog) | No | Yes |
| RBAC with custom roles | No | Yes |
| High-availability cluster | No | Yes |
| SLA-backed support | No | Yes |
| On-premise enterprise installer | No | Yes |
| Usage analytics dashboard | No | Yes |
| Commercial license | Apache 2.0 | Enterprise EULA |

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Security Model](docs/security-model.md)
- [Contributing Guide](CONTRIBUTING.md)

## Getting Involved

Community Edition is free and open source under Apache 2.0.

For organizations that need SSO, LDAP, RBAC, HA clustering, SLA support, or a commercial license, the Enterprise edition is available as a private pilot.

Request access: **sovereign-agentops@anthropic.com** (replace with actual contact)

---

Built on the MCP protocol. Governance, not lock-in.
