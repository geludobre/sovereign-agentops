# Changelog

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
