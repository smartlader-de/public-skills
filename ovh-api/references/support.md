# Support Reference — OVH v2 API

## Table of Contents

1. [List support tickets](#1-list-support-tickets)
2. [Get ticket details and messages](#2-get-ticket-details-and-messages)
3. [Create a support ticket](#3-create-a-support-ticket)
4. [Reply to a ticket](#4-reply-to-a-ticket)
5. [Close a ticket](#5-close-a-ticket)
6. [Common patterns and gotchas](#6-common-patterns-and-gotchas)

---

## 1. List support tickets

```bash
python scripts/ovh_request.py --method GET --path /v2/support/tickets
```

Filter by status:
```bash
python scripts/ovh_request.py --method GET --path "/v2/support/tickets?status=open"
```

Statuses: `open`, `closed`.

---

## 2. Get ticket details and messages

### Get ticket details
```bash
python scripts/ovh_request.py --method GET --path /v2/support/tickets/{ticketId}
```

Key fields: `ticketId`, `subject`, `status`, `product`, `creationDate`, `lastMessageFrom`.

### Get messages in a ticket
```bash
python scripts/ovh_request.py --method GET --path /v2/support/tickets/{ticketId}/messages
```

---

## 3. Create a support ticket

```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/support/tickets/create \
  --body '{
    "serviceName": "vps-abc123.vps.ovh.net",
    "type": "incident",
    "subject": "VPS not reachable",
    "body": "My VPS has been unreachable since 14:00 UTC. Last successful ping was at 13:58 UTC.\n\nServer: vps-abc123.vps.ovh.net\nSeverity: High"
  }'
```

Types: `incident`, `billing`, `assistance`, `new-feature`.
`serviceName` is optional but helps OVH route to the right team.

---

## 4. Reply to a ticket

```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/support/tickets/{ticketId}/reply \
  --body '{"body":"Thank you for the update. The server is now accessible."}'
```

---

## 5. Close a ticket

```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/support/tickets/{ticketId}/close
```

---

## 6. Common patterns and gotchas

- **Always include serviceName**: tickets without a service name take longer to route — include the affected resource
- **Incident vs assistance**: use `incident` for things that are broken now; `assistance` for configuration questions
- **Response time varies**: OVH support SLAs depend on your hosting plan — dedicated server plans get faster response
- **API tickets = same queue**: tickets created via API appear in your OVH Manager portal — you can follow up either way
- **Attach context upfront**: include server name, timestamps, error messages, and what you've already tried — reduces back-and-forth
