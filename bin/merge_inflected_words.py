#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# merge_inflected_words.py -- Merge -ed/-ing canonical IDs into base form
#
# Problem: words like "cancelled", "closed", "running" should NOT be standalone IDs.
# They should be variants of the base word (cancel, close, run).
#
# Strategy:
#   1. Find words with -ed/-ing/-tion/-ment suffixes that can be merged
#   2. Find (or create) base word entry
#   3. Transfer description_ko (preserve Korean) if base has none
#   4. Add as variant on base
#   5. Remove orphan entry
#
# Usage:
#   python bin/merge_inflected_words.py --dry-run    (preview)
#   python bin/merge_inflected_words.py --apply      (run)

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

GLOSSARY_DIR = Path(__file__).parent.parent
WORDS_PATH   = GLOSSARY_DIR / "dictionary" / "words.json"

# Words to merge: (inflected_id, base_id, variant_type)
# These are manually curated to avoid wrong merges
MERGE_MAP: List[Tuple[str, str, str]] = [
    # -ed status adjectives → merge as past_participle of verb
    ("cancelled",   "cancel",   "past"),
    ("completed",   "complete", "past_participle"),
    ("confirmed",   "confirm",  "past_participle"),
    ("connected",   "connect",  "past_participle"),
    ("disabled",    "disable",  "past_participle"),
    ("enabled",     "enable",   "past_participle"),
    ("extended",    "extend",   "past_participle"),
    ("failed",      "fail",     "past_participle"),
    ("filled",      "fill",     "past_participle"),
    ("halted",      "halt",     "past_participle"),
    ("realized",    "realize",  "past_participle"),
    ("rejected",    "reject",   "past_participle"),
    ("relaxed",     "relax",    "past_participle"),
    ("stopped",     "stop",     "past_participle"),
    ("submitted",   "submit",   "past_participle"),
    ("used",        "use",      "past_participle"),
    # -ing words → merge as present_participle of verb
    ("clustering",  "cluster",  "present_participle"),
    ("pending",     None,       None),   # pending is a standalone status, skip
    ("ranking",     "rank",     "present_participle"),
    ("reporting",   "report",   "present_participle"),
    ("running",     "run",      "present_participle"),
    ("scoring",     "score",    "present_participle"),
    ("setting",     "set",      "present_participle"),
    ("starting",    "start",    "present_participle"),
    ("tracking",    "track",    "present_participle"),
    ("trading",     "trade",    "present_participle"),
    ("trailing",    "trail",    "present_participle"),
]

# Words that stay as standalone (not merged)
KEEP_STANDALONE: set = {
    "closed",    # "closed position" — domain noun phrase → keep
    "pending",   # "pending order"   — domain noun phrase → keep
    "unrealized", # compound adj with clear standalone use
    "swing",     # "swing trading"   — swing as base noun → keep
    "trading",   # "trading session" — core domain noun → keep
    "reporting",  # "reporting period" — domain noun → keep
    "scoring",    # "scoring system"  — domain noun → keep
    "setting",    # "setting value"   — domain noun → keep
    "trailing",   # "trailing stop"   — domain adjective → keep
}


def _rule_plural(word_id: str) -> str:
    if word_id.endswith(("s", "x", "z", "ch", "sh")):
        return word_id + "es"
    if word_id.endswith("y") and len(word_id) > 1 and word_id[-2] not in "aeiou":
        return word_id[:-1] + "ies"
    return word_id + "s"


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply",   action="store_true")
    args = parser.parse_args()

    data  = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
    words: List[Dict] = data["words"]
    wmap  = {w["id"]: w for w in words}
    now   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    to_remove: List[str] = []
    added_bases: List[Dict] = []
    ops: List[str] = []

    for inflected_id, base_id, vtype in MERGE_MAP:
        if inflected_id in KEEP_STANDALONE:
            ops.append(f"  [KEEP]  {inflected_id}")
            continue
        if base_id is None:
            ops.append(f"  [SKIP]  {inflected_id} (no base defined)")
            continue

        inflected = wmap.get(inflected_id)
        if not inflected:
            ops.append(f"  [MISS]  {inflected_id} (not in words.json)")
            continue

        base = wmap.get(base_id)
        if not base:
            # Create minimal base entry
            ko_from_inflected = (inflected.get("lang") or {}).get("ko", base_id)
            desc_ko_from_inflected = (inflected.get("description_i18n") or {}).get("ko", "")

            base_new: Dict = {
                "id":              base_id,
                "lang":            {"en": base_id, "ko": ko_from_inflected},
                "domain":          inflected.get("domain", "general"),
                "canonical_pos":   "verb",
                "description_i18n": {},
                "status":          "active",
                "created_at":      now,
                "updated_at":      now,
                "variants":        [{
                    "type":  vtype,
                    "value": inflected_id,
                }],
            }
            if desc_ko_from_inflected:
                base_new["description_i18n"]["ko"] = desc_ko_from_inflected
            added_bases.append(base_new)
            wmap[base_id] = base_new
            to_remove.append(inflected_id)
            ops.append(f"  [NEW]   {inflected_id} → base {base_id!r} (created) +{vtype}")
        else:
            # Merge into existing base
            variants = base.setdefault("variants", [])
            already = any(
                v.get("value", "").lower() == inflected_id.lower()
                for v in variants
            )
            if not already:
                variants.append({"type": vtype, "value": inflected_id})
                ops.append(f"  [MERGE] {inflected_id} → {base_id!r} +{vtype}")
            else:
                ops.append(f"  [DUP]   {inflected_id} → {base_id!r} already has variant")
            to_remove.append(inflected_id)

    # Also transfer description_en from inflected if base has none
    for base_new in added_bases:
        bid = base_new["id"]
        inflected_lk = next(
            (inf for inf, b, _ in MERGE_MAP if b == bid and inf not in KEEP_STANDALONE),
            None
        )
        if inflected_lk:
            src = wmap.get(inflected_lk) or {}
            if src.get("description_i18n", {}).get("en"):
                base_new["description_i18n"]["en"] = src["description_i18n"]["en"]

    print(f"\n{'='*60}")
    print(f"  Merge Inflected Words  |  {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print(f"{'='*60}")
    for op in ops:
        print(op)

    print(f"\n  Will remove {len(to_remove)} inflected IDs: {to_remove}")
    print(f"  Will create {len(added_bases)} new base entries: {[b['id'] for b in added_bases]}")

    if args.dry_run:
        print("\n[DRY-RUN] No changes written.")
        return 0

    # Apply: remove inflected words, add new bases
    new_words = [w for w in words if w["id"] not in to_remove]
    new_words.extend(added_bases)
    data["words"] = new_words

    WORDS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(f"\n[APPLY] words.json saved. {len(words)} → {len(new_words)} words.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
