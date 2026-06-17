# Architecture

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
  |  - path jail          - SQLite persistence    |
  |  - pattern detection  - chain verification    |
  +-----------------------------------------------+
             |             |             |
             v             v             v
  +-----------------------------------------------+
  |            SELF-HOSTED SERVICES               |
  |                                               |
  |  MCP Server    Web UI      API Gateway        |
  |  (60 tools)    (38 tabs)  (REST + WS)        |
  |                                               |
  |  PostgreSQL 16    Redis 7    SearXNG          |
  |  Ollama           LM Studio  FCC Proxy        |
  +-----------------------------------------------+
```

## Components

### Agent Runtimes

The platform is runtime-agnostic. Four independent runtimes connect through the same MCP protocol:

| Runtime | Dependency | Offline | Use Case |
|---------|------------|---------|----------|
| Claude Code | Anthropic API (or proxy) | No | Interactive coding, CLI agent |
| OpenCode | Optional (15+ providers) | Yes | Multi-provider routing, local models |
| Direct MCP Client | None | Yes | Custom tooling, API access |
| Workflow Engine | None | Yes | Batch automation, pipelines |

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
3. Links each receipt to the previous one via SHA-256 hash chain
4. Stores in a local SQLite database
5. Exposes verification endpoints for tamper detection

### Web UI

Flask + SocketIO control panel with 38 tabs covering all MCP tool domains. Served via Nginx reverse proxy on port 443 (HTTPS) with HTTP-to-HTTPS redirect. Direct port 8080 access available for local-only deployments.

### Infrastructure Services

| Service | Role |
|---------|------|
| PostgreSQL 16 | Primary data store for workspaces, receipts, metadata |
| Redis 7 | Session store, rate limiter, pub/sub for real-time events |
| Ollama | Local LLM inference (llama3.1 8B, port 11434) |
| LM Studio | Local LLM inference (Gemma 4 12B, port 1234) |
| Free Claude Code Proxy | Multi-provider router (15+ providers, port 8082) |
| SearXNG | Private web search, no external tracking |

## Multi-Runtime Proof Matrix

All 28 governance dimensions verified passing across every runtime:

| Test | Direct MCP | Claude Code | Web API | Workflow Engine |
|------|:----------:|:-----------:|:-------:|:---------------:|
| Block `sudo` | PASS | PASS | PASS | PASS |
| Block path traversal | PASS | PASS | PASS | PASS |
| Generate signed receipt | PASS | PASS | PASS | PASS |
| Verify receipt chain | PASS | PASS | PASS | PASS |
| Receipt tamper detection | PASS | PASS | PASS | PASS |
| Route local model (LM Studio) | PASS | PASS | PASS | PASS |
| Operate without public API | PASS | PASS | PASS | PASS |

This proves that governance is enforced at the MCP layer, not within any specific runtime. A blocked command is blocked whether issued by Claude Code, OpenCode, a direct MCP call, or a workflow pipeline.

## Deployment Model

Local-first by default. All services run on your hardware with no external dependencies. The platform can optionally route AI requests through external providers via the Free Claude Code proxy layer, but the control plane, policy engine, and receipt database never leave your network.

## Extension Points

| Point | Purpose |
|-------|---------|
| MCP protocol | 60 tools discoverable by any MCP client |
| Settings file | PATH injection, MCP enablement, model selection |
| PATH scripts | Shell-level automation surfaced to agents |
| Memory system | Persistent cross-session context |
| Skills & plugins | Marketplace extensions |
