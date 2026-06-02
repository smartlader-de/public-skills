# 1Password MCP Secrets Skill Design

## Summary

Create a Codex skill named `one-password-mcp-secrets` that helps agents manage project environment variables through 1Password Environments. The skill is MCP-first: it should prefer the 1Password MCP server because that path can create/manage Environments, list variable names, import dotenv files, and coordinate mounted runtime env access without returning secret values to the agent.

The MVP uses exact variable-name matching between 1Password and providers. Provider-specific renames are deferred to roadmap mapping support.

## Goals

- Use 1Password Environments as the source of truth for project env vars.
- Make 1Password MCP setup the first recommended path when MCP is missing.
- Support metadata-only import, audit, and sync planning without exposing values.
- Support controlled sync to Netlify and Cloudflare in the MVP.
- Keep fallback CLI workflows explicit and guarded.
- Produce summaries that report names, contexts, and status only.

## Non-Goals

- Do not build a password-manager UI.
- Do not silently install, enable, or configure MCP.
- Do not expose raw secret values unless the user explicitly approves a fallback path.
- Do not support provider-specific variable renames in MVP.
- Do not make provider deletion or secret rotation part of the first implementation.

## Architecture

The skill should be organized as a compact `SKILL.md` plus focused bundled resources:

```text
one-password-mcp-secrets/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── one-password-environments.md
│   ├── mcp-setup.md
│   ├── netlify.md
│   ├── cloudflare.md
│   └── security.md
└── scripts/
    ├── compare-env-names.js
    ├── parse-dotenv.js
    └── redact-output.sh
```

`SKILL.md` should contain the core workflow, trigger guidance, safety rules, and when to load each reference file. Provider details belong in reference files so future agents only load Netlify or Cloudflare guidance when needed.

## Core Workflow

Every task follows this order:

1. Classify intent: setup, import, audit, sync, local runtime, or fallback.
2. Detect 1Password MCP availability.
3. If MCP is missing, recommend MCP setup before value-based CLI fallback.
4. Determine source and destination.
5. Run metadata-only comparison first.
6. Ask for explicit confirmation before production writes, overwrites, deletes, rotations, or raw value access.
7. Execute the chosen workflow.
8. Verify by names, contexts, and status only.
9. Summarize without secrets.

## MCP Setup Behavior

The skill should detect and guide MCP setup before using lower-safety fallbacks.

Detection checks:

- Whether 1Password MCP tools are already exposed in the current agent session.
- Whether the 1Password app contains the local MCP binary, for example `/Applications/1Password.app/Contents/MacOS/onepassword-mcp` on macOS.
- Whether the current Codex MCP config includes a 1Password server entry.

Setup rules:

- Ask before editing Codex MCP configuration.
- Explain required 1Password app settings and possible enterprise policy requirements.
- Treat the 1Password MCP server as beta and platform-dependent.
- After setup, verify availability with metadata-only operations.
- If setup is declined or unavailable, continue only with an explicit fallback path.

## 1Password Storage Model

The skill treats a 1Password Environment as individual variables, not a single stored `.env` blob.

Each variable has:

- `name`
- `value`
- `masked` or hidden-by-default state

Dotenv files are interfaces around those variables:

- Import converts dotenv entries into individual Environment variables.
- Reading may present variables as `KEY=value` lines.
- Runtime workflows inject variables into subprocess environments.
- MCP-mounted `.env` files are compatibility surfaces, not persistent source files.

## Access Paths

Preferred order:

1. 1Password MCP for Environment management and metadata-only workflows.
2. CLI Environment support such as `op environment read` and `op run --environment`, when detected.
3. Classic `op run --env-file` with `op://` references, when the project can represent variables as references.
4. Classic vault/item workflows, only with explicit approval.
5. Manual desktop workflow when automation is unavailable.

The skill must feature-detect commands and flags instead of assuming that a given `op` version supports Environments.

## Import Workflow

For requests like “Import this project’s `.env` files into 1Password Environments”:

1. Locate dotenv-like files, including `.env`, `.env.local`, `.env.production`, `.env.cloud`, and provider-specific variants.
2. Parse variable names without printing values.
3. Infer target Environment names from project name and file suffix.
4. Present a proposed import plan containing file names, target Environment names, and variable names only.
5. Prefer MCP import or Environment creation.
6. If MCP is unavailable, offer setup first.
7. If setup is declined, provide manual desktop import guidance or guarded CLI fallback.

Comments and ordering do not need to be preserved in MVP. Dotenv import is key/value oriented.

