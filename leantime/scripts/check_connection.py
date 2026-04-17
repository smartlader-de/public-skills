#!/usr/bin/env python3
"""Check Leantime credentials and probe instance reachability.

Credential lookup order (highest priority first):
  1. Environment variables (LEANTIME_URL, LEANTIME_API_KEY)
  2. .env in the current working directory  (project-specific override)
  3. ~/.config/leantime/.env               (global user config, written by setup_credentials.py)
"""

import json
import os
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

REQUIRED_KEYS = ["LEANTIME_URL", "LEANTIME_API_KEY"]
PROBE_TIMEOUT = 10
PROBE_METHOD = "leantime.rpc.users.getAll"
GLOBAL_CONFIG = Path.home() / ".config" / "leantime" / ".env"


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def parse_dotenv(path: Path) -> dict:
    """Parse a .env file. Returns dict of key→value."""
    result = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            result[key.strip()] = val.strip().strip('"').strip("'")
    return result


def load_credentials() -> tuple[str, str] | None:
    """
    Merge credentials from all sources (later sources win) then validate.
    Returns (url, key) or None on failure.
    """
    merged: dict[str, str] = {}
    sources_checked: list[str] = []

    # Source 3 (lowest): global user config
    if GLOBAL_CONFIG.exists():
        merged.update(parse_dotenv(GLOBAL_CONFIG))
        sources_checked.append(str(GLOBAL_CONFIG))
    else:
        sources_checked.append(f"{GLOBAL_CONFIG} (not found)")

    # Source 2: project .env in CWD
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        merged.update(parse_dotenv(cwd_env))
        sources_checked.append(str(cwd_env))
    else:
        sources_checked.append(f"{cwd_env} (not found)")

    # Source 1 (highest): environment variables
    for k in REQUIRED_KEYS:
        if os.environ.get(k):
            merged[k] = os.environ[k]

    missing = [k for k in REQUIRED_KEYS if not merged.get(k)]
    if missing:
        err(f"Missing required variable(s): {', '.join(missing)}")
        err("")
        err("Checked (in priority order):")
        err("  1. Environment variables")
        for s in reversed(sources_checked):
            err(f"  2/3. {s}")
        err("")
        err("Run the setup wizard:  python scripts/setup_credentials.py")
        err("Or see references/setup.md for manual instructions.")
        return None

    return merged["LEANTIME_URL"].rstrip("/"), merged["LEANTIME_API_KEY"]


def probe(url: str, key: str) -> int:
    """POST a probe request. Returns user count on success, -1 on failure."""
    endpoint = f"{url}/api/jsonrpc"
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": "skill-probe",
        "method": PROBE_METHOD,
        "params": {},
    }).encode()

    req = urllib.request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "User-Agent": "Mozilla/5.0 (compatible; Leantime-Skill/1.0)",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code in (401, 403):
            err(f"HTTP {e.code}: API key rejected.")
            err("Generate a new key at: Company Settings → API")
            err("Then re-run:  python scripts/setup_credentials.py")
            return -1
        if e.code == 404:
            err(f"HTTP 404: endpoint not found at {endpoint}")
            err("Check that LEANTIME_URL points to your Leantime root URL")
            err("(e.g. https://pm.example.com, not https://pm.example.com/api)")
            return -1
        err(f"HTTP {e.code} from {endpoint}: {body[:200]}")
        return -1
    except urllib.error.URLError as e:
        reason = str(e.reason)
        if any(x in reason for x in ("Name or service not known", "nodename nor servname", "Name does not resolve")):
            err("DNS failure: cannot resolve host in LEANTIME_URL")
            err(f"  URL tried: {endpoint}")
            err("Check that LEANTIME_URL is correct and the hostname resolves.")
        elif "timed out" in reason.lower() or isinstance(e.reason, socket.timeout):
            err(f"Connection to {url} timed out after {PROBE_TIMEOUT}s.")
            err("The instance may be slow, down, or behind a firewall.")
        elif "Connection refused" in reason:
            err(f"Connection refused at {url}")
            err("Confirm the Leantime service is running and the port is correct.")
        else:
            err(f"Network error: {reason}")
            err(f"  URL tried: {endpoint}")
        return -1
    except socket.timeout:
        err(f"Connection to {url} timed out after {PROBE_TIMEOUT}s.")
        return -1

    if body.lstrip().startswith("<"):
        err("Received an HTML response instead of JSON.")
        err("A reverse proxy or login page is intercepting the request.")
        err("Verify LEANTIME_URL is the correct root and /api/jsonrpc is exposed.")
        return -1

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        err(f"Malformed JSON response from {endpoint}")
        err(f"First 200 chars: {body[:200]}")
        return -1

    if "error" in data:
        code = data["error"].get("code", "?")
        message = data["error"].get("message", "unknown error")
        err(f"JSON-RPC error {code}: {message}")
        if code in (-32600, -32601):
            err("The API key may lack permissions for the probe method.")
        return -1

    result = data.get("result", [])
    return len(result) if isinstance(result, list) else 1


def main() -> int:
    creds = load_credentials()
    if creds is None:
        return 1

    url, key = creds
    user_count = probe(url, key)
    if user_count < 0:
        return 1

    print(f"Connected to {url} (API key valid, {user_count} users visible)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
