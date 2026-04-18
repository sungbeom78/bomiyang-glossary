#!/usr/bin/env python3
"""Find first unclosed string before line 599 in normalize_build.py."""
import tokenize, io
from pathlib import Path

src = Path("bin/normalize_build.py").read_text(encoding="utf-8")

gen = tokenize.generate_tokens(io.StringIO(src).readline)
string_opens = []
try:
    for tok in gen:
        # STRING tokens are complete (open+close). If we get EOF in multi-line,
        # it means the last STRING token was opened but never closed.
        pass
    print("OK no error")
except tokenize.TokenError as e:
    print("TokenError:", e)

# Find the string that contains line 599
# Strategy: try from beginning, show all STRING tokens that span multiple lines
src2 = Path("bin/normalize_build.py").read_text(encoding="utf-8")
lines = src2.splitlines()

gen2 = tokenize.generate_tokens(io.StringIO(src2).readline)
prev_multi = None
try:
    for tok in gen2:
        if tok.type == tokenize.STRING:
            if tok.start[0] != tok.end[0]:
                # Multi-line string
                if tok.start[0] > 320 and tok.start[0] < 620:
                    print(f"MULTI-LINE STRING: line {tok.start[0]}-{tok.end[0]}: {tok.string[:60]!r}")
                    prev_multi = tok
except tokenize.TokenError as e:
    print("TokenError:", e)
    if prev_multi:
        print("Last multi-line STRING:")
        print(f"  start={prev_multi.start} end={prev_multi.end}")
        # Show source around the start
        sl = prev_multi.start[0]
        for i, l in enumerate(lines[sl-2:sl+5], sl-1):
            print(f"  {i}: {l!r}")
