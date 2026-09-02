# Contributing to ForgeReceipts

**Forks are first-class.** This project is Apache-2.0; you do not need
permission to fork, patch, or redistribute. Pull requests are welcome
if you want a change upstream. Keep a fork forever if you do not.

**Forks are welcome and always allowed.**

This repository is **one software product**. Do not split the *Lock
engines into separate apps or separate download counters. The only
counted download page for ForgeReceipts is

https://forgereceipts-download-tracker.vibelock.workers.dev/

## How to run tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q
```

Python 3.10+. Core is stdlib. pytest is the dev extra. No network.

## Ground rules

1. **Not legal advice.** Do not add outcome guarantees, win
   probabilities, or language that practices law. The Pattern Strength
   Score is a documented local heuristic only.
2. **No court connectivity.** Do not talk to Odyssey, any e-filing
   portal, email, or the cloud. Filing assistant = local templates and
   conceptual checklists.
3. **No telemetry, no accounts.** Local-first. Data dir is
   `./.forgereceipts` and is gitignored.
4. **Append-only ledger.** TemporalLock is the chain. No edit, no
   delete. Corrections are new receipts. Child impact is required on
   incident and journal entries.
5. **MirageGrid is logical only.** Do not add real IP hiding, proxies,
   VPNs, or Tor. Nodes are identities, not network hops.
6. **No CSAM. No targeting minors.** Time with Child is parenting
   documentation the user already has.
7. **Keep engines vendored as copies** under `engines/`. Do not git
   submodule sibling repos. Do not give engines their own download
   counters inside this product.
8. New behavior needs a test that fails without the change.

## License of contributions

By submitting a change you agree it is licensed under Apache-2.0, the
same license as the rest of the tree. Keep the copyright lines honest.
Canonical author: Aziel Eliab, Indianapolis.
