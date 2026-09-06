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

Default asset: `forgereceipts-0.3.0.tar.gz`
GitHub: `https://github.com/AzielEliab/forgereceipts`

Hosted asset: `public/forgereceipts-0.3.0.tar.gz` (`DEFAULT_ASSET`).
`/download` serves that gzip as HTTP 200 via the `ASSETS` binding.
**Remaining deploy:** `wrangler deploy` this Worker, and publish GitHub
release `v0.3.0`.

## Use with AI assistants

This Worker also hosts the product runtime API (CORS `*`). `/v1` routes do **not** increment `DOWNLOADS`. Any MCP- or OpenAPI-capable assistant can call it: ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude (Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot / Bing, Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence surfaces, Amazon Q tooling, DuckAssist, You.com, Cohere, and other MCP/OpenAPI-capable assistants. Public identity: Aziel Eliab only.

| Method | Path | Notes |
|--------|------|-------|
| GET | `/v1/health` | Liveness |
| GET | `/openapi.json` | OpenAPI 3.1 |
| GET | `/ai` | How to wire any MCP/OpenAPI-capable assistant; MCP catalog |

See the product README section **Use with AI assistants**.
OpenAPI: https://forgereceipts-download-tracker.vibelock.workers.dev/openapi.json
