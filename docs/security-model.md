# Security Model

## Overview

Sovereign AgentOps follows a defense-in-depth approach with local-first deployment, default-deny auth, workspace isolation, and cryptographic audit. The security model assumes the deployment environment is trusted (your hardware, your network) and focuses on preventing agent actions from violating operational policy.

## Local-First Deployment

All control-plane components run on your hardware. No telemetry, usage data, or execution logs are transmitted externally. AI model inference can optionally route through external providers, but the policy engine, receipt database, and audit trail remain local.

Key properties:
- Zero external dependencies for control-plane operation
- No outbound connections required for policy enforcement
- Receipt database never leaves the host
- Full offline operation with local LLMs (Ollama, LM Studio)

## Authentication

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

## Workspace Policy Enforcement

The `aug_workspace_policy` MCP tool controls what actions agents can perform:

| Control | Description |
|---------|-------------|
| Command allowlist | Explicitly permitted commands and patterns |
| Command blocklist | Forbidden commands (e.g., sudo, raw rm -rf) |
| Path jail | Restrict file system access to allowed directories |
| Dangerous pattern detection | Regex-based shell injection and abuse detection |

Policies apply at the MCP layer and are runtime-agnostic -- they block actions regardless of which agent runtime initiated them. Policy violations are logged and trigger a signed receipt documenting the blocked action.

## Execution Receipts

Every agent action produces a cryptographically signed receipt:

- **Signing algorithm:** Ed25519
- **Chain structure:** Each receipt includes the SHA-256 hash of the previous receipt, forming a tamper-evident chain
- **Persistence:** SQLite-backed with export capability
- **Verification:** The `aug_receipt` MCP tool exposes verify, stats, and export actions

### What a receipt contains

- Tool name and arguments
- Timestamp and actor identity
- Result or error
- Previous receipt hash (chain link)
- Ed25519 signature
- Receipt status (valid, tampered, revoked)

### Key Management

- Signing keys generated on first use via `Ed25519.generate_key_pair()`
- Public key exportable for third-party verification
- Key rotation supported through `rotate_key` action
- Private key stored with restricted file permissions

## Transport Security

- **TLS 1.3** (optional downgrade to 1.2 for legacy clients)
- **HSTS preload** configured (can be disabled for internal CAs)
- **HTTP Strict Transport Security** headers set
- **WebSocket over WSS** with origin validation
- **HTTP-to-HTTPS redirect** enforced when TLS is active

### WebSocket Hardening

- Short-lived WS-specific tokens (5-minute TTL, separate signing secret)
- Token rotation on reconnect (one-time use, replay rejected)
- HttpOnly cookie-based auth (query string fallback removed)
- Origin header validation
- Per-IP rate limiting: 20 connections per 60-second sliding window

## API Hardening

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
| Auth default-deny | Yes | Yes |
| Session-based auth (JWT) | Yes | Yes |
| Brute force protection | Yes | Yes |
| Workspace policy enforcement | Yes | Yes |
| Ed25519-signed receipts | Yes | Yes |
| Receipt chain verification | Yes | Yes |
| Key rotation | Yes | Yes |
| TLS 1.3 | Yes | Yes |
| WebSocket hardening | Yes | Yes |
| CSRF protection | Yes | Yes |
| Rate limiting | Yes | Yes |
| SAML/OIDC single sign-on | No | Yes |
| LDAP/AD integration | No | Yes |
| Audit log export (Splunk, Datadog, syslog) | No | Yes |
| RBAC with custom roles | No | Yes |
| Session policies (IP allowlist, geo-fencing) | No | Yes |
| Secrets vault integration (HashiCorp Vault) | No | Yes |
| Signed attestations for compliance reporting | No | Yes |
| Dedicated HSM support | No | Yes |
