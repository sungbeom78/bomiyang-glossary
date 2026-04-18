#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
post_clean_from.py -- Post-migration from field quality filter.

Rules (applied after migrate_v3_2.py):
  1. from must be a real English word (alpha only, length >= 3)
  2. from must NOT equal the word's own id (self-reference)
  3. from must NOT be a known stage/meta word
  4. from should NOT be a plural of the word itself (from='kills' for word='kill')
  5. from should NOT be a proper noun or meta-linguistic term

Usage:
  python bin/post_clean_from.py --dry-run
  python bin/post_clean_from.py --apply
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

GLOSSARY_DIR  = Path(__file__).parent.parent
WORDS_PATH    = GLOSSARY_DIR / "dictionary" / "words.json"

sys.path.insert(0, str(Path(__file__).parent))
from normalize_build import norm_id, is_lexical_from, read_json, write_json

# Known bad from values: meta-linguistic, morphological terms, too generic
BAD_FROM_VALUES = {
    # morphology / meta
    "deverbal", "lemma", "suffix", "prefix", "compound", "derivation",
    "derivative", "base", "root", "stem", "form", "word", "term",
    "phrase", "clause", "sentence", "grammar", "syntax", "morpheme",
    # too short after norm
}

# Stage/language words already covered by is_lexical_from, but add extras
EXTRA_STAGE = {
    "late", "early", "modern", "post", "new", "neo", "proto",
}


def is_bad_from(from_val: str, word_id: str, all_ids: set) -> tuple:
    """Return (True, reason) if from_val should be cleared."""
    nid = norm_id(from_val)
    if not nid:
        return True, "empty_after_norm"
    if len(nid) <= 2:
        return True, "too_short"
    if nid == word_id:
        return True, "self_reference"
    if nid in BAD_FROM_VALUES:
        return True, f"bad_meta_term:{nid}"
    if nid in EXTRA_STAGE:
        return True, f"stage_word:{nid}"
    # Check if from is a simple inflection of the word itself
    # (e.g., word=kill, from=kills; word=size, from=sizes)
    if nid == word_id + "s":
        return True, "plural_self_reference"
    if nid == word_id + "d" or nid == word_id + "ed":
        return True, "past_self_reference"
    if not is_lexical_from(nid, all_ids):
        return True, "not_lexical"
    return False, ""


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply",   action="store_true")
    args = parser.parse_args()

    data  = read_json(WORDS_PATH)
    words = data["words"]
    all_ids = {w["id"] for w in words}

    cleared = 0
    for w in words:
        from_val = w.get("from")
        if not from_val:
            continue
        bad, reason = is_bad_from(from_val, w["id"], all_ids)
        if bad:
            print(f"  CLEAR from={from_val!r} on {w['id']!r}: {reason}")
            if not args.dry_run:
                w.pop("from", None)
            cleared += 1

    print(f"\n{'='*50}")
    print(f"  from fields to clear: {cleared}")
    if args.dry_run:
        print("  [DRY-RUN] No files modified.")
    else:
        write_json(WORDS_PATH, data)
        print(f"  [APPLY] words.json saved.")


if __name__ == "__main__":
    main()
