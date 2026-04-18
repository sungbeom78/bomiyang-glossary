#!/usr/bin/env python3
"""Fix self-conflict variants: remove variants where value == word.id."""
import json
from pathlib import Path

words_path = Path("dictionary/words.json")
data = json.loads(words_path.read_text(encoding="utf-8"))

fixed = 0
for w in data["words"]:
    wid = w["id"]
    en = (w.get("lang") or {}).get("en", "")
    variants = w.get("variants") or []
    # Remove variants where the value equals the word's own id or en form
    before_len = len(variants)
    cleaned = []
    for v in variants:
        val = (v.get("value") or "").strip().lower()
        # Skip: value == word id, or value == en form, or value is empty
        if val and val != wid.lower() and val != en.lower():
            cleaned.append(v)
        else:
            print(f"  REMOVE self-conflict: {wid} variant type={v.get('type')} value={v.get('value')!r}")
    w["variants"] = cleaned
    if len(cleaned) < before_len:
        fixed += 1

words_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"\nFixed {fixed} words.")
