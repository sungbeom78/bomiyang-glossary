#!/usr/bin/env python3
"""Diagnose inflection extraction from Wiktionary (activate)."""
import sys, json, time
sys.path.insert(0, "bin")
from migrate_words_relations import fetch_wiktionary, _get_sections, _find_english_subsections, _extract_inflections

url, soup = fetch_wiktionary("activate")
sections = _get_sections(soup)
eng = _find_english_subsections(sections)
print("English subsections:", [s["title"] for s in eng])

for s in eng:
    if s["title"].lower() in ("verb", "noun", "adjective"):
        print(f"\n=== {s['title']} section:")
        for n in s["nodes"][:5]:
            if hasattr(n, "name"):
                txt = str(n)[:300]
                print(f"  tag={n.name}: {txt}")

# Also try Free Dictionary API for inflections
print("\n\n=== Free Dictionary API test (activate) ===")
import urllib.request
with urllib.request.urlopen("https://api.dictionaryapi.dev/api/v2/entries/en/activate", timeout=10) as r:
    d = json.loads(r.read())
entry = d[0] if d else {}
print("phonetic:", entry.get("phonetic"))
for m in entry.get("meanings", []):
    print(f"  pos={m['partOfSpeech']}, defs={len(m.get('definitions',[]))}")
    # inflections?
    print(f"  inflections from meaning:", m.get("inflections", []))
    print(f"  synonyms:", m.get("synonyms", [])[:5])
    print(f"  antonyms:", m.get("antonyms", [])[:5])
print("sourceUrls:", entry.get("sourceUrls"))
