#!/usr/bin/env python3
"""Find triple-quote balance issues in a Python file."""
import re
from pathlib import Path

src = Path("bin/normalize_build.py").read_text(encoding="utf-8")
lines = src.splitlines()

# Count triple-quote markers
in_triple = False
triple_char = None
start_line = 0
for i, line in enumerate(lines, 1):
    # Simple approach: count """ and ''' occurrences
    j = 0
    while j < len(line):
        if not in_triple:
            if line[j:j+3] in ('"""', "'''"):
                in_triple = True
                triple_char = line[j:j+3]
                start_line = i
                j += 3
            else:
                j += 1
        else:
            if line[j:j+3] == triple_char:
                in_triple = False
                triple_char = None
                j += 3
            else:
                j += 1

if in_triple:
    print(f"UNCLOSED triple-quote {triple_char!r} opened at line {start_line}")
    print(f"Context:")
    for l in lines[start_line-1:start_line+5]:
        print(f"  {l}")
else:
    print("Triple-quotes OK")
