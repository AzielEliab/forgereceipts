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
| GET | `/download?asset=` | Increment KV, 302 to hosted asset or GitHub |
| GET | `/stats` | JSON totals |
| POST | `/event` | A fork reports a download |

Default asset: `forgereceipts-0.1.0.tar.gz`
GitHub: `https://github.com/AzielEliab/forgereceipts`
