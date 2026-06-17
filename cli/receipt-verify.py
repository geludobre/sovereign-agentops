#!/usr/bin/env python3
"""Verify Sovereign AgentOps Ed25519-signed execution receipts.

Modes: display (default), --verify, --gen-demo.  Exit 0 = valid, 1 = invalid.
Requires: cryptography  (pip install cryptography)
"""
import argparse, json, sys
from pathlib import Path

# Embedded demo Ed25519 public key (hex, 32 bytes) — RFC 8032 Section 7.1.
DEMO_PUBKEY_HEX = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"


def _pubkey(hex_key=None):
    """Load Ed25519PublicKey from hex string (or embedded demo key)."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        print("Error: 'cryptography' package required.\n"
              "  pip install cryptography", file=sys.stderr)
        sys.exit(1)
    raw = bytes.fromhex((hex_key or DEMO_PUBKEY_HEX).replace(" ", ""))
    if len(raw) != 32:
        print(f"Error: pubkey must be 32 bytes, got {len(raw)}.", file=sys.stderr)
        sys.exit(1)
    return Ed25519PublicKey.from_public_bytes(raw)


def _canonical(obj):
    """Deterministic JSON — sorted keys, no whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def verify_sig(receipt, pubkey):
    """Verify ed25519:<hex> signature. Returns (True, msg) or (False, reason)."""
    body = dict(receipt)
    sig = body.pop("signature", None)
    if not sig or not isinstance(sig, str) or not sig.startswith("ed25519:"):
        return False, "missing or invalid 'signature' field"
    try:
        sig_bytes = bytes.fromhex(sig[8:])
    except ValueError as e:
        return False, f"hex decode error: {e}"
    if len(sig_bytes) != 64:
        return False, f"Ed25519 sig must be 64 bytes, got {len(sig_bytes)}"
    try:
        pubkey.verify(sig_bytes, _canonical(body))
        return True, "VALID"
    except Exception as e:
        return False, str(e)


def display(receipt):
    """Print receipt in human-friendly format."""
    body, sig = dict(receipt), receipt.get("signature", "")
    sig_short = sig if len(sig) < 80 else sig[:36] + "..." + sig[-8:]
    print("\n" + "=" * 64)
    print("  SOVEREIGN AGENTOPS — EXECUTION RECEIPT")
    print("=" * 64)
    for k in ("schema_version", "run_id", "workspace_id", "actor",
              "agent_runtime", "tool", "command", "timestamp"):
        print(f"  {k:<20}{body.get(k, '?')}")
    if body.get("arguments"):
        print(f"  {'arguments':<20}{json.dumps(body['arguments'])}")
    if body.get("policy_decision"):
        print(f"  {'policy_decision':<20}{body['policy_decision']}")
    print(f"  {'signature':<20}{sig_short}\n" + "-" * 64)


def gen_demo(dirpath):
    """Generate fresh Ed25519 key pair, sign a demo receipt, save outputs."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError:
        print("Error: 'cryptography' package required.\n"
              "  pip install cryptography", file=sys.stderr)
        sys.exit(1)
    out = Path(dirpath)
    out.mkdir(parents=True, exist_ok=True)
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    receipt = {
        "schema_version": "1.0",
        "run_id": "demo-run-001",
        "workspace_id": "wksp-demo-001",
        "actor": "developer@example.com",
        "agent_runtime": "claude-code",
        "tool": "demo_policy_check",
        "command": "git push origin main",
        "arguments": {"repo": "sovereign-agentops-community", "branch": "main"},
        "policy_decision": "command 'git' is in allowlist for workspace 'demo'",
        "timestamp": "2026-06-15T10:00:00Z",
    }
    receipt["signature"] = "ed25519:" + priv.sign(_canonical(receipt)).hex()
    (out / "signed-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (out / "public-key.hex").write_text(pub.public_bytes_raw().hex() + "\n")
    (out / "private-key.hex").write_text(priv.private_bytes_raw().hex() + "\n")
    print(f"\n  Demo data -> {out.resolve()}/")
    print(f"  Verify: python3 receipt-verify.py --verify {out / 'signed-receipt.json'}\n")


def main():
    ap = argparse.ArgumentParser(
        description="Verify Sovereign AgentOps Ed25519-signed execution receipts.",
        epilog=(
            "Examples:\n"
            "  %(prog)s f.json              display\n"
            "  %(prog)s --verify f.json     verify\n"
            "  %(prog)s --gen-demo ./dir    generate demo data\n"
            "  %(prog)s --key $(cat k.hex) --verify f.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("file", nargs="?", help="Receipt JSON file")
    ap.add_argument("--verify", action="store_true", help="Verify signature")
    ap.add_argument("--gen-demo", metavar="DIR", help="Generate demo data")
    ap.add_argument("--key", metavar="HEX", help="Public key hex (overrides embedded)")
    args = ap.parse_args()

    if args.gen_demo:
        gen_demo(args.gen_demo)
        return
    if not args.file:
        ap.print_help()
        sys.exit(1)
    try:
        with open(args.file) as f:
            receipt = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    display(receipt)

    if args.verify:
        ok, msg = verify_sig(receipt, _pubkey(args.key))
        print(f"  {'Verification':<20}{'VALID' if ok else 'INVALID'}")
        print(f"  {'Detail':<20}{msg}")
        sys.exit(0 if ok else 1)
    else:
        hint = ("use --verify to check sig" if "signature" in receipt else "no signature")
        print(f"  ({hint})")

    print("=" * 64)


if __name__ == "__main__":
    main()
