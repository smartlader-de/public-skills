# Public Cloud Reference — OVH v2 API

## Table of Contents

1. [List projects](#1-list-projects)
2. [Instances](#2-instances)
3. [Volumes (block storage)](#3-volumes-block-storage)
4. [Snapshots](#4-snapshots)
5. [Networks and subnets](#5-networks-and-subnets)
6. [SSH keys](#6-ssh-keys)
7. [Regions](#7-regions)
8. [Common patterns and gotchas](#8-common-patterns-and-gotchas)

---

## 1. List projects

```bash
python scripts/ovh_request.py --method GET --path /v2/cloud/project
```

Returns an array of project IDs (UUIDs). All cloud resources live under a project.

Get project details:
```bash
python scripts/ovh_request.py --method GET --path /v2/cloud/project/{projectId}
```

---

## 2. Instances

### List instances
```bash
python scripts/ovh_request.py --method GET --path /v2/cloud/project/{projectId}/instance
```

### Get instance details
```bash
python scripts/ovh_request.py --method GET --path /v2/cloud/project/{projectId}/instance/{instanceId}
```

Key fields: `id`, `name`, `status` (ACTIVE/SHUTOFF/ERROR), `flavor` (size), `region`, `ipAddresses`.

### Create an instance
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/cloud/project/{projectId}/instance \
  --body '{
    "name": "my-instance",
    "flavorId": "b2-7",
    "imageId": "uuid-of-ubuntu-image",
    "region": "GRA9",
    "sshKeyId": "my-key"
  }'
```

Get available flavors: `GET /v2/cloud/project/{projectId}/flavor?region=GRA9`
Get available images: `GET /v2/cloud/project/{projectId}/image?region=GRA9&osType=linux`

### Stop / Start an instance
```bash
# Stop
python scripts/ovh_request.py --method POST --path /v2/cloud/project/{projectId}/instance/{instanceId}/stop

# Start
python scripts/ovh_request.py --method POST --path /v2/cloud/project/{projectId}/instance/{instanceId}/start
```

### Delete an instance ⚠ DESTRUCTIVE
```bash
python scripts/ovh_request.py --method DELETE --path /v2/cloud/project/{projectId}/instance/{instanceId}
```
Destroys the instance and its ephemeral disk. Attached volumes survive. Full destructive-ops protocol required.

---

## 3. Volumes (block storage)

### List volumes
```bash
python scripts/ovh_request.py --method GET --path /v2/cloud/project/{projectId}/volume
```

### Create a volume
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/cloud/project/{projectId}/volume \
  --body '{"name":"data-vol","size":50,"region":"GRA9","type":"classic"}'
```

Types: `classic` (HDD), `high-speed` (SSD), `high-speed-gen2` (NVMe).

### Attach / detach volume
```bash
# Attach
python scripts/ovh_request.py \
  --method POST \
  --path /v2/cloud/project/{projectId}/volume/{volumeId}/attach \
  --body '{"instanceId":"instance-uuid"}'

# Detach
python scripts/ovh_request.py \
  --method POST \
  --path /v2/cloud/project/{projectId}/volume/{volumeId}/detach \
  --body '{"instanceId":"instance-uuid"}'
```

### Delete a volume ⚠ DESTRUCTIVE
```bash
python scripts/ovh_request.py --method DELETE --path /v2/cloud/project/{projectId}/volume/{volumeId}
```
Permanently deletes volume data. Destructive-ops protocol required.

---

## 4. Snapshots

### List snapshots
```bash
python scripts/ovh_request.py --method GET --path /v2/cloud/project/{projectId}/snapshot
```

### Create snapshot from instance
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/cloud/project/{projectId}/instance/{instanceId}/snapshot \
  --body '{"snapshotName":"backup-2026-04-16"}'
```

### Delete snapshot ⚠ DESTRUCTIVE
```bash
python scripts/ovh_request.py --method DELETE --path /v2/cloud/project/{projectId}/snapshot/{snapshotId}
```
Destructive-ops protocol required.

---

## 5. Networks and subnets

### List networks
```bash
python scripts/ovh_request.py --method GET --path /v2/cloud/project/{projectId}/network/private
```

### Create private network
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/cloud/project/{projectId}/network/private \
  --body '{"name":"my-network","regions":[{"region":"GRA9"}]}'
```

### List subnets
```bash
python scripts/ovh_request.py --method GET \
  --path /v2/cloud/project/{projectId}/network/private/{networkId}/subnet
```

---

## 6. SSH keys

### List SSH keys
```bash
python scripts/ovh_request.py --method GET --path /v2/cloud/project/{projectId}/sshkey
```

### Add SSH key
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/cloud/project/{projectId}/sshkey \
  --body '{"name":"my-key","publicKey":"ssh-ed25519 AAAA..."}'
```

---

## 7. Regions

```bash
python scripts/ovh_request.py --method GET --path /v2/cloud/project/{projectId}/region
```

Returns available regions (GRA9, BHS5, WAW1, etc.) with their status.

---

## 8. Common patterns and gotchas

- **Project ID is a UUID**: always a 32-char hex UUID, not a name — check with `GET /v2/cloud/project`
- **Region matters everywhere**: most resources (flavors, images, instances) are region-specific — always include `?region=` in queries
- **Instance ephemeral disk**: instance deletion loses the OS disk; attached volumes survive separately
- **Quota limits**: large operations may hit project quotas — check `GET /v2/cloud/project/{projectId}/quota`
- **Floating IPs**: to assign a static public IP, use `POST /v2/cloud/project/{projectId}/floatingip` not instance IPs
- **Object storage**: S3-compatible, accessed via `/v2/cloud/project/{projectId}/storage` — separate from block volumes
