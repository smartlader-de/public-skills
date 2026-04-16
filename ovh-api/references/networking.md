# Networking Reference — OVH v2 API

## Table of Contents

1. [IP blocks](#1-ip-blocks)
2. [Failover IP management](#2-failover-ip-management)
3. [Load Balancer (ipLoadbalancing)](#3-load-balancer-iploadbalancing)
4. [vRack (private network)](#4-vrack-private-network)
5. [Firewall](#5-firewall-destructive)
6. [Common patterns and gotchas](#6-common-patterns-and-gotchas)

---

## 1. IP blocks

### List all IPs on the account
```bash
python scripts/ovh_request.py --method GET --path /v2/ip
```

**Response shape:**
```json
[
  {
    "ip": "1.2.3.4/32",
    "type": "failover",
    "routedTo": {"serviceName": "ns123456.ip-1-2-3.eu"},
    "country": "DE"
  }
]
```

Filter by type: `GET /v2/ip?type=failover`
Types: `failover`, `dedicated`, `block`, `mrtg`.

### Get a specific IP block
```bash
python scripts/ovh_request.py --method GET --path /v2/ip/1.2.3.4%2F32
```
Note: forward slash in CIDR must be URL-encoded as `%2F`.

---

## 2. Failover IP management

### Route a failover IP to a server
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/ip/1.2.3.4%2F32/move \
  --body '{"to":"ns123456.ip-1-2-3.eu"}'
```

### List services IP can be routed to
```bash
python scripts/ovh_request.py --method GET --path /v2/ip/1.2.3.4%2F32/move
```

### Set reverse DNS
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/ip/1.2.3.4%2F32/reverse \
  --body '{"ipReverse":"1.2.3.4","reverse":"mail.example.com."}'
```
Note: trailing dot on the reverse hostname is required.

---

## 3. Load Balancer (ipLoadbalancing)

### List load balancers
```bash
python scripts/ovh_request.py --method GET --path /v2/ipLoadbalancing
```

### Get LB details
```bash
python scripts/ovh_request.py --method GET --path /v2/ipLoadbalancing/{serviceName}
```

### List server farms (backend pools)
```bash
python scripts/ovh_request.py --method GET --path /v2/ipLoadbalancing/{serviceName}/tcp/farm
```

### Add a server to a farm
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/ipLoadbalancing/{serviceName}/tcp/farm/{farmId}/server \
  --body '{"address":"10.0.0.1","port":80,"status":"active","weight":1}'
```

### Apply pending changes
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/ipLoadbalancing/{serviceName}/refresh
```
Changes are staged — always refresh after modifications to apply them.

---

## 4. vRack (private network)

### List vRacks
```bash
python scripts/ovh_request.py --method GET --path /v2/vrack
```

### List services in a vRack
```bash
python scripts/ovh_request.py --method GET --path /v2/vrack/{vrackId}/server
```

### Add a dedicated server to vRack
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/vrack/{vrackId}/dedicatedServer \
  --body '{"dedicatedServer":"ns123456.ip-1-2-3.eu"}'
```

### Remove a server from vRack ⚠ DESTRUCTIVE
```bash
python scripts/ovh_request.py \
  --method DELETE \
  --path /v2/vrack/{vrackId}/dedicatedServer/ns123456.ip-1-2-3.eu
```
This removes the private network interface from the server. Any traffic routed through vRack will stop. Destructive-ops protocol required.

---

## 5. Firewall ⚠ DESTRUCTIVE

**WARNING: Firewall changes can lock you out of your own infrastructure.**
Even POST (adding rules) or DELETE (removing rules) can result in complete server inaccessibility if misconfigured.
All firewall operations should be treated as destructive and follow the full protocol.

### Enable firewall on an IP
```bash
python scripts/ovh_request.py \
  --method PUT \
  --path /v2/ip/1.2.3.4%2F32/firewall/1.2.3.4 \
  --body '{"enabled":true}'
```

### List firewall rules
```bash
python scripts/ovh_request.py --method GET --path /v2/ip/1.2.3.4%2F32/firewall/1.2.3.4/rule
```

### Add a firewall rule ⚠ DESTRUCTIVE
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/ip/1.2.3.4%2F32/firewall/1.2.3.4/rule \
  --body '{
    "sequence": 0,
    "action": "permit",
    "protocol": "tcp",
    "tcpOption": {"option": "established"},
    "rule": "permit tcp any any established"
  }'
```

Rules are applied by sequence number (0 = highest priority). Always verify existing rules before adding.

### Delete a firewall rule ⚠ DESTRUCTIVE
```bash
python scripts/ovh_request.py \
  --method DELETE \
  --path /v2/ip/1.2.3.4%2F32/firewall/1.2.3.4/rule/{sequence}
```
Removing an "allow" rule effectively blocks that traffic. Destructive-ops protocol required.

---

## 6. Common patterns and gotchas

- **URL-encode IP slashes**: `1.2.3.4/32` → `1.2.3.4%2F32` in paths
- **LB changes need refresh**: modifications to LB farms/servers are staged and only take effect after `/refresh`
- **vRack deletion blocker**: cannot delete a vRack with servers attached — detach first
- **Firewall sequence order**: lower number = higher priority; gaps in numbering are fine
- **Reverse DNS trailing dot**: always append `.` to reverse DNS hostnames (`mail.example.com.`)
- **Failover IP routing takes ~30s**: after a move, propagation takes up to a minute
