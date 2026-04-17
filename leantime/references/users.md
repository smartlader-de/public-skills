# Leantime Users Reference

Live-tested against a real Leantime instance. All method names, param shapes,
and response schemas are verified.

**This reference is READ-ONLY.** User creation, modification, and deletion
are out of scope. Manage users directly in the Leantime admin interface.

**Endpoint:** `POST $LEANTIME_URL/api/jsonrpc`
**Auth header:** `x-api-key: $LEANTIME_API_KEY`

> **Security warning:** `getUser` returns sensitive fields including the
> bcrypt password hash, active session token, and 2FA secret. Never log or
> expose the full `getUser` response. Use `getAll` when you only need IDs
> and names.

---

## Canonical Request Template

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -H "User-Agent: Mozilla/5.0 (compatible; Leantime-Skill/1.0)" \
  -d '<BODY>'
```

---

## User Object Fields

### From `getAll` (summary shape)

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | User ID — use in ticket `editorId` |
| `firstname` | string | |
| `lastname` | string | |
| `username` | string | Login email |
| `role` | string | Role code (e.g. `"50"` = admin) |
| `status` | string | `"A"` = active |
| `profileId` | string | Avatar reference (`""` = none) |
| `clientId` | int | `0` = internal user |
| `clientName` | null | |
| `jobTitle` | string | |
| `jobLevel` | string | |
| `department` | string | |
| `modified` | string | `"YYYY-MM-DD HH:MM:SS"` |
| `twoFAEnabled` | int | `1` = enabled |

### Additional fields from `getUser` (detail shape — handle with care)

| Field | Type | Sensitivity |
|-------|------|-------------|
| `password` | string | **bcrypt hash — never log or expose** |
| `session` | string | **active session token — never log or expose** |
| `twoFASecret` | string | **TOTP secret — never log or expose** |
| `sessiontime` | string | Unix timestamp of session expiry |
| `phone` | string | |
| `lastlogin` | string | `"YYYY-MM-DD HH:MM:SS"` |
| `expires` | null | Account expiry |
| `wage` | float | |
| `hours` | float | |
| `description` | null | |
| `notifications` | int | |
| `settings` | string | PHP-serialized preferences string |
| `createdOn` | string | `"YYYY-MM-DD HH:MM:SS"` |
| `source` | null | |
| `pwReset` | null | |
| `pwResetExpiration` | null | |
| `pwResetCount` | null | |
| `forcePwReset` | null | |
| `lastpwd_change` | null | |

### Role Codes (observed)

| Code | Meaning |
|------|---------|
| `"50"` | Administrator |

---

## 1. List All Users

**Method:** `leantime.rpc.users.getAll`

**Params:** `{}`

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.users.getAll",
  "params": {}
}
```

**Returns:** Array of user summary objects. Use `id` values here when
assigning tickets (`editorId`) or looking up authors.

---

## 2. Get User by ID

**Method:** `leantime.rpc.users.getUser`

| Param | Type | Required |
|-------|------|----------|
| `id` | int | yes |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.users.getUser",
  "params": { "id": 1 }
}
```

**Returns:** Full user object including sensitive fields. Extract only the
fields you need (`firstname`, `lastname`, `username`, `role`, `status`).

---

## Out-of-Scope Reminder

User creation, modification, and deletion are out of scope in v1.

If asked to create, update, or delete a user, respond:
> "User management is out of scope for this skill. Please manage users
> directly in your Leantime instance under **Settings → Users**."

Do not attempt to call `addUser`, `updateUser`, `deleteUser`, or any variant.

---

## Rate Limiting

Cloudflare enforces ~5 requests/minute. Exceeding it returns:
```json
{"error": "Too many requests per minute."}
```
This is NOT a JSON-RPC envelope. Add 2–4 second delays between calls.
