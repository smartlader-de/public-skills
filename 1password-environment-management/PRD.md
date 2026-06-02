# PRD: 1Password MCP Secrets Manager Skill

## Working Name

`one-password-mcp-secrets`

## Purpose

Let Codex, Claude, or another agent securely manage project environment variables through 1Password Environments and the 1Password MCP Server, with support for local runtime injection and controlled syncing to deployment providers such as Netlify, Cloudflare, Vercel, Supabase, and CI systems.

## Problem

Project secrets are often spread across local `.env` files, provider dashboards, CLI sessions, and chat history. This creates risk:

- Secrets may be stored on disk in plaintext.
- Agents may accidentally print or retain secret values.
- Netlify, Cloudflare, and other providers can drift from the real source of truth.
- Onboarding or redeploying requires manual reconstruction of env vars.
- Rotating secrets across providers is tedious and error-prone.

The user wants 1Password to become the secure source of truth while allowing AI agents to help retrieve, validate, and push secrets to infrastructure providers.

## Goals

1. Use 1Password Environments as the preferred source of truth for project env vars.
2. Use the 1Password MCP Server when available so agents can manage Environments without directly receiving secret values.
3. Support provider sync workflows:
   - Netlify env vars
   - Cloudflare Worker secrets
   - Vercel env vars
   - local runtime injection with `op run --environment`
   - local mounted `.env` files through the 1Password MCP flow
   - future providers through adapters
4. Prevent secret leakage in terminal output, chat, logs, temp files, and generated docs.
5. Provide clear fallback behavior using `op` CLI only when MCP is unavailable or a provider adapter requires raw values.
6. Support environment separation:
   - local
   - staging
   - production
   - preview
   - branch-specific contexts

## Non-Goals

- Do not replace 1Password itself.
- Do not build a general password manager UI.
- Do not expose raw secret values to the agent unless the user explicitly authorizes a fallback path.
- Do not store provider API tokens in project files.
- Do not assume every provider uses the same env-var semantics.

## Target Users

- Developers using Codex or Claude agents for deployment automation.
- Solo founders managing multiple deployment targets.
- Teams that want 1Password as the single source of truth for env vars.
- Agents that need to configure Netlify, Cloudflare, or similar platforms safely.

## Primary Use Cases

### Import Existing Project Secrets

User says:

```text
Import this project's .env files into 1Password Environments.
```

Skill behavior:

- Detect `.env`, `.env.local`, `.env.production`, `.env.cloud`, and similar files.
- Classify environment files by context.
- Propose Environment names, for example:
  - `chargealert-local`
  - `chargealert-production`
- Use 1Password MCP to create or update Environments if available.
- Otherwise instruct the user through the desktop import flow.
- Never print secret values.

### Sync 1Password Environment to Netlify

User says:

```text
Push chargealert-production secrets to Netlify production.
```

Skill behavior:

- Resolve 1Password Environment ID or name.
- Resolve Netlify site.
- Compare variable names without exposing values.
- Push missing or changed vars using Netlify CLI/API.
- Mark sensitive values as `--secret` where supported.
- Verify by listing variable names and contexts only.

### Sync 1Password Environment to Cloudflare

User says:

```text
Push these secrets to Cloudflare Workers.
```

Skill behavior:

- Resolve Worker/project.
- Map vars to `wrangler secret put`, `secret bulk`, or deployment secret file flow.
- Avoid plaintext temp files where possible.
- If a temp file is unavoidable, create it with restrictive permissions, delete it immediately, and do not print contents.

### Mount Local Runtime Env

User says:

```text
Make local dev use 1Password instead of plaintext .env.
```

Skill behavior:

- Prefer `op run --environment <environmentID> -- <command>` for local development when the project can run under a subprocess.
- Recommend MCP-managed mounted `.env` files when the user wants editor/tooling compatibility with dotenv-based workflows.
- Ensure it is gitignored.
- Explain 1Password desktop authorization prompts.
- Update project scripts only if requested and after project-specific impact checks where required.

### Rotate or Audit Secrets

User says:

```text
Check what providers are missing from 1Password.
```

Skill behavior:

- Compare variable names across 1Password and provider metadata.
- Report:
  - missing in 1Password
  - missing in provider
  - extra in provider
  - context mismatch
