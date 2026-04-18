#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_v3_2.py -- Full data migration for Glossary v3.2

Steps per word:
  1. Clean variants by canonical_pos  (remove wrong-type variants)
  2. Clear from field if it's a stage/language value
  3. Fetch Wiktionary via wikt_sense.fetch_and_process()
  4. Apply result (update from if empty, add filtered variants)

Then rebuild:
  - dictionary/words__derived_terms.json
  - build/index/normalize_index.json

Usage:
  python bin/migrate_v3_2.py --dry-run          (show what would change, no write)
  python bin/migrate_v3_2.py --apply            (enrich variants from Wiktionary)
  python bin/migrate_v3_2.py --apply --clean-only  (only clean, no Wiktionary fetch)
  python bin/migrate_v3_2.py --apply --word active  (single word)
  python bin/migrate_v3_2.py --apply --resume   (skip words already enriched)
  python bin/migrate_v3_2.py --apply --sleep 0.5 --batch 20
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
GLOSSARY_DIR = Path(__file__).parent.parent
WORDS_PATH   = GLOSSARY_DIR / "dictionary" / "words.json"
DERIVED_PATH = GLOSSARY_DIR / "dictionary" / "words__derived_terms.json"
INDEX_DIR    = GLOSSARY_DIR / "build" / "index"

sys.path.insert(0, str(Path(__file__).parent))

from normalize_build import (
    norm_id,
    add_variant_safe,
    is_lexical_from,
    _rule_plural,
    _build_normalize_index,
    read_json,
    write_json,
)
from wikt_sense import (
    fetch_and_process,
    filter_variants_by_pos,
    VARIANTS_KEEP_BY_POS,
    _is_lexical_token,
)

# ---------------------------------------------------------------------------
# Step 1: Clean variants by canonical_pos
# ---------------------------------------------------------------------------

def clean_variants_by_pos(word: Dict) -> int:
    """Remove variants whose type doesn't match canonical_pos. Returns removed count."""
    pos   = word.get("canonical_pos", "")
    vlist = word.get("variants") or []
    allowed = VARIANTS_KEEP_BY_POS.get(pos)
    if allowed is None:
        return 0  # unknown pos -> keep all
    original = len(vlist)
    # Also remove composite comparative/superlative (spec v3.2)
    filtered = [
        v for v in vlist
        if v.get("type") in allowed
        and not (
            v.get("type") in ("comparative", "superlative")
            and (
                (v.get("value") or "").startswith("more ")
                or (v.get("value") or "").startswith("most ")
            )
        )
    ]
    word["variants"] = filtered
    return original - len(filtered)


# ---------------------------------------------------------------------------
# Step 2: Clean from field
# ---------------------------------------------------------------------------

LANG_STAGE_VALUES = {
    "latin", "greek", "french", "english", "german", "dutch",
    "norse", "arabic", "hebrew", "sanskrit", "persian", "italian",
    "spanish", "portuguese", "gothic", "celtic", "proto", "old",
    "middle", "classical", "medieval", "vulgar", "ancient",
    "late", "early", "modern", "post",
}


def clean_from_field(word: Dict, all_word_ids: Set[str]) -> bool:
    """
    Keep from only if is_lexical_from() is True.
    Otherwise clear it. Returns True if cleared.
    """
    from_val = word.get("from")
    if not from_val:
        return False
    if not is_lexical_from(from_val, all_word_ids):
        word.pop("from", None)
        return True
    return False


# ---------------------------------------------------------------------------
# Step 3+4: Wiktionary enrichment
# ---------------------------------------------------------------------------

def enrich_word(
    word: Dict,
    dry_run: bool = False,
    resume: bool = False,
) -> Dict[str, Any]:
    """
    Fetch Wiktionary and apply sense selection result.
    Returns summary dict with changes.
    """
    wid = word["id"]
    term = (word.get("lang") or {}).get("en") or wid

    # If resume: skip words that already have variants
    if resume and (word.get("variants") or []):
        return {"word": wid, "status": "skipped"}

    try:
        _, result = fetch_and_process(term, word)
    except Exception as exc:
        return {"word": wid, "status": "fetch_error", "error": str(exc)}

    if result is None:
        return {"word": wid, "status": "fetch_fail"}

    changes = {"word": wid, "status": "ok", "variants_added": 0, "from_set": False}

    if dry_run:
        changes["new_variants"] = result.variants
        changes["new_from"]     = result.from_word
        return changes

    # Apply from (only if word has no from yet, and result has lexical from)
    if result.from_word and not word.get("from"):
        if _is_lexical_token(result.from_word):
            word["from"] = norm_id(result.from_word)
            changes["from_set"] = True

    # Apply variants
    for v in result.variants:
        if add_variant_safe(word, v["type"], v["value"]):
            changes["variants_added"] += 1

    # Rule-based plural fallback for nouns with no Wiktionary plural
    pos = word.get("canonical_pos", "")
    if pos == "noun":
        has_plural = any(v.get("type") == "plural" for v in (word.get("variants") or []))
        if not has_plural:
            rule_pl = _rule_plural(wid)
            if rule_pl != wid:
                if add_variant_safe(word, "plural", rule_pl):
                    changes["variants_added"] += 1
                    changes["rule_plural"] = rule_pl

    return changes


# ---------------------------------------------------------------------------
# Build derived index
# ---------------------------------------------------------------------------

