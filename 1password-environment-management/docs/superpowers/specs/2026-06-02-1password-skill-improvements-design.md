# 1Password Skill Improvements — Design Spec

**Date:** 2026-06-02  
**Status:** Approved  
**Source:** Post-mortem of first real use (OVH-bits Dokploy installation session)

## Context

The `1password-environment-manager` skill was first used in a Codex session to manage secrets during a Dokploy server installation. The session surfaced seven concrete gaps between what the skill documented and what the agent needed to do. This spec covers the improvements agreed upon.

## Problem Summary

Seven gaps observed in the first use:

1. MCP server registration in Codex was undocumented — agent had to discover and edit `config.toml` at runtime
2. The correct MCP auth flow was missing — agent called `list_environments` before `authenticate`, hit a scope error
3. Wrong account_id mental model — MCP `authenticate` returns a different account_id than `op account list`
4. No "create secrets first in 1Password" principle — agent created Docker Swarm secrets first, then tried to copy them into 1Password (wrong direction)
5. 1Password SSH Agent integration was absent — user had to provide the socket snippet manually
6. No empty-account bootstrap path — agent had no guidance when `list_environments` returned empty
7. Codex vs Claude Code MCP availability was not distinguished — tool availability works differently per runtime

## Scope

Additive changes only. Nothing removed from the existing skill.

### New Files

- `references/mcp-quickstart.md`
- `references/ssh-agent.md`

### Modified Files

- `SKILL.md` — three targeted additions to existing sections, one new workflow section

---

## Design

### `references/mcp-quickstart.md`

Covers everything an agent needs to actually drive the MCP server — the operational detail the main SKILL.md lazy-loads on demand.

**Sections:**

**1. Registration by runtime**

| Runtime | How MCP tools become available |
|---|---|
| Claude Code | Auto-available if the binary exists at `/Applications/1Password.app/Contents/MacOS/onepassword-mcp` and the MCP server is registered |
| Codex | Requires a `[mcp_servers.onepassword]` entry in `~/.codex/config.toml` pointing to the binary, then a session restart |

Codex config entry:
```toml
[mcp_servers.onepassword]
command = "/Applications/1Password.app/Contents/MacOS/onepassword-mcp"
```

**2. The correct auth flow**

Always in this order:

```
1. Call authenticate (no arguments)
2. Extract account_id from the result content
3. Pass account_id in every subsequent call
```

The `account_id` returned by `authenticate` is not the same as the account URL or user ID from `op account list`. Using the wrong value produces a `Missing required scope` error (`-32600`).

**3. Tool reference table**

| Tool | Purpose | Access type |
|---|---|---|
| `authenticate` | Establish session, receive account_id | setup |
| `list_environments` | List environment names | read-only |
| `create_environment` | Create a new environment | write |
| `rename_environment` | Rename an existing environment | write |
| `list_variables` | List variable names only (not values) | read-only |
| `append_variables` | Add variables, with `concealed` flag per variable | write |
| `create_local_env_file` | Create a mounted .env file for an environment | write |
| `list_local_env_files` | List mounted .env file paths | read-only |

**4. Desktop approval UX**

The MCP server is a 1Password Labs experiment. Prerequisites:
- Enable in 1Password app: Settings → 1Password Labs → "Enable local MCP server"
- Feature flag: `ai-local-mcp-server`

Approval prompts appear:
- Once per new MCP client connection
- Once per Environment on first variable or file access

If MCP calls hang without returning, a desktop approval is waiting. Check the 1Password app.

**5. Empty account bootstrap**

When `list_environments` returns an empty array, no Environments exist yet. Create one before attempting any variable operations:

```
create_environment(accountId, environmentName)
→ returns environmentId
→ use environmentId in all subsequent variable calls
```

Naming convention: `<project>/<context>` — e.g. `ovh-bits/production`, `my-app/staging`.

**6. Python stdio bridge**

For Codex sessions where MCP tools are not yet available (before config registration + restart), drive the binary directly:

```python
import json, subprocess, select

p = subprocess.Popen(
    ['/Applications/1Password.app/Contents/MacOS/onepassword-mcp'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1
)

def call(method, params=None, id=1):
    msg = {'jsonrpc': '2.0', 'method': method, 'id': id}
    if params: msg['params'] = params
    p.stdin.write(json.dumps(msg) + '\n')
    p.stdin.flush()
    select.select([p.stdout.fileno()], [], [], 30)
    return json.loads(p.stdout.readline())

# Initialize
call('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'agent', 'version': '0.1'}})
p.stdin.write(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) + '\n')
p.stdin.flush()

# Authenticate — use the returned account_id, not op account list ID
auth = call('tools/call', {'name': 'authenticate', 'arguments': {}}, id=2)
account_id = json.loads(auth['result']['content'][0]['text'])['account_id']
```

This bridge is a last resort. Register the server in config and restart the session when possible.

---

### `references/ssh-agent.md`

Short reference connecting 1Password SSH agent to the skill's trust model.

**Sections:**

**1. What it is**

1Password can act as the local SSH agent, so private keys are stored in 1Password and SSH operations require 1Password approval. This extends the same trust model to server access.

**2. Setup**

Add to `~/.ssh/config`:

```
Host *
    IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
```

Enable in 1Password app: Settings → Developer → Use the SSH agent.

**3. Why it matters for this skill**

When managing server secrets, SSH access to that server is itself a credential. With 1Password SSH agent:
- No private keys on disk
- SSH access audited through 1Password
- Fits the same approval-gate model as secret access via MCP

**4. Storing server credentials**

SSH host keys and server passwords can be stored in 1Password Environments or classic vault items alongside the secrets the skill manages. See `references/one-password-environments.md` for variable storage patterns.

---

### SKILL.md Changes

**Change 1 — `When To Use` section**

Add one trigger:

> - Generate new credentials during infrastructure or service setup.

**Change 2 — `MCP Detection` section**

Add a fourth detection step:

> 4. If MCP tools are not in this session, load `references/mcp-quickstart.md` for registration and bootstrap instructions before proceeding.

**Change 3 — `Access Path Priority` section**

Add a note after item 1:

> Note: In Codex sessions, MCP tools require a `config.toml` entry and session restart. See `references/mcp-quickstart.md`.

**Change 4 — New `Infrastructure Secret Creation Workflow` section**

```markdown
## Infrastructure Secret Creation Workflow

When generating new secrets during infrastructure setup (database passwords, API
tokens, auth secrets, service join tokens):

1. Create or identify the target Environment via MCP.
2. Generate each secret value using a local tool (`openssl rand`, etc.) and pipe
   directly to MCP `append_variables` with `concealed: true` — do not print the value.
3. Use `op run --environment ENV_ID -- <command>` to inject values from 1Password
   into the target system (Docker service, cloud provider, etc.).
4. Never create secrets in the target system first and copy to 1Password second.
   If that already happened: generate a new value in 1Password, update the target
   system, discard the original value.

Load `references/mcp-quickstart.md` for the `append_variables` call pattern and
MCP auth flow.
```

---

## What This Does Not Cover

- Secret rotation (deferred, per original PRD)
- Vercel, Supabase, CI adapters (deferred)
- Cross-account MCP usage
- Windows/Linux binary paths for the MCP server
