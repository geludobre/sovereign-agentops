# Changelog

## 2.4.1 (2026-07-12)

### Platform

- **N1 Keybinding Editor** — Unified keybinding registry for CodeMirror 6 + Monaco editors with localStorage and project settings.json persistence. 18 editor commands with full keyboard shortcut customization.
- **N4 Extension Marketplace** — Complete plugin marketplace: PluginManifest, PluginRegistry with dependency resolution and semver support, GitHub-based registry index, 8 Flask API endpoints (search/featured/install/uninstall/updates/publish/dependencies/refresh), marketplace UI tab with search, filter, install, detail modal. Enterprise license gating for premium plugins.
- **7 Autonomous Digital Organization Frontiers Complete** — Token Independence (semantic cache, local model runtime, intent router, predictive cache), Recursive Self-Improvement, Predictive Governance, Agent-Owned Assets, Self-Negotiating Treaties, Digital Twin Simulator, Autonomous Incident Resolution.
- **3 Unreplicable Moats Built** — Governance Recipe Marketplace (4 built-in recipes: SOC2, PCI DSS, HIPAA, Startup + custom CRUD), Federation Starter Packs (quick_peer_setup 3-step handshake, LAN UDP discovery, 4 governance templates, bulk operations), Precedent Accelerator (trend analysis, auto-amendment speedup 3→2, drift detection, precedent search).
- **Enterprise License Gating** — MCP-level tool filtering (_ENTERPRISE_TOOLS), Flask @require_license decorator with 10 feature tiers, /api/license/{status,features,activate} API endpoints, Ed25519 license verification.

### Enterprise

- All 5 enterprise-hardening sub-phases complete: SSO (OIDC/SAML/LDAP/Keycloak), HA clustering (Redis-backed session store, distributed task queue, leader election), Security CI (bandit/semgrep/ZAP), k6 load testing (5 scenarios: smoke/load/stress/soak/spike), Federation validation + chaos (17 integration tests).
- 140 automated tests passing (unit + integration + chaos + load + federation).

### Infrastructure

- 91 MCP tools (91 static + 0 dynamic plugins), 486 API endpoints, 88 Web UI tabs, 8 background daemons.
- PWA with service worker, offline support, install prompt, HTTPS/TLS via Nginx reverse proxy.
- 5 agent runtimes governed uniformly: Claude Code, OpenCode, Direct MCP, Workflow Engine, Collaborator Desktop.

---

## 2.0.0 (2026-07-08)

### Major

- **Real Ed25519 crypto.** Replaced SHA-256 demo signing with Ed25519 (RFC 8032)
  using the `cryptography` library. The server generates a fresh Ed25519 keypair on
  first run, persists it to `~/.config/agentops/ed25519_private.key`, and uses it for
  all receipt signing. Public key is returned in every signed receipt for external
  verification via `cli/receipt-verify.py`.

- **Receipt self-verification.** Every signed receipt can be verified immediately
  via `demo_receipt_verify`. Receipts use the standard `ed25519:hex` format
  compatible with the CLI verification tool.

- **New tool: `demo_server_info`.** Returns server metadata: version, edition,
  public key, key path, crypto backend, and protocol version.

- **Proper test suite.** 25+ pytest tests covering all 7 tools, JSON-RPC protocol
  layer, Ed25519 sign/verify round-trips, policy enforcement edge cases, workspace
  jail path resolution, and audit log behavior.

- **CI pipeline.** GitHub Actions workflow that runs tests on push/PR to main.

- **Modern Python packaging.** `pyproject.toml` with setuptools, pytest config,
  coverage settings, and optional dev/test dependency groups.

- **Makefile.** Common operations: `test`, `coverage`, `lint`, `docker-build`,
  `clean`.

### Infrastructure

- `requirements.txt` now lists `cryptography>=41.0.0` as the sole dependency
- `Dockerfile` updated to install the `cryptography` package
- `.dockerignore` added to keep build context lean
- `SECURITY.md` with responsible disclosure policy

### Documentation

- **Honest feature comparison.** README updated to accurately reflect what the
  Community Edition contains (7 demo tools + 1 CLI) vs the Enterprise platform
  (98 MCP tools, 455+ endpoints, 91+ web UI tabs, full governance stack).
  No more misleading claims about 60 tools or 38 tabs.

- **Quickstart works.** The README now guides users through a working stdio MCP
  session with real commands that produce Ed25519-signed receipts.

### License

`LICENSE.community` — Apache 2.0 with Community Edition exclusion clause.
Enterprise features require a commercial license.

---

## 1.0.0 (2026-06-15)

### Initial Community Edition release

- 6 demo MCP tools using SHA-256 demonstration "signing"
- Ed25519 receipt verification CLI (`cli/receipt-verify.py`)
- Architecture and security-model documentation
- Docker Compose demo environment
- Example workspace policy and signed receipt
