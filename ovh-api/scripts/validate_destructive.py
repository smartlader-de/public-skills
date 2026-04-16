#!/usr/bin/env python3
"""
Validate a destructive operation plan before execution.

Usage:
  python scripts/validate_destructive.py /tmp/ovh-pending.json

Reads the plan, confirms the resource exists, checks dependencies,
and warns on production patterns.

Exit codes:
  0 = safe to proceed (prints validation summary)
  1 = blocked (prints specific blockers with resolution steps)
  2 = plan file invalid
  3 = resource not found
"""

import json
import subprocess
import sys
from pathlib import Path


PRODUCTION_PATTERNS = [
    "prod", "production", "live", "main", "primary", "master",
    "www", "api", "mail", "smtp", "mx",
]


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def load_plan(plan_path: str) -> dict:
    path = Path(plan_path)
    if not path.exists():
        err(f"Plan file not found: {plan_path}")
        err("Create the plan before running validation.")
        sys.exit(2)

    try:
        plan = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        err(f"Plan file is not valid JSON: {e}")
        sys.exit(2)

    required = ["resource_type", "resource_id", "method", "path", "irreversible"]
    missing = [k for k in required if k not in plan]
    if missing:
        err(f"Plan is missing required fields: {', '.join(missing)}")
        sys.exit(2)

    return plan


def run_get(path: str) -> tuple[int, dict]:
    """Run a GET request via ovh_request.py. Returns (exit_code, parsed_json_or_empty)."""
    script = Path(__file__).parent / "ovh_request.py"
    result = subprocess.run(
        [sys.executable, str(script), "--method", "GET", "--path", path],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        try:
            return 0, json.loads(result.stdout)
        except json.JSONDecodeError:
            return 0, {}
    return result.returncode, {}


def check_resource_exists(plan: dict) -> tuple[bool, dict]:
    """Confirm the target resource can be fetched."""
    path = plan["path"]
    # For DELETE paths, GET the same path to confirm existence
    code, data = run_get(path)
    if code == 0:
        return True, data
    elif code == 2:
        return False, {}
    else:
        # Network or auth error — can't validate
        return None, {}


def check_vrack_dependencies(resource_id: str) -> list[str]:
    """Check if a vRack has attached servers (deletion would sever them)."""
    blockers = []
    code, data = run_get(f"/v2/vrack/{resource_id}/server")
    if code == 0 and isinstance(data, list) and len(data) > 0:
        blockers.append(
            f"vRack '{resource_id}' has {len(data)} attached server(s): {data[:3]}..."
            "\n  Resolution: detach all servers from the vRack before deleting it."
        )
    return blockers


def check_domain_nameservers(resource_id: str, resource_data: dict) -> list[str]:
    """Warn if domain nameservers are being changed on what looks like a live domain."""
    warnings = []
    # Check DNS zone records count as a proxy for "in use"
    code, records = run_get(f"/v2/domain/zone/{resource_id}/record")
    if code == 0 and isinstance(records, list) and len(records) > 3:
        warnings.append(
            f"Domain '{resource_id}' has {len(records)} DNS records — likely in production use."
            "\n  Consider: export zone before any destructive change."
        )
    return warnings


def check_production_patterns(resource_id: str) -> list[str]:
    """Warn if the resource identifier contains patterns suggesting production."""
    warnings = []
    lower_id = resource_id.lower()
    matched = [p for p in PRODUCTION_PATTERNS if p in lower_id]
    if matched:
        warnings.append(
            f"Resource identifier '{resource_id}' contains production pattern(s): {matched}."
            "\n  Verify this is not a live production resource before proceeding."
        )
    return warnings


def main() -> int:
    if len(sys.argv) < 2:
        err("Usage: python scripts/validate_destructive.py <plan_file.json>")
        return 2

    plan = load_plan(sys.argv[1])

    print(f"\nValidating destructive operation:")
    print(f"  Resource : {plan['resource_type']} / {plan['resource_id']}")
    print(f"  Action   : {plan['method']} {plan['path']}")
    print(f"  Reason   : {plan.get('reason', '(none given)')}")
    print()

    blockers = []
    warnings = []

    # 1. Confirm resource exists
    print("Checking resource exists...", end=" ", flush=True)
    exists, resource_data = check_resource_exists(plan)
    if exists is False:
        print("NOT FOUND")
        blockers.append(
            f"Resource not found: GET {plan['path']} returned 404."
            "\n  Resolution: verify the resource identifier is correct and the resource still exists."
        )
    elif exists is None:
        print("SKIPPED (network/auth error — validate credentials first)")
        warnings.append("Could not confirm resource existence due to a network or auth error.")
    else:
        print("OK")

    # 2. Dependency checks by resource type
    rt = plan["resource_type"].lower()

    if rt == "vrack":
        print("Checking vRack dependencies...", end=" ", flush=True)
        dep_blockers = check_vrack_dependencies(plan["resource_id"])
        if dep_blockers:
            print("BLOCKED")
            blockers.extend(dep_blockers)
        else:
            print("OK")

    if rt in ("domain", "dns", "zone"):
        print("Checking domain activity...", end=" ", flush=True)
        dom_warnings = check_domain_nameservers(plan["resource_id"], resource_data)
        if dom_warnings:
            print("WARN")
            warnings.extend(dom_warnings)
        else:
            print("OK")

    # 3. Production pattern check
    print("Checking for production patterns...", end=" ", flush=True)
    prod_warnings = check_production_patterns(plan["resource_id"])
    if prod_warnings:
        print("WARN")
        warnings.extend(prod_warnings)
    else:
        print("OK")

    print()

    # Report
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  ⚠  {w}")
        print()

    if blockers:
        print("BLOCKED — cannot proceed:")
        for b in blockers:
            print(f"  ✗  {b}")
        print()
        print("Resolve the above issues before attempting this operation.")
        return 1

    print("VALIDATION PASSED")
    print("All checks passed. You may proceed to the triple confirmation step.")
    print("Remember: this action is irreversible. Proceed with care.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
