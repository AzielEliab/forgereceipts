"""One-click sample so a 6th grader can see a receipt without picking a file."""

from __future__ import annotations

from pathlib import Path

from forgereceipts.forensics import sha256_bytes

SAMPLE_NAME = "sample-demo.txt"
SAMPLE_TEXT = (
    "This is a sample file for ForgeReceipts.\n"
    "Not legal advice. A receipt is not legal proof.\n"
)
SAMPLE_BYTES = SAMPLE_TEXT.encode("utf-8")


def sample_sha256() -> str:
    return sha256_bytes(SAMPLE_BYTES)


def write_sample(data_dir: str | Path) -> Path:
    dest = Path(data_dir) / "demo" / SAMPLE_NAME
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(SAMPLE_BYTES)
    return dest
