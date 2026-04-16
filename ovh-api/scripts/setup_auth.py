#!/usr/bin/env python3
"""
Interactive OVH API credential setup wizard.

Guides the user through:
1. Choose region (EU / CA / US)
2. Create an OVH API application (opens browser)
3. Enter app key + app secret
4. Generate consumer key (POST /1.0/auth/credential)
5. Validate in browser
6. Verify via /1.0/me
7. Persist to .env via write_env.py
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path


ENDPOINTS = {
    "eu": {
        "base": "https://eu.api.ovh.com",
        "create_app_url": "https://eu.api.ovh.com/createApp/",
        "label": "Europe (eu.api.ovh.com)",
    },
    "ca": {
        "base": "https://ca.api.ovh.com",
        "create_app_url": "https://ca.api.ovh.com/createApp/",
        "label": "Canada (ca.api.ovh.com)",
    },
    "us": {
        "base": "https://us.api.ovh.com",
        "create_app_url": "https://us.api.ovh.com/createApp/",
        "label": "United States (us.api.ovh.com)",
    },
}

# Request full access rights; user can restrict on the OVH portal
ACCESS_RULES = [
    {"method": "GET", "path": "/*"},
    {"method": "POST", "path": "/*"},
    {"method": "PUT", "path": "/*"},
    {"method": "DELETE", "path": "/*"},
]


def ask(prompt: str, default: str = "") -> str:
    default_hint = f" [{default}]" if default else ""
    try:
        val = input(f"{prompt}{default_hint}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nSetup cancelled.")
        sys.exit(0)
    return val or default


def open_url(url: str) -> None:
    """Open a URL — tries webbrowser.open, falls back to print."""
    opened = False
    try:
        opened = webbrowser.open(url)
    except Exception:
        pass
    if not opened:
        print(f"\n  Open this URL in your browser:\n  {url}\n")
    else:
        print(f"  (Opened in browser: {url})")


def post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"message": raw}
        raise RuntimeError(f"HTTP {e.code}: {data.get('message', raw)}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def get_json(base_url: str, path: str, app_key: str, consumer_key: str, app_secret: str) -> dict:
    """Simple GET with OVH auth (uses ovh_request.py subprocess for signing)."""
    script = Path(__file__).parent / "ovh_request.py"
    result = subprocess.run(
        [sys.executable, str(script), "--method", "GET", "--path", path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)


def step_choose_region() -> dict:
    print("\n── Step 1: Choose your OVH region ──")
    for key, info in ENDPOINTS.items():
        print(f"  {key.upper()}  {info['label']}")
    region = ask("Region", "eu").lower()
    if region not in ENDPOINTS:
        print(f"Invalid region '{region}'. Defaulting to EU.")
        region = "eu"
    ep = ENDPOINTS[region]
    print(f"Using: {ep['label']}")
    return {"region": region, **ep}


def step_create_app(ep: dict) -> tuple[str, str]:
    print("\n── Step 2: Create an OVH API application ──")
    print("You need an Application Key and Application Secret from the OVH portal.")
    print(f"\nOpening: {ep['create_app_url']}")
    open_url(ep["create_app_url"])
    print("\nOn that page:")
    print("  1. Log in with your OVH account")
    print("  2. Fill in any name and description for the application")
    print("  3. Click 'Create keys'")
    print("  4. Copy the Application Key and Application Secret shown\n")

    app_key = ""
    while not app_key:
        app_key = ask("Paste your Application Key").strip()
        if not app_key:
            print("Application Key cannot be empty.")

    app_secret = ""
    while not app_secret:
        app_secret = ask("Paste your Application Secret").strip()
        if not app_secret:
            print("Application Secret cannot be empty.")

    return app_key, app_secret


def step_generate_consumer_key(ep: dict, app_key: str) -> tuple[str, str]:
    print("\n── Step 3: Generate a Consumer Key ──")
    print("Requesting a validation URL from OVH...")

    url = f"{ep['base']}/1.0/auth/credential"
    payload = {
        "accessRules": ACCESS_RULES,
        "redirection": "https://eu.api.ovh.com/console/",
    }

    try:
        # POST requires only X-Ovh-Application header (no signing)
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Ovh-Application": app_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"message": raw}
        if e.code == 403:
            print(f"\nERROR: Application key rejected ({data.get('message', 'forbidden')}).")
            print("Double-check that you pasted the Application Key correctly (not the secret).")
            sys.exit(1)
        print(f"\nERROR [HTTP {e.code}]: {data.get('message', raw)}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\nERROR: Could not reach {ep['base']}: {e.reason}")
        print("Check your internet connection.")
        sys.exit(1)

    consumer_key = data["consumerKey"]
    validation_url = data["validationUrl"]

    print(f"\nValidation URL: {validation_url}")
    print("\nOpening validation page...")
    open_url(validation_url)
    print("\nOn that page:")
    print("  1. Log in with your OVH account (if not already)")
    print("  2. Choose the validity period (recommend: 'Unlimited')")
    print("  3. Click 'Log in and authorize access'")
    print("  4. Come back here once done\n")

    ask("Press Enter once you have authorized access", "")
    return consumer_key, validation_url


def step_verify(ep: dict, app_key: str, app_secret: str, consumer_key: str) -> dict:
    print("\n── Step 4: Verify connection ──")
    print("Checking credentials via /1.0/me ...")

    # Write temp .env so ovh_request.py can pick it up
    tmp_env = Path.cwd() / ".env.ovh_setup_tmp"
    endpoint_key = f"ovh-{ep['region']}"
    tmp_env.write_text(
        f"OVH_APPLICATION_KEY={app_key}\n"
        f"OVH_APPLICATION_SECRET={app_secret}\n"
        f"OVH_CONSUMER_KEY={consumer_key}\n"
        f"OVH_ENDPOINT={endpoint_key}\n"
    )

    # Temporarily point CWD .env to our temp file by symlinking or renaming
    env_path = Path.cwd() / ".env"
    renamed_existing = None
    if env_path.exists():
        renamed_existing = Path.cwd() / ".env.pre_setup_backup"
        env_path.rename(renamed_existing)
    tmp_env.rename(env_path)

    try:
        script = Path(__file__).parent / "ovh_request.py"
        result = subprocess.run(
            [sys.executable, str(script), "--method", "GET", "--path", "/1.0/me"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        me = json.loads(result.stdout)
        return me
    finally:
        # Restore: rename .env back to tmp, then restore old .env if any
        if env_path.exists():
            env_path.rename(tmp_env)
        if renamed_existing and renamed_existing.exists():
            renamed_existing.rename(env_path)
        if tmp_env.exists():
            tmp_env.unlink(missing_ok=True)


def step_persist(ep: dict, app_key: str, app_secret: str, consumer_key: str) -> None:
    print("\n── Step 5: Save credentials ──")
    script = Path(__file__).parent / "write_env.py"
    result = subprocess.run(
        [
            sys.executable, str(script),
            "--app-key", app_key,
            "--app-secret", app_secret,
            "--consumer-key", consumer_key,
            "--endpoint", ep["region"],
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 1 and "already exists" in result.stderr:
        overwrite = ask(".env already exists. Overwrite? (yes/no)", "no").lower()
        if overwrite in ("yes", "y"):
            subprocess.run(
                [
                    sys.executable, str(script),
                    "--app-key", app_key,
                    "--app-secret", app_secret,
                    "--consumer-key", consumer_key,
                    "--endpoint", ep["region"],
                    "--force",
                ],
                check=True,
            )
        else:
            print("Skipped saving. Your credentials were NOT persisted.")
            print(f"  OVH_APPLICATION_KEY={app_key}")
            print(f"  OVH_APPLICATION_SECRET={app_secret}")
            print(f"  OVH_CONSUMER_KEY={consumer_key}")
            print(f"  OVH_ENDPOINT=ovh-{ep['region']}")
            return
    elif result.returncode != 0:
        print(f"ERROR saving .env: {result.stderr.strip()}")
        print("Credentials (copy manually):")
        print(f"  OVH_APPLICATION_KEY={app_key}")
        print(f"  OVH_APPLICATION_SECRET={app_secret}")
        print(f"  OVH_CONSUMER_KEY={consumer_key}")
        print(f"  OVH_ENDPOINT=ovh-{ep['region']}")
        return
    print(result.stdout.strip())


def main() -> int:
    print("=" * 60)
    print("  OVH API Credential Setup Wizard")
    print("=" * 60)
    print("\nThis wizard sets up OVH API credentials in .env (current directory).")
    print("You will need access to your OVH account in a browser.\n")

    ep = step_choose_region()
    app_key, app_secret = step_create_app(ep)
    consumer_key, _ = step_generate_consumer_key(ep, app_key)

    print("\nVerifying credentials...")
    try:
        me = step_verify(ep, app_key, app_secret, consumer_key)
        nickname = me.get("nichandle", me.get("login", "unknown"))
        name = f"{me.get('firstname', '')} {me.get('name', '')}".strip()
        print(f"Verified! Connected as: {nickname} ({name})")
    except RuntimeError as e:
        print(f"\nVerification failed: {e}")
        print("The consumer key may not have been authorized yet.")
        print("Go back to the validation URL and authorize, then run this script again.")
        return 1

    step_persist(ep, app_key, app_secret, consumer_key)

    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("=" * 60)
    print("\nNext step: run  python scripts/check_credentials.py  to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
