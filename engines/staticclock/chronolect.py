"""Chronolect: analytical clock windows.

Default analytical window is 08:30–10:30 local. v0.1 documents three
regional overrides for later cultural morning starts. All other anchors
use the default. The picked clock time sits inside the window. This is
not a scheduler and does not optimize for reach.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from staticclock.polarize import pick_index

DEFAULT_WINDOW: tuple[str, str] = ("08:30", "10:30")

# Documented overrides (v0.1: three). Rest of the Top-30 use DEFAULT_WINDOW.
OVERRIDES: dict[str, tuple[str, str]] = {
    "Spain": ("09:30", "11:30"),       # later Mediterranean morning
    "Argentina": ("09:30", "11:30"),   # Rioplatense later cultural start
    "Egypt": ("09:00", "11:00"),       # later administrative morning
}


def parse_hhmm(text: str) -> time:
    hour_s, minute_s = text.split(":")
    return time(int(hour_s), int(minute_s))


def window_for(region: str) -> tuple[str, str]:
    return OVERRIDES.get(region, DEFAULT_WINDOW)


def slots_in(window: tuple[str, str], step_minutes: int = 15) -> list[str]:
    start = parse_hhmm(window[0])
    end = parse_hhmm(window[1])
    start_m = start.hour * 60 + start.minute
    end_m = end.hour * 60 + end.minute
    out: list[str] = []
    m = start_m
    while m <= end_m:
        out.append(f"{m // 60:02d}:{m % 60:02d}")
        m += step_minutes
    return out


def pick_time(region: str, nonce: bytes) -> str:
    window = window_for(region)
    slots = slots_in(window)
    return slots[pick_index(len(slots), nonce, b"time")]


def local_date(iana: str, when: datetime | None = None) -> date:
    tz = ZoneInfo(iana)
    now = when if when is not None else datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)
    return now.date()


def in_window(hhmm: str, window: tuple[str, str]) -> bool:
    t = parse_hhmm(hhmm)
    start = parse_hhmm(window[0])
    end = parse_hhmm(window[1])
    return start <= t <= end
