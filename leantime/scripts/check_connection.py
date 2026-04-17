#!/usr/bin/env python3
"""Check Leantime credentials from .env (CWD) and probe instance reachability."""

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


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def load_dotenv() -> dict:
    """Parse .env from CWD. Returns dict of key→value (may be empty/incomplete)."""
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return {}

    result = {}
    with env_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            result[key.strip()] = val.strip().strip('"').strip("'")
    return result


def load_credentials() -> tuple[str, str] | None:
    """Load and validate LEANTIME_URL and LEANTIME_API_KEY. Returns (url, key) or None."""
    env = {**load_dotenv(), **os.environ}

    missing = [k for k in REQUIRED_KEYS if not env.get(k)]
    if missing:
        err(f"Missing required variable(s): {', '.join(missing)}")
        err("")
        env_path = Path.cwd() / ".env"
        if not env_path.exists():
            err(f"No .env file found in {Path.cwd()}")
        else:
            err(f".env found at {env_path} but missing the above variable(s)")
        err("")
        err("Create or update .env with:")
        for k in missing:
            err(f"  {k}=<value>")
        err("")
        err("See references/setup.md for full provisioning instructions.")
        err("Or run:  python scripts/setup_credentials.py  for an interactive setup wizard.")
        return None

    url = env["LEANTIME_URL"].rstrip("/")
    key = env["LEANTIME_API_KEY"]
    return url, key


def probe(url: str, key: str) -> int:
    """
    POST a probe request to the JSON-RPC endpoint.
    Returns the number of users on success, or raises on failure.
    """
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
            err("Then update LEANTIME_API_KEY in your .env")
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
            err(f"DNS failure: cannot resolve host in LEANTIME_URL")
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

    # Check for HTML response (proxy / login redirect)
    stripped = body.lstrip()
    if stripped.startswith("<"):
        err("Received an HTML response instead of JSON.")
        err("This usually means a reverse proxy or login page is intercepting the request.")
        err("Verify:")
        err("  - LEANTIME_URL is the correct base URL")
        err("  - /api/jsonrpc is exposed by your Leantime instance (v3.x required)")
        err("  - No VPN or IP allowlist is blocking access")
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
    if not isinstance(result, list):
        # Some Leantime versions wrap in a dict; count keys as a fallback
        return 1

    return len(result)


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
