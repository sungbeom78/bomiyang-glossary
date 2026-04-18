#!/usr/bin/env python3
"""Find all multi-line strings in normalize_build.py."""
import tokenize, io
from pathlib import Path

src = Path("bin/normalize_build.py").read_text(encoding="utf-8")
gen = tokenize.generate_tokens(io.StringIO(src).readline)
try:
    for tok in gen:
        if tok.type == tokenize.STRING and tok.start[0] != tok.end[0]:
            s = tok.string
            print(f"MULTI-LINE STRING: line {tok.start[0]}-{tok.end[0]}: {s[:50]!r}")
    print("OK no error")
except tokenize.TokenError as e:
    print("TokenError:", e)
