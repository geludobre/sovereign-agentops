# Key Pillars

The Autonomous Digital Organization Platform is built on two layers of
differentiators: **operational pillars** (the governed execution layer that makes
AI operations production-grade) and **unreplicable moats** (advantages that
compound over time and cannot be cloned by competitors).

## Operational Pillars

Six production-grade operational pillars form the governed execution layer. Each
follows the same pattern: `module → MCP tool → Flask route → Web UI panel`, with
JSON persistence in `~/.claude/toolkit/config/`.

| Pillar | What it does |
|--------|-------------|
| **Guardrail Engine** | Compiled rule engine: parameterized, time-window, rate-limit, and context-aware policies with graduated enforcement |
| **Sandbox Environment** | Process isolation via temp workspace + subprocess with resource limits, path jail, timeout, and audit trail (optional Docker) |
| **HITL Router** | Approval queue with priority/SLA escalation, webhook delivery, and decision audit trail |
| **Registry & Lineage** | Artifact registry with SHA-256 hash verification, lineage DAG tracking, and version tagging |
| **AI War Room** | Incident lifecycle (reported → triaged → investigating → resolved → post_mortem), runbook automation, oncall scheduling |
| **Monitor Plane** | Prometheus `/metrics`, JSON metrics API, agent perf tracking, and webhook delivery |

All six pillars are protected by `@require_auth` and operate uniformly across every
agent runtime (Claude Code, OpenCode, Direct MCP, Workflow Engine, Collaborator
Desktop).

## Unreplicable Moats

Three advantages get **stronger over time** and cannot be cloned:

1. **Constitutional Case Law** — Every policy override creates a signed precedent.
   Three consistent overrides → the constitution auto-suggests an amendment. A
   6-month-old instance has 50–100+ precedents encoding real organizational wisdom.
   Competitors can clone code but **not** accumulated case law.

2. **Treaty-Based Federation** — Cross-instance governance treaties with
   dual-signed ledgers. Each federated peer increases network value. Centralized
   cloud platforms **cannot** do cross-instance treaties. A federation of 100+
   instances is a serious network moat.

3. **MCP Protocol Layer** — Runtime-agnostic governance. Any future agent
   framework that speaks MCP is automatically governed. Cloud IDEs tie governance
   to their own runtime — this platform doesn't. Future-proof against any new
   agent paradigm.

## Why These Pillars Matter

- **Uniform enforcement** — Guardrails, sandboxes, and HITL apply identically
  whether an action comes from Claude Code, a web API call, or the Collaborator
  desktop IDE.
- **Auditability** — Every action produces an Ed25519-signed receipt linked by a
  SHA-256 hash chain. Tamper detection is built in.
- **Compounding advantage** — Case law, federation, and protocol adoption all
  increase in value the longer the platform runs. This is the category moat.

See [Architecture](architecture.md) for the full component design and
[README](../README.md) for the Community vs. Enterprise feature comparison.
