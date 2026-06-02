# Roadmap

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
