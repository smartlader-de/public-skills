# Leantime Projects Reference

JSON-RPC methods for listing, retrieving, and creating projects.

**JSON-RPC endpoint:** `POST $LEANTIME_URL/api/jsonrpc`
**Auth header:** `x-api-key: $LEANTIME_API_KEY`

---

## Canonical Request Template

All examples below use this envelope:

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '<BODY>'
```

---

## 1. List All Projects

**Method:** `leantime.rpc.projects.getAll`

**Params:** `{}` (no parameters required)

**Request body:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.projects.getAll",
  "params": {}
}
```

**Sample curl:**

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.projects.getAll","params":{}}'
```

**Success response shape:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": [
    {
      "id": "42",
      "name": "Website Redesign",
      "description": "Redesign the company website",
      "status": "active",
      "clientId": "5",
      "ownerId": "3",
      "startDate": "2026-01-01",
      "endDate": "2026-06-30"
    }
  ]
}
```

Key response fields: `id`, `name`, `description`, `status`, `clientId`,
`ownerId`, `startDate`, `endDate`.

---

## 2. Get Project by ID

**Method:** `leantime.rpc.projects.getProject`

**Required params:**

| Param | Type | Description |
|-------|------|-------------|
| `id` | string or int | The project ID |

**Request body:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.projects.getProject",
  "params": { "id": "42" }
}
```

**Sample curl:**

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.projects.getProject","params":{"id":"42"}}'
```

**Success response shape:** Single project object (same fields as list above).

---

## 3. Create Project

**Method:** `leantime.rpc.projects.addProject`

**Required params:**

| Param | Type | Description |
|-------|------|-------------|
| `name` | string | Project name |

**Optional params:**

| Param | Type | Description |
|-------|------|-------------|
| `description` | string | Project description |
| `clientId` | string | Client/organisation ID |
| `ownerId` | string | User ID of project owner |
| `startDate` | string | `YYYY-MM-DD` format |
| `endDate` | string | `YYYY-MM-DD` format |
| `status` | string | e.g. `"active"`, `"inactive"` |

**Request body:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.projects.addProject",
  "params": {
    "name": "Q3 Marketing Campaign",
    "description": "All tasks for the Q3 campaign",
    "startDate": "2026-07-01",
    "endDate": "2026-09-30"
  }
}
```

**Sample curl:**

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.projects.addProject","params":{"name":"Q3 Marketing Campaign","description":"All tasks for the Q3 campaign"}}'
```

**Success response:** Returns the new project `id` or the full project object.

---

## Discovering Method Names

If any documented method above returns a JSON-RPC error `-32601` (Method not
found), the method name may differ in your Leantime version. To investigate:

1. Check the Leantime source at `app/Domain/Projects/Repositories/` and
   `app/Domain/Projects/Services/` for the RPC class names
2. Try variant method names: `leantime.rpc.project.*` (singular)
3. Use `leantime.rpc.projects.getProjectsAssignedToUser` if `getAll` is
   restricted to admins in your version

Always prefer the version that returns results rather than an error.
