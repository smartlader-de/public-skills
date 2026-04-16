#!/usr/bin/env python3
"""Check OVH credentials from .env (CWD) or ~/.ovh.conf and probe endpoint reachability."""

import configparser
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REQUIRED_ENV_KEYS = ["OVH_APPLICATION_KEY", "OVH_APPLICATION_SECRET", "OVH_CONSUMER_KEY", "OVH_ENDPOINT"]
VALID_ENDPOINTS = {
    "ovh-eu": "eu.api.ovh.com",
    "ovh-ca": "ca.api.ovh.com",
    "ovh-us": "us.api.ovh.com",
    "eu": "eu.api.ovh.com",
    "ca": "ca.api.ovh.com",
    "us": "us.api.ovh.com",
}
ENDPOINT_URLS = {
    "eu.api.ovh.com": "https://eu.api.ovh.com",
    "ca.api.ovh.com": "https://ca.api.ovh.com",
    "us.api.ovh.com": "https://us.api.ovh.com",
}
PROBE_TIMEOUT = 10  # OVH /auth/time is fast; 10s is generous


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def load_from_dotenv() -> dict | None:
    """Load credentials from .env in CWD. Returns dict or None if not found/incomplete."""
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return None

    creds = {}
    with env_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                creds[key.strip()] = val.strip().strip('"').strip("'")

    missing = [k for k in REQUIRED_ENV_KEYS if not creds.get(k)]
    if missing:
        err(f".env found at {env_path} but missing: {', '.join(missing)}")
        err("Run scripts/setup_auth.py to generate missing credentials.")
        return None

    return {
        "app_key": creds["OVH_APPLICATION_KEY"],
        "app_secret": creds["OVH_APPLICATION_SECRET"],
        "consumer_key": creds["OVH_CONSUMER_KEY"],
        "endpoint": creds["OVH_ENDPOINT"],
        "source": f".env ({env_path})",
    }


def load_from_ovh_conf() -> dict | None:
    """Load credentials from ~/.ovh.conf (official OVH INI format)."""
    conf_path = Path.home() / ".ovh.conf"
    if not conf_path.exists():
        return None

    config = configparser.ConfigParser()
    config.read(conf_path)

    # Try sections in preference order: default, then any named section
    sections_to_try = ["default"] + [s for s in config.sections() if s != "default"]

    for section in sections_to_try:
        if section not in config:
            continue
        sec = config[section]
        app_key = sec.get("application_key", "").strip()
        app_secret = sec.get("application_secret", "").strip()
        consumer_key = sec.get("consumer_key", "").strip()
        endpoint = sec.get("endpoint", "").strip()

        if not all([app_key, app_secret, consumer_key, endpoint]):
            continue

        return {
            "app_key": app_key,
            "app_secret": app_secret,
            "consumer_key": consumer_key,
            "endpoint": endpoint,
            "source": f"~/.ovh.conf [section: {section}]",
        }

    err(f"~/.ovh.conf found at {conf_path} but no complete section with all four credentials.")
    err("Missing: application_key, application_secret, consumer_key, endpoint")
    err("Run scripts/setup_auth.py to set up credentials.")
    return None


def resolve_endpoint_url(endpoint: str) -> str | None:
    """Convert endpoint alias or hostname to full base URL."""
    endpoint = endpoint.lower().strip()
    if endpoint in VALID_ENDPOINTS:
        host = VALID_ENDPOINTS[endpoint]
        return ENDPOINT_URLS[host]
    # Direct hostname
    for host, url in ENDPOINT_URLS.items():
        if endpoint == host or endpoint == url or endpoint.endswith(host):
            return url
    return None


def probe_endpoint(base_url: str) -> bool:
    """Probe /auth/time to confirm the endpoint is reachable."""
    url = f"{base_url}/1.0/auth/time"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as resp:
            _ = resp.read()
            return True
    except urllib.error.HTTPError as e:
        # /auth/time returns 200 even without auth; any HTTP response means reachable
        return e.code < 500
    except urllib.error.URLError as e:
        reason = str(e.reason)
        if "Name or service not known" in reason or "nodename nor servname" in reason:
            err(f"DNS failure: cannot resolve {base_url.split('//')[1]}")
            err("Check your internet connection or try a different endpoint (EU/CA/US).")
        elif "timed out" in reason.lower():
            err(f"Connection to {base_url} timed out after {PROBE_TIMEOUT}s.")
            err("OVH API may be temporarily slow. Try again in a moment.")
        else:
            err(f"Network error reaching {base_url}: {reason}")
        return False


def main() -> int:
    creds = load_from_dotenv()
    source_tried = [".env (CWD)"]

    if creds is None:
        creds = load_from_ovh_conf()
        source_tried.append("~/.ovh.conf")

    if creds is None:
        err("No valid OVH credentials found.")
        err(f"Checked: {', '.join(source_tried)}")
        err("")
        err("Next step: run  python scripts/setup_auth.py  to create credentials.")
        return 1

    base_url = resolve_endpoint_url(creds["endpoint"])
    if base_url is None:
        err(f"Unrecognised endpoint: '{creds['endpoint']}'")
        err(f"Valid values: {', '.join(VALID_ENDPOINTS.keys())}")
        err("Edit your credentials source and correct the endpoint.")
        return 1

    if not probe_endpoint(base_url):
        # probe_endpoint already printed a specific error
        return 1

    result = {
        "status": "ok",
        "source": creds["source"],
        "endpoint": creds["endpoint"],
        "base_url": base_url,
        "app_key": creds["app_key"][:4] + "****",  # partial display only
    }
    print(json.dumps(result))
    print(f"Connected via {creds['source']} → {base_url}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
