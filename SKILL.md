---
name: ForgeReceipts
description: Use when calling ForgeReceipts hosted /v1 or installing the local package. Author Aziel Eliab.
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
| POST | `/v1/receipt` | Preview a local receipt hash. Hosted never stores files. |

Grok: import OpenAPI as a custom tool. ChatGPT: GPT Actions. Venice: HTTP tools.

## Example

```bash
curl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/health
curl -s -A 'Mozilla/5.0' https://forgereceipts-download-tracker.vibelock.workers.dev/v1/skill
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
