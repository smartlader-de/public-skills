# MCP Quickstart

Operational detail for driving the 1Password MCP server. Load this file when
`list_environments` returns an error, MCP tools are absent, or you need the
correct auth flow.

## 1. Registration by Runtime

| Runtime | How MCP tools become available |
|---|---|
| Claude Code | Auto-available if the binary exists at `/Applications/1Password.app/Contents/MacOS/onepassword-mcp` and the MCP server is registered in Claude Code settings |
| Codex | Requires a `[mcp_servers.onepassword]` entry in `~/.codex/config.toml` pointing to the binary, then a session restart |

Codex config entry to add to `~/.codex/config.toml`:

```toml
[mcp_servers.onepassword]
command = "/Applications/1Password.app/Contents/MacOS/onepassword-mcp"
```

After adding the entry, restart the Codex session. MCP tools will then appear
in the tool list.

## 2. The Correct Auth Flow

Always call tools in this order:

```
1. Call authenticate (no arguments)
2. Extract account_id from the result content
3. Check project-local account binding before writes
4. Pass account_id in every subsequent call
```

The `account_id` returned by `authenticate` is **not** the same as the account
URL or user ID from `op account list`. Using the wrong value produces a
`Missing required scope` error (JSON-RPC code `-32600`).

Example call sequence:

```
authenticate()
  → { account_id: "XXXXXXXXXXXXXXXXXX" }

list_environments(accountId: "XXXXXXXXXXXXXXXXXX")
  → [{ id: "...", name: "ovh-bits/production" }, ...]
```

If `.1password/environments.json` exists and contains a different saved
`account_id` for the target project/context, stop before calling write tools.
Load `references/account-binding.md` for the exact guard and user-facing
message.

## 3. Tool Reference

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

Always use `concealed: true` for secret values in `append_variables`.

## 4. Desktop Approval UX

The MCP server is a 1Password Labs experiment.

Prerequisites:
- Enable in 1Password app: Settings → 1Password Labs → "Enable local MCP server"
- Feature flag: `ai-local-mcp-server`

Approval prompts appear:
- Once per new MCP client connection
- Once per Environment on first variable or file access

**If MCP calls hang without returning:** a desktop approval is waiting. Check
the 1Password app. Do not retry the call — wait for the user to approve.

**If authentication succeeds but Environment authorization fails:** check for
account mismatch before retrying. Repeated `authenticate` or `append_variables`
attempts can produce multiple desktop prompts while still targeting the wrong
account.

## 5. Empty Account Bootstrap

When `list_environments` returns an empty array, no Environments exist yet.
Create one before attempting any variable operations:

```
create_environment(accountId, environmentName)
  → returns environmentId
  → use environmentId in all subsequent variable calls
```

Naming convention: `<project>/<context>` — for example:
- `ovh-bits/production`
- `my-app/staging`
- `client-portal/development`

## 6. Python stdio Bridge

For Codex sessions where MCP tools are not yet available (before config
registration + session restart), drive the binary directly via stdio:

```python
import json, subprocess, select

p = subprocess.Popen(
    ['/Applications/1Password.app/Contents/MacOS/onepassword-mcp'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1
)

def call(method, params=None, id=1):
    msg = {'jsonrpc': '2.0', 'method': method, 'id': id}
    if params:
        msg['params'] = params
    p.stdin.write(json.dumps(msg) + '\n')
    p.stdin.flush()
    select.select([p.stdout.fileno()], [], [], 30)
    return json.loads(p.stdout.readline())

# Initialize the MCP connection
call('initialize', {
    'protocolVersion': '2024-11-05',
    'capabilities': {},
    'clientInfo': {'name': 'agent', 'version': '0.1'}
})
p.stdin.write(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) + '\n')
p.stdin.flush()

# Authenticate — use the returned account_id, not the op account list ID
auth = call('tools/call', {'name': 'authenticate', 'arguments': {}}, id=2)
account_id = json.loads(auth['result']['content'][0]['text'])['account_id']

# Now call other tools using account_id
envs = call('tools/call', {'name': 'list_environments', 'arguments': {'accountId': account_id}}, id=3)
```

This bridge is a **last resort**. Register the server in config and restart the
session when possible — native MCP tools are more reliable than subprocess I/O.
