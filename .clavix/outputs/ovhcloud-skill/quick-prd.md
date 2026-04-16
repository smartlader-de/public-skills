# OVHCloud Skill - Quick PRD

Build a Claude skill for full OVH Cloud infrastructure management via the OVH v2 API. Every invocation checks credentials first, then prompts "Read-only or Full access?" before doing anything. Read mode restricts all operations to GET requests. Full access unlocks mutations but wraps every destructive operation (DELETE, reboot, reinstall, terminate) in a triple opt-in: describe the action → confirm resource name → type CONFIRM. The skill is lazy-loaded: a lean SKILL.md dispatches to separate reference files per OVH product family (VPS, Dedicated, Public Cloud, Networking, Backup, Domains, Hosting, Licenses, Support), so only the relevant section loads per task. Auth setup is guided: if no valid credentials are found in `.env` (project folder) or `~/.ovh.conf`, walk the user through creating an OVH API application, generating keys, selecting their endpoint (EU/CA/US), and writing the config.

No external dependencies are required. The skill uses native HTTP (`curl` or Python `urllib`/`httpx`) with inline OVH v2 request signing, and optionally uses `python-ovh` if already installed. Credentials are read from `.env` (`OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY`, `OVH_ENDPOINT`) or `~/.ovh.conf`. The skill triggers on `/ovhcloud` or any mention of "OVH", "my VPS", or "my dedicated server" in an infrastructure context.

Out of scope for v1: OVH v1 API, Go SDK, billing/payment operations, multi-account management, and telephony products. The design principle is safety-first: read mode is always suggested first, full access is opt-in, and irreversible actions require three explicit confirmations.

---

*Generated with Clavix Planning Mode*
*Generated: 2026-04-16*