- Never report values.

## Functional Requirements

### MCP Detection

The Skill must first detect whether a 1Password MCP server is available.

Required behavior:

1. Prefer MCP tools for Environments.
2. If MCP is unavailable, make MCP setup the recommended next step before attempting value-based CLI fallback.
3. Check whether the 1Password app includes the local MCP server binary.
4. Guide the user through enabling the local MCP server in 1Password and adding it to Codex.
5. Only after MCP is unavailable, unsupported, or declined, check whether `op` CLI supports `op environment read` and `op run --environment`.
6. If the installed `op` CLI lacks Environment support, explain that a current CLI, 1Password app, or desktop workflow is required.
7. If neither MCP nor CLI Environments are available, fall back to classic vault/item workflows only with explicit user approval.

The Skill must treat the 1Password MCP server as a beta capability and document setup assumptions:

- It may require enabling the local MCP server from 1Password settings.
- Enterprise users may need an admin policy allowing local MCP server access.
- Current platform support should be checked before use.
- MCP workflows should be preferred for creating Environments, listing variable names, importing `.env` files, and managing mounted local `.env` files because the server is designed not to return secret values to the agent.

### MCP Setup Workflow

When MCP is not already configured, the Skill should offer setup before any raw secret access path.

Required behavior:

- Detect whether the local MCP server binary exists, for example `/Applications/1Password.app/Contents/MacOS/onepassword-mcp` on macOS.
- Check current Codex MCP configuration for a 1Password MCP server entry.
- Explain any required 1Password app setting, admin policy, or platform limitation.
- Ask for explicit user authorization before editing Codex MCP configuration or instructing the user to enable beta MCP functionality.
- After setup, verify MCP availability using metadata-only operations.
- Do not proceed to provider syncs until MCP setup is complete, declined, or unavailable.

### 1Password Source Types

The Skill must support:

- 1Password Environments, preferred
- classic vault items with fields, fallback
- `op://` secret references, fallback/integration mode
- `op run --environment <environmentID> -- <command>`, preferred local development mode when supported
- `op run --env-file <file> -- <command>` with `op://` references, classic CLI compatibility mode
- local mounted `.env` files, compatibility mode

### 1Password Environment Storage Model

The Skill must treat a 1Password Environment as a collection of individual variables, not as one stored `.env` file blob.

Each variable has:

- `name`
- `value`
- `masked` / hidden-by-default status

Dotenv files are an interface around that variable collection:

- Importing a `.env` file should create or update individual Environment variables.
- Reading an Environment may present variables as `KEY=value` lines.
- Running a command may inject variables into a subprocess environment.
- MCP-managed mounted `.env` files should be treated as runtime compatibility surfaces, not persistent plaintext source files.

### 1Password Environment Operations

The Skill must distinguish between metadata operations and value operations:

Metadata operations should use MCP when available and may be reported to the user:

- create or select an Environment
- list Environment names and IDs
- list variable names
- import variable names from dotenv files
- compare variable names across providers

Value operations require stricter handling:

- Use `op run --environment <environmentID> -- <command>` when secrets only need to be available to a subprocess.
- Use `op environment read <environmentID>` only when a provider sync cannot be performed through MCP or another non-exposing path.
- If the installed CLI lacks Environment support, use classic `op run --env-file` with `op://` secret references only after confirming that the project can represent required variables as references.
- Do not pipe raw output to commands that may log, echo, trace, cache, or persist values.
- Prefer provider CLIs that accept values on stdin or from process environment.

### Provider Adapters

The Skill should include adapter guidance for:

#### Netlify

- `netlify env:set`
- `netlify env:import`
- `--context production`
- `--secret`
- `--scope builds/functions/runtime` where relevant

#### Cloudflare

- `wrangler secret put`
- `wrangler secret bulk`
- `wrangler deploy --secrets-file`
- environment-specific Worker configuration

#### Vercel

- `vercel env add`
- environment targets such as production, preview, development

#### Generic Provider

- Accept a mapping file.
- Push env vars through CLI/API.
- Verify names only.

Provider adapters must define:

- supported contexts or environments
- whether the provider supports secret values without echoing them
- whether overwrites are destructive or versioned
- whether values can be supplied through stdin, process environment, or API body
- the safest verification command that lists names and contexts only

