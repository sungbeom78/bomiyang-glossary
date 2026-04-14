#!/usr/bin/env python3
"""
Migrate Glossary to v1.2 Schema
Run this to refactor dictionary/words.json and dictionary/compounds.json into v1.2 Sparse JSON format.
Support for --dry-run to display diff without writing to disk.
"""

import os
import json
import argparse
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DICT_DIR = ROOT / "dictionary"
WORDS_PATH = DICT_DIR / "words.json"
COMPOUNDS_PATH = DICT_DIR / "compounds.json"

POS_ENUM = {"noun", "verb", "adj", "adv", "prefix", "suffix", "proper", "mixed"}

def remove_empty(d):
    """Recursively remove empty lists, empty dicts, empty strings, or None values from a dictionary."""
    if not isinstance(d, (dict, list)):
        return d
    
    if isinstance(d, list):
        return [v for v in (remove_empty(v) for v in d) if v is not None and v != "" and v != [] and v != {}]
    
    return {k: v for k, v in ((k, remove_empty(v)) for k, v in d.items()) if v is not None and v != "" and v != [] and v != {}}

def migrate_word(word):
    """Migrate a single word entry to v1.2 schema."""
    new_w = {
        "id": word.get("id"),
        "domain": word.get("domain", "general"),
        "status": "active",
        "lang": {
            "en": word.get("en"),
            "ko": word.get("ko")
        },
        "variants": {},
        "description_i18n": {
            "ko": word.get("description", "")
        }
    }

    pos = word.get("pos")
    if pos in POS_ENUM:
        new_w["canonical_pos"] = pos
    else:
        new_w["canonical_pos"] = "mixed"

    if word.get("abbr"):
        new_w["variants"]["abbreviation"] = word.get("abbr")

    if word.get("plural") and word.get("plural") != "-":
        new_w["variants"]["plural"] = word.get("plural")
        
    if "not" in word:
        new_w["not"] = word["not"]
        
    if "reason" in word:
        new_w["reason"] = word["reason"]

    return remove_empty(new_w)

def migrate_compound(comp):
    """Migrate a single compound entry to v1.2 schema."""
    new_c = {
        "id": comp.get("id"),
        "words": comp.get("words", []),
        "domain": comp.get("domain", "general"),
        "status": "active",
        "lang": {
            "en": comp.get("en"),
            "ko": comp.get("ko")
        },
        "abbr": {},
        "variants": {},
        "description_i18n": {
            "ko": comp.get("description", "")
        }
    }

    if comp.get("abbr_long"):
        new_c["abbr"]["long"] = comp.get("abbr_long")
    if comp.get("abbr_short") and comp.get("abbr_short") != "-":
        new_c["abbr"]["short"] = comp.get("abbr_short")

    if comp.get("plural") and comp.get("plural") != "-":
        new_c["variants"]["plural"] = comp.get("plural")

    if "not" in comp:
        new_c["not"] = comp["not"]

    if "reason" in comp:
        new_c["reason"] = comp["reason"]

    return remove_empty(new_c)

def generate_diff_summary(original, migrated, type_name):
    print(f"\n--- {type_name} Diff Summary ---")
    if not original:
        print("No items found.")
        return
    
    # Just show the first item as a demonstration of structure change
    print("[Sample: First Item Original]")
    print(json.dumps(original[0], ensure_ascii=False, indent=2))
    print("\n[Sample: First Item Migrated]")
    print(json.dumps(migrated[0], ensure_ascii=False, indent=2))
    
    # Calculate some stats
    orig_keys_count = sum(len(x.keys()) for x in original)
    mig_keys_count = sum(len(x.keys()) for x in migrated)
    print(f"\nTotal items: {len(original)}")
    print(f"Total keys (approximate size reduction via sparse approach): {orig_keys_count} -> {mig_keys_count}")

def main():
    parser = argparse.ArgumentParser(description="Migrate dictionary files to v1.2 schema.")
    parser.add_argument("--dry-run", action="store_true", help="Print diffs instead of writing files.")
    args = parser.parse_args()

    # Read original files
    words_data = {"version": "1.0.0", "description": "", "words": []}
    if WORDS_PATH.exists():
        with open(WORDS_PATH, "r", encoding="utf-8") as f:
            words_data = json.load(f)

    compounds_data = {"version": "1.0.0", "description": "", "compounds": []}
    if COMPOUNDS_PATH.exists():
        with open(COMPOUNDS_PATH, "r", encoding="utf-8") as f:
            compounds_data = json.load(f)

    # Process
    old_words = words_data.get("words", [])
    old_compounds = compounds_data.get("compounds", [])
    
    migrated_words = [migrate_word(w) for w in old_words]
    migrated_compounds = [migrate_compound(c) for c in old_compounds]

    words_data["version"] = "1.2.0"
    words_data["words"] = migrated_words
    
    compounds_data["version"] = "1.2.0"
    compounds_data["compounds"] = migrated_compounds

    if args.dry_run:
        print("[DRY-RUN MODE] No files will be modified.")
        generate_diff_summary(old_words, migrated_words, "Words")
        generate_diff_summary(old_compounds, migrated_compounds, "Compounds")
    else:
        # Write back
        with open(WORDS_PATH, "w", encoding="utf-8") as f:
            json.dump(words_data, f, ensure_ascii=False, indent=2)
        with open(COMPOUNDS_PATH, "w", encoding="utf-8") as f:
            json.dump(compounds_data, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully migrated {len(migrated_words)} words and {len(migrated_compounds)} compounds to v1.2 schema.")

if __name__ == "__main__":
    main()
