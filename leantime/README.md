# Leantime Skill v1.0

A Claude skill for managing Leantime projects, tickets, users, and comments
via the JSON-RPC 2.0 API. Single API key auth — no OAuth, no HMAC.

## What it covers

- Projects: list, get by ID, create
- Tickets: list (with optional project filter), get by ID, create, update
- Users: list all, get by ID (read-only)
- Comments: add to a ticket, list for a ticket
- Connectivity probe (`scripts/check_connection.py`) with clear remediation on failure
- No external dependencies — Python 3.8+ stdlib only

## Requirements

- A reachable Leantime v3.x instance (self-hosted or cloud)
- An API key from **Company Settings → API** in your Leantime instance
- Python 3.8+ (for the connectivity probe)
- curl (default on macOS and most Linux distros)

## Installation

```bash
npx skills add smartlader-de/public-skills --skill leantime
```

Or install manually:

```bash
cp -r public-skills/leantime ~/.claude/skills/leantime
```

Or if installing directly from this repository:

```bash
mkdir -p ~/.claude/skills/leantime
cp -r . ~/.claude/skills/leantime/
```

## Uninstall

```bash
rm -rf ~/.claude/skills/leantime
```

## First-time setup

Run the interactive setup wizard — it will ask for your URL and API key,
verify the connection, and write `.env` automatically:

```bash
cd your-project-directory
python ~/.claude/skills/leantime/scripts/setup_credentials.py
```

Or create `.env` manually:

```bash
echo "LEANTIME_URL=https://your-leantime.example.com" >> .env
echo "LEANTIME_API_KEY=your-api-key-here" >> .env
python ~/.claude/skills/leantime/scripts/check_connection.py
```

For full step-by-step instructions including API key generation, see
`references/setup.md` inside the skill.

## Credential sources

The skill reads credentials from `.env` in the current working directory:

```
LEANTIME_URL=https://your-leantime.example.com
LEANTIME_API_KEY=<your-api-key>
```

Generate your API key at: **Leantime → Company Settings → API**

## Directory structure

```
leantime/
├── SKILL.md                  ← Main skill instructions (loaded by Claude)
├── README.md                 ← This file (not loaded by Claude)
├── scripts/
│   ├── check_connection.py   ← Validate credentials + probe endpoint
│   └── setup_credentials.py  ← Interactive credential setup wizard
├── references/
│   ├── setup.md              ← API key provisioning and .env creation guide
│   ├── projects.md           ← Project RPC methods
│   ├── tickets.md            ← Ticket RPC methods
│   ├── users.md              ← User read-only RPC methods
│   └── comments.md           ← Comment RPC methods
└── evals/
    ├── evals.json            ← Test scenarios
    └── trigger-queries.json  ← Description optimization queries
```

## Version history

- **v1.0** (2026-04-17): Initial public release.
  Covers projects, tickets, users, and comments via JSON-RPC 2.0. All v1
  operations are additive — no delete or admin operations exposed.
