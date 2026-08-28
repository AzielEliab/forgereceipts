# ForgeReceipts

Local-first evidence integrity platform for pro se fathers in family court.

**Author:** Aziel Eliab (Collin Horton), Indianapolis
**Date:** July 2026
**License:** [Apache-2.0](LICENSE)

> Child's Best Interests First. Integrity Over Narrative. Local Control. Always.

**This software is not legal advice.** It does not guarantee any court outcome. It does not contact courts, Odyssey, email, or any cloud service. No telemetry. No accounts.

See the spec: [docs/whitepaper.md](docs/whitepaper.md).
Engine map: [docs/engines.md](docs/engines.md).
How to contribute: [CONTRIBUTING.md](CONTRIBUTING.md).

**Forks are welcome and always allowed.**

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
forgereceipts ui
```

Open http://127.0.0.1:8787 (loopback only). No CDN, no telemetry. Not legal advice.

Counted download: [https://forgereceipts-download-tracker.vibelock.workers.dev/](https://forgereceipts-download-tracker.vibelock.workers.dev/)



---

## Download

**This is the only download counter for the whole ForgeReceipts product.**

# → [https://forgereceipts-download-tracker.vibelock.workers.dev/](https://forgereceipts-download-tracker.vibelock.workers.dev/) ←

The big button on that page is the download. The number next to it is
**ForgeReceipts only** — one Worker, one KV, one product. TemporalLock,
VibeLock, CodeLock, VeilLock, GodLock, ShadowLock, StaticClock, and
MirageGrid are engines inside this tree, not separate downloads.

Direct tarball (also counted): [forgereceipts-0.1.0.tar.gz](https://forgereceipts-download-tracker.vibelock.workers.dev/download?asset=forgereceipts-0.1.0.tar.gz)

- Live count JSON: [https://forgereceipts-download-tracker.vibelock.workers.dev/count](https://forgereceipts-download-tracker.vibelock.workers.dev/count)
- GitHub: [https://github.com/AzielEliab/forgereceipts](https://github.com/AzielEliab/forgereceipts)

---

## iPhone & Android

A local-first Flutter client lives in [`mobile/`](mobile/). Open that
folder in Android Studio or Xcode through Flutter (`flutter create .`
first if `android/` / `ios/` still hold the skeleton READMEs). On-device
receipt list, add a note, **Not legal advice** banner. No court filing.

Counted desktop download: [https://forgereceipts-download-tracker.vibelock.workers.dev/](https://forgereceipts-download-tracker.vibelock.workers.dev/)

Forks are welcome and always allowed.

---

## What it is

One unified local-first product. TemporalLock is the append-only ledger.
Incident log, Forensics (SHA-256), Time with Child journal, a local filing
assistant (templates and conceptual e-filing checklists — no court
connection), Verify, an optional PBKDF2 session lock, and Tools panels
for the other *Lock engines if they import.

Data lives in `./.forgereceipts` (gitignored). Never uploaded.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
forgereceipts ui          # http://127.0.0.1:8787  THE product
forgereceipts version
python -m pytest -q
```

Optional engine extras (numpy / scipy / cryptography) for VibeLock and VeilLock:

```bash
pip install -e ".[dev,engines]"
```

The UI binds **127.0.0.1 only**. Self-contained CSS. No CDN.

## Motto

Child's Best Interests First. Integrity Over Narrative. Local Control. Always.
