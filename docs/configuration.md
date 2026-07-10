# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBUI_PASSWORD` | — | Enables remote access when set |
| `CHAT_MODEL` | `opencode/nemotron-3-ultra-free` | Chat AI model |
| `ETH_RPC_URL` | — | Ethereum RPC for crypto wallet |
| `ANTHROPIC_AUTH_TOKEN` | `freecc` | FCC proxy auth token |

## License

Enterprise Edition requires a signed license. Generate one:

```bash
python3 scripts/license.py generate --customer "Acme Corp" --tier enterprise
```

## Directory Layout

| Path | Purpose |
|------|---------|
| `~/.claude/toolkit/mcp/` | MCP server (server.py) |
| `~/.claude/toolkit/web/` | Flask web UI |
| `~/.claude/toolkit/config/` | JSON state files |
| `~/.claude/vault/` | Encrypted secrets |
| `~/.claude/bin/` | CLI tools |
