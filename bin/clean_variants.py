#!/usr/bin/env python3
"""
clean_variants.py — words.json 에서 복합 comparative/superlative 제거.
- type=adjective AND value starts with 'more ' or 'most ' → 제거
"""
import json
from pathlib import Path

WORDS_PATH = Path(__file__).parent.parent / "dictionary" / "words.json"

data = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
words = data["words"]

removed = 0
for w in words:
    variants = w.get("variants") or []
    before = len(variants)
    cleaned = []
    for v in variants:
        val = (v.get("value") or "").strip()
        vtype = v.get("type", "")
        # Remove composite comparative/superlative (e.g. "more active", "most active")
        if vtype == "adjective" and (val.lower().startswith("more ") or val.lower().startswith("most ")):
            print(f"  REMOVE {w['id']}: {vtype}={val!r}")
        else:
            cleaned.append(v)
    removed += before - len(cleaned)
    w["variants"] = cleaned

WORDS_PATH.write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"\n✓ {removed}건 제거 완료 → words.json updated")
