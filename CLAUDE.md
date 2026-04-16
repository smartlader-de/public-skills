# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A **multi-skill library** for Claude agents. Each top-level directory is a self-contained skill that extends Claude with domain-specific capabilities.

Install via:
```bash
npx skills add christianzebrowski/public-skills --skill ovh-api
npx skills add christianzebrowski/public-skills --list   # list all
```

## Skill Directory Convention

Each skill directory **must** match the `name` field in its `SKILL.md` frontmatter exactly (lowercase, hyphens only). The structure inside every skill follows:

```
<skill-name>/
├── SKILL.md           ← Required. Loaded by Claude on invocation. Keep lean.
├── README.md          ← User-facing docs. Not loaded by Claude.
├── scripts/           ← Executable helpers (any language)
├── references/        ← Lazy-loaded reference material (loaded per-task, not upfront)
└── evals/
    ├── evals.json          ← Test scenario definitions
    └── trigger-queries.json ← Natural language phrases that activate the skill
```

## Skills in This Repo

| Directory | Skill Name | Purpose |
|-----------|------------|---------|
| `ovh-api/` | `ovh-api` | OVH Cloud infrastructure management via v2 REST API |

## Adding a New Skill

1. Create `<skill-name>/SKILL.md` with `name:` matching the directory
2. Add `description:` rich enough to serve as the activation trigger
3. Add scripts, references, evals as needed
4. Add a row to the table above and to the root `README.md`

## ovhcloud Skill — Architecture Notes

Every invocation pipeline:
1. **Credential check** — `scripts/check_credentials.py` reads `.env` (cwd) or `~/.ovh.conf`. Missing → `scripts/setup_auth.py`.
2. **Mode gate** — User chooses read-only (GET only) or full-access before any operation.
3. **Lazy-load** — Only `references/<product-family>.md` matching the current task is loaded.
4. **Destructive ops** — DELETE, reinstall, reboot, terminate, DNS-destructive → write `/tmp/ovh-pending.json` → `validate_destructive.py` → triple confirmation (yes/no → type resource name → type CONFIRM). Non-bypassable.
5. **Execute** — `scripts/ovh_request.py` builds HMAC-SHA1 signed OVH v2 API requests.

Scripts use Python 3.8+ stdlib only — zero external dependencies is a hard constraint.

```bash
python ovh-api/scripts/check_credentials.py
python ovh-api/scripts/ovh_request.py --method GET --path /v2/vps
python ovh-api/scripts/setup_auth.py
python ovh-api/scripts/validate_destructive.py /tmp/ovh-pending.json
```
