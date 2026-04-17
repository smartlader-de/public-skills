# Leantime Projects Reference

Live-tested against a real Leantime instance. All method names, param shapes,
and response schemas are verified — not guessed.

**Endpoint:** `POST $LEANTIME_URL/api/jsonrpc`
**Auth header:** `x-api-key: $LEANTIME_API_KEY`
**User-Agent:** Must not be the default Python/urllib UA — Cloudflare blocks it.

> **Critical param shape:** `addProject` and `patch` wrap their data inside
> a `values` or `params` key respectively — NOT as flat top-level params.
> Get this wrong and you get `-32602 Invalid params`.

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

## Project Object Fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Project ID |
| `name` | string | Project name |
| `details` | string | Description (may contain HTML) |
| `clientId` | int\|null | Client ID (`null` = no client) |
| `clientName` | string\|null | Client name (denormalized) |
| `state` | null | Reserved, always null |
| `hourBudget` | string | e.g. `"0"` |
| `dollarBudget` | float | e.g. `0` |
| `menuType` | string | `""` or `"default"` |
| `type` | string | Always `"project"` |
| `parent` | int\|null | Parent project ID (`0` = none) |
| `parentId` | null | Deprecated alias |
| `parentName` | null | Deprecated alias |
| `modified` | string | `"YYYY-MM-DD HH:MM:SS"` |
| `start` | null | Rarely populated |
| `end` | null | Rarely populated |
| `isFavorite` | int | `1` favorited, `0` not |

`getProject` additionally returns: `psettings`, `avatar`, `cover`

---

## 1. List All Projects

**Method:** `leantime.rpc.projects.getAll`

**Params:** `{}`

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.projects.getAll",
  "params": {}
}
```

**Returns:** Array of project objects.

---

## 2. Get Project by ID

**Method:** `leantime.rpc.projects.getProject`

| Param | Type | Required |
|-------|------|----------|
| `id` | int | yes |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.projects.getProject",
  "params": { "id": 2 }
}
```

**Returns:** Single project object with extended fields (`psettings`, `avatar`, `cover`).

---

## 3. Create Project

**Method:** `leantime.rpc.projects.addProject`

> All project data goes inside a `values` object — not flat.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `values.name` | string | **yes** | Missing → `-32000 Undefined array key "name"` |
| `values.details` | string | no | HTML allowed |
| `values.clientId` | int | **yes** | Use `0` for no client — server accesses this key unconditionally (PHP bug) |
| `values.type` | string | no | Default `"project"` |
| `values.hourBudget` | string | no | |
| `values.dollarBudget` | float | no | |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.projects.addProject",
  "params": {
    "values": {
      "name": "Q3 Marketing Campaign",
      "details": "All tasks for the Q3 campaign",
      "clientId": 1
    }
  }
}
```

**Returns:** `[newProjectId]` — array containing the new integer ID.

---

## 4. Patch Project (Partial Update)

**Method:** `leantime.rpc.projects.patch`

> `id` is top-level; fields to change go inside `params`.

| Param | Location | Required |
|-------|----------|----------|
| `id` | top-level | **yes** |
| fields to change | `params.*` | at least one |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.projects.patch",
  "params": {
    "id": 2,
    "params": {
      "name": "Renamed Project",
      "details": "Updated description"
    }
  }
}
```

**Returns:** `[true]` on success.

**Errors:**
- Missing `id` → `-32602 Required Parameter Missing: id`
- Missing `params` → `-32602 Required Parameter Missing: params`

---

## Methods That Do NOT Exist

These return `-32601 Method not found` — do not call them:

| Method | Status |
|--------|--------|
| `getMyProjects` | not found |
| `getUsersProjects` | not found |
| `updateProject` | not found |
| `deleteProject` | not found |

Use `patch` for all updates. There is no delete operation.

---

## Rate Limiting

Cloudflare enforces ~5 requests/minute. Exceeding it returns:
```json
{"error": "Too many requests per minute."}
```
This is NOT a JSON-RPC envelope — check for it separately. Add 2–4 second
delays between calls in scripts.
