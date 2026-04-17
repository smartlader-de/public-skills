# Leantime Comments Reference

JSON-RPC methods for adding comments to tickets and listing comments on a
ticket.

**JSON-RPC endpoint:** `POST $LEANTIME_URL/api/jsonrpc`
**Auth header:** `x-api-key: $LEANTIME_API_KEY`

> **Leantime quirk:** Comments are managed under the `tickets` RPC domain
> (not a standalone `comments` namespace). The methods below reflect the
> standard v3.x paths; if they return `-32601` (Method not found), check
> `app/Domain/Tickets/Repositories/` in your Leantime source for the exact
> registered method name.

---

## Canonical Request Template

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '<BODY>'
```

---

## Common Comment Fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Comment ID (read) |
| `text` | string | Comment body (may accept HTML) |
| `moduleId` | string | The ticket ID the comment belongs to |
| `userId` | string | Author user ID |
| `date` | string | `YYYY-MM-DD HH:MM:SS` — usually set by the server |

---

## 1. Add Comment to a Ticket

**Method:** `leantime.rpc.tickets.addComment`

**Required params:**

| Param | Type | Description |
|-------|------|-------------|
| `text` | string | Comment text |
| `moduleId` | string | ID of the ticket to comment on |

**Optional params:**

| Param | Type | Description |
|-------|------|-------------|
| `userId` | string | Author user ID (defaults to API key owner) |

**Request body:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.addComment",
  "params": {
    "text": "Fixed in PR #42 — deploying to staging now.",
    "moduleId": "101"
  }
}
```

**Sample curl:**

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.tickets.addComment","params":{"text":"Fixed in PR #42","moduleId":"101"}}'
```

**Success response:** Returns the new comment `id` or `true`.

---

## 2. Get Comments for a Ticket

**Method:** `leantime.rpc.tickets.getComments`

**Required params:**

| Param | Type | Description |
|-------|------|-------------|
| `moduleId` | string | The ticket ID |

**Request body:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.getComments",
  "params": { "moduleId": "101" }
}
```

**Sample curl:**

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.tickets.getComments","params":{"moduleId":"101"}}'
```

**Success response shape:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": [
    {
      "id": "55",
      "text": "Reproduced on Chrome 124. Assigned to Bob.",
      "moduleId": "101",
      "userId": "3",
      "date": "2026-04-10 14:23:00"
    },
    {
      "id": "56",
      "text": "Fixed in PR #42 — deploying to staging now.",
      "moduleId": "101",
      "userId": "7",
      "date": "2026-04-17 09:05:00"
    }
  ]
}
```

---

## Worked Example

### Add a comment "fixed in PR #42" to ticket 17

```bash
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "leantime.rpc.tickets.addComment",
    "params": {
      "text": "Fixed in PR #42 — will be live after next deploy.",
      "moduleId": "17"
    }
  }'
```

---

## Alternative Method Names

If the above methods return `-32601`, try these alternatives which appear in
some Leantime builds:

- `leantime.rpc.comments.addComment` with `ticketId` instead of `moduleId`
- `leantime.rpc.comments.getComments` with `ticketId`

Check `app/Domain/Comments/` in your Leantime source if neither works.
