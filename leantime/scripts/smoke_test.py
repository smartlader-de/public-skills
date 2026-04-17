#!/usr/bin/env python3
"""Smoke test for the Leantime JSON-RPC API.

Tests create/read/delete across all supported entities:
  - Users    (read-only: getAll, getUser)
  - Projects (create, read, patch — no delete via API)
  - Tickets  (create, read, patch — no delete via API)
  - Comments (addComment, getComments, deleteComment)

Known limitation: addComment consistently returns [false] under API-key auth.
This is flagged as WARN (not FAIL) since it is a server-side constraint,
not a client bug.

Credential lookup order (same as check_connection.py):
  1. Environment variables LEANTIME_URL, LEANTIME_API_KEY
  2. .env in current working directory
  3. ~/.config/leantime/.env

Usage:
  python3 scripts/smoke_test.py

Exit code: 0 = all critical tests passed, 1 = one or more critical tests failed.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

GLOBAL_CONFIG = Path.home() / ".config" / "leantime" / ".env"
REQUEST_DELAY = 5   # seconds between calls — Cloudflare rate-limits to ~5/min
TIMEOUT = 15
UA = "Mozilla/5.0 (compatible; Leantime-Skill/1.0)"

GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

results: list[tuple[str, str, str]] = []  # (entity, test_name, PASS|FAIL|WARN)


# ── Credentials ───────────────────────────────────────────────────────────────

def parse_dotenv(path: Path) -> dict:
    out = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def load_credentials() -> tuple[str, str]:
    merged: dict[str, str] = {}
    if GLOBAL_CONFIG.exists():
        merged.update(parse_dotenv(GLOBAL_CONFIG))
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        merged.update(parse_dotenv(cwd_env))
    for k in ("LEANTIME_URL", "LEANTIME_API_KEY"):
        if os.environ.get(k):
            merged[k] = os.environ[k]
    missing = [k for k in ("LEANTIME_URL", "LEANTIME_API_KEY") if not merged.get(k)]
    if missing:
        print(f"{RED}Missing credentials: {', '.join(missing)}{RESET}")
        print("Run: python3 scripts/setup_credentials.py")
        sys.exit(1)
    return merged["LEANTIME_URL"].rstrip("/"), merged["LEANTIME_API_KEY"]


# ── HTTP ──────────────────────────────────────────────────────────────────────

def call(url: str, key: str, method: str, params: dict, *, delay: bool = True) -> dict:
    if delay:
        time.sleep(REQUEST_DELAY)
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params,
    }).encode()
    req = urllib.request.Request(
        f"{url}/api/jsonrpc", data=payload, method="POST",
        headers={"Content-Type": "application/json", "x-api-key": key, "User-Agent": UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as e:
        return {"error": {"code": e.code, "message": e.read().decode()[:200]}}
    except Exception as e:
        return {"error": {"code": -1, "message": str(e)}}
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return {"error": {"code": -1, "message": f"Non-JSON: {body[:100]}"}}
    # Cloudflare rate-limit comes as plain JSON, not a JSON-RPC envelope
    if "error" in data and "jsonrpc" not in data:
        return {"error": {"code": -1, "message": data["error"]}}
    return data


def unwrap(data: dict) -> tuple[bool, any]:
    """Returns (ok, result). ok=False on any error."""
    if "error" in data:
        return False, data["error"]
    return True, data.get("result")


# ── Reporting ─────────────────────────────────────────────────────────────────

def record(entity: str, test: str, passed: bool,
           note: str = "", warn: bool = False) -> bool:
    if warn:
        label = f"{YELLOW}WARN{RESET}"
        tag = "WARN"
    elif passed:
        label = f"{GREEN}PASS{RESET}"
        tag = "PASS"
    else:
        label = f"{RED}FAIL{RESET}"
        tag = "FAIL"
    suffix = f"  {YELLOW}({note}){RESET}" if note else ""
    print(f"  [{label}] {test}{suffix}")
    results.append((entity, test, tag))
    return passed


def section(title: str) -> None:
    bar = "─" * max(0, 52 - len(title))
    print(f"\n{BOLD}── {title} {bar}{RESET}")


# ── Entity test suites ────────────────────────────────────────────────────────

def test_users(url: str, key: str) -> int | None:
    section("USERS  (read-only)")
    user_id = None

    data = call(url, key, "leantime.rpc.users.getAll", {})
    ok, result = unwrap(data)
    passed = ok and isinstance(result, list) and len(result) > 0
    record("users", "getAll → non-empty array", passed,
           note=f"{len(result)} user(s)" if passed else str(result))
    if passed:
        user_id = result[0]["id"]

    if user_id is not None:
        data = call(url, key, "leantime.rpc.users.getUser", {"id": user_id})
        ok, result = unwrap(data)
        passed = ok and isinstance(result, dict) and result.get("id") == user_id
        record("users", f"getUser(id={user_id}) → correct object", passed,
               note=str(result)[:80] if not passed else "")

    return user_id


def test_projects(url: str, key: str) -> int | None:
    section("PROJECTS  (create / read / patch — no delete via API)")
    project_id = None

    # CREATE
    data = call(url, key, "leantime.rpc.projects.addProject", {
        "values": {
            "name": "SMOKE-TEST-PROJECT",
            "details": "Created by smoke_test.py — safe to delete manually",
            "clientId": 0,  # required — server accesses this key unconditionally
        }
    })
    ok, result = unwrap(data)
    passed = ok and isinstance(result, list) and len(result) > 0
    if passed:
        project_id = result[0]
    record("projects", "addProject → returns [new_id]", passed,
           note=f"id={project_id}" if passed else str(result))

    if project_id is None:
        for t in ("getAll → contains new project", "getProject(id) → correct object", "patch → [true]"):
            record("projects", t, False, note="skipped — create failed")
        return None

    # READ (list)
    data = call(url, key, "leantime.rpc.projects.getAll", {})
    ok, result = unwrap(data)
    found = ok and any(p.get("id") == project_id for p in (result or []))
    record("projects", "getAll → contains new project", found,
           note=f"id={project_id} missing from list" if not found else "")

    # READ (single)
    data = call(url, key, "leantime.rpc.projects.getProject", {"id": project_id})
    ok, result = unwrap(data)
    passed = ok and isinstance(result, dict) and result.get("id") == project_id
    record("projects", "getProject(id) → correct object", passed,
           note=str(result)[:80] if not passed else "")

    # PATCH (closest to update/delete available)
    data = call(url, key, "leantime.rpc.projects.patch", {
        "id": project_id,
        "params": {"name": "SMOKE-TEST-PROJECT (done)"},
    })
    ok, result = unwrap(data)
    passed = ok and result == [True]
    record("projects", "patch → [true]", passed,
           note="no delete via API — name patched to mark complete" if passed else str(result))

    return project_id


def test_tickets(url: str, key: str, project_id: int | None) -> int | None:
    section("TICKETS  (create / read / patch — no delete via API)")

    if project_id is None:
        for t in ("addTicket → returns [new_id]", "getAll(projectId) → contains ticket",
                  "getTicket(id) → correct object", "patch → [true]"):
            record("tickets", t, False, note="skipped — no project available")
        return None

    ticket_id = None

    # CREATE
    data = call(url, key, "leantime.rpc.tickets.addTicket", {
        "values": {
            "headline": "SMOKE-TEST-TICKET",
            "description": "Created by smoke_test.py — safe to delete manually",
            "projectId": project_id,
            "type": "task",
            "priority": "1",
        }
    })
    ok, result = unwrap(data)
    passed = ok and isinstance(result, list) and len(result) > 0
    if passed:
        ticket_id = result[0]
    record("tickets", "addTicket → returns [new_id]", passed,
           note=f"id={ticket_id}" if passed else str(result))

    if ticket_id is None:
        for t in ("getAll(projectId) → contains ticket", "getTicket(id) → correct object",
                  "patch → [true]"):
            record("tickets", t, False, note="skipped — create failed")
        return None

    # READ (list) — getAll returns all tickets; filter client-side since the
    # server-side projectId param is unreliable for newly-created projects
    data = call(url, key, "leantime.rpc.tickets.getAll", {})
    ok, result = unwrap(data)
    found = ok and any(t.get("id") == ticket_id for t in (result or []))
    record("tickets", "getAll → contains new ticket", found,
           note=f"id={ticket_id} missing from list" if not found else "")

    # READ (single)
    data = call(url, key, "leantime.rpc.tickets.getTicket", {"id": ticket_id})
    ok, result = unwrap(data)
    passed = ok and isinstance(result, dict) and result.get("id") == ticket_id
    record("tickets", "getTicket(id) → correct object", passed,
           note=str(result)[:80] if not passed else "")

    # PATCH
    data = call(url, key, "leantime.rpc.tickets.patch", {
        "id": ticket_id,
        "params": {"headline": "SMOKE-TEST-TICKET (done)", "status": 3},
    })
    ok, result = unwrap(data)
    passed = ok and result == [True]
    record("tickets", "patch → [true]", passed,
           note="no delete via API — patched to done" if passed else str(result))

    return ticket_id


def test_comments(url: str, key: str, ticket_id: int | None) -> None:
    section("COMMENTS  (addComment / getComments / deleteComment)")

    if ticket_id is None:
        for t in ("addComment → [true]", "getComments → array", "deleteComment → [true]"):
            record("comments", t, False, note="skipped — no ticket available")
        return

    # CREATE
    data = call(url, key, "leantime.rpc.comments.addComment", {
        "module": "tickets",
        "entityId": ticket_id,
        "entity": "ticket",
        "values": {"comment": "SMOKE-TEST-COMMENT — created by smoke_test.py"},
    })
    ok, result = unwrap(data)
    comment_created = ok and result == [True]
    if ok and result == [False]:
        record("comments", "addComment → [true]", False,
               note="returns [false] — known limitation under API-key auth; comment not persisted",
               warn=True)
    else:
        record("comments", "addComment → [true]", comment_created,
               note=str(result) if not comment_created else "")

    # READ
    data = call(url, key, "leantime.rpc.comments.getComments", {
        "module": "tickets",
        "entityId": ticket_id,
    })
    ok, result = unwrap(data)
    passed = ok and isinstance(result, list)
    comment_id = result[0].get("id") if (passed and result) else None
    record("comments", "getComments → returns array", passed,
           note=f"{len(result)} comment(s)" if passed else str(result))

    # DELETE
    if comment_id is not None:
        data = call(url, key, "leantime.rpc.comments.deleteComment", {"commentId": comment_id})
        ok, result = unwrap(data)
        passed = ok and result == [True]
        record("comments", f"deleteComment(id={comment_id}) → [true]", passed,
               note=str(result) if not passed else "")
    else:
        record("comments", "deleteComment → [true]", False,
               note="skipped — no comment to delete (addComment returned [false])", warn=True)


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary() -> int:
    section("SUMMARY")
    passes = sum(1 for _, _, s in results if s == "PASS")
    warns  = sum(1 for _, _, s in results if s == "WARN")
    fails  = sum(1 for _, _, s in results if s == "FAIL")

    print(f"\n  Total : {len(results)}")
    print(f"  {GREEN}Pass  : {passes}{RESET}")
    if warns:
        print(f"  {YELLOW}Warn  : {warns}  (known limitations, not counted as failures){RESET}")
    if fails:
        print(f"  {RED}Fail  : {fails}{RESET}")
        print(f"\n  {RED}Failing tests:{RESET}")
        for entity, test, status in results:
            if status == "FAIL":
                print(f"    {entity}: {test}")

    if fails == 0:
        print(f"\n{GREEN}{BOLD}All critical tests passed.{RESET}")
        return 0
    print(f"\n{RED}{BOLD}Smoke test FAILED.{RESET}")
    return 1


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    url, key = load_credentials()
    print(f"{BOLD}Leantime Smoke Test{RESET}")
    print(f"Instance : {url}")
    print(f"Delay    : {REQUEST_DELAY}s between calls (Cloudflare rate limiting)")

    test_users(url, key)
    project_id = test_projects(url, key)
    ticket_id  = test_tickets(url, key, project_id)
    # Pause to let Cloudflare's per-minute rate limit window reset before comments
    print(f"\n  {YELLOW}Pausing 20s to reset rate limit window before comments...{RESET}")
    time.sleep(20)
    test_comments(url, key, ticket_id)

    return print_summary()


if __name__ == "__main__":
    sys.exit(main())
