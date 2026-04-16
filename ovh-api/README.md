# OVH Cloud Skill v1.0

A Claude skill for managing OVH Cloud infrastructure via the OVH v2 REST API.
Safety-first design: read-only mode default, triple confirmation for destructive ops.

## What it covers

- VPS, Dedicated Servers, Public Cloud (instances/volumes/snapshots)
- Networking (IPs, Load Balancer, vRack, Firewall)
- Backup Services, Domains & DNS, Web Hosting, Licenses, Support
- Interactive credential setup wizard (no prior OVH API experience needed)
- No external dependencies — Python 3.8+ stdlib only

## Requirements

- Python 3.8+
- Network access to OVH API (`eu.api.ovh.com`, `ca.api.ovh.com`, or `us.api.ovh.com`)
- An OVH account at [ovh.com](https://www.ovh.com) (free to create)

## Installation

```bash
npx skills add smartlader-de/public-skills --skill ovh-api
```

Or install manually:

```bash
# Clone or download this repo, then:
cp -r public-skills/ovh-api ~/.claude/skills/ovh-api
```

Or if installing directly:
```bash
mkdir -p ~/.claude/skills/ovh-api
cp -r . ~/.claude/skills/ovh-api/
```

## Uninstall

```bash
rm -rf ~/.claude/skills/ovh-api
```

## First-time setup

On first use, the skill will guide you through credential setup, or run manually:

```bash
cd your-project-directory
python ~/.claude/skills/ovh-api/scripts/setup_auth.py
```

This creates a `.env` file in your current directory with your OVH credentials.

## Credential sources

The skill reads credentials from (in order):

1. `.env` in the current working directory:
   ```
   OVH_APPLICATION_KEY=your-app-key
   OVH_APPLICATION_SECRET=your-app-secret
   OVH_CONSUMER_KEY=your-consumer-key
   OVH_ENDPOINT=ovh-eu
   ```

2. `~/.ovh.conf` (official OVH client INI format):
   ```ini
   [default]
   endpoint=ovh-eu
   application_key=your-app-key
   application_secret=your-app-secret
   consumer_key=your-consumer-key
   ```

## Directory structure

```
ovh-api/
├── SKILL.md              ← Main skill instructions (loaded by Claude)
├── README.md             ← This file (not loaded by Claude)
├── scripts/
│   ├── check_credentials.py   ← Validate credentials + probe endpoint
│   ├── ovh_request.py         ← HMAC-SHA1 signed OVH API requests
│   ├── setup_auth.py          ← Interactive credential setup wizard
│   ├── validate_destructive.py ← Pre-flight checks for destructive ops
│   └── write_env.py           ← Write credentials to .env safely
├── references/
│   ├── destructive-ops.md     ← Plan-validate-execute protocol
│   ├── vps.md                 ← VPS endpoints
│   ├── dedicated.md           ← Dedicated server endpoints
│   ├── public-cloud.md        ← Cloud instances, volumes, networks
│   ├── networking.md          ← IPs, Load Balancer, vRack, Firewall
│   ├── backup.md              ← Backup services and storage
│   ├── domains.md             ← Domains, DNS zones, records
│   ├── hosting.md             ← Web hosting, databases
│   ├── licenses.md            ← cPanel, Plesk, Windows licenses
│   ├── support.md             ← Support tickets
│   └── glossary.md            ← Canonical terminology
└── evals/
    ├── evals.json             ← Test scenarios
    └── trigger-queries.json   ← Description optimization queries
```

## Version history

- **v1.0** (2026-04-16): Initial public release.
  Safety-first design with triple opt-in protocol, lazy-loading references, and direct OVH v2 API support.

## Links

- OVH v2 API console: https://eu.api.ovh.com/console/?section=%2Fip&branch=v2
- OVH developer docs: https://developers.ovh.com/
- Create OVH API application (EU): https://eu.api.ovh.com/createApp/
- PRD: `.clavix/outputs/ovhcloud-skill/full-prd.md`

Note: keep this historical PRD reference as-is, and do not add new internal/local planning paths to public-facing docs.
