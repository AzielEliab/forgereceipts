# ForgeReceipts download tracker (Cloudflare Worker)

**This is the only download counter for the whole ForgeReceipts product.**

Counts GitHub-release downloads for ForgeReceipts across the canonical
repository, other branches, and forks. Forks are identified by GitHub
`owner/repo`.

Worker name: `forgereceipts-download-tracker`
Intended URL: `https://forgereceipts-download-tracker.vibelock.workers.dev/`

The homepage is async `indexHtml` with a live count. `GET /count`
returns JSON. The download button shows `${n} counted`.

**Do not deploy wrangler from this tree until KV is a real id.**
`wrangler.toml` ships `id = "REPLACE_ME"`. Account id is set.

No secrets belong in this directory.

## Bindings

| Binding     | Type | Purpose |
|-------------|------|---------|
| `DOWNLOADS` | KV   | Counters keyed `project|owner|repo|branch|fork` |

## Routes

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/` | Index with live count and download button (`${n} counted`) |
| GET | `/count` | `{ project, total }` |
| GET | `/download?asset=` | Increment KV, **200 gzip** of the hosted tarball |
| GET | `/stats` | JSON totals |
| POST | `/event` | A fork reports a download |

Default asset: `forgereceipts-0.2.0.tar.gz`
GitHub: `https://github.com/AzielEliab/forgereceipts`

## Use with Grok, ChatGPT, Venice

This Worker also hosts the product runtime API (CORS `*`). `/v1` routes do **not** increment `DOWNLOADS`.

| Method | Path | Notes |
|--------|------|-------|
| GET | `/v1/health` | Liveness |
| GET | `/openapi.json` | OpenAPI 3.1 |
| GET | `/ai` | ChatGPT Actions, Grok/xAI tools, Venice HTTP tools; MCP catalog |

See the product README section **Use with Grok, ChatGPT, Venice**.
OpenAPI: https://forgereceipts-download-tracker.vibelock.workers.dev/openapi.json
