# SSH Agent Integration

Reference for connecting 1Password SSH agent to projects managed by this skill.

## 1. What It Is

1Password can act as the local SSH agent. Private keys are stored in 1Password
and SSH operations require 1Password approval. This extends the same trust model
(nothing on disk, approval gate) to server access.

## 2. Setup

Add to `~/.ssh/config`:

```
Host *
    IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
```

Enable in 1Password app: Settings → Developer → "Use the SSH agent".

After enabling, test with:

```bash
ssh-add -l
```

Keys stored in 1Password will appear in the list.

## 3. Why It Matters for This Skill

When managing server secrets, SSH access to that server is itself a credential.
With 1Password SSH agent:

- No private keys on disk
- SSH access audited through 1Password
- Fits the same approval-gate model as secret access via MCP

If you're managing secrets for a server (Dokploy, Docker Swarm, VPS), route SSH
to that server through 1Password SSH agent as well.

## 4. Storing Server Credentials

SSH host keys and server passwords can be stored in 1Password Environments or
classic vault items alongside the secrets this skill manages.

For consistency:
- Store infrastructure access credentials (SSH keys, server passwords, API tokens)
  in the same Environment as the application secrets for that server.
- Use `concealed: true` when writing via `append_variables`.
- See `references/one-password-environments.md` for variable storage patterns.
