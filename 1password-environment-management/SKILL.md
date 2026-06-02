---
name: one-password-mcp-secrets
description: Use when managing project environment variables, provider secrets, or local runtime secrets through 1Password Environments, 1Password MCP, or guarded op CLI workflows
---

# one-password-mcp-secrets

Manage project environment variables through 1Password Environments. MCP-first. Values never reach the agent by default.

## When To Use

Use this skill when a user asks to:

- Import `.env` files or project secrets into 1Password.
- Check whether 1Password and a deployment provider are in sync.
- Push secrets from 1Password to Netlify or Cloudflare.
- Set up local development so secrets come from 1Password at runtime.
- Understand or configure the 1Password MCP server for secret management.

Do not use this skill for general password-manager operations or secret rotation. Rotation is deferred.

## Core Workflow

Follow this order every time:

1. Classify intent: setup, import, audit, sync, local runtime, or fallback.
2. Load `references/security.md`.
3. Detect 1Password MCP availability.
4. If MCP is missing, recommend MCP setup before any value-based CLI fallback.
5. Determine source, destination, provider, and context.
6. Run metadata-only comparison first: names, contexts, and status only.
7. Ask for explicit confirmation before production writes, overwrites, deletes, rotations, MCP configuration, or raw value access.
8. Execute the chosen workflow.
9. Verify by names, contexts, and status only.
10. Summarize without secrets.

## MCP Detection

Check in this order:

1. Are 1Password MCP tools available in this agent session?
2. Does the local MCP binary exist, such as `/Applications/1Password.app/Contents/MacOS/onepassword-mcp` on macOS?
3. Is Codex configured to launch that MCP server?

If MCP is missing, offer setup. Do not proceed to CLI fallback until setup is declined or unavailable.

Load `references/mcp-setup.md` for setup details.

## Access Path Priority

1. 1Password MCP for Environment management and metadata-only workflows.
2. `op run --environment` for subprocess runtime injection when supported.
3. `op environment read` only as guarded raw-value fallback.
4. `op run --env-file` with `op://` references for classic compatibility.
5. Classic vault/item workflows only with explicit approval.
6. Manual desktop workflow when automation is unavailable.

Always feature-detect CLI support. Do not assume the installed `op` version supports Environments.

Load `references/one-password-environments.md` for storage model and CLI guidance.

## Import Workflow

For importing project `.env` files into 1Password:

1. Locate dotenv-like files such as `.env`, `.env.local`, `.env.production`, `.env.cloud`, and provider variants.
2. Run `node scripts/parse-dotenv.js <file...>` to extract names only.
3. Infer target Environment names from project name and file suffix.
4. Present a proposed import plan with file names, target Environment names, and variable names only.
5. Confirm before proceeding.
6. Prefer MCP import or guided desktop import.
7. Use CLI fallback only with explicit approval.

Comments and ordering do not need to be preserved in MVP.

## Audit Workflow

For drift checks:

1. List 1Password Environment variable names through MCP when possible.
2. List provider variable names using the relevant provider reference.
3. Write name-only JSON files.
4. Run `node scripts/compare-env-names.js source.json target.json`.
5. Report missing in 1Password, missing in provider, extra in provider, and context mismatch.
6. Do not compare values, hashes, or lengths without explicit approval.

Load provider references as needed:

- Netlify: `references/netlify.md`
- Cloudflare: `references/cloudflare.md`

## Provider Sync Workflow

For pushing 1Password secrets to Netlify or Cloudflare:

1. Run audit workflow first.
2. Confirm the diff with the user.
3. Confirm before each write and list which names will be created or overwritten.
4. Prefer `op run --environment ENV_ID -- <provider-command>` only when the provider command can receive the value without argv exposure.
5. For Netlify automated writes, use the API-body pattern in `references/netlify.md`; use `netlify env:set KEY "$VALUE"` only as an explicitly approved manual fallback.
6. For Cloudflare, prefer interactive `wrangler secret put`; use stdin automation only with explicit approval.
7. Verify by listing names and contexts after sync.
8. Summarize names synced, names skipped, and non-secret errors.

## Local Runtime Workflow

For local development:

1. Prefer `op run --environment ENV_ID -- your-command` when supported.
2. Prefer MCP-managed mounted `.env` files when dotenv compatibility is required.
3. Use `op run --env-file .env -- your-command` with `op://` references as classic compatibility.

Always ensure generated or mounted dotenv paths are in `.gitignore`. Do not update project scripts without user confirmation.

## CLI Fallback

If MCP is unavailable and the user declines setup, say:

```text
1Password MCP is not available. I can use a guarded CLI fallback, but this may require raw value access. Do you approve?
```

Never read values without explicit approval. Pipe displayed command output through `scripts/redact-output.sh`, but remember redaction is only defense in depth.

## Scripts

| Script | Purpose | Usage |
|---|---|---|
| `scripts/parse-dotenv.js` | Extract variable names from dotenv files | `node scripts/parse-dotenv.js .env .env.local` |
| `scripts/compare-env-names.js` | Compare two name sets | `node scripts/compare-env-names.js source.json target.json` |
| `scripts/redact-output.sh` | Redact common token patterns from output | `some-command | bash scripts/redact-output.sh` |

## Not Supported In MVP

- Provider-specific variable renaming
- Vercel, Supabase, or CI adapters
- Secret rotation
- Reverse sync from provider to 1Password
- Value hash comparison
