"""
Display name generation utilities (Teams-style unique name assignment).

Flow:
    1. format_display_name  — canonicalize to title-case for storage.
    2. normalize_name       — lowercase for DB comparison.
    3. generate_candidate   — pick next available suffix (e.g. "John Doe 2").
"""

import re


def format_display_name(name: str) -> str:
    """Title-case each word for consistent display.

    >>> format_display_name("john  DOE")
    'John Doe'
    """
    return " ".join(word.capitalize() for word in name.strip().split())


def normalize_name(name: str) -> str:
    """Collapse whitespace and lowercase — used for DB prefix matching.

    >>> normalize_name("John  Doe")
    'john doe'
    """
    return " ".join(name.lower().split())


def generate_candidate(base: str, existing: list[str]) -> str:
    """Return the next available suffixed name.

    Given base="John Doe" and existing=["John Doe", "John Doe 1"],
    returns "John Doe 2".

    First user gets no suffix ("John Doe"), subsequent users get " 1", " 2", etc.
    """
    pattern = re.compile(rf"^{re.escape(base)}(?: (\d+))?$", re.IGNORECASE)
    suffixes = [
        int(m.group(1)) if m.group(1) else 0 for name in existing if (m := pattern.match(name))
    ]
    next_suffix = max(suffixes, default=-1) + 1
    return base if next_suffix == 0 else f"{base} {next_suffix}"
