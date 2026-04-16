# Web Hosting Reference — OVH v2 API

## Table of Contents

1. [List hosting plans](#1-list-hosting-plans)
2. [Get hosting details](#2-get-hosting-details)
3. [Databases](#3-databases)
4. [FTP accounts](#4-ftp-accounts)
5. [Attached domains](#5-attached-domains)
6. [Common patterns and gotchas](#6-common-patterns-and-gotchas)

---

## 1. List hosting plans

```bash
python scripts/ovh_request.py --method GET --path /v2/hosting/web
```

Returns array of hosting service names.

---

## 2. Get hosting details

```bash
python scripts/ovh_request.py --method GET --path /v2/hosting/web/{serviceName}
```

Key fields: `serviceName`, `state`, `cluster`, `offer`, `hostingIp`, `primaryLogin`.

---

## 3. Databases

### List databases
```bash
python scripts/ovh_request.py --method GET --path /v2/hosting/web/{serviceName}/database
```

### Get database details
```bash
python scripts/ovh_request.py --method GET --path /v2/hosting/web/{serviceName}/database/{dbName}
```

### Create a database
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/hosting/web/{serviceName}/database \
  --body '{"dbName":"mydb","type":"mysql","version":"8.0","user":"mydbuser","password":"...","quota":200}'
```

### Delete a database ⚠ DESTRUCTIVE
```bash
python scripts/ovh_request.py --method DELETE --path /v2/hosting/web/{serviceName}/database/{dbName}
```
Deletes all data. Destructive-ops protocol required.

---

## 4. FTP accounts

### List FTP users
```bash
python scripts/ovh_request.py --method GET --path /v2/hosting/web/{serviceName}/user
```

### Change FTP password
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/hosting/web/{serviceName}/user/{login}/changePassword \
  --body '{"password":"new-strong-password"}'
```

---

## 5. Attached domains

### List attached domains
```bash
python scripts/ovh_request.py --method GET --path /v2/hosting/web/{serviceName}/attachedDomain
```

### Add an attached domain
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/hosting/web/{serviceName}/attachedDomain \
  --body '{"domain":"shop.example.com","path":"/shop","ssl":false}'
```

---

## 6. Common patterns and gotchas

- **Hosting service name ≠ domain name**: the hosting plan has its own identifier (like `cluster012.hosting.ovh.net`) separate from attached domains
- **Shared hosting limits**: PHP version, max DB size, and FTP accounts are plan-dependent — check `offer` field
- **SSL provisioning takes time**: enabling Let's Encrypt via hosting panel is async — check via `/v2/hosting/web/{name}/ssl`
- **Database deletion is final**: unlike deleting a file, deleted databases cannot be recovered — always dump first
