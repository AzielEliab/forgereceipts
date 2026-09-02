"""Hard size limits. Local-only. No telemetry.

12 MiB is large enough for a photo or a PDF exhibit and small enough
that a bad paste cannot fill the disk from the UI.
"""

from __future__ import annotations

MAX_BODY = 12 * 1024 * 1024
MAX_FILE_BYTES = 12 * 1024 * 1024
MAX_JSON_CHARS = 2 * 1024 * 1024
MAX_NOTE_CHARS = 16_384
MAX_BODY_MIB = MAX_BODY // (1024 * 1024)
