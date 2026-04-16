# Product Requirements Document: OVHCloud Skill

## Problem & Goal

Managing OVH Cloud infrastructure requires navigating a sprawling API console with hundreds of endpoints across dozens of product families. The goal is a Claude skill that gives users full control over their OVH infrastructure through natural language — with credential setup guidance, lazy-loaded domain knowledge, a read/full mode gate on every invocation, and triple confirmation before any destructive operation.

## Requirements

### Must-Have Features

1. **Auth Setup Wizard**
   - On invocation, check for valid credentials in `.env` (project folder) or `~/.ovh.conf` (official OVH config format)
   - If neither exists: guide the user step-by-step to create an OVH API application, generate app key / app secret / consumer key, select endpoint (EU `eu.api.ovh.com`, CA `ca.api.ovh.com`, US `us.api.ovh.com`), and write credentials to `.env`
   - Ask which server/region the user is managing if not already known

2. **Credential Check + Mode Gate on Every Invocation**
   - Always check credentials first
   - After credentials confirmed: ask "Read-only mode or Full access?" before proceeding
   - Read-only mode: only GET requests allowed; any attempt to mutate is blocked with a warning
   - Full access mode: all operations available, but destructive ops require triple opt-in

3. **Triple Opt-In for Destructive Operations**
   - Destructive = any DELETE, reboot, reinstall, cancel, terminate, or irreversible state change
   - Step 1: Describe exactly what will be destroyed/changed and ask "Are you sure? (yes/no)"
   - Step 2: Ask user to type the resource name/ID to confirm
   - Step 3: Final "This cannot be undone. Type CONFIRM to proceed."
   - If any step fails or times out: abort with no action taken

4. **Lazy-Loading by OVH Product Domain**
   - Skill SKILL.md stays lean; reference files cover individual OVH product families
   - Load only the relevant reference file based on the user's task
   - Product families (v2 API): VPS, Dedicated Servers, Cloud (Public Cloud), Networking, Backup Services, Domains & DNS, Hosting, Licenses, Support
   - Each reference file contains: endpoint list, common operations, request/response examples, gotchas

5. **Native HTTP — No Required Dependencies**
   - Default: direct HTTP calls via `curl` or Python's `urllib`/`httpx` (no install needed)
   - Optional: detect if `python-ovh` is installed and use it if available (cleaner auth handling)
   - Include OVHv2 request signing logic inline in the skill so it works out of the box

### Technical Requirements

- **API Version**: OVH v2 only (`/v2` endpoints as documented at `https://eu.api.ovh.com/console/?section=%2FbackupServices&branch=v2`)
- **Credential Sources** (both supported):
  - `.env` in the project working directory (`OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY`, `OVH_ENDPOINT`)
  - `~/.ovh.conf` (INI format, official OVH client config)
- **Trigger phrases**: `/ovhcloud`, mentions of "OVH", "ovh cloud", "my VPS", "my dedicated server" in OVH context
- **HTTP client fallback order**: `python-ovh` (if installed) → Python `httpx`/`urllib` → `curl`

## Out of Scope (v1)

- OVH API v1 endpoints
- Go SDK integration
- Billing, invoicing, or payment operations
- Multi-account or multi-project management
- OVH telephony / VOIP products

## Additional Context

- Skill should feel like a safety-first tool — read mode is the default suggestion, full access requires explicit choice
- The lazy-loading architecture is critical: the full OVH API surface is enormous; loading everything would be wasteful and slow
- Reference files should be self-contained enough that Claude can operate on a product family without needing to load others
- The auth wizard should be friendly and step-by-step — many users won't know how to generate OVH API tokens

---

*Generated with Clavix Planning Mode*
*Generated: 2026-04-16*
