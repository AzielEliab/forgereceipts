"""Standalone Worker seals retry fields inside the receipt hash.

Author: Aziel Eliab. Not a forensic finding.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = (ROOT / "workers/download-tracker/src/runtime.js").read_text(encoding="utf-8")
SCRIPT = ROOT / "workers/download-tracker/scripts/verify-receipt-attempt.mjs"

CITE = ("request_id", "attempt_n", "parent_receipt_id", "correlation_id", "outcome")


def test_openapi_and_doctor_cite_attempt_fields() -> None:
    for name in CITE:
        assert name in RUNTIME
    assert 'export const AXES' in RUNTIME
    for name in ("request_id", "attempt_n", "parent_receipt_id", "correlation_id"):
        assert f'"{name}"' in RUNTIME
    assert '"/v1/doctor"' in RUNTIME
    assert "forensic_claim: false" in RUNTIME


def test_attempt_n_changes_receipt_hash() -> None:
    proc = subprocess.run(
        ["node", str(SCRIPT)],
        cwd=ROOT / "workers/download-tracker",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "attempt_n" in proc.stdout
