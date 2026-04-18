#!/usr/bin/env python3
"""Hexdump lines 334-342 of normalize_build.py."""
from pathlib import Path
src = Path("bin/normalize_build.py").read_text(encoding="utf-8")
lines = src.splitlines(keepends=True)
for i, line in enumerate(lines[333:342], start=334):
    hex_chars = " ".join(f"{ord(c):04x}" for c in line[:60])
    print(f"L{i:03d}: {line!r}")
    # Check for non-standard quote chars
    for j, c in enumerate(line):
        if ord(c) > 127 or ord(c) in (8220, 8221, 8216, 8217):
            print(f"  SPECIAL char at col {j}: U+{ord(c):04X} {c!r}")
