---
name: ForgeReceipts
description: Use when calling ForgeReceipts hosted /v1 or installing the local package. This Worker /v1/mesh/* PROXY to aziel-runtime via AZIEL_RUNTIME. Suite mesh default OFF. QNM-BUILD-1.0 live|locked|isolated. No Node Gate. No auto-heal. Not anonymity. Author Aziel Eliab.
---

# ForgeReceipts

Local-first evidence integrity packaging. Not legal advice. Does not contact courts, Odyssey, email, or any cloud service. No telemetry. Author: Aziel Eliab.

**THIS IS:** a local-first evidence integrity platform that packages receipts. Hosted /v1 never stores files.

**THIS IS NOT:** legal advice, a court filing, counsel, Odyssey/email/cloud contact, or a guarantee of any court outcome.

Author: **Aziel Eliab**. Forks are welcome and always allowed. Apache-2.0.

Always send `User-Agent: Mozilla/5.0`. Cloudflare Workers may 403 an empty agent.

## Call these URLs

- Worker OpenAPI: https://forgereceipts-download-tracker.vibelock.workers.dev/openapi.json
- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json
- MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`
- Live skill (this markdown): `GET https://forgereceipts-download-tracker.vibelock.workers.dev/v1/skill`

Ops (do **not** increment downloads or views):

| Method | Path | What |
|--------|------|------|
| GET | `/v1/health` | Liveness. Does not increment downloads. |
| GET | `/v1/skill` | This markdown. Does not increment downloads. |
| GET | `/v1/mesh` | PROXY suite mesh status. Default OFF. QNM live\|locked\|isolated. Never enables. |
| GET | `/v1/mesh/status` | PROXY alias of GET /v1/mesh. MESH-OK + enabled:false by default. |
| GET | `/v1/mesh/nodes` | PROXY Live Nodes roster (5-minute presence). |
| POST | `/v1/mesh/{enable,disable,join,heartbeat,leave,broadcast}` | PROXY. Bearer required to enable. No auto-heal. Anon-broadcast is not a publish path. |
| POST | `/v1/receipt` | Preview a local receipt hash. Hosted never stores files. |

Works with ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude (Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot / Bing, Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence surfaces, Amazon Q tooling, DuckAssist, You.com, Cohere, and other MCP/OpenAPI-capable assistants. Import the OpenAPI spec, add HTTP tools, or connect via MCP. Public identity: Aziel Eliab only. This Worker `/v1/mesh/*` PROXY to aziel-runtime via AZIEL_RUNTIME. Catalog MCP `mesh_*` + FragGate `slug=mesh`. Suite mesh default OFF. QNM-BUILD-1.0 live|locked|isolated. No Node Gate. No auto-heal. Not anonymity. Not legal advice.

## Example

```bash
curl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/health
curl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/skill
curl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/mesh
curl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/mesh/status
curl -s -A 'Mozilla/5.0' -X POST https://forgereceipts-download-tracker.vibelock.workers.dev/v1/receipt \
  -H 'content-type: application/json' \
  -d '{"sha256":"0"}'
```

## Local (after one-click install)

```bash
curl -fsSL https://forgereceipts-download-tracker.vibelock.workers.dev/install.sh | bash
forgereceipts ui
```

Then open http://127.0.0.1:8787 (loopback only).

DOI: https://doi.org/10.5281/zenodo.21436074  
Record: https://zenodo.org/records/21436074  

Counted download (gzip HTTP 200, no 302): https://forgereceipts-download-tracker.vibelock.workers.dev/download?asset=forgereceipts-0.3.0.tar.gz
GitHub: https://github.com/AzielEliab/forgereceipts
