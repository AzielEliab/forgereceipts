# ForgeReceipts

**A Local-First Evidence Integrity Platform for Pro Se Fathers in Family Court**

Whitepaper v1.0 — July 2026

Author: Aziel Eliab (Collin Horton)
Indianapolis, Indiana

Empowering Documentation · Child-Focused Advocacy · Procedural Equity

**DISCLAIMER:** This document describes a documentation and organization
tool. It is **not legal advice** and does not guarantee any court
outcome. Family law varies by jurisdiction. Consult a licensed attorney
in your state. Canonical author is Aziel Eliab (Collin Horton),
Indianapolis. Ignore any duplicate byline.

---

## 1. Executive summary

ForgeReceipts is a local-first, privacy-preserving evidence integrity
platform designed for pro se litigants—particularly fathers—in
high-conflict custody and family court proceedings. It transforms how
individuals build, organize, and present verifiable records by combining
cryptographic hash-chaining, a national legal-name stub, positive
parenting documentation, and beginner-accessible procedural templates.

This repository is **one software product**. Papers in the same series
(TemporalLock, VibeLock, CodeLock, VeilLock, GodLock, ShadowLock,
StaticClock, MirageGrid) are engines inside ForgeReceipts, not separate
apps and not separate downloads. There is one counted download page for
the product.

Core capabilities in v0.1.0:

- Hash-chained evidence logging (TemporalLock) with SHA-256 verification
- Required child-impact field on incident and journal receipts
- Forensics mode: hash a local file, store the hash on a receipt, re-verify later
- Time with Child journal with optional file hash and a private note
- Filing assistant: local caption/exhibit templates and conceptual e-filing checklists
- Optional local passphrase (PBKDF2-HMAC-SHA256); data dir `./.forgereceipts`
- Pattern Strength Score as a transparent local heuristic — not a win probability
- Tools panels that import the other engines when present
- Progressive-web-app-style UI on **127.0.0.1 only**, no CDN, no telemetry, no accounts

v0.2.0 adds giant Add file / Import receipt / Export receipt, list + detail views,
simple/advanced, `forgereceipts doctor`, `forgereceipts verify-receipt`,
plain errors on bad JSON, size limits, `FORGERECEIPTS_DEBUG=1`, and a sample demo.
A receipt is not legal proof.

All data remains on the user's device. The platform addresses the
documentation gap, knowledge gap, and credibility gap that
disadvantage self-represented parents, so fathers can produce
organized, child-focused records. Admissibility is a question for the
court and counsel — this software does not declare records admissible.

---

## 2. The problem

In contested custody cases, documentation quality often determines
what a court can even evaluate. Pro se litigants frequently lack tools
to produce organized, timestamped records. Common failures include
inconsistent logging, missing corroboration, inability to show that a
file is the same bytes later, poor exhibit labeling, and failure to
connect facts to the child's interests.

Fathers frequently struggle to present evidence of involvement or of
interference patterns. Digital files are vulnerable to alteration
*claims* when there is no hash. Children suffer when a parent cannot
document either violations or their own positive parenting.

ForgeReceipts does not claim to fix family court. It gives one person
a local, append-only place to keep receipts.

---

## 3. Principles

1. **Integrity Over Narrative.** Hash-chained, cryptographically
   verifiable receipts. A receipt is an observation with evidence and
   an observer-assigned confidence. It is not a verdict and not a
   truth score. Corrections are new receipts. There is no edit and no
   delete.

2. **Child-First Documentation.** Incident and journal entries require
   an explicit child-impact field. The software will not append
   without it.

3. **Local-First Privacy.** All data remains on the user's device. No
   cloud accounts, no telemetry, no third-party access. The UI binds
   127.0.0.1 only.

