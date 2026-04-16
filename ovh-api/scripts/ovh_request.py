#!/usr/bin/env python3
"""
OVH v2 API request helper with HMAC-SHA1 signing.

Usage:
  python scripts/ovh_request.py --method GET --path /v2/vps
  python scripts/ovh_request.py --method POST --path /v2/vps/vps-abc123/reboot --body '{}'

Reads credentials from .env (CWD) or ~/.ovh.conf. Prints JSON response to stdout.
Structured errors go to stderr with meaningful exit codes.

Exit codes:
  0 = success
  1 = auth error (invalid credentials, signature rejected, expired consumer key)
  2 = not found (404)
  3 = network error (DNS, timeout, connection refused)
  4 = server error (5xx)
  5 = usage error (bad arguments, missing credentials)
"""

import argparse
import configparser
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# --- Constants (with explanations) ---

REQUEST_TIMEOUT = 30
# OVH API occasionally takes 15-20s on /v2/dedicated endpoints; 30s gives safe margin.

MAX_RETRIES = 3
# Most transient 5xx errors resolve by the second retry; more than 3 wastes time.

TIME_DRIFT_THRESHOLD = 30
# OVH rejects requests more than 30s skewed from their server time (signature window).

ENDPOINT_BASES = {
    "ovh-eu": "https://eu.api.ovh.com",
    "ovh-ca": "https://ca.api.ovh.com",
    "ovh-us": "https://us.api.ovh.com",
    "eu": "https://eu.api.ovh.com",
    "ca": "https://ca.api.ovh.com",
    "us": "https://us.api.ovh.com",
    "eu.api.ovh.com": "https://eu.api.ovh.com",
    "ca.api.ovh.com": "https://ca.api.ovh.com",
    "us.api.ovh.com": "https://us.api.ovh.com",
}


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


# --- Credential loading ---

def load_credentials() -> dict:
    """Load credentials from .env (CWD first) or ~/.ovh.conf."""
    creds = _load_dotenv()
    if creds:
        return creds
    creds = _load_ovh_conf()
    if creds:
        return creds
    err("No credentials found in .env (CWD) or ~/.ovh.conf")
    err("Run  python scripts/setup_auth.py  to set up credentials.")
    sys.exit(5)


def _load_dotenv() -> dict | None:
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return None
    raw = {}
    with env_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            raw[k.strip()] = v.strip().strip('"').strip("'")
    required = ["OVH_APPLICATION_KEY", "OVH_APPLICATION_SECRET", "OVH_CONSUMER_KEY", "OVH_ENDPOINT"]
    if all(raw.get(k) for k in required):
        return {
            "app_key": raw["OVH_APPLICATION_KEY"],
            "app_secret": raw["OVH_APPLICATION_SECRET"],
            "consumer_key": raw["OVH_CONSUMER_KEY"],
            "endpoint": raw["OVH_ENDPOINT"],
        }
    return None


def _load_ovh_conf() -> dict | None:
    conf_path = Path.home() / ".ovh.conf"
    if not conf_path.exists():
        return None
    config = configparser.ConfigParser()
    config.read(conf_path)
    for section in ["default"] + list(config.sections()):
        if section not in config:
            continue
        sec = config[section]
        ak = sec.get("application_key", "").strip()
        asc = sec.get("application_secret", "").strip()
        ck = sec.get("consumer_key", "").strip()
        ep = sec.get("endpoint", "").strip()
        if ak and asc and ck and ep:
            return {"app_key": ak, "app_secret": asc, "consumer_key": ck, "endpoint": ep}
    return None


# --- OVH signing ---

def get_server_time(base_url: str) -> int:
    """Fetch OVH server time. Required to avoid clock-drift 401s."""
    url = f"{base_url}/1.0/auth/time"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return int(resp.read().decode())
    except Exception as e:
        err(f"Failed to fetch server time from {url}: {e}")
        err("Cannot sign requests without server time. Check network connectivity.")
        sys.exit(3)


def sign_request(app_secret: str, consumer_key: str, method: str, url: str, body: str, timestamp: int) -> str:
    """
    OVH HMAC-SHA1 signature.
    Formula: "$1$" + SHA1(app_secret + "+" + consumer_key + "+" + method + "+" + url + "+" + body + "+" + timestamp)
    """
    msg = "+".join([app_secret, consumer_key, method.upper(), url, body, str(timestamp)])
    digest = hmac.new(app_secret.encode(), msg.encode(), hashlib.sha1).hexdigest()
    return f"$1${digest}"


# --- HTTP execution ---

