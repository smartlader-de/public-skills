# Roadmap

## V1.1

### Project-Local Account Binding

Add a gitignored `.1password/environments.json` metadata file that records the
expected 1Password account and Environment for each project/context.

This prevents prompt loops and wrong-account writes when MCP authentication
succeeds against a different 1Password account than the one originally used for
the project.

Rules:

- Store metadata only: account IDs, Environment names, Environment IDs, and
  context labels.
- Never store variable values, hashes, lengths, vault item IDs, or classic vault
  references.
- Check the binding after MCP authentication and before any Environment write.
- On mismatch, stop before writes and ask the user to switch accounts or approve
  metadata-only rebinding.

## Post-MVP

### Provider Variable Mapping

Support an optional project-level mapping file, for example `secrets.map.json`, for provider-specific variable renames.

MVP should require exact variable-name matches between 1Password Environments and provider destinations. Mapping support can be added later after the MCP-first import, audit, and sync workflows are reliable.

Example future use case:

```json
{
  "production": {
    "DATABASE_URL": {
      "netlify": "POSTGRES_URL",
      "cloudflare": "DATABASE_URL"
    }
  }
}
```

Open design questions:

- What mapping-file schema should be used?
- Should mappings be environment-specific, provider-specific, or both?
- How should the skill verify mapped variables without exposing values?
- Should reverse sync from providers to 1Password be allowed when names differ?
