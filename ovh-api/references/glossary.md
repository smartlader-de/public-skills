# Terminology Glossary — OVH Skill

Canonical terms used throughout this skill. Using these consistently prevents
confusion across reference files and in responses to users.

| Term | Use This | Not These | Meaning |
|------|----------|-----------|---------|
| **endpoint** | endpoint | region, datacenter, URL root, server location | The OVH API base URL: `eu.api.ovh.com`, `ca.api.ovh.com`, or `us.api.ovh.com` |
| **credentials** | credentials | keys, tokens, API keys, auth | The triple: Application Key + Application Secret + Consumer Key |
| **destructive** | destructive | dangerous, irreversible, permanent, unsafe | Any operation that cannot be undone after execution |
| **mode** | mode | level, tier, access type | Read-only vs Full access — chosen at skill invocation |
| **resource** | resource | object, item, entity, thing | Any OVH-managed asset: VPS, domain, volume, IP, etc. |
| **service name** | service name | ID, identifier, handle | The string OVH uses to identify a resource (e.g., `vps-abc123.vps.ovh.net`) |
| **consumer key** | consumer key | CK, token, auth token | Third part of OVH credentials — generated after authorizing app access |
| **application key** | application key | AK, API key, app ID | First part of OVH credentials — public identifier for the application |
| **application secret** | application secret | AS, API secret, app secret key | Second part of OVH credentials — private signing key |

## Usage notes

All reference files in `references/` should use the terms from the left column.
If you catch inconsistency in a reference file, prefer the canonical term.
