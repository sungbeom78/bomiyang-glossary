#!/usr/bin/env python3
"""Find the exact unclosed triple-quote in normalize_build.py."""
import tokenize, io
from pathlib import Path

src = Path("bin/normalize_build.py").read_text(encoding="utf-8")
lines = src.splitlines()

# Find token that covers line 599-608
gen = tokenize.generate_tokens(io.StringIO(src).readline)
prev = None
try:
    for tok in gen:
        if tok.start[0] >= 595:
            print(f"tok type={tok.type} string={tok.string[:40]!r} start={tok.start} end={tok.end}")
        if tok.start[0] > 615:
            break
        prev = tok
except tokenize.TokenError as e:
    print("TokenError:", e)
    if prev:
        print("Last OK token:", prev)
