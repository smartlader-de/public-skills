# Leantime Users Reference

JSON-RPC methods for listing and retrieving users.

**This reference is READ-ONLY in v1.** User creation, modification, and
deletion are out of scope. If a user asks to create or modify a user account,
refuse and explain that user management must be done directly in the Leantime
admin interface.

**JSON-RPC endpoint:** `POST $LEANTIME_URL/api/jsonrpc`
**Auth header:** `x-api-key: $LEANTIME_API_KEY`

---

## Canonical Request Template

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '<BODY>'
```

---

## Common User Fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | User ID (used in ticket `editorId`, comment `userId`) |
| `firstname` | string | First name |
| `lastname` | string | Last name |
| `username` | string | Login username (often email address) |
| `role` | string | e.g. `"admin"`, `"editor"`, `"viewer"`, `"client"` |
| `status` | string | `"1"` active, `"0"` inactive |
| `profileId` | string | Profile / avatar reference |

---

## 1. List All Users

**Method:** `leantime.rpc.users.getAll`

**Params:** `{}` (no parameters required)

**Request body:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.users.getAll",
  "params": {}
}
```

**Sample curl:**

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.users.getAll","params":{}}'
```

**Success response shape:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": [
    {
      "id": "3",
      "firstname": "Alice",
      "lastname": "Smith",
      "username": "alice@example.com",
      "role": "admin",
      "status": "1"
    },
    {
      "id": "7",
      "firstname": "Bob",
      "lastname": "Jones",
      "username": "bob@example.com",
      "role": "editor",
      "status": "1"
    }
  ]
}
```

Use the `id` values here to look up or assign users in tickets (`editorId`)
and comments (`userId`).

---

## 2. Get User by ID

**Method:** `leantime.rpc.users.getUser`

**Required params:**

| Param | Type | Description |
|-------|------|-------------|
| `id` | string | The user ID |

**Request body:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.users.getUser",
  "params": { "id": "7" }
}
```

**Sample curl:**

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.users.getUser","params":{"id":"7"}}'
```

**Success response:** Single user object (same fields as list above).

---

## Out-of-Scope Reminder

**User creation, modification, and deletion are out of scope in v1.**

If the user asks to:
- Create a new user account
- Change a user's password, role, or email
- Delete or deactivate a user

Respond: "User management is out of scope for this skill in v1. Please manage
users directly in your Leantime instance under **Settings → Users**."

Do not attempt to call any `addUser`, `updateUser`, or `deleteUser` methods.
