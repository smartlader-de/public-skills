# Account Binding Reference

> Load this reference after MCP authentication and before Environment writes,
> imports, syncs, mounted files, or infrastructure secret creation.

## Purpose

Project-local account binding prevents repeated 1Password prompts and
wrong-account writes when a user has more than one 1Password account.

The binding stores metadata only:

- authenticated `account_id`
- Environment names and IDs
- context labels such as `production` or `staging`
- timestamps or agent names, when useful for troubleshooting

Never store variable values, value hashes, value lengths, vault item IDs, or
classic vault references in this file.

## Location

Use this project-local path:

```text
.1password/environments.json
```

The `.1password/` directory must be listed in `.gitignore` before creating the
file. If it is not ignored, add the ignore rule first and verify it with:

```bash
git check-ignore .1password/environments.json
```

## Suggested Shape

```json
{
  "version": 1,
  "bindings": [
    {
      "project": "ovh-bits",
      "context": "production",
      "environment_name": "ovh-bits/production",
      "account_id": "FSUTNS7VXBBPHBSOA6ZP7BYY7Y",
      "environment_id": "avnw46sj6xhztmmcwfzffycmrq",
      "updated_at": "2026-06-03T05:52:39Z"
    }
  ]
}
```

Use exact `environment_name` matches for MVP. Do not infer that similarly named
Environments are equivalent.

## Guard Workflow

After `authenticate` returns an `account_id`:

1. Read `.1password/environments.json` if it exists.
2. Find a binding for the target project/context or exact Environment name.
3. If no binding exists, continue with metadata-only discovery and write the
   binding only after the user confirms the selected account/environment.
4. If a binding exists and `account_id` matches, continue.
5. If a binding exists and `account_id` differs, stop before any writes.

When account mismatch is detected, report:

```text
1Password authentication succeeded, but this session is using account
CURRENT_ACCOUNT_ID. This project is bound to SAVED_ACCOUNT_ID for
ENVIRONMENT_NAME.

No secrets were read or written. Please switch 1Password to the saved account,
or confirm that I should rebind this project to CURRENT_ACCOUNT_ID after I list
metadata-only Environments in that account.
```

Do not retry `authenticate`, `append_variables`, `create_environment`, or
mounted-file operations in a loop after this mismatch. Repeated retries can
trigger repeated desktop approval prompts without changing the selected account.

Use the bundled helper when available:

```bash
node scripts/check-account-binding.js \
  --account-id CURRENT_ACCOUNT_ID \
  --environment-name ovh-bits/production
```

Exit code `2` means stop before writes and report the mismatch. Exit code `0`
means the binding matches or no binding exists yet.

## Creating Or Updating The Binding

Only create or update the binding after:

1. `authenticate` has returned an account ID.
2. `list_environments` has confirmed the target Environment name in that same
   account, or `create_environment` has created it with explicit user approval.
3. The user has confirmed the selected account/environment when ambiguity exists.

This is a metadata-only local write. It does not require raw secret access, but
it still changes local project state, so summarize the account ID and
Environment name being bound.

## Stale Binding Handling

If the saved `environment_id` is missing from `list_environments` but the
`account_id` matches:

1. Look for an exact `environment_name` match.
2. If found, update the saved `environment_id`.
3. If not found, ask whether to create the Environment or choose another one.

If both account and Environment differ, treat it as an account mismatch first.
