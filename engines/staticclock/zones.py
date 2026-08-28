"""Read-only IANA timezone reference.

Computed with zoneinfo from the local tz database. No network. Listing
zones does not mint a nonce and does not change an advisory.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from staticclock.anchors import TOP_30
from staticclock.index import record


def list_timezones(when: datetime | None = None) -> list[dict[str, str]]:
    """Return IANA zones for the Top-30 anchors with current local times."""
    rows: list[dict[str, str]] = []
    for name in TOP_30:
        iana = str(record(name)["iana"])
        tz = ZoneInfo(iana)
        now = datetime.now(tz) if when is None else when.astimezone(tz)
        rows.append(
            {
                "region": name,
                "iana": iana,
                "local_time": now.strftime("%H:%M"),
                "local_date": now.date().isoformat(),
                "utc_offset": now.strftime("%z"),
            }
        )
    return rows
