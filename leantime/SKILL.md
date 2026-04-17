---
name: leantime
description: |
  Manages Leantime projects, tickets, users, and comments via the JSON-RPC 2.0
  API. Use this skill whenever the user mentions Leantime, their project
  management tool, kanban board, self-hosted PM, tickets, tasks, sprints,
  milestones, or wants to list, create, update, or comment on any Leantime
  resource. Connects to the user's own Leantime instance using a single API key.
  On every invocation, runs scripts/check_connection.py first to validate
  credentials and reachability, then lazy-loads only the relevant reference file
  per task. Guides new users through API key setup via references/setup.md.
  All v1 operations are additive (list/get/create/update/add comment) — no
  delete or admin operations are exposed.
compatibility: Leantime v3.x via JSON-RPC 2.0 API, network access to the user's Leantime instance, no external runtime dependencies beyond Python 3.8+
license: MIT
metadata:
  version: "1.0"
---

# Leantime Skill

Manages Leantime projects, tickets, users, and comments via the JSON-RPC 2.0
API. Lightweight auth (single API key), no destructive operations in v1.

---

## Invocation Workflow (copy and check off each step)

```
Leantime Skill Workflow:
- [ ] Step 1: Run scripts/check_connection.py — confirm LEANTIME_URL + LEANTIME_API_KEY are valid
- [ ] Step 2: Identify the target resource (projects / tickets / users / comments)
- [ ] Step 3: Load ONLY the matching references/<resource>.md
- [ ] Step 4: Construct the JSON-RPC request using the canonical curl template below
- [ ] Step 5: Execute via curl
- [ ] Step 6: Verify the response — check for JSON-RPC error object before reporting success
```

Copy this checklist into your response and tick off items as you complete them.

---

## Credential Check

Before any operation, validate credentials and instance reachability:

```bash
python scripts/check_connection.py
# Exit 0: "Connected to <LEANTIME_URL> (API key valid, <N> users visible)"
# Exit 1: prints exactly what is missing or wrong, with remediation steps
```

The script reads `.env` from the current working directory. Required variables:

```
LEANTIME_URL=https://your-leantime.example.com
LEANTIME_API_KEY=<your-api-key>
```

If the script fails, direct the user to `references/setup.md` for full provisioning steps.

---

## JSON-RPC Request Shape

All Leantime API calls use a single endpoint with this structure:

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "<method>",
    "params": { ... }
  }'
```

**Key points:**
- Single endpoint: `POST /api/jsonrpc` — never GET
- Auth header: `x-api-key` (not Bearer, not Basic)
- Every request body is a JSON-RPC 2.0 envelope: `jsonrpc`, `id`, `method`, `params`
- `id` can be any integer or string; use `1` for one-off calls

---

## Resource Routing Table

Determine which reference file to load based on the user's intent:

| User intent | Load this reference |
|-------------|---------------------|
| List projects, get project, create project | `references/projects.md` |
| List tickets, get ticket, create ticket, update ticket | `references/tickets.md` |
| List users, get user by ID | `references/users.md` |
| Add comment, get comments for a ticket | `references/comments.md` |
| First-time setup, credential errors | `references/setup.md` |

**Rule: Load ONLY the reference file matching the current task. Do not preload multiple files.**

References are one level deep — no reference file links to another reference file.

---

## Error Handling

JSON-RPC errors are returned as HTTP 200 with an `error` field in the body:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "..."
  }
}
```

**Handling rules:**
1. Check HTTP status first — 401/403 = bad API key, 404 = wrong URL path
2. If HTTP 200, check body for `error` field before assuming success
3. An HTML response body (not JSON) means the instance URL is wrong or the API path is not exposed
4. Never silently swallow failures — always surface both the `code` and `message` to the user
5. `result: null` with no `error` is a valid success response for some methods

---

## Out of Scope (v1)

The following are explicitly out of scope in v1. Refuse politely and do not attempt:

- Time tracking / timesheets
- User creation, modification, or deletion
- Admin operations and API key management
- Webhooks and event subscriptions
- Any DELETE operation on any resource
