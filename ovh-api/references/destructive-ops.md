# Destructive Operations — Plan-Validate-Execute Protocol

## Table of Contents

1. [What Counts as Destructive](#1-what-counts-as-destructive)
2. [Protocol Overview](#2-protocol-overview)
3. [Step 1: Plan (Write Intent)](#3-step-1-plan-write-intent)
4. [Step 2: Validate (Run Validator)](#4-step-2-validate-run-validator)
5. [Step 3: Triple Confirmation](#5-step-3-triple-confirmation)
6. [Step 4: Execute](#6-step-4-execute)
7. [Step 5: Log](#7-step-5-log)
8. [Rules That Cannot Be Bypassed](#8-rules-that-cannot-be-bypassed)
9. [Examples](#9-examples)

---

## 1. What Counts as Destructive

Any operation that cannot be reversed after execution:

| Category | Triggers |
|----------|----------|
| Resource deletion | `DELETE` on any resource endpoint |
| Server operations | `/reinstall`, `/reboot` (if service is in use) |
| Termination | `/terminate`, `/cancel` |
| Domain changes | Nameserver changes on production domains |
| Network security | Firewall rule removal (can lock out server access) |
| Scheduled actions | Any task that starts a countdown to deletion |

**Rule of thumb**: if the action loses data, changes routing, or removes access — it is destructive.

---

## 2. Protocol Overview

```
1. PLAN     → Write intent to /tmp/ovh-pending.json
2. VALIDATE → Run scripts/validate_destructive.py — check resource exists + dependencies
3. CONFIRM  → Three explicit user confirmations
4. EXECUTE  → Call scripts/ovh_request.py with plan's method/path
5. LOG      → Append result to ~/.ovh-skill-history.log
```

This protocol exists to prevent mistakes, not to annoy. Never skip any step, even if the user says "yes to everything" or "just do it". The three confirmations are deliberately spread across separate prompts — a distracted user should catch at least one.

---

## 3. Step 1: Plan (Write Intent)

Before any destructive action, write the intended operation to a plan file:

```bash
# Create the plan
cat > /tmp/ovh-pending.json << 'EOF'
{
  "resource_type": "vps",
  "resource_id": "vps-abc123.ovh.net",
  "method": "DELETE",
  "path": "/v2/vps/vps-abc123.ovh.net",
  "reason": "User requested deletion of test VPS",
  "irreversible": true,
  "timestamp": "2026-04-16T10:30:00Z"
}
EOF
```

Required fields:
- `resource_type` — category (vps, dedicated, domain, etc.)
- `resource_id` — unique identifier of the resource
- `method` — HTTP method
- `path` — full API path
- `reason` — why this action is being taken (for the log)
- `irreversible` — always `true` for destructive ops

---

## 4. Step 2: Validate (Run Validator)

```bash
python scripts/validate_destructive.py /tmp/ovh-pending.json
# Exit 0: safe to proceed — prints validation summary
# Non-zero: blocked — prints specific blockers and resolutions
```

The validator:
1. Confirms the resource exists (GET request)
2. Checks for dependencies that would be affected
3. Warns on patterns indicating production use
4. Returns a structured report

Do **not** proceed if the validator returns non-zero. The blockers must be resolved first.

---

## 5. Step 3: Triple Confirmation

Only after validation passes, present three separate confirmation prompts. Do not combine them.

**Confirmation 1 — Describe and ask:**
```
You are about to DELETE vps-abc123.ovh.net (VPS, Paris datacenter, 2 vCPU / 4 GB RAM).
This action is IRREVERSIBLE. All data on this server will be lost permanently.

Are you sure you want to proceed? (yes / no)
```
Wait for explicit `yes`. Any other response = abort.

**Confirmation 2 — Type the resource identifier:**
```
To confirm, type the resource identifier exactly as shown:
  vps-abc123.ovh.net
```
Compare input character-by-character. Any mismatch = abort with: "Identifier did not match. Action cancelled."

**Confirmation 3 — Final commit:**
```
This cannot be undone. Type CONFIRM (all caps) to proceed.
```
Only `CONFIRM` (exact, case-sensitive) proceeds. Anything else = abort.

---

## 6. Step 4: Execute

Only after all three confirmations pass:

```bash
python scripts/ovh_request.py \
  --method DELETE \
  --path /v2/vps/vps-abc123.ovh.net
```

Capture the response. Report success or failure clearly to the user.

---

## 7. Step 5: Log

Append the executed action to the history log:

```bash
echo "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"resource\":\"vps-abc123.ovh.net\",\"action\":\"DELETE\",\"outcome\":\"success\"}" >> ~/.ovh-skill-history.log
```

The log file is append-only. It provides an audit trail in case of disputes.

---

## 8. Rules That Cannot Be Bypassed

1. **Never skip the protocol** — even if the user says "I'm sure", "yes to all", or "skip confirmations"
2. **Never proceed after a failed confirmation** — abort completely, do not re-ask
3. **Never combine confirmation prompts** — each must be a separate response
4. **Never execute if validator returns non-zero** — resolve blockers first
5. **Always log** — even failed attempts should be logged with outcome: "cancelled" or "blocked"

---

## 9. Examples

### Delete a VPS

```bash
# Step 1: Plan
cat > /tmp/ovh-pending.json << 'EOF'
{"resource_type":"vps","resource_id":"vps-test.ovh.net","method":"DELETE","path":"/v2/vps/vps-test.ovh.net","reason":"user requested cleanup","irreversible":true}
EOF

# Step 2: Validate
python scripts/validate_destructive.py /tmp/ovh-pending.json

# Step 3: Triple confirmation (interactive — handled by Claude, not scripted)

# Step 4: Execute
python scripts/ovh_request.py --method DELETE --path /v2/vps/vps-test.ovh.net
```

### Reinstall a Dedicated Server

The reinstall path for dedicated is:
```
POST /v2/dedicated/server/{serviceName}/reinstall
```
Body: `{"templateName": "ubuntu2204-server_64", "sshKey": "my-key"}`

This is destructive (overwrites all data). Full protocol applies.
