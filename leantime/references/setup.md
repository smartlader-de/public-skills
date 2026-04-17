# Leantime Setup: API Key Provisioning and Credential Configuration

This guide walks through obtaining a Leantime API key and configuring the
`.env` file the skill expects.

---

## Step 1: Log into Leantime as an admin

Open your Leantime instance in a browser and log in with an account that has
administrator privileges. Non-admin accounts may not have access to the API
settings page.

## Step 2: Navigate to Company Settings → API

In the top navigation, open the admin area. Look for:

**Settings → Company Settings → API**

The exact menu path may vary slightly between Leantime versions, but the
section is labelled "API" and lives under company-level settings (not personal
profile settings).

## Step 3: Generate an API key

On the API settings page, click **Generate API Key** (or **Create New Key**).
Leantime will display the key once. Copy it immediately — it will not be shown
again in full.

## Step 4: Save credentials

**Recommended — run the interactive setup wizard (writes to `~/.config/leantime/.env`):**

```bash
python scripts/setup_credentials.py
```

This stores credentials globally so every project can use the skill without
per-project setup. The file is created with permissions `600` (owner read/write only).

**Or — create the file manually:**

```bash
mkdir -p ~/.config/leantime
cat > ~/.config/leantime/.env <<EOF
LEANTIME_URL=https://your-leantime.example.com
LEANTIME_API_KEY=paste-your-key-here
EOF
chmod 600 ~/.config/leantime/.env
```

**Project-specific override:** If you need different credentials for a specific
project, create a `.env` in that project's root directory — it takes priority
over the global config.

**Notes:**
- `LEANTIME_URL` must be the base URL with no trailing slash
- Do not commit credential files to version control — add them to `.gitignore`

## Step 5: Run the connectivity probe

From your project directory, run:

```bash
python scripts/check_connection.py
```

### Exit-code contract

| Exit code | Meaning |
|-----------|---------|
| `0` | Connected — API key valid, instance reachable |
| `1` | Failed — a specific remediation message is printed to stderr |

A successful run prints:

```
Connected to https://your-leantime.example.com (API key valid, 5 users visible)
```

---

## Troubleshooting

### 401 or 403 response

Your API key is invalid or expired. Return to **Company Settings → API**,
revoke the old key, generate a new one, and update `LEANTIME_API_KEY` in
your `.env`.

### 404 response

The URL is reachable but the `/api/jsonrpc` path was not found. Verify:
- `LEANTIME_URL` points to the Leantime root (e.g. `https://pm.example.com`),
  not a sub-path
- Your Leantime version supports the JSON-RPC API (v3.x required)

### HTML response instead of JSON

The probe received an HTML page rather than a JSON response. This usually means:
- The URL points to a redirect, login page, or proxy that intercepts the request
- A reverse proxy (nginx/Apache) is not forwarding `/api/jsonrpc` to Leantime
- The instance requires VPN or IP allowlist access

### Connection refused or DNS error

The host cannot be reached at all:
- Confirm `LEANTIME_URL` uses the correct scheme (`https://` not `http://` if
  TLS is enforced)
- Check that the hostname resolves: `nslookup your-leantime.example.com`
- If self-hosted, confirm the Leantime service is running

### "Missing LEANTIME_URL / LEANTIME_API_KEY"

The `.env` file was not found in the current working directory, or one of the
required variables is absent. Repeat Steps 4–5 above.

---

## Verifying with curl

You can also test the connection manually:

```bash
source .env
curl -s -X POST "$LEANTIME_URL/api/jsonrpc" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LEANTIME_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"leantime.rpc.users.getAll","params":{}}' \
  | python3 -m json.tool
```

A successful response includes a `result` array of user objects.
