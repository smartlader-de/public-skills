# Leantime Comments Reference

Live-tested against a real Leantime instance. All method names, param shapes,
and response schemas are verified.

**Endpoint:** `POST $LEANTIME_URL/api/jsonrpc`
**Auth header:** `x-api-key: $LEANTIME_API_KEY`

> **Namespace correction:** Comments are at `leantime.rpc.comments.*` —
> NOT `leantime.rpc.tickets.*` as some older docs suggest. The `tickets`
> namespace has no comment methods at all.

> **Critical param shape:** `getComments` takes `{module, entityId}` and
> `addComment` takes `{module, entityId, entity, values}`. The old `moduleId`
> and `ticketId` param names do not work.

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

## 1. Get Comments for a Ticket

**Method:** `leantime.rpc.comments.getComments`

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `module` | string | **yes** | Always `"tickets"` for ticket comments |
| `entityId` | int | **yes** | The ticket ID |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.comments.getComments",
  "params": {
    "module": "tickets",
    "entityId": 11
  }
}
```

**Returns:** Array of comment objects (empty array `[]` if no comments).

**Errors:**
- Missing `module` → `-32602 Required Parameter Missing: module`
- Missing `entityId` → `-32602 Required Parameter Missing: entityId`

---

## 2. Add Comment to a Ticket

**Method:** `leantime.rpc.comments.addComment`

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `module` | string | **yes** | `"tickets"` |
| `entityId` | int | **yes** | The ticket ID |
| `entity` | string | **yes** | Entity type — use `"ticket"` |
| `values.comment` | string | **yes** | Comment text |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.comments.addComment",
  "params": {
    "module": "tickets",
    "entityId": 11,
    "entity": "ticket",
    "values": {
      "comment": "Fixed in PR #42 — deploying to staging."
    }
  }
}
```

**Returns:** `[true]` on success, `[false]` on failure (no error object raised).
Always check the value — `[false]` means the comment was not saved.

**Errors (from missing params):**
- Missing `values` → `-32602 Required Parameter Missing: values`
- Missing `module` → `-32602 Required Parameter Missing: module`
- Missing `entityId` → `-32602 Required Parameter Missing: entityId`
- Missing `entity` → `-32602 Required Parameter Missing: entity`

---

## 3. Delete Comment

**Method:** `leantime.rpc.comments.deleteComment`

| Param | Type | Required |
|-------|------|----------|
| `commentId` | int | **yes** |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.comments.deleteComment",
  "params": {
    "commentId": 55
  }
}
```

**Returns:** `[true]` on success, `[false]` if comment not found.

**Error:** Missing `commentId` → `-32602 Required Parameter Missing: commentId`

---

## Methods That Do NOT Exist

| Method | Status |
|--------|--------|
| `leantime.rpc.comments.createComment` | not found |
| `leantime.rpc.comments.patch` | not found |
| `leantime.rpc.tickets.addComment` | not found |
| `leantime.rpc.tickets.getComments` | not found |

---

## Rate Limiting

Cloudflare enforces ~5 requests/minute. Exceeding it returns:
```json
{"error": "Too many requests per minute."}
```
This is NOT a JSON-RPC envelope. Add 2–4 second delays between calls.
