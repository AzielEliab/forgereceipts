# Engines inside ForgeReceipts

ForgeReceipts is **one product**. The papers in this series are engines
copied under `engines/` (Python packages only, not `.venv`). The app
imports them. They are not separate downloads.

| Paper / engine | Module | Role in ForgeReceipts |
|----------------|--------|------------------------|
| TemporalLock | `engines/temporallock` | The ledger. Hash-chained append-only receipts for Incident log, Time with Child, and Forensics hashes. Verify screen walks the chain. |
| VibeLock | `engines/vibelock` | Tools panel: physical-consistency score of a **synthetic local wav** pair. Optional (`numpy`/`scipy`). |
| CodeLock | `engines/codelock` | Tools panel: gate-tethered cognitive render. Requires the exact acknowledgment phrase. Not encryption. |
| ShadowLock | `engines/shadowlock` | Tools panel: observe pasted JSONL, report, forget. Read-only. |
| VeilLock | `engines/veillock` | Tools panel: encrypt **synthetic** RGB frames in-process. Optional (`numpy`/`cryptography`). Not a live capture pipeline. |
| GodLock | `engines/godlock` | Tools panel: submit text to the in-memory ABAD engine (`persist=False`). Not an anonymity network. |
| StaticClock | `engines/staticclock` | Tools panel: advise a geo, then forget. Advisory only — not a scheduler. |
| MirageGrid | `engines/miragegrid` | Tools panel: assign one **logical** node from a static pool of 25. Not a proxy, VPN, Tor hop, or IP-hiding network. |

v0.1.0 ships these as vendored copies. Missing optional dependencies
make a panel report "unavailable"; they must not 500 the UI.
