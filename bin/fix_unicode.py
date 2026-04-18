#!/usr/bin/env python3
"""Fix all non-ASCII chars in normalize_build.py string literals and comments."""
from pathlib import Path

p = Path("bin/normalize_build.py")
t = p.read_text(encoding="utf-8")

replacements = [
    ("\u2192", "->"),    # right arrow
    ("\u2014", " - "),   # em dash
    ("\u2013", " - "),   # en dash
    ("\u2018", "'"),     # left single quote
    ("\u2019", "'"),     # right single quote
]
for old, new in replacements:
    count = t.count(old)
    if count:
        print(f"  replaced {count}x {old!r}")
        t = t.replace(old, new)

p.write_text(t, encoding="utf-8")
print("done")