def build_derived_index(words: List[Dict]) -> List[Dict]:
    seen: Set[str] = set()
    items: List[Dict] = []

    for w in words:
        wid = w["id"]

        # from synonyms
        for syn in (w.get("synonyms") or []):
            surf = norm_id(syn)
            if surf and surf not in seen:
                seen.add(surf)
                items.append({"surface": surf, "canonical_id": wid,
                              "type": "synonym", "source": "dictionary", "confidence": "medium"})

        # from variants
        for v in (w.get("variants") or []):
            surf = norm_id(v.get("value") or "")
            if surf and surf not in seen and surf != wid:
                seen.add(surf)
                items.append({"surface": surf, "canonical_id": wid,
                              "type": "variant", "variant_type": v.get("type", ""),
                              "source": "wiktionary", "confidence": "high"})

    return items


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Glossary v3.2 Full Data Migration")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run",  action="store_true")
    mode.add_argument("--apply",    action="store_true")
    parser.add_argument("--clean-only", action="store_true",
                        help="Only clean variants+from, skip Wiktionary fetch")
    parser.add_argument("--resume", action="store_true",
                        help="Skip words that already have variants")
    parser.add_argument("--word",   metavar="ID",
                        help="Process single word only")
    parser.add_argument("--batch",  type=int, default=50,
                        help="Words per progress report batch")
    parser.add_argument("--sleep",  type=float, default=0.5,
                        help="Sleep seconds between Wiktionary requests")
    args = parser.parse_args()

    data  = read_json(WORDS_PATH)
    words: List[Dict] = data["words"]
    all_word_ids: Set[str] = {w["id"] for w in words}

    if args.word:
        target = [w for w in words if w["id"] == args.word]
        if not target:
            print(f"[ERROR] word not found: {args.word!r}")
            return 1
        words = target

    stats = {
        "total":            len(words),
        "variants_removed": 0,
        "from_cleared":     0,
        "variants_added":   0,
        "from_set":         0,
        "fetch_fail":       0,
        "skipped":          0,
    }

    print(f"\n{'='*60}")
    print(f"  Glossary v3.2 Migration  |  {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print(f"  words: {len(words)}  |  clean-only: {args.clean_only}")
    print(f"{'='*60}\n")

    for i, word in enumerate(words, 1):
        wid = word["id"]
        prefix = f"[{i:>3}/{len(words)}] {wid:<30}"

        # --- Step 1: Clean variants ---
        removed = clean_variants_by_pos(word) if not args.dry_run else 0
        stats["variants_removed"] += removed

        # --- Step 2: Clean from ---
        cleared = clean_from_field(word, all_word_ids) if not args.dry_run else False
        if cleared:
            stats["from_cleared"] += 1

        # --- Step 3+4: Enrich from Wiktionary ---
        if args.clean_only:
            msg_parts = []
            if removed:  msg_parts.append(f"-{removed}v")
            if cleared:  msg_parts.append("from cleared")
            print(f"{prefix} {' '.join(msg_parts) or 'ok'}")
        else:
            result = enrich_word(word, dry_run=args.dry_run, resume=args.resume)
            status = result["status"]

            if status == "skipped":
                stats["skipped"] += 1
                print(f"{prefix} [SKIP] already enriched")
            elif status in ("fetch_fail", "fetch_error"):
                stats["fetch_fail"] += 1
                err = result.get("error", "")
                print(f"{prefix} [WARN] {status} {err}")
            else:
                va = result.get("variants_added", 0)
                fs = result.get("from_set", False)
                stats["variants_added"] += va
                if fs:
                    stats["from_set"] += 1
                msg_parts = []
                if removed:        msg_parts.append(f"-{removed}clean")
                if cleared:        msg_parts.append("from-cleared")
                if va:             msg_parts.append(f"+{va}variants")
                if fs:             msg_parts.append(f"from={word.get('from')!r}")
                if args.dry_run:
                    new_v  = result.get("new_variants", [])
                    new_fr = result.get("new_from")
                    if new_v:  msg_parts.append(f"new_v={[v['value'] for v in new_v]}")
                    if new_fr: msg_parts.append(f"new_from={new_fr!r}")
                print(f"{prefix} {' '.join(msg_parts) or 'ok'}")

            if not args.dry_run and args.sleep > 0 and status not in ("skipped",):
                time.sleep(args.sleep)

    print(f"\n{'='*60}")
    print("  Stats:")
    for k, v in stats.items():
        print(f"    {k:<20}: {v}")
    print(f"{'='*60}\n")

    if args.dry_run:
        print("[DRY-RUN] No files modified.")
        return 0

    # --- Save words.json ---
    if not args.word:  # only write full file if not single-word mode
        all_data = read_json(WORDS_PATH)
        all_data["words"] = words if not args.word else all_data["words"]
        write_json(WORDS_PATH, data)
        print(f"[APPLY] words.json saved ({len(data['words'])} words)")

    # --- Rebuild derived index ---
    full_words: List[Dict] = read_json(WORDS_PATH)["words"]
    derived_items = build_derived_index(full_words)
    derived_data = {
        "_note": "Auto-generated by migrate_v3_2.py. Do not edit manually.",
        "items": derived_items,
    }
    write_json(DERIVED_PATH, derived_data)
    print(f"[APPLY] {DERIVED_PATH.name} written ({len(derived_items)} items)")

    # --- Rebuild normalize index ---
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    _build_normalize_index(full_words, derived_items, apply=True)

    print("\n[DONE] Migration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
