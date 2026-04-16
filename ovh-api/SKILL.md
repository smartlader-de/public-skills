---
name: ovh-api
description: |
  Manages OVH Cloud infrastructure via the OVH v2 REST API. Handles full lifecycle
  operations across VPS, Dedicated Servers, Public Cloud, Networking, Backup Services,
  Domains & DNS, Hosting, Licenses, and Support — all from natural language. Use this
  skill whenever the user mentions OVH, OVHcloud, their VPS, their dedicated server,
  my OVH account, OVH API, EU datacenter, ca endpoint, us endpoint, or wants to list,
  reboot, reinstall, configure, or delete any OVH resource. On every invocation,
  checks credentials first (from .env or ~/.ovh.conf), presents a read-only vs.
  full-access mode gate, and enforces a triple opt-in plan-validate-execute protocol
  before any destructive operation. Lazy-loads only the relevant product-family
  reference file per task. Guides new users through complete API credential setup with
  no external dependencies required beyond Python 3.8+.
compatibility: Requires Python 3.8+ and network access to eu.api.ovh.com, ca.api.ovh.com, or us.api.ovh.com. No external dependencies required (python-ovh detected opportunistically if already installed).
license: MIT
metadata:
  version: "2.0"
---

# OVH Cloud Skill

Manages OVH Cloud infrastructure via the OVH v2 REST API with safety-first
design: credential check → mode gate → lazy-load product context → execute.

---

## Invocation Workflow (copy and check off each step)

```
OVH Skill Workflow:
- [ ] Step 1: Run scripts/check_credentials.py — handle missing with scripts/setup_auth.py
- [ ] Step 2: Ask user: Read-only or Full access?
- [ ] Step 3: Identify product family (VPS / Dedicated / Cloud / Networking / Backup / Domains / Hosting / Licenses / Support)
- [ ] Step 4: Load ONLY the matching references/<family>.md
- [ ] Step 5: If operation is destructive, load references/destructive-ops.md and run plan-validate-execute
- [ ] Step 6: Execute via scripts/ovh_request.py
```

Copy this checklist into your response and tick off items as you complete them.

---

## Step 1: Credential Check

Before any operation, check for valid credentials:

1. Check for `.env` in the current working directory containing all four keys:
   `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY`, `OVH_ENDPOINT`
2. If `.env` missing or incomplete, check `~/.ovh.conf` (INI format, official OVH config)
3. Run `scripts/check_credentials.py` to validate and confirm endpoint reachability
4. If neither source has valid credentials: run `scripts/setup_auth.py` (interactive wizard)

```bash
python scripts/check_credentials.py
# Exit 0: prints "Connected to OVH account <nickname> at <endpoint>"
# Exit 1: prints exactly what is missing and what to run next
```

---

## Step 2: Mode Selection

After credentials are confirmed, ALWAYS ask before proceeding:

> You are connected to OVH account `{nickname}` at `{endpoint}`.
> Choose mode:
> - **Read-only** (safe — GET requests only, no mutations possible)
> - **Full access** (can modify and delete resources, with triple confirmation for destructive ops)

No default. Wait for explicit answer. Store selection for the duration of this invocation.

### Read-Only Mode Rules

In read-only mode:
- ONLY HTTP GET requests are allowed via `scripts/ovh_request.py`
- POST, PUT, PATCH, DELETE are blocked — the skill MUST refuse and explain
- If the user requests a mutating action, respond: "That operation requires Full access mode.
  Re-invoke the skill and choose Full access when prompted."
- Rationale: prevents accidental mutations during exploration

---

## Step 3: Identify Product Family and Load Reference

Determine which product family the user's task involves:

| Family | Reference file | Load when |
|--------|---------------|-----------|
| VPS | `references/vps.md` | User mentions VPS, virtual private server |
| Dedicated Servers | `references/dedicated.md` | User mentions bare metal, dedicated, dedibox |
| Public Cloud | `references/public-cloud.md` | User mentions cloud instances, volumes, snapshots, object storage |
| Networking | `references/networking.md` | User mentions IP, Load Balancer, vRack, firewall |
| Backup Services | `references/backup.md` | User mentions backup, restore, backupStorage |
| Domains & DNS | `references/domains.md` | User mentions domain, DNS, zone, nameservers |
| Hosting | `references/hosting.md` | User mentions web hosting, shared hosting |
| Licenses | `references/licenses.md` | User mentions license, cPanel, Plesk |
| Support | `references/support.md` | User mentions ticket, support request |

**Rule: Load ONLY the reference file matching the current task. Do not preload multiple files.**

References are one level deep — no reference file links to another reference file.

---

## Destructive Operations

Destructive operations MUST follow the plan-validate-execute protocol.

Triggers: any DELETE, `/reinstall`, `/reboot`, `/terminate`, `/cancel`,
nameserver changes on production domains, firewall rule removal.

**MUST load `references/destructive-ops.md` and run `scripts/validate_destructive.py`
before executing any destructive call.**

See `references/destructive-ops.md` for the full protocol.

---

## Optional: python-ovh

If `pip show python-ovh` succeeds (already installed), Claude MAY use the python-ovh
library instead of `scripts/ovh_request.py` for cleaner auth handling. Not required.
Default path is the stdlib script. Never install python-ovh as a dependency.

---

## Verification

After each operation, run a sanity check:

```bash
python scripts/ovh_request.py --method GET --path /1.0/me
# Should return your account details: {firstname, lastname, nichandle, email}
```

If this fails, run `scripts/check_credentials.py` for diagnosis.

---

*OVH Skill v2.0 — direct OVH v2 API, no third-party wrappers*
