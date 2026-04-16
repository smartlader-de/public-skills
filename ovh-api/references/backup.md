# Backup Services Reference — OVH v2 API

## Table of Contents

1. [List backup services](#1-list-backup-services)
2. [Get backup service details](#2-get-backup-service-details)
3. [Backups and restore points](#3-backups-and-restore-points)
4. [Restore a backup](#4-restore-a-backup)
5. [Delete a backup](#5-delete-a-backup-destructive)
6. [Backup Storage (FTP/NFS)](#6-backup-storage-ftpnfs)
7. [Common patterns and gotchas](#7-common-patterns-and-gotchas)

API console reference: https://eu.api.ovh.com/console/?section=%2FbackupServices&branch=v2

---

## 1. List backup services

```bash
python scripts/ovh_request.py --method GET --path /v2/backupServices
```

Returns array of backup service IDs.

---

## 2. Get backup service details

```bash
python scripts/ovh_request.py --method GET --path /v2/backupServices/{serviceName}
```

**Key fields:**
```json
{
  "serviceName": "backup-abc123",
  "status": "active",
  "serverName": "ns123456.ip-1-2-3.eu",
  "quota": {"used": 51200, "available": 102400}
}
```

---

## 3. Backups and restore points

### List backups
```bash
python scripts/ovh_request.py --method GET --path /v2/backupServices/{serviceName}/backup
```

### Get backup details
```bash
python scripts/ovh_request.py --method GET --path /v2/backupServices/{serviceName}/backup/{backupId}
```

**Key fields:** `creationDate`, `size`, `serverName`, `description`, `encrypted`.

---

## 4. Restore a backup

Restore is non-destructive (creates a new restore point, does not delete existing data):

```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/backupServices/{serviceName}/backup/{backupId}/restore \
  --body '{"destination":"ns123456.ip-1-2-3.eu"}'
```

Returns a task ID. Poll the backup service's task endpoint for completion.

---

## 5. Delete a backup ⚠ DESTRUCTIVE

Permanently removes a backup restore point — this data cannot be recovered.
Full destructive-ops protocol required.

```bash
python scripts/ovh_request.py \
  --method DELETE \
  --path /v2/backupServices/{serviceName}/backup/{backupId}
```

---

## 6. Backup Storage (FTP/NFS)

OVH backup storage is a separate FTP/NFS endpoint for manual backup uploads.

### Get backup storage credentials
```bash
python scripts/ovh_request.py \
  --method GET \
  --path /v2/dedicated/server/{serverName}/features/backupStorage
```

### Enable backup storage
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/dedicated/server/{serverName}/features/backupStorage
```

### List backup storage access
```bash
python scripts/ovh_request.py \
  --method GET \
  --path /v2/dedicated/server/{serverName}/features/backupStorage/access
```

### Add access (allow a server to connect)
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/dedicated/server/{serverName}/features/backupStorage/access \
  --body '{"ipBlock":"1.2.3.4/32","proto":"FTP"}'
```

Protocols: `FTP`, `NFS`, `CIFS`.

---

## 7. Common patterns and gotchas

- **Backup vs backup storage**: `backupServices` = OVH-managed snapshots; `backupStorage` = FTP/NFS disk space you manage yourself — they are different products
- **Restore creates, not replaces**: restoring a backup mounts it alongside existing data; you manually copy what you need
- **Backup deletion is permanent**: unlike files in a trash folder, deleted backups cannot be recovered
- **Quota is per service**: check `quota.available` before large restores
- **Encryption note**: if `encrypted: true`, ensure you have the decryption key before attempting restore
