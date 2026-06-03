# 1Password Plugin V2 — Design Spec

**Date:** 2026-06-03
**Status:** Approved
**Scope:** Convert standalone `1password-environment-manager` skill to a multi-skill plugin; add V2 SSH & Git skill

---

## Context

The `1password-environment-manager` skill (V1) manages project environment variables through 1Password Environments. Real-world usage showed that SSH key management and server access often occur in the same workflow as secret management. Rather than expanding the single skill, we adopt the superpowers plugin pattern: one plugin, multiple independently invocable skills, shared references.

**Versioning plan:**
- V1: Environments (current, complete)
- V2: SSH & Git (this spec)
- V3: CLI (future)
- V4: SDKs (future)

---

## Section 1: Plugin Structure & Migration

### Repository

The folder renames from `1password-environment-management` to `1password` inside the `public-skills` monorepo.

### Directory Layout

```
1password/
  .claude-plugin/
    plugin.json              ← plugin manifest
  skills/
    environments/
      SKILL.md               ← V1 content, verbatim from current SKILL.md
    ssh-git/
      SKILL.md               ← V2 content (new)
  references/                ← shared across all skills
    mcp-quickstart.md        ← existing
    ssh-agent.md             ← existing
    security.md              ← existing
    one-password-environments.md ← existing
    cloudflare.md            ← existing
    netlify.md               ← existing
    mcp-setup.md             ← existing
    ssh-git.md               ← new (V2)
  scripts/                   ← unchanged
  tests/                     ← unchanged
  docs/                      ← unchanged
  PRD.md                     ← updated to reflect plugin structure
  ROADMAP.md                 ← updated
  package.json               ← unchanged
```

### plugin.json

```json
{
  "name": "1password",
  "description": "1Password developer workflows for agents: environment secrets, SSH & Git, CLI, and SDKs",
  "version": "2.0.0",
  "author": {
    "name": "smartlader.de"
  },
  "repository": "https://github.com/smartlader-de/public-skills",
  "license": "MIT",
  "keywords": ["1password", "secrets", "ssh", "git", "environments", "mcp"]
}
```

### Migration: environments skill

`SKILL.md` moves verbatim to `skills/environments/SKILL.md`. Only the frontmatter changes:

```yaml
---
name: environments
description: Use when managing project environment variables, .env files, provider secrets, deployment secrets, or local runtime secrets through 1Password Environments and MCP.
---
```

Skills invoke as `1password:environments` and `1password:ssh-git`. V3 and V4 each add one `skills/<name>/SKILL.md` with no structural changes.

### Installation

The existing installed skill at `~/.agents/skills/1password-environment-manager/` is removed. The plugin is installed from the new structure. CLAUDE.md trigger rules are updated to use `1password:environments` and `1password:ssh-git`.

---

## Section 2: ssh-git Skill (V2)

### `skills/ssh-git/SKILL.md`

**Frontmatter:**

```yaml
---
name: ssh-git
description: Use when generating SSH keys in 1Password, registering public keys with GitHub/GitLab/servers, configuring Git commit signing, or authenticating SSH sessions using 1Password-managed keys.
---
```

**When To Use** — invoke this skill when:

- Generating or importing an SSH key to store in 1Password
- Registering a public key with GitHub, GitLab, a VPS, or Dokploy
- Configuring Git to sign commits via the 1Password SSH agent
- SSH-ing to a server using a key stored in 1Password
- Auditing which SSH keys exist in 1Password

**Core principle:** Private keys never leave 1Password. The agent only handles public keys and configuration — never the private key material.

**Four Workflows:**

#### Key Generation Workflow
1. Confirm no existing key for this purpose already exists in 1Password (`op item list --categories SSH Key`).
2. Generate key in 1Password: either guide the user through the app UI (Settings → Developer → SSH Keys → New) or use `op item create --category "SSH Key"` with `--generate-password`.
3. Retrieve and display the public key only: `op read "op://vault/item/public key"`.
4. Confirm the key appears in `ssh-add -l` (via 1Password SSH agent).
5. Never print, log, or expose the private key.

Load `references/ssh-agent.md` to verify agent setup before step 4.

#### Provider Registration Workflow
1. Retrieve the public key via `op read` or MCP `list_variables` / `append_variables`.
2. For GitHub: POST to `/user/keys` API with the public key and a label.
3. For GitLab: POST to `/user/keys` API.
4. For servers: append the public key to `~/.ssh/authorized_keys` on the remote host.
5. Verify with `ssh -T git@github.com` (GitHub) or equivalent.

Load `references/ssh-git.md` for provider API call patterns and `authorized_keys` format.

#### Git Signing Workflow
1. Retrieve the public key for signing.
2. Write `~/.ssh/allowed_signers` with the user's email and public key.
3. Configure `~/.gitconfig`: `gpg.format = ssh`, `gpg.ssh.allowedSignersFile`, `user.signingKey`.
4. Optionally set `commit.gpgSign = true` for automatic signing.
5. Verify with `git commit --allow-empty -m "test signing" && git log --show-signature -1`.

Load `references/ssh-git.md` for the exact config blocks.

#### Server SSH Workflow
1. Verify 1Password SSH agent is running and the key appears in `ssh-add -l`.
2. Confirm the public key is registered in `authorized_keys` on the target server (use Provider Registration Workflow if not).
3. Test: `ssh -v user@host` — confirm handshake uses 1Password agent.
4. For per-host key selection, configure `~/.ssh/config` with `IdentityFile` pointing to the public key path (1Password agent resolves the private key).

Load `references/ssh-agent.md` for agent setup and `references/ssh-git.md` for SSH config syntax.

---

## Section 3: Shared References & CLAUDE.md

### New Reference: `references/ssh-git.md`

Contents:
- **GitHub public key API** — `POST /user/keys` with `curl` and `gh` CLI patterns
- **GitLab public key API** — `POST /user/keys` pattern
- **`authorized_keys` format** — exact line format, comment field convention
- **`.gitconfig` signing blocks** — complete config for `gpg.format = ssh`, `allowedSignersFile`, `user.signingKey`, `commit.gpgSign`
- **`allowed_signers` format** — email + keytype + pubkey
- **SSH agent config file** — per-host key selection with `IdentityAgent` and `IdentityFile` combinations
- **Test commands** — `ssh -T git@github.com`, `git log --show-signature`, `ssh-add -l`

### Existing References — No Changes

All seven existing references remain unchanged and continue to be shared across both skills.

### CLAUDE.md Update

Both `~/.claude/CLAUDE.md` and the project-level `CLAUDE.md` update the trigger section:

**Before:**
```
When handling project environment variables, .env files, provider secrets,
deployment env vars, local runtime secrets, or secret sync/audit/import work,
use the 1password-environment-manager skill before taking action.
```

**After:**
```
When handling project environment variables, .env files, provider secrets,
deployment env vars, local runtime secrets, or secret sync/audit/import work,
use the 1password:environments skill before taking action.

When handling SSH keys, Git commit signing, SSH authentication to servers,
or registering public keys with GitHub, GitLab, or remote hosts,
use the 1password:ssh-git skill before taking action.
```

---

## What This Does Not Cover

- CLI workflows beyond Environments and SSH (`op vault`, `op item`, service accounts) — V3
- Programmatic access via Python/Node/Go SDKs — V4
- Secret rotation — deferred (existing non-goal)
- Windows/Linux binary paths for MCP server — deferred
- A guide/umbrella meta-skill — deferred until cross-workflow routing proves necessary