## Audit Workflow

For drift checks:

1. Resolve source Environment and provider target.
2. List variable names and provider contexts only.
3. Compare exact names.
4. Report:
   - missing in 1Password
   - missing in provider
   - extra in provider
   - context mismatch
5. Do not compare values by default.

Hashes, lengths, and value comparison require explicit user approval and should be avoided in MVP unless necessary.

## Provider Sync

The MVP supports Netlify and Cloudflare.

Common adapter requirements:

- Define provider contexts or environments.
- Identify the safest command/API path for setting secrets.
- Prefer stdin, subprocess environment, or API body over command-line arguments containing values.
- Verify by listing names and contexts only.
- Require confirmation before production writes and overwrites.

Netlify MVP:

- Support production context first.
- Use documented Netlify CLI/API environment variable commands.
- Mark sensitive values as secret where supported.
- Verify by listing environment variable names and contexts only.

Cloudflare MVP:

- Support Worker secrets first.
- Prefer `wrangler secret put` or safe equivalent paths.
- Avoid plaintext temp files.
- If a temp file is unavoidable, create it with restrictive permissions, delete it immediately, and never print contents.

## Local Runtime Workflow

For local development:

1. Prefer `op run --environment <environmentID> -- <command>` when CLI Environment support exists.
2. Prefer MCP-managed mounted `.env` files when dotenv compatibility is needed.
3. Use `op run --env-file <file> -- <command>` with `op://` references as a classic compatibility mode.
4. Ensure generated or mounted dotenv paths are gitignored.
5. Update project scripts only after the user asks for it and the skill checks project-specific impact.

## Secret Safety

The skill must enforce these rules:

- Never print secret values.
- Never paste secrets into chat.
- Never write secrets to persistent files unless explicitly required.
- Never use shell tracing around secret operations.
- Avoid inline shell assignments containing secret values.
- Avoid commands that expose values through process listings or shell history.
- Use temp files only with restrictive permissions and immediate cleanup.
- Report only names, contexts, presence/absence, and sync status.

Explicit user authorization is required before:

- Reading raw values through CLI or SDK fallback.
- Pushing to production providers.
- Overwriting existing provider values.
- Deleting provider values.
- Rotating credentials.
- Enabling, installing, or configuring beta MCP functionality.

## Scripts

### `parse-dotenv.js`

Parse dotenv-like files and output variable names plus basic file metadata without printing values. It should support quoted values, blank lines, comments, and `export KEY=value` syntax.

### `compare-env-names.js`

Compare two or more variable-name sets and output missing/extra/common names. It should not accept or print values.

### `redact-output.sh`

Provide a conservative redaction helper for command output that may contain common token patterns. This is defense in depth and does not replace the rule to avoid printing secrets.

## References

### `one-password-environments.md`

Current 1Password Environment concepts, storage model, CLI Environment detection, `op run --environment`, and `op environment read` notes.

### `mcp-setup.md`

How to detect the local MCP server binary, what Codex config should look like, what 1Password app settings may be required, and how to verify setup without exposing values.

### `netlify.md`

Netlify env var contexts, CLI/API commands, secret flags, overwrite behavior, and verification commands.

### `cloudflare.md`

Cloudflare Worker secret commands, environment-specific Worker configuration, temp-file avoidance, and verification commands.

### `security.md`

Secret-handling rules, approval gates, safe command patterns, unsafe command patterns, and examples of acceptable summaries.

## Testing And Validation

Validation should cover:

- Skill folder validation with the system skill validation script.
- Dotenv parser tests with comments, quoted values, empty values, and `export` syntax.
- Name comparison tests for missing, extra, and common variables.
- Dry-run examples for import, audit, MCP setup, Netlify sync, Cloudflare sync, and local runtime.
- Negative examples where the skill must refuse to print values or proceed without approval.

No test should require real secrets. Use placeholder names and dummy values only.

## Success Criteria

- A future agent can choose MCP-first behavior without needing the PRD.
- The skill clearly explains how variables are stored in 1Password Environments.
- The skill can audit exact variable-name drift without value access.
- The skill can guide MCP setup before falling back to CLI paths.
- The skill supports Netlify and Cloudflare MVP workflows safely.
- The skill leaves provider-specific mapping support out of MVP and points to the roadmap.

## Deferred Work

- Provider-specific variable mapping through `secrets.map.json`.
- Vercel adapter.
- Supabase adapter.
- CI adapter.
- Secret rotation workflows.
- Value hash comparison workflows.
- Reverse sync from providers into 1Password.
