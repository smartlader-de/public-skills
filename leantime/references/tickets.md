# Leantime Tickets Reference

Live-tested against a real Leantime instance. All method names, param shapes,
and response schemas are verified.

**Endpoint:** `POST $LEANTIME_URL/api/jsonrpc`
**Auth header:** `x-api-key: $LEANTIME_API_KEY`

> **Critical param shape:** `addTicket` and `updateTicket` wrap all ticket
> data inside a `values` object. `patch` uses `id` + `params`. Flat params
> do not work.

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

## Ticket Object Fields

### From `getAll` (summary shape)

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Ticket ID |
| `headline` | string | Title |
| `description` | string | Body (may contain HTML) |
| `type` | string | `"task"`, `"story"`, `"bug"`, `"subtask"`, `"milestone"` |
| `projectId` | int | Parent project |
| `projectName` | string | Denormalized project name |
| `clientId` | int\|null | |
| `clientName` | string\|null | |
| `status` | int | See status table below |
| `statusLabel` | string | e.g. `"New"` (present on some records) |
| `priority` | string | `""` unset, `"1"` low, `"2"` medium, `"3"` high |
| `editorId` | string | Assigned user ID (`""` = unassigned) |
| `editorFirstname` | string\|null | |
| `editorLastname` | string\|null | |
| `authorId` | int\|null | Creator user ID |
| `authorFirstname` | string\|null | |
| `authorLastname` | string\|null | |
| `milestoneid` | int | `0` = no milestone |
| `milestoneHeadline` | string\|null | |
| `milestoneColor` | string | e.g. `"var(--grey)"` or `"#124F7D"` |
| `sprint` | int | Sprint ID (`0` = no sprint) |
| `sprintName` | null | Usually null |
| `storypoints` | int | |
| `planHours` | float | |
| `hourRemaining` | float | |
| `bookedHours` | string | e.g. `"0.00"` |
| `date` | string | Created at `"YYYY-MM-DD HH:MM:SS"` |
| `dateToFinish` | string | Due date; `"0000-00-00 00:00:00"` = none |
| `editFrom` | string | `"0000-00-00 00:00:00"` = none |
| `editTo` | string | `"0000-00-00 00:00:00"` = none |
| `tags` | string | CSS color or tag text (e.g. `"#124F7D"`) |
| `dependingTicketId` | int | `0` = none |
| `parentHeadline` | null | Parent ticket title (subtasks) |
| `sortindex` | int\|null | |
| `commentCount` | int | |
| `fileCount` | int | |
| `subtaskCount` | int | |

### Additional fields from `getTicket` (detail shape)

| Field | Type | Notes |
|-------|------|-------|
| `projectDescription` | string | |
| `userId` | int | API key's user ID |
| `acceptanceCriteria` | string | |
| `url` | null | External URL |
| `timelineDate` | null | |
| `timelineDateToFinish` | null | |
| `timeToFinish` | null | |
| `timeFrom` | null | |
| `timeTo` | null | |
| `doneTickets` | null | Subtask progress |
| `allTickets` | null | Subtask total |
| `percentDone` | null | |
| `children` | null | Subtask array |
| `collaborators` | array | Usually `[]` |
| `modified` | null | |

### Status Values (observed)

| Value | Meaning |
|-------|---------|
| `0` | Open / To Do |
| `3` | New (shown with `statusLabel: "New"`) |

---

## 1. List Tickets

**Method:** `leantime.rpc.tickets.getAll`

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `projectId` | int | no | Filter to a specific project |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.getAll",
  "params": { "projectId": 2 }
}
```

**Returns:** Array of ticket summary objects. Omit `projectId` to get all tickets across all projects.

---

## 2. Get Ticket by ID

**Method:** `leantime.rpc.tickets.getTicket`

| Param | Type | Required |
|-------|------|----------|
| `id` | int | yes |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.getTicket",
  "params": { "id": 11 }
}
```

**Returns:** Single ticket object with extended fields.

---

## 3. Create Ticket

**Method:** `leantime.rpc.tickets.addTicket`

> All ticket data goes inside `values`. Flat params return `-32602`.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `values.headline` | string | **yes** | |
| `values.projectId` | int | **yes** | |
| `values.description` | string | no | HTML allowed |
| `values.type` | string | no | `"task"`, `"story"`, `"bug"`, `"subtask"` |
| `values.priority` | string | no | `"1"` / `"2"` / `"3"` |
| `values.status` | int | no | Default `0` |
| `values.editorId` | int | no | Assigned user ID |
| `values.milestoneid` | int | no | |
| `values.sprint` | int | no | |
| `values.storypoints` | int | no | |
| `values.dateToFinish` | string | no | `"YYYY-MM-DD HH:MM:SS"` |
| `values.tags` | string | no | |
| `values.acceptanceCriteria` | string | no | |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.addTicket",
  "params": {
    "values": {
      "headline": "Fix login page bug",
      "description": "Safari iOS 17 — form submit does nothing",
      "projectId": 2,
      "type": "bug",
      "priority": "3"
    }
  }
}
```

**Returns:** `[newTicketId]` — array containing the new integer ID.

---

## 4. Patch Ticket (Partial Update — Preferred)

**Method:** `leantime.rpc.tickets.patch`

> `id` is top-level; fields to change go inside `params`.

| Param | Location | Required |
|-------|----------|----------|
| `id` | top-level | **yes** |
| fields to change | `params.*` | at least one |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.patch",
  "params": {
    "id": 11,
    "params": {
      "status": 3,
      "headline": "Updated title"
    }
  }
}
```

**Returns:** `[true]` on success.

**Errors:**
- Missing `id` → `-32602 Required Parameter Missing: id`
- Missing `params` → `-32602 Required Parameter Missing: params`

---

## 5. Update Ticket (Full Update)

**Method:** `leantime.rpc.tickets.updateTicket`

> Requires both `id` and `projectId` inside `values`. Prefer `patch` for
> partial updates — `updateTicket` is strict about required fields.

| Field | Type | Required |
|-------|------|----------|
| `values.id` | int | **yes** |
| `values.projectId` | int | **yes** |
| other fields | any | no |

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "leantime.rpc.tickets.updateTicket",
  "params": {
    "values": {
      "id": 11,
      "projectId": 2,
      "status": 3,
      "headline": "Updated title"
    }
  }
}
```

**Returns:** `{"msg": "...", "type": "error"|"success"}` — always check `type`.
Missing `projectId` → `{"msg": "project id is not set", "type": "error"}`.

---

## Methods That Do NOT Exist

| Method | Status |
|--------|--------|
| `deleteTicket` | not found |

There is no delete operation via the API.

---

## Rate Limiting

Cloudflare enforces ~5 requests/minute. Exceeding it returns:
```json
{"error": "Too many requests per minute."}
```
This is NOT a JSON-RPC envelope. Add 2–4 second delays between calls.
