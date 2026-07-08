# Architecture

> **Note:** This document describes the Enterprise platform architecture. The
> Community Edition provides a standalone MCP governance server with 7 demo tools
> using real Ed25519 crypto — it does not include the web UI, PostgreSQL/Redis
> persistence, the full 98-tool MCP suite, or multi-runtime orchestration.
> See [README.md](../README.md) for the feature comparison.

## High-Level Design

Sovereign AgentOps interposes a governed MCP tool layer between agent runtimes and infrastructure. Every agent action -- code read, shell command, network request, database query -- passes through policy enforcement and produces a signed execution receipt before reaching the target system.

```
AGENT RUNTIMES
  Claude Code   OpenCode   Direct MCP Client   Workflow Engine
       |            |             |                  |
       +-----+------+------+-----+----+------+------+
             |             |             |
             v             v             v
  +-----------------------------------------------+
  |            MCP GOVERNANCE LAYER               |
  |                                               |
  |  Policy Enforcer      Execution Receipts      |
  |  - command allowlist  - Ed25519 signing       |
  |  - blocklist          - hash-chain linking    |
  |  - path jail          - in-memory audit       |
  |  - pattern detection  - external verification |
  +-----------------------------------------------+
             |             |             |
             v             v             v
  +-----------------------------------------------+
  |            SELF-HOSTED SERVICES               |
  |                                               |
  |  MCP Server (7 demo tools)    CLI tools       |
  |  Docker Compose demo                         |
  |                                               |
  |  Enterprise: 98 tools, 91+ UI tabs,           |
  |  PostgreSQL 16, Redis 7, SearXNG,             |
  |  Ollama, LM Studio, FCC Proxy                 |
  +-----------------------------------------------+
```

## Components

### Community Edition

The Community Edition is a single-process MCP server (`tools/mcp_server.py`) that:

1. Listens for JSON-RPC 2.0 requests over stdin/stdout
2. Provides 7 demo tools: policy check, receipt sign/verify, model route, workspace jail, audit log, server info
3. Signs all receipts with real Ed25519 (RFC 8032) via the `cryptography` Python library
4. Maintains an in-memory signed audit log
5. Generates a fresh Ed25519 keypair on first run, stored at `~/.config/agentops/ed25519_private.key`
6. Works standalone, via Docker, or connected to any MCP-compatible client

### Enterprise Platform (additional components)

The full Enterprise platform includes all Community Edition capabilities plus:

- **98 MCP tools** (93 static + 5 dynamic plugins) across search, code, infra, security, network, data, AI, automation, governance, and operations domains
- **Web UI** with 91+ tabs: Flask + SocketIO control panel with the Cortex organizational graph, Agents dashboard, IM Bridge, Orchestrator, Service Catalogue, Observability Hub, Governance Staging, Compliance Suite, Fleet Command
- **PostgreSQL 16** for persistent storage of workspaces, receipts, and metadata
- **Redis 7** for session store, rate limiting, and pub/sub real-time events
- **Constitutional Governance** — 6-layer platform: Cortex, Policy Constitution, Autonomy Charter, Org Memory (Neocortex), Treaty-Based Federation
- **6 operational pillars**: Guardrail Engine, Sandbox, HITL Router, Registry & Lineage, AI War Room, Monitor Plane
- **5 agent runtimes**: Claude Code, OpenCode, Direct MCP, Workflow Engine, Collaborator Desktop IDE
- **Local LLM integration**: Ollama, LM Studio, llama.cpp (all configurable)
- **Multi-provider AI routing**: 15+ providers via Free Claude Code proxy
- **Agent orchestration**: capability registry, message bus, delegation protocol, DAG tracking

### Agent Runtimes

The platform is runtime-agnostic. Five independent runtimes connect through the same MCP protocol:

| Runtime | Dependency | Offline | Use Case |
|---------|------------|---------|----------|
| Claude Code | Anthropic API (or proxy) | No | Interactive coding, CLI agent |
| OpenCode | Optional (15+ providers) | Yes | Multi-provider routing, local models |
| Direct MCP Client | None | Yes | Custom tooling, API access |
| Workflow Engine | None | Yes | Batch automation, pipelines |
| Collaborator Desktop | None | Yes | Native IDE (Electron, Monaco, xterm) |

No runtime is privileged. The same policies and receipts apply to all.

### MCP Governance Layer

**Policy Enforcer** intercepts every tool invocation and checks:

1. Command allowlists and blocklists (e.g., block `sudo`, `chmod 777`)
2. Path jail rules (e.g., restrict file access to `/workspace`)
3. Dangerous pattern detection (e.g., shell injection patterns)
4. Workspace-scoped permissions

**Execution Receipt Engine** records every action:

1. Captures tool name, arguments, result, and actor identity
2. Signs the record with an Ed25519 key
3. Links each receipt to the previous one via SHA-256 hash chain (Enterprise)
4. Stores in local SQLite database (Enterprise) or in-memory (Community)
5. Exposes verification endpoints for tamper detection

### Web UI (Enterprise)

Flask + SocketIO control panel with 91+ tabs covering all MCP tool domains, the Cortex organizational graph, governance dashboards, compliance reports, fleet command, and more. Served via Nginx reverse proxy on port 443 (HTTPS) with HTTP-to-HTTPS redirect.

### Infrastructure Services (Enterprise)

| Service | Role |
|---------|------|
| PostgreSQL 16 | Primary data store for workspaces, receipts, metadata |
| Redis 7 | Session store, rate limiter, pub/sub for real-time events |
| Ollama | Local LLM inference (llama3.1 8B, port 11434) |
| LM Studio | Local LLM inference (Gemma 4 12B, port 1234) |
| Free Claude Code Proxy | Multi-provider router (15+ providers, port 8082) |
| SearXNG | Private web search, no external tracking |

## Multi-Runtime Proof Matrix

The Enterprise platform has verified 35/35 governance tests passing across all 5 runtimes:

| Test | Direct MCP | Claude Code | Web API | Workflow Eng | Collaborator |
|------|:----------:|:-----------:|:-------:|:------------:|:------------:|
| Block `sudo` | PASS | PASS | PASS | PASS | PASS |
| Block path traversal | PASS | PASS | PASS | PASS | PASS |
| Generate signed receipt | PASS | PASS | PASS | PASS | PASS |
| Verify receipt chain | PASS | PASS | PASS | PASS | PASS |
| Receipt tamper detection | PASS | PASS | PASS | PASS | PASS |
| Route local model | PASS | PASS | PASS | PASS | PASS |
| Operate without public API | PASS | PASS | PASS | PASS | PASS |

The Community Edition's demo tools can be connected to any MCP client to verify
the same governance concepts.

## Deployment Model

**Community Edition:** Single-process stdio MCP server. Docker Compose for containerized evaluation. No external services required.

**Enterprise:** Local-first by default. All services run on your hardware with no external dependencies. The control plane, policy engine, and receipt database never leave your network.

## Extension Points

| Point | Community | Enterprise |
|-------|-----------|------------|
| MCP protocol | 7 demo tools | 98 tools (93 static + 5 plugins) |
| CLI tools | Receipt verification | Full suite |
| Settings & PATH | User-configured | Managed platform-wide |
| Memory system | -- | Cross-session knowledge graph (Neocortex) |
| Skills & plugins | -- | Marketplace extensions |
