# Domains & DNS Reference — OVH v2 API

## Table of Contents

1. [List domains](#1-list-domains)
2. [Get domain details](#2-get-domain-details)
3. [DNS zones](#3-dns-zones)
4. [DNS records — list and get](#4-dns-records--list-and-get)
5. [Add a DNS record](#5-add-a-dns-record)
6. [Update a DNS record](#6-update-a-dns-record)
7. [Delete a DNS record](#7-delete-a-dns-record-destructive)
8. [Nameservers](#8-nameservers-destructive)
9. [Domain transfer and expiry](#9-domain-transfer-and-expiry)
10. [Common patterns and gotchas](#10-common-patterns-and-gotchas)

---

## 1. List domains

```bash
python scripts/ovh_request.py --method GET --path /v2/domain
```

Returns array of domain names: `["example.com", "mysite.net"]`

---

## 2. Get domain details

```bash
python scripts/ovh_request.py --method GET --path /v2/domain/example.com
```

**Key fields:** `domain`, `expiration`, `transferLockStatus`, `nameServerType` (hosted/external).

---

## 3. DNS zones

### List zones (usually same as domain list)
```bash
python scripts/ovh_request.py --method GET --path /v2/domain/zone
```

### Get zone details
```bash
python scripts/ovh_request.py --method GET --path /v2/domain/zone/example.com
```

### Export zone (BIND format)
```bash
python scripts/ovh_request.py --method GET --path /v2/domain/zone/example.com/export
```
Useful before any destructive DNS changes — save this output as a backup.

### Refresh zone
```bash
python scripts/ovh_request.py --method POST --path /v2/domain/zone/example.com/refresh
```
Forces DNS propagation after record changes.

---

## 4. DNS records — list and get

### List all records
```bash
python scripts/ovh_request.py --method GET --path /v2/domain/zone/example.com/record
```

Returns array of record IDs.

### Filter by type
```bash
python scripts/ovh_request.py --method GET --path "/v2/domain/zone/example.com/record?fieldType=A"
```

Types: `A`, `AAAA`, `CNAME`, `MX`, `TXT`, `NS`, `SRV`, `CAA`, `DKIM`.

### Get a specific record
```bash
python scripts/ovh_request.py --method GET --path /v2/domain/zone/example.com/record/12345
```

**Response shape:**
```json
{
  "id": 12345,
  "fieldType": "A",
  "subDomain": "www",
  "target": "1.2.3.4",
  "ttl": 3600
}
```

`subDomain` is empty string for the root domain (`@`).

---

## 5. Add a DNS record

```bash
# Add an A record for www.example.com
python scripts/ovh_request.py \
  --method POST \
  --path /v2/domain/zone/example.com/record \
  --body '{"fieldType":"A","subDomain":"www","target":"1.2.3.4","ttl":3600}'

# Add MX record
python scripts/ovh_request.py \
  --method POST \
  --path /v2/domain/zone/example.com/record \
  --body '{"fieldType":"MX","subDomain":"","target":"10 mail.example.com.","ttl":3600}'

# Add TXT record (e.g., SPF)
python scripts/ovh_request.py \
  --method POST \
  --path /v2/domain/zone/example.com/record \
  --body '{"fieldType":"TXT","subDomain":"","target":"\"v=spf1 include:mx.ovh.com ~all\"","ttl":3600}'
```

After adding, always run: `python scripts/ovh_request.py --method POST --path /v2/domain/zone/example.com/refresh`

---

## 6. Update a DNS record

```bash
python scripts/ovh_request.py \
  --method PUT \
  --path /v2/domain/zone/example.com/record/12345 \
  --body '{"target":"5.6.7.8","ttl":300}'
```

Only supply fields you want to change. Refresh after update.

---

## 7. Delete a DNS record ⚠ DESTRUCTIVE

Deleting DNS records breaks services immediately after TTL expiry.
MX record deletion breaks email delivery. A/CNAME deletion breaks web access.
Full destructive-ops protocol required.

```bash
python scripts/ovh_request.py \
  --method DELETE \
  --path /v2/domain/zone/example.com/record/12345
```

Always export the zone first: `GET /v2/domain/zone/example.com/export`

---

## 8. Nameservers ⚠ DESTRUCTIVE

Changing nameservers affects the entire domain immediately.
Takes 24-48h to propagate globally. Wrong nameservers = complete domain failure.
Full destructive-ops protocol required. Always export zone first.

### List current nameservers
```bash
python scripts/ovh_request.py --method GET --path /v2/domain/zone/example.com/nameServer
```

### Reset to OVH nameservers
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/domain/zone/example.com/nameServer/resetDefault
```

---

## 9. Domain transfer and expiry

### Check expiry
```bash
python scripts/ovh_request.py --method GET --path /v2/domain/example.com
# Check: expiration field
```

### Enable/disable transfer lock
```bash
python scripts/ovh_request.py \
  --method PUT \
  --path /v2/domain/example.com \
  --body '{"transferLockStatus":"locked"}'
```

### Get AUTH/EPP transfer code
```bash
python scripts/ovh_request.py --method GET --path /v2/domain/example.com/authInfo
```

---

## 10. Common patterns and gotchas

- **Always export zone before destructive changes**: `GET /v2/domain/zone/{zone}/export` saves you in case of mistakes
- **Refresh after every change**: DNS changes are staged — always call `/refresh` or they won't propagate
- **MX target needs trailing dot**: `10 mail.example.com.` — missing dot causes broken email
- **TTL strategy**: lower TTL (300s) before migrations for faster propagation; raise back to 3600 after
- **subDomain is empty string for root**: `""` means the root domain (`@`), not a subdomain named `@`
- **Nameserver changes propagate slowly**: 24-48h worldwide; OVH internal propagation is faster (~minutes)
- **DNS record deletion doesn't refresh automatically**: always run `/refresh` after deletions too