### Secret Handling Rules

The Skill must enforce:

- Never print secret values.
- Never paste secrets into chat.
- Never write secrets to persistent files unless explicitly required.
- Avoid shell tracing with `set -x`.
- Redact known token patterns in logs.
- Use temp files only with `chmod 600` or stricter.
- Delete temp files after use.
- Report only:
  - variable names
  - presence/absence
  - value length or hash only if needed and explicitly approved
  - provider context
  - sync status

The Skill must avoid any command pattern that exposes raw values through shell history or process listings. Prefer:

- `op run --environment <environmentID> -- provider-cli ...`
- stdin-based provider commands
- short-lived subprocess environment variables
- MCP-managed mounted files where supported

Avoid:

- inline shell assignments containing secret values
- `echo "$SECRET"` pipelines unless the provider CLI has no safer input mode and the user explicitly approves
- `set -x`
- persistent dotenv rewrites

### Authorization

The Skill must require explicit user authorization before:

- Reading secret values through fallback CLI.
- Pushing secrets to production providers.
- Deleting provider env vars.
- Overwriting existing provider env vars.
- Rotating or regenerating credentials.
- Enabling, installing, or configuring beta MCP server functionality.

## Documentation Sources

When using or updating this Skill, check current 1Password documentation for:

- 1Password Environments
- 1Password MCP Server for Codex
- `op environment read`
- `op run --environment`

The feature surface is new enough that the Skill should not rely only on remembered command syntax.

## Recommended Skill Structure

```text
one-password-mcp-secrets/
├── SKILL.md
├── references/
│   ├── one-password-environments.md
│   ├── netlify.md
│   ├── cloudflare.md
│   ├── vercel.md
│   └── security.md
└── scripts/
    ├── redact-output.sh
    ├── compare-env-names.js
    └── parse-dotenv.js
```

## Core Workflow

Every task should follow this sequence:

1. Identify user intent:
   - import
   - sync
   - audit
   - mount
   - rotate
   - provider setup
2. Identify source:
   - 1Password Environment
   - local `.env`
   - vault item
   - provider
3. Identify destination:
   - 1Password Environment
   - Netlify
   - Cloudflare
   - local mounted env
   - other provider
4. Choose access path:
   - MCP preferred
   - MCP setup recommended when MCP is missing
   - CLI Environment support, when detected
   - classic `op run --env-file` with `op://` references for compatibility
   - classic `op` vault/item fallback
   - desktop manual flow if needed
5. Run metadata-only comparison first.
6. Ask for confirmation before production writes.
7. Perform sync.
8. Verify by names/status only.
9. Summarize without secrets.

## Example Skill Trigger Description

```yaml
name: one-password-mcp-secrets
description: >
  Use when managing project passwords, API keys, environment variables, or provider
  secrets through 1Password MCP, 1Password Environments, or op CLI. Supports importing
  .env files into 1Password, syncing secrets to Netlify, Cloudflare, Vercel, and other
  providers, auditing secret drift, running local commands with `op run --environment`,
  mounting local .env files, and safely coordinating agent workflows without exposing
  secret values.
```

## Success Metrics

- User can store all project env vars in 1Password Environments.
- Agent can sync secrets to Netlify/Cloudflare without displaying values.
- Provider env var names match 1Password source-of-truth names.
- Local `.env` plaintext files can be removed or replaced with `op run --environment` or mounted 1Password files.
- Secret syncs produce auditable summaries without leaks.
- Fallback paths are explicit and safe.

## Open Questions

- Should production syncs require a second confirmation every time?
- Should the Skill maintain a project-level mapping file, for example `secrets.map.json`, for provider-specific variable renames?
- Should local `.env` imports preserve comments, or only key/value pairs?
- Should public env vars like `MAPBOX_PUBLIC_TOKEN` be treated separately from hidden secrets?

## Recommended MVP

Build the first version around:

1. Detect 1Password MCP availability.
2. Offer MCP setup when unavailable.
3. Import/audit `.env` and `.env.cloud` by variable name.
4. Manage 1Password Environments as source of truth.
5. Sync to Netlify production.
6. Sync to Cloudflare Worker secrets.
7. Never expose secret values.

This gives the core secure workflow without trying to support every provider on day one.