4. **Empowerment Through Education — without practicing law.** Plain
   English, templates, and named national sources (Troxel, Stanley,
   UCCJEA) as blurbs that tell the user to read the primary source.
   Not legal advice. Indiana is a default *selector label* because the
   author lives in Indianapolis; v0.1.0 does not encode Indiana
   statutes.

---

## 4. Architecture (one product)

```
forgereceipts ui   →  http://127.0.0.1:8787/
        │
        ├─ TemporalLock chain   (ledger JSONL)
        ├─ Forensics SHA-256
        ├─ Time with Child
        ├─ Filing templates (local export)
        ├─ Verify PASS/FAIL
        ├─ Optional PBKDF2 lock
        └─ Tools  →  VibeLock, CodeLock, ShadowLock,
                     VeilLock, GodLock, StaticClock, MirageGrid
```

Engines are copied under `engines/` and imported. Optional numeric /
crypto extra dependencies may be absent; Tools panels must degrade
without taking down the product.

**Not in v0.1.0 (on purpose):**

- No Odyssey or any court portal
- No email, no cloud sync, no accounts
- No real IP hiding even though MirageGrid is included (logical nodes only)
- No fabricated statutes or case holdings
- No fake court-win probabilities

---

## 5. Ledger (TemporalLock)

Each receipt hashes:

`timestamp, summary, evidence, confidence, prev_hash`

SHA-256 of canonical UTF-8 JSON (sorted keys, compact separators).
Genesis `prev_hash` is 64 zero hex characters. Extra ForgeReceipts
fields (`kind`, `child_impact`, `file_sha256`, `private_note`) ride on
the JSONL line. Child impact is also copied into `evidence` so it
enters the core hash. Private notes do not.

Verify walks hashes and consecutive links and returns PASS or FAIL.
Forks are valid and detectable; this product does not pick a winner.

---

## 6. Screens

1. **Home** — disclaimer, motto, Pattern Strength Score, national legal stub.
2. **Incident log** — append-only entries; child impact required.
3. **Forensics** — SHA-256 a local file; store hash; re-verify later.
4. **Time with Child** — journal; optional file hash; private note.
5. **Filing assistant** — caption placeholders, Petitioner's Exhibit 1 /
   Respondent's Exhibit A, conceptual e-filing checklist, export .txt/.html.
6. **Tools** — engine panels if importable.
7. **Verify** — paste or load JSONL, PASS/FAIL.
8. **Lock** — optional local passphrase (pbkdf2_hmac).

---

## 7. Pattern Strength Score

Transparent local heuristic. **Not a court-win probability.**

```
PSS = 100 * (0.40 * F + 0.35 * C + 0.25 * J)

F = min(1, unique stored file hashes / 10)
C = min(1, chain length / 20)
J = min(1, journal entries / 10)
```

Weights are engineering defaults. Documented in `forgereceipts/score.py`.

---

## 8. Legal reference stub

Shipped names: Troxel v. Granville, 530 U.S. 57 (2000); Stanley v.
Illinois, 405 U.S. 645 (1972); UCCJEA. Plain-English blurbs that
refuse to state a holding for the user's facts. Indiana is the default
selector label. Consult an attorney. Not legal advice.

---

## 9. Security and ethics

- Not legal advice, no outcome guarantees
- No contacting courts, Odyssey, email, or cloud
- No real anonymity network
- No CSAM, no targeting minors; Time with Child is the user's own
  parenting documentation
- Passphrase: `hashlib.pbkdf2_hmac` (SHA-256, 200_000 iterations).
  Verifier on disk; derived material in memory. Not full-disk encryption.

---

## 10. Conclusion

ForgeReceipts gives pro se fathers a cryptographically grounded,
child-focused, local documentation product. It does not file, serve,
or argue. It keeps receipts. Courts and counsel decide what those
receipts mean.

Child's Best Interests First. Integrity Over Narrative. Local Control. Always.

Signed

Aziel Eliab (Collin Horton)
Indianapolis, Indiana
July 2026

**Not Legal Advice**
