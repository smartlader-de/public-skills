# Leantime Tickets Reference

JSON-RPC methods for listing, retrieving, creating, and updating tickets
(also called "to-dos" or "tasks" in Leantime's UI).

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

## Common Ticket Fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Ticket ID (read) |
| `headline` | string | Ticket title / summary |
| `description` | string | Full description (may contain HTML) |
| `projectId` | string | Parent project ID |
| `editorId` | string | Assigned user ID |
| `status` | string/int | e.g. `"0"` open, `"1"` done (varies by Leantime version) |
| `priority` | string | `"1"` low, `"2"` medium, `"3"` high |
| `type` | string | e.g. `"story"`, `"bug"`, `"task"`, `"subtask"` |
| `dateToFinish` | string | Due date `YYYY-MM-DD HH:MM:SS` |
| `tags` | string | Comma-separated tag string |
| `storypoints` | string/int | Story point estimate |
| `milestoneid` | string | Associated milestone ID |

---

## 1. List Tickets

**Method:** `leantime.rpc.tickets.getAll`

**Optional params:**

| Param | Type | Description |
|-------|------|-------------|
| `projectId` | string | Filter to a specific project (omit for all tickets) |

**Request body (all tickets):**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.getAll",
  "params": {}
}
```

**Request body (filtered to project 42):**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.getAll",
  "params": { "projectId": "42" }
}
```

**Sample curl:**

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.tickets.getAll","params":{"projectId":"42"}}'
```

**Success response shape:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": [
    {
      "id": "101",
      "headline": "Fix login page bug",
      "description": "Users can't log in with SSO",
      "projectId": "42",
      "editorId": "7",
      "status": "0",
      "priority": "3",
      "type": "bug",
      "dateToFinish": "2026-05-01 00:00:00"
    }
  ]
}
```

---

## 2. Get Ticket by ID

**Method:** `leantime.rpc.tickets.getTicket`

**Required params:**

| Param | Type | Description |
|-------|------|-------------|
| `id` | string | Ticket ID |

**Request body:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.getTicket",
  "params": { "id": "101" }
}
```

**Sample curl:**

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.tickets.getTicket","params":{"id":"101"}}'
```

**Success response:** Single ticket object (same fields as list above).

---

## 3. Create Ticket

**Method:** `leantime.rpc.tickets.addTicket`

**Required params:**

| Param | Type | Description |
|-------|------|-------------|
| `headline` | string | Ticket title |
| `projectId` | string | Parent project ID |

**Optional params:** `description`, `editorId`, `status`, `priority`, `type`,
`dateToFinish`, `tags`, `storypoints`, `milestoneid`

**Request body:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.addTicket",
  "params": {
    "headline": "Implement dark mode",
    "description": "Add a dark mode toggle to user settings",
    "projectId": "42",
    "priority": "2",
    "type": "story",
    "dateToFinish": "2026-06-15 00:00:00"
  }
}
```

**Sample curl:**

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.tickets.addTicket","params":{"headline":"Implement dark mode","projectId":"42","priority":"2","type":"story"}}'
```

**Success response:** Returns the new ticket `id` or full ticket object.

---

## 4. Update Ticket

**Method:** `leantime.rpc.tickets.updateTicket`

**Required params:**

| Param | Type | Description |
|-------|------|-------------|
| `id` | string | Ticket ID to update |

**Optional params:** Any ticket field you want to change.

> **Important:** Leantime performs partial updates — send only the fields you
> want to change. Omitting a field does NOT clear it. However, some Leantime
> versions may reset fields if `headline` or `projectId` is omitted; when in
> doubt, include them.

**Request body (move ticket 101 to Done):**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.updateTicket",
  "params": {
    "id": "101",
    "status": "1"
  }
}
```

**Sample curl:**

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.tickets.updateTicket","params":{"id":"101","status":"1"}}'
```

**Success response:** Returns `true`, `1`, or the updated ticket object.

---

## Worked Examples

### Create a bug ticket in project 42

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "leantime.rpc.tickets.addTicket",
    "params": {
      "headline": "Login page broken on mobile",
      "description": "Safari iOS 17 — form submit does nothing",
      "projectId": "42",
      "type": "bug",
      "priority": "3"
    }
  }'
```

### Move ticket 42 to Done

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.tickets.updateTicket","params":{"id":"42","status":"1"}}'
```

### List open tickets assigned to user 7

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.tickets.getAll","params":{"editorId":"7","status":"0"}}'
```

---

## Discovering Method Names

If documented methods return error `-32601` (Method not found), the RPC name
may differ in your Leantime version. Check:
`app/Domain/Tickets/Repositories/` and `app/Domain/Tickets/Services/`
for the registered RPC class. Variants: `leantime.rpc.ticket.*` (singular),
`leantime.rpc.todos.*`.
