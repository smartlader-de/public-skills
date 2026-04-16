# VPS Reference — OVH v2 API

## Table of Contents

1. [List VPS instances](#1-list-vps-instances)
2. [Get VPS details](#2-get-vps-details)
3. [Get VPS IP addresses](#3-get-vps-ip-addresses)
4. [Reboot a VPS](#4-reboot-a-vps-destructive)
5. [Reinstall a VPS](#5-reinstall-a-vps-destructive)
6. [Delete a VPS](#6-delete-a-vps-destructive)
7. [Get VPS tasks](#7-get-vps-tasks)
8. [Common patterns and gotchas](#8-common-patterns-and-gotchas)

---

## 1. List VPS instances

```bash
python scripts/ovh_request.py --method GET --path /v2/vps
```

**Response shape:**
```json
[
  "vps-abc123.vps.ovh.net",
  "vps-xyz789.vps.ovh.net"
]
```
Returns an array of VPS service names (identifiers). Use these IDs in subsequent calls.

---

## 2. Get VPS details

```bash
python scripts/ovh_request.py --method GET --path /v2/vps/vps-abc123.vps.ovh.net
```

**Response shape:**
```json
{
  "name": "vps-abc123.vps.ovh.net",
  "state": "running",
  "netbootMode": "local",
  "memoryLimit": 2048,
  "vcore": 1,
  "cluster": "rbx1",
  "displayName": "My Web Server"
}
```

Key fields: `state` (running/stopped/rebooting/rescue), `memoryLimit` (MB), `vcore` (vCPU count), `cluster` (datacenter).

---

## 3. Get VPS IP addresses

```bash
python scripts/ovh_request.py --method GET --path /v2/vps/vps-abc123.vps.ovh.net/ips
```

**Response shape:**
```json
[
  {
    "ipAddress": "1.2.3.4",
    "type": "primary",
    "version": 4
  },
  {
    "ipAddress": "2001:db8::1",
    "type": "additional",
    "version": 6
  }
]
```

---

## 4. Reboot a VPS ⚠ DESTRUCTIVE

Interrupts service. Follow destructive-ops protocol.

```bash
# Plan first
cat > /tmp/ovh-pending.json << 'EOF'
{"resource_type":"vps","resource_id":"vps-abc123.vps.ovh.net","method":"POST","path":"/v2/vps/vps-abc123.vps.ovh.net/reboot","reason":"user requested reboot","irreversible":false}
EOF

python scripts/validate_destructive.py /tmp/ovh-pending.json
# Then triple confirmation, then:
python scripts/ovh_request.py --method POST --path /v2/vps/vps-abc123.vps.ovh.net/reboot --body '{}'
```

**Response:** A task object with `id` — poll `/v2/vps/{name}/tasks/{taskId}` for completion.

Note: reboot is not truly irreversible (server comes back up), but it interrupts running services, so the destructive-ops protocol still applies.

---

## 5. Reinstall a VPS ⚠ DESTRUCTIVE

Wipes all data. Full destructive-ops protocol required.

```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/vps/vps-abc123.vps.ovh.net/reinstall \
  --body '{"templateName":"ubuntu2204-server_64","sshKey":"my-ssh-key-name"}'
```

Get available templates first:
```bash
python scripts/ovh_request.py --method GET --path /v2/vps/vps-abc123.vps.ovh.net/availableTemplates
```

---

## 6. Delete a VPS ⚠ DESTRUCTIVE

Terminates service contract and deletes server. Full destructive-ops protocol required.

```bash
python scripts/ovh_request.py --method DELETE --path /v2/vps/vps-abc123.vps.ovh.net
```

**Response:** HTTP 200 with empty body on success. The service enters "terminated" state and is removed from billing.

---

## 7. Get VPS tasks

```bash
python scripts/ovh_request.py --method GET --path /v2/vps/vps-abc123.vps.ovh.net/tasks
```

Poll a specific task:
```bash
python scripts/ovh_request.py --method GET --path /v2/vps/vps-abc123.vps.ovh.net/tasks/12345
```

Task states: `todo`, `doing`, `done`, `error`, `cancelled`.

---

## 8. Common patterns and gotchas

- **VPS IDs include the TLD**: e.g., `vps-abc123.vps.ovh.net` — don't strip the domain part
- **State transitions are async**: reboot/reinstall return a task ID immediately; poll tasks endpoint to track progress
- **Rescue mode**: to boot into rescue, use `/v2/vps/{name}/setNetboot` with `netbootMode: "rescue"` then reboot
- **SSH keys**: register via `/v2/me/sshKey` before using in reinstall payloads
- **Monitoring**: `/v2/vps/{name}/monitoring` returns CPU/RAM stats (only available for certain plans)
