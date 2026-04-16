# Dedicated Servers Reference — OVH v2 API

## Table of Contents

1. [List dedicated servers](#1-list-dedicated-servers)
2. [Get server details](#2-get-server-details)
3. [Get IP addresses](#3-get-ip-addresses)
4. [List available installation templates](#4-list-available-installation-templates)
5. [Reinstall (OS install)](#5-reinstall-os-install-destructive)
6. [Reboot](#6-reboot-destructive)
7. [IPMI / KVM access](#7-ipmi--kvm-access)
8. [Poll a task](#8-poll-a-task)
9. [Rescue mode](#9-rescue-mode)
10. [Common patterns and gotchas](#10-common-patterns-and-gotchas)

---

## 1. List dedicated servers

```bash
python scripts/ovh_request.py --method GET --path /v2/dedicated/server
```

**Response:** Array of service names, e.g. `["ns123456.ip-1-2-3.eu"]`

---

## 2. Get server details

```bash
python scripts/ovh_request.py --method GET --path /v2/dedicated/server/ns123456.ip-1-2-3.eu
```

**Key fields:**
```json
{
  "name": "ns123456.ip-1-2-3.eu",
  "state": "ready",
  "datacenter": "gra3",
  "professionalUse": false,
  "rack": "G05",
  "os": "debian12_64",
  "monitoring": true
}
```

States: `ready`, `hacked`, `hackedBlocked`, `ok`.

---

## 3. Get IP addresses

```bash
python scripts/ovh_request.py --method GET --path /v2/dedicated/server/ns123456.ip-1-2-3.eu/ips
```

---

## 4. List available installation templates

Get templates available for the server:
```bash
python scripts/ovh_request.py \
  --method GET \
  --path /v2/dedicated/server/ns123456.ip-1-2-3.eu/install/compatibleTemplates
```

OVH provides template names like `debian12_64`, `ubuntu2204-server_64`, `proxmox-ve-8_64`.

---

## 5. Reinstall (OS install) ⚠ DESTRUCTIVE

Wipes all data and installs a fresh OS. Full destructive-ops protocol required.

```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/dedicated/server/ns123456.ip-1-2-3.eu/install/start \
  --body '{
    "templateName": "debian12_64",
    "details": {
      "customHostname": "my-server",
      "sshKeyName": "my-key",
      "useDistribKernel": true
    }
  }'
```

Returns a task object. Poll `/v2/dedicated/server/{name}/task/{taskId}` for progress.

Installation takes 15-45 minutes depending on template and server.

---

## 6. Reboot ⚠ DESTRUCTIVE

Hard reboot via IPMI (no graceful shutdown):

```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/dedicated/server/ns123456.ip-1-2-3.eu/reboot
```

For a soft reboot (if SSH accessible), prefer `ssh root@server "reboot"` instead — it flushes disk buffers.

---

## 7. IPMI / KVM access

Request a KVM console session:
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/dedicated/server/ns123456.ip-1-2-3.eu/features/ipmi/access \
  --body '{"type":"kvmipHtml5URL","duration":1}'
```

Response includes `value` (the KVM URL) and `expiration` (ISO timestamp).

Types: `kvmipHtml5URL` (browser KVM), `serialOverLanURL` (serial console), `ipmiOverHttpURL`.

---

## 8. Poll a task

After any async operation (install, reboot), poll the returned task ID:

```bash
python scripts/ovh_request.py \
  --method GET \
  --path /v2/dedicated/server/ns123456.ip-1-2-3.eu/task/12345
```

**Task states:** `init`, `customerError`, `doing`, `done`, `error`, `ovhError`, `todo`, `waitingForCustomer`

Poll every 30-60 seconds for long operations (installs take 15-45 min).

---

## 9. Rescue mode

Boot into OVH rescue system for disk repairs without losing data:

```bash
# Enable rescue boot
python scripts/ovh_request.py \
  --method PUT \
  --path /v2/dedicated/server/ns123456.ip-1-2-3.eu \
  --body '{"bootId": <rescue_boot_id>}'
```

Get rescue `bootId`:
```bash
python scripts/ovh_request.py --method GET --path /v2/dedicated/server/ns123456.ip-1-2-3.eu/boot?bootType=rescue
```

After enabling, reboot the server. OVH emails rescue credentials to your account email.

---

## 10. Common patterns and gotchas

- **Server names are IPs in disguise**: `ns123456.ip-1-2-3.eu` — the `ip-1-2-3` part encodes the primary IP
- **Async everything**: installs, reboots, and template operations all return task IDs — always poll
- **IPMI sessions expire**: KVM sessions last 1 hour by default; request a new one if it expires
- **Firewall gotcha**: OVH hardware-level firewall (`/v2/dedicated/server/{name}/firewall`) blocks traffic even before the OS — misconfiguring it can lock you out completely (destructive op)
- **Monitoring alerts**: set up `/v2/dedicated/server/{name}/alertContact` to receive OVH hardware alerts
- **Service names vs display names**: the `name` field (like `ns123456.ip-1-2-3.eu`) is used in all API calls; `displayName` is cosmetic only
