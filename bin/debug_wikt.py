#!/usr/bin/env python3
"""Debug script to inspect Wiktionary HTML structure for 'activate'."""
import sys
import json
import re
import requests
from bs4 import BeautifulSoup, Tag

url = "https://en.wiktionary.org/wiki/activate"
headers = {"User-Agent": "Mozilla/5.0 (compatible; BOMTS-Glossary-Migrator/1.0)"}
resp = requests.get(url, timeout=15, headers=headers)
soup = BeautifulSoup(resp.text, "lxml")

print("=== Looking for English section ===")
eng = soup.find(id="English")
print(f"English anchor tag: {eng.name if eng else None}")

if eng:
    h2 = eng.find_parent(["h2", "h3"])
    print(f"H2 parent name: {h2.name if h2 else None}")
    if h2:
        print(f"H2 text: {h2.get_text(' ', strip=True)[:80]}")
        print()
        print("=== Siblings after English h2: ===")
        node = h2.find_next_sibling()
        count = 0
        while node and count < 30:
            text_preview = node.get_text(" ", strip=True)[:60]
            node_id = node.get("id") if hasattr(node, "get") else None
            print(f"  [{count}] tag={node.name!r} id={node_id!r} text={text_preview!r}")
            count += 1
            if node.name == "h2":
                break
            node = node.find_next_sibling()

print()
print("=== Looking for Etymology heading by text ===")
for tag in soup.find_all(["h3", "h4", "h5"]):
    txt = tag.get_text(" ", strip=True)
    if "Etymology" in txt or "Synonym" in txt or "Antonym" in txt or "Derived" in txt:
        print(f"  Found: tag={tag.name} id={tag.get('id')} text={txt[:80]!r}")

print()
print("=== Looking for #English > subheadings directly ===")
all_headings = soup.find_all(["h3", "h4"])
in_english = False
for h in all_headings:
    txt = h.get_text(" ", strip=True)
    if "English" in txt:
        in_english = True
    if in_english:
        print(f"  {h.name}: {txt[:80]!r}")
        if len([x for x in [h] if x]) > 10:
            break

print()
print("=== Full structure dump of first 'mw-heading' elements ===")
for mw in soup.find_all(class_=re.compile("mw-heading")):
    txt = mw.get_text(" ", strip=True)
    print(f"  cls={mw.get('class')} text={txt[:80]!r}")
