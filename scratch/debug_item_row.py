"""debug_item_row.py — 항목 행 HTML 영역 원문 출력"""
from pathlib import Path

content = (Path(__file__).parent.parent / "web" / "index.html").read_text(encoding="utf-8")

idx = content.find("발견: ${t.count}회")
if idx >= 0:
    region = content[idx - 10 : idx + 500]
    print(repr(region))
else:
    print("NOT FOUND")
