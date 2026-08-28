"""StaticClock: a chrono-linguistic release advisory system.

August 2026 whitepaper implementation by Aziel Eliab.

Software-only advisory. Least-distorting, most analytically stable
release window for information based on timezone, language, and
regional dialect. Does not optimize for reach, virality, or engagement.
No memory, identity, or historical data. One advisory for one moment,
then forget.

It does not help messages travel farther. It helps them arrive intact.

Forks are welcome and always allowed.
"""

from __future__ import annotations

from staticclock.engine import OUTPUT_FIELDS, Advisory, StaticClock
from staticclock.zones import list_timezones

__version__ = "0.1.0"
__author__ = "Aziel Eliab"
__all__ = [
    "Advisory",
    "OUTPUT_FIELDS",
    "StaticClock",
    "list_timezones",
    "__version__",
]
