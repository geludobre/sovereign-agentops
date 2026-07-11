# Security Model

> **Note:** This document describes the Enterprise platform security architecture.
> The Community Edition implements the core cryptographic verification concept
> (real Ed25519 signing and verification) but does not include the full
> defense-in-depth stack described below.

## Overview

Autonomous Digital Organization Platform follows a defense-in-depth approach with local-first deployment, default-deny auth, workspace isolation, and cryptographic audit. The security model assumes the deployment environment is trusted (your hardware, your network) and focuses on preventing agent actions from violating operational policy.

## Local-First Deployment

All control-plane components run on your hardware. No telemetry, usage data, or execution logs are transmitted externally. AI model inference can optionally route through external providers, but the policy engine, receipt database, and audit trail remain local.

Key properties:
- Zero external dependencies for control-plane operation
- No outbound connections required for policy enforcement
- Receipt database never leaves the host
- Full offline operation with local LLMs (Ollama, LM Studio)

## Authentication (Enterprise)

### Default-Deny Principle

- With no `WEBUI_PASSWORD` configured: the web UI binds to localhost only
- With `WEBUI_PASSWORD` set: remote access is allowed with session-based auth
- Unauthenticated requests to protected endpoints are rejected before any processing

### Session Management

- JWT-based sessions with short-lived access tokens (15 minutes)
- Refresh token rotation with 7-day expiry
- HttpOnly, SameSite=Strict cookies with optional `__Host-` prefix behind HTTPS
- Server-side session revocation

### Brute Force Protection

Progressive delay and lockout:
- 5 failed attempts: 30-second delay
- 10 failed attempts: 15-minute lockout
- 20 failed attempts: 1-hour lockout

## Workspace Policy Enforcement (Community + Enterprise)

The Community Edition's `demo_policy_check` tool demonstrates policy enforcement concepts:

| Control | Community | Enterprise |
|---------|-----------|------------|
| Command allowlist | Static rules in code | Configurable per-workspace |
| Command blocklist | Predefined dangerous patterns | Custom blocklists |
| Path jail | Functional directory check | Full workspace isolation |
| Dangerous pattern detection | Fork bomb, rm -rf /, sudo | Regex-based + ML detection |

Policies apply at the MCP layer and are runtime-agnostic -- they block actions regardless of which agent runtime initiated them.

## Execution Receipts (Community + Enterprise)

Every agent action produces a cryptographically signed receipt:

- **Signing algorithm:** Ed25519 (RFC 8032) — **real crypto, same in both editions**
- **Chain structure:** Enterprise: each receipt includes the SHA-256 hash of the previous receipt. Community: standalone receipt verification
- **Persistence:** Enterprise: SQLite-backed. Community: in-memory audit log
- **Verification:** Both editions expose verification tools. Community: `demo_receipt_verify` MCP tool + `cli/receipt-verify.py`

### What a receipt contains

The Community Edition receipt schema (`schema_version: 1.0`):

- `run_id` (UUID)
- `workspace_id` (always `community-demo`)
- `actor` (always `community-user`)
- `agent_runtime` (always `direct-mcp`)
- `tool` — name of the MCP tool
- `action` — action performed
- `target` — target of the action
- `timestamp` — ISO 8601 UTC
- `policy_decision` — policy result
- `signature` — Ed25519 hex signature over the canonical receipt

Enterprise receipts add: previous receipt hash (chain link), receipt status, policy version metadata, and environment context.

### Key Management

- Ed25519 keypair generated on first use
- Private key stored at `~/.config/agentops/ed25519_private.key` (permissions 0o400)
- Public key returned in every signed receipt for external verification
- Key file location overridable via `AGENTOPS_KEY_DIR` environment variable

## Transport Security (Enterprise)

The Enterprise platform provides:

- **TLS 1.3** (optional downgrade to 1.2 for legacy clients)
- **HSTS preload** configured
- **HTTP Strict Transport Security** headers
- **WebSocket over WSS** with origin validation
- **HTTP-to-HTTPS redirect** when TLS is active

### WebSocket Hardening (Enterprise)

- Short-lived WS-specific tokens (5-minute TTL, separate signing secret)
- Token rotation on reconnect (one-time use, replay rejected)
- HttpOnly cookie-based auth (query string fallback removed)
- Origin header validation
- Per-IP rate limiting: 20 connections per 60-second sliding window

## API Hardening (Enterprise)

- CSRF protection with SameSite=Strict cookies
- Dynamic `secure` flag on cookies based on request scheme
- Rate limiting on auth endpoints, WebSocket connections, and tool calls
- `X-Permitted-Cross-Domain-Policies` headers set
- Server version header removed
- Fernet-based API key encryption (AES-CBC + HMAC-SHA256)

## Community vs Enterprise Security

| Control | Community | Enterprise |
|---------|-----------|------------|
| Local-first deployment | Yes | Yes |
| Ed25519-signed receipts | Yes | Yes |
| Receipt verification (MCP) | Yes | Yes |
| Receipt verification (CLI) | Yes | Yes |
| Policy enforcement (demo) | Yes | Yes |
| Workspace path jail (demo) | Yes | Yes |
| Persistent Ed25519 key | Yes | Yes |
| Auth default-deny | N/A (no web UI) | Yes |
| Session-based auth (JWT) | N/A (no web UI) | Yes |
| Brute force protection | N/A (no web UI) | Yes |
| Full workspace policy engine | No | Yes |
| Receipt chain verification | No | Yes |
| Key rotation | No | Yes |
| TLS 1.3 / HSTS | No | Yes |
| WebSocket hardening | N/A (no WS) | Yes |
| CSRF protection | N/A (no API) | Yes |
| Rate limiting | N/A (no API) | Yes |
| SAML/OIDC single sign-on | No | Yes |
| LDAP/AD integration | No | Yes |
| Audit log export (Splunk, Datadog, syslog) | No | Yes |
| RBAC with custom roles | No | Yes |
| Session policies (IP allowlist, geo-fencing) | No | Yes |
| Secrets vault integration (HashiCorp Vault) | No | Yes |
| Signed attestations for compliance reporting | No | Yes |
| Dedicated HSM support | No | Yes |
