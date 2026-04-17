#!/usr/bin/env python3
"""Interactive Leantime credential setup — writes LEANTIME_URL and LEANTIME_API_KEY to ~/.config/leantime/.env."""

import getpass
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROBE_METHOD = "leantime.rpc.users.getAll"
PROBE_TIMEOUT = 10
CONFIG_DIR = Path.home() / ".config" / "leantime"
CONFIG_FILE = CONFIG_DIR / ".env"


def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        val = input(f"{prompt}{hint}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nSetup cancelled.")
        sys.exit(0)
    return val or default


def ask_secret(prompt: str) -> str:
    try:
        val = getpass.getpass(f"{prompt}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nSetup cancelled.")
        sys.exit(0)
    return val


def probe(url: str, key: str) -> tuple[bool, str]:
    """Return (success, message)."""
    endpoint = f"{url.rstrip('/')}/api/jsonrpc"
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": "setup-probe",
        "method": PROBE_METHOD,
        "params": {},
    }).encode()
    req = urllib.request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "x-api-key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False, f"HTTP {e.code}: API key rejected — check Company Settings → API"
        if e.code == 404:
            return False, "HTTP 404: /api/jsonrpc not found — is LEANTIME_URL pointing to the Leantime root?"
        return False, f"HTTP {e.code} from {endpoint}"
    except urllib.error.URLError as e:
        return False, f"Cannot reach {url}: {e.reason}"
    except Exception as e:
        return False, str(e)

    if "error" in data:
        msg = data["error"].get("message", "unknown error")
        return False, f"JSON-RPC error: {msg}"

    count = len(data.get("result", [])) if isinstance(data.get("result"), list) else 1
    return True, f"Connected — {count} users visible"


def write_config(url: str, key: str) -> Path:
    """Write credentials to ~/.config/leantime/.env, merging with any existing content."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.exists():
        existing = CONFIG_FILE.read_text()
        has_url = "LEANTIME_URL=" in existing
        has_key = "LEANTIME_API_KEY=" in existing

        if has_url or has_key:
            print(f"\nCredentials already exist at {CONFIG_FILE}")
            choice = ask("Overwrite existing entries? (yes/no)", "no").lower()
            if choice not in ("yes", "y"):
                print("Skipped. Credentials NOT updated.")
                print(f"  LEANTIME_URL={url}")
                print("  LEANTIME_API_KEY=<hidden>")
                return CONFIG_FILE

            # Replace existing LEANTIME_* lines
            lines = [l for l in existing.splitlines() if not l.startswith("LEANTIME_")]
            lines += [f"LEANTIME_URL={url}", f"LEANTIME_API_KEY={key}"]
            CONFIG_FILE.write_text("\n".join(lines) + "\n")
        else:
            with CONFIG_FILE.open("a") as f:
                f.write(f"\nLEANTIME_URL={url}\nLEANTIME_API_KEY={key}\n")
    else:
        CONFIG_FILE.write_text(f"LEANTIME_URL={url}\nLEANTIME_API_KEY={key}\n")

    # Restrict permissions so only the owner can read the key
    CONFIG_FILE.chmod(0o600)
    return CONFIG_FILE


def main() -> int:
    print("=" * 56)
    print("  Leantime Credential Setup")
    print("=" * 56)
    print(f"\nCredentials will be saved to: {CONFIG_FILE}")
    print("(Shared across all projects — set up once)\n")
    print("You will need an API key from:")
    print("  Leantime → Company Settings → API\n")

    # ── Step 1: URL ──────────────────────────────────────────
    print("── Step 1: Leantime instance URL ──")
    print("Enter the base URL of your Leantime instance.")
    print("Example: https://pm.example.com  (no trailing slash)\n")

    url = ""
    while not url:
        url = ask("LEANTIME_URL").rstrip("/")
        if not url:
            print("URL cannot be empty.")
        elif not url.startswith("http"):
            print("URL must start with http:// or https://")
            url = ""

    # ── Step 2: API key ──────────────────────────────────────
    print("\n── Step 2: API key ──")
    print("Generate a key at: Company Settings → API")
    print("(Input is hidden while you type)\n")

    key = ""
    while not key:
        key = ask_secret("LEANTIME_API_KEY")
        if not key:
            print("API key cannot be empty.")

    # ── Step 3: Probe ─────────────────────────────────────────
    print("\n── Step 3: Verifying connection ──")
    print(f"Connecting to {url}/api/jsonrpc ...")

    ok, msg = probe(url, key)
    if not ok:
        print(f"\nVerification failed: {msg}")
        save_anyway = ask("Save credentials anyway? (yes/no)", "no").lower()
        if save_anyway not in ("yes", "y"):
            print("Credentials NOT saved. Fix the issue and run setup again.")
            return 1
        print("Saving unverified credentials...")
    else:
        print(f"✓ {msg}")

    # ── Step 4: Write config ──────────────────────────────────
    print("\n── Step 4: Saving credentials ──")
    saved_path = write_config(url, key)
    print(f"Saved to {saved_path}  (permissions: 600)")

    # ── Done ──────────────────────────────────────────────────
    print("\n" + "=" * 56)
    print("  Setup complete!")
    print("=" * 56)
    print("\nCredentials are now available to all projects.")
    print("Next step: run  python scripts/check_connection.py  to confirm.")
    print("\nTo override for a specific project, create a .env in that")
    print("project directory — it takes priority over the global config.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