def do_request(base_url: str, creds: dict, method: str, path: str, body: str) -> tuple[int, any]:
    """Execute a signed OVH API request. Returns (status_code, parsed_json_or_text)."""
    if not path.startswith("/"):
        path = "/" + path

    full_url = base_url + path
    server_ts = get_server_time(base_url)

    local_ts = int(time.time())
    drift = abs(local_ts - server_ts)
    if drift > TIME_DRIFT_THRESHOLD:
        err(f"WARNING: Local clock is {drift}s off from OVH server time.")
        err("Requests may be rejected. Check your system clock (NTP sync recommended).")

    sig = sign_request(
        creds["app_secret"],
        creds["consumer_key"],
        method,
        full_url,
        body,
        server_ts,
    )

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Ovh-Application": creds["app_key"],
        "X-Ovh-Consumer": creds["consumer_key"],
        "X-Ovh-Timestamp": str(server_ts),
        "X-Ovh-Signature": sig,
    }

    data = body.encode() if body else None
    req = urllib.request.Request(full_url, data=data, headers=headers, method=method.upper())

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                raw = resp.read().decode()
                try:
                    return resp.status, json.loads(raw)
                except json.JSONDecodeError:
                    return resp.status, raw

        except urllib.error.HTTPError as e:
            raw = e.read().decode()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"message": raw}

            if e.code == 401:
                msg = payload.get("message", "")
                err(f"[401 Unauthorized] {msg}")
                if "Invalid signature" in msg or "signature" in msg.lower():
                    err("Signature rejected. Possible causes:")
                    err("  - OVH_APPLICATION_SECRET is wrong")
                    err("  - OVH_CONSUMER_KEY is expired or revoked")
                    err("  - Clock drift > 30s (check system time)")
                    err("Run  python scripts/check_credentials.py  to diagnose.")
                elif "This credential is not valid" in msg or "consumer key" in msg.lower():
                    err("Consumer key is invalid or expired.")
                    err("Run  python scripts/setup_auth.py  to generate a new one.")
                sys.exit(1)

            elif e.code == 403:
                err(f"[403 Forbidden] {payload.get('message', 'Access denied.')}")
                err("Your application key may not have permission for this endpoint.")
                err("Check the access rights granted during consumer key creation.")
                sys.exit(1)

            elif e.code == 404:
                err(f"[404 Not Found] {path}")
                # Suggest parent path for navigation
                parent = "/".join(path.rstrip("/").split("/")[:-1])
                if parent and parent != path:
                    err(f"Try the parent path to list available resources: {parent}")
                sys.exit(2)

            elif e.code >= 500 and attempt < MAX_RETRIES:
                err(f"[{e.code}] Server error on attempt {attempt}/{MAX_RETRIES}. Retrying...")
                time.sleep(2 ** (attempt - 1))
                continue
            elif e.code >= 500:
                err(f"[{e.code}] OVH server error after {MAX_RETRIES} attempts: {payload.get('message', raw)}")
                sys.exit(4)
            else:
                err(f"[{e.code}] {payload.get('message', raw)}")
                sys.exit(4)

        except urllib.error.URLError as e:
            reason = str(e.reason)
            if "Name or service not known" in reason or "nodename nor servname" in reason:
                err(f"DNS failure: cannot resolve OVH API host.")
                err("Check internet connection or try a different endpoint (EU/CA/US).")
                sys.exit(3)
            elif "timed out" in reason.lower():
                if attempt < MAX_RETRIES:
                    err(f"Timeout on attempt {attempt}/{MAX_RETRIES}. Retrying...")
                    continue
                err(f"Connection to {base_url} timed out after {MAX_RETRIES} attempts.")
                sys.exit(3)
            elif "Connection refused" in reason:
                err(f"Connection refused by {base_url}. OVH API may be down.")
                sys.exit(3)
            else:
                err(f"Network error: {reason}")
                sys.exit(3)

    err("Request failed after all retries.")
    sys.exit(4)


def main() -> int:
    parser = argparse.ArgumentParser(description="Make a signed OVH v2 API request")
    parser.add_argument("--method", default="GET", help="HTTP method (GET, POST, PUT, DELETE, PATCH)")
    parser.add_argument("--path", required=True, help="API path, e.g. /v2/vps or /1.0/me")
    parser.add_argument("--body", default="", help="JSON request body (for POST/PUT/PATCH)")
    parser.add_argument("--endpoint", help="Override endpoint (eu/ca/us or full hostname)")
    args = parser.parse_args()

    creds = load_credentials()

    endpoint = args.endpoint or creds["endpoint"]
    base_url = ENDPOINT_BASES.get(endpoint.lower())
    if not base_url:
        err(f"Unknown endpoint: {endpoint}")
        err(f"Valid options: {', '.join(ENDPOINT_BASES.keys())}")
        sys.exit(5)

    creds["endpoint"] = endpoint  # use override if provided

    status, response = do_request(base_url, creds, args.method, args.path, args.body)

    print(json.dumps(response, indent=2))
    return 0 if status < 400 else 4


if __name__ == "__main__":
    sys.exit(main())
