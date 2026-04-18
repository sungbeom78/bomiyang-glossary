#!/usr/bin/env python3
"""Convert normalize_build.py from CRLF to LF."""
from pathlib import Path
p = Path("bin/normalize_build.py")
content = p.read_bytes()
lf_content = content.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
p.write_bytes(lf_content)
crlf_count = content.count(b'\r\n')
print(f"Converted {crlf_count} CRLF to LF")
