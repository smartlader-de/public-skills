# Licenses Reference — OVH v2 API

## Table of Contents

1. [List licenses](#1-list-licenses)
2. [cPanel licenses](#2-cpanel-licenses)
3. [Plesk licenses](#3-plesk-licenses)
4. [Windows licenses](#4-windows-licenses)
5. [Common patterns and gotchas](#5-common-patterns-and-gotchas)

---

## 1. List licenses

List all licenses on the account:
```bash
python scripts/ovh_request.py --method GET --path /v2/license
```

For a specific type:
```bash
python scripts/ovh_request.py --method GET --path /v2/license/cpanel
python scripts/ovh_request.py --method GET --path /v2/license/plesk
python scripts/ovh_request.py --method GET --path /v2/license/windows
```

---

## 2. cPanel licenses

### List cPanel licenses
```bash
python scripts/ovh_request.py --method GET --path /v2/license/cpanel
```

### Get license details
```bash
python scripts/ovh_request.py --method GET --path /v2/license/cpanel/{serviceName}
```

Key fields: `domain`, `ip`, `status`, `version` (PREMIER, PRO, etc.).

### Change the IP a license is assigned to
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/license/cpanel/{serviceName}/changeIp \
  --body '{"ip":"1.2.3.4"}'
```

---

## 3. Plesk licenses

```bash
python scripts/ovh_request.py --method GET --path /v2/license/plesk
python scripts/ovh_request.py --method GET --path /v2/license/plesk/{serviceName}
```

### Change assigned IP
```bash
python scripts/ovh_request.py \
  --method POST \
  --path /v2/license/plesk/{serviceName}/changeIp \
  --body '{"ip":"1.2.3.4"}'
```

---

## 4. Windows licenses

```bash
python scripts/ovh_request.py --method GET --path /v2/license/windows
python scripts/ovh_request.py --method GET --path /v2/license/windows/{serviceName}
```

---

## 5. Common patterns and gotchas

- **Licenses are IP-bound**: most OVH licenses (cPanel, Plesk) attach to a specific IP — reassign if server IP changes
- **One license per server**: you cannot use the same license key on multiple IPs
- **License status takes a few minutes**: after an IP change, the new license takes up to 15 minutes to activate
- **Windows licensing**: OVH Windows licenses cover the OVH-installed OS only — bring-your-own-license scenarios are not supported through this API
