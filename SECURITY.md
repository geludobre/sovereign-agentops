# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

The Sovereign AgentOps project takes security seriously. If you discover a
security vulnerability, please **do not** file a public GitHub issue.

Instead, send a description of the issue to the maintainers. You can expect:

- **Acknowledgement** within 48 hours of your report
- **Initial assessment** within 5 business days
- **Coordinated disclosure** — we will work with you on a timeline for
  public disclosure once a fix is available

Please include:
- Type of issue (buffer overflow, SQL injection, privilege escalation, etc.)
- Full details of the exploit scenario
- Steps to reproduce or a proof of concept
- Affected versions and configurations

## Scope

This security policy covers the Community Edition of Sovereign AgentOps
published at https://github.com/FinBridge/sovereign-agentops.

Enterprise Edition customers should refer to their support agreement for
security-related communications.

## Cryptography Notice

Community Edition uses Ed25519 (RFC 8032) via the `cryptography` Python library
for execution receipt signing. Key material is generated locally and stored at
`~/.config/agentops/ed25519_private.key` with file permissions `0o400`.

This is **real, production-grade cryptography**. However, the Community Edition
server is a demonstration tool — it does not implement key rotation, hardware
backing, or HSMs. For production deployment, please evaluate the Enterprise
Edition.
