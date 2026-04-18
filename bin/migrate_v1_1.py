#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# migrate_v1_1.py -- AI-Centric Full Data Migration (Hard Gate Spec v1.1)
#
# Pipeline per word:
#   1. Reset variants/from/description for clean re-enrichment
#   2. Wiktionary fetch -> parser -> dictionary score -> AI -> Hard Gate
#   3. Apply result (or reject)
#   4. Rebuild derived index + normalize index
#
# Usage:
#   python bin/migrate_v1_1.py --apply                 (full migration)
#   python bin/migrate_v1_1.py --apply --word bot      (single word)
#   python bin/migrate_v1_1.py --apply --resume        (skip already-enriched)
#   python bin/migrate_v1_1.py --dry-run               (preview only)
#   python bin/migrate_v1_1.py --apply --sleep 1.5     (throttle)

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

GLOSSARY_DIR = Path(__file__).parent.parent
WORDS_PATH   = GLOSSARY_DIR / "dictionary" / "words.json"
DERIVED_PATH = GLOSSARY_DIR / "dictionary" / "words__derived_terms.json"
INDEX_DIR    = GLOSSARY_DIR / "build" / "index"

sys.path.insert(0, str(Path(__file__).parent))

from normalize_build import norm_id, add_variant_safe, read_json, write_json, _build_normalize_index
from wikt_sense import (
    fetch_and_process,
    PipelineResult,
    STATUS_WORDS,
    _load_ai_env,
)


# ---------------------------------------------------------------------------
# Per-word migration
# ---------------------------------------------------------------------------

def migrate_word(
    word: Dict,
    ai_env: Optional[Dict],
    dry_run: bool = False,
    resume: bool = False,
) -> Dict[str, Any]:
    wid = word["id"]
    term = (word.get("lang") or {}).get("en") or wid

    # Resume: skip if already has description_en (indicates v1.1 enrichment done)
    if resume:
        desc_en = (word.get("description_i18n") or {}).get("en")
        if desc_en and len(desc_en) > 5:
            return {"word": wid, "status": "skipped", "reason": "already enriched"}

    # Fetch and process through unified pipeline
    try:
        _, result = fetch_and_process(term, word, ai_env=ai_env)
    except Exception as exc:
        return {"word": wid, "status": "error", "reason": str(exc)}

    if result is None:
        return {"word": wid, "status": "fetch_fail"}

    summary: Dict[str, Any] = {
        "word": wid,
        "status": result.status,
        "ai_used": result.ai_used,
        "confidence": result.confidence,
        "score": result.dict_score.score if result.dict_score else 0,
    }

    if result.status == "rejected":
        summary["rejection_reason"] = result.rejection_reason
        # Don't apply rejected data, but do log it
        return summary

    if dry_run:
        summary["new_pos"] = result.selected_pos
        summary["new_from"] = result.from_word
        summary["new_variants"] = result.variants
        summary["new_desc"] = result.description_en
        return summary

    # ── Apply to word dict ──
    # 1. Reset variants for clean application
    word["variants"] = []

    # 2. Apply selected_pos
    if result.selected_pos:
        word["canonical_pos"] = result.selected_pos

    # 3. Apply description_en
    if result.description_en:
        if "description_i18n" not in word:
            word["description_i18n"] = {}
        word["description_i18n"]["en"] = result.description_en
        summary["desc_set"] = True

    # 4. Apply from
    if result.from_word:
        word["from"] = norm_id(result.from_word)
        summary["from_set"] = result.from_word
    else:
        # Clear bad from values
        word.pop("from", None)

    # 5. Apply variants
    for v in result.variants:
        add_variant_safe(word, v["type"], v["value"])
    summary["n_variants"] = len(result.variants)

    # 6. Update timestamp
    word["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return summary


# ---------------------------------------------------------------------------
# Build derived index
# ---------------------------------------------------------------------------

def build_derived_index(words: List[Dict]) -> List[Dict]:
    seen: Set[str] = set()
    items: List[Dict] = []

    for w in words:
        wid = w["id"]
        for syn in (w.get("synonyms") or []):
            surf = norm_id(syn)
            if surf and surf not in seen:
                seen.add(surf)
                items.append({"surface": surf, "canonical_id": wid,
                              "type": "synonym", "source": "dictionary", "confidence": "medium"})
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
    parser = argparse.ArgumentParser(description="Glossary v1.1 AI-Centric Migration")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run",  action="store_true")
    mode.add_argument("--apply",    action="store_true")
    parser.add_argument("--resume", action="store_true",
                        help="Skip words that already have description_en")
    parser.add_argument("--word",   metavar="ID",
                        help="Process single word only")
    parser.add_argument("--word-list", metavar="ID,...",
                        help="Comma-separated list of word IDs to process")
    parser.add_argument("--only-incomplete", action="store_true",
                        help="Process only words with plural-only variants or no variants")
    parser.add_argument("--batch",  type=int, default=50)
    parser.add_argument("--sleep",  type=float, default=1.0,
                        help="Sleep seconds between API requests")
    args = parser.parse_args()

    # Load AI env
    ai_env = _load_ai_env()
    if ai_env is None:
        print("[ERROR] .env not found -- AI env required for v1.1 migration")
        return 1

    api_type = ai_env.get("API_KEY_TYPE", "unknown")
    api_model = ai_env.get("API_MODEL", "unknown")
    print(f"[INFO] AI: {api_type} / {api_model}")

    data  = read_json(WORDS_PATH)
    words: List[Dict] = data["words"]

    STATUS_KEEP = {"closed", "pending", "trading", "reporting",
                   "scoring", "setting", "trailing"}

    if args.word:
        target = [w for w in words if w["id"] == args.word]
        if not target:
            print(f"[ERROR] word not found: {args.word!r}")
            return 1
        process_words = target
    elif getattr(args, "word_list", None):
        ids = {s.strip() for s in args.word_list.split(",") if s.strip()}
        process_words = [w for w in words if w["id"] in ids]
    elif getattr(args, "only_incomplete", False):
        process_words = [
            w for w in words
            if w["id"] not in STATUS_KEEP
            and (
                not w.get("variants")
                or all(v.get("type") == "plural" for v in w.get("variants", []))
            )
        ]
        print(f"[INFO] only-incomplete mode: {len(process_words)} words selected")
    else:
        process_words = words

    stats = {
        "total":      len(process_words),
        "ok":         0,
        "rejected":   0,
        "fetch_fail": 0,
        "error":      0,
        "skipped":    0,
        "desc_set":   0,
        "from_set":   0,
        "ai_used":    0,
    }

    rejected_log: List[Dict] = []

    print(f"\n{'='*65}")
    print(f"  Glossary v1.1 AI-Centric Migration  |  {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print(f"  words: {len(process_words)}  |  resume: {args.resume}  |  sleep: {args.sleep}s")
    print(f"{'='*65}\n")

    for i, word in enumerate(process_words, 1):
        wid = word["id"]
        prefix = f"[{i:>3}/{len(process_words)}] {wid:<25}"

        result = migrate_word(word, ai_env, dry_run=args.dry_run, resume=args.resume)
        status = result["status"]

        if status == "skipped":
            stats["skipped"] += 1
            print(f"{prefix} [SKIP] {result.get('reason','')}")
        elif status == "fetch_fail":
            stats["fetch_fail"] += 1
            print(f"{prefix} [WARN] fetch_fail")
        elif status == "error":
            stats["error"] += 1
            print(f"{prefix} [ERR]  {result.get('reason','')}")
        elif status == "rejected":
            stats["rejected"] += 1
            rejected_log.append(result)
            print(f"{prefix} [GATE] {result.get('rejection_reason','')}")
        elif status == "ok":
            stats["ok"] += 1
            if result.get("ai_used"):
                stats["ai_used"] += 1
            if result.get("desc_set"):
                stats["desc_set"] += 1
            if result.get("from_set"):
                stats["from_set"] += 1
            parts = []
            nv = result.get("n_variants", 0)
            if nv: parts.append(f"+{nv}v")
            if result.get("desc_set"): parts.append("desc")
            if result.get("from_set"): parts.append(f"from={result['from_set']}")
            ai_tag = "[AI]" if result.get("ai_used") else "[FB]"
            conf_tag = result.get("confidence", "?")
            print(f"{prefix} {ai_tag} {conf_tag:6} {' '.join(parts) or 'ok'}")
        else:
            # dry-run
            parts = []
            if result.get("new_desc"): parts.append("desc")
            if result.get("new_from"): parts.append(f"from={result['new_from']}")
            nv = len(result.get("new_variants", []))
            if nv: parts.append(f"+{nv}v")
            ai_tag = "[AI]" if result.get("ai_used") else "[FB]"
            print(f"{prefix} {ai_tag} {' '.join(parts) or 'ok'}")

        # Throttle between AI calls
        if not args.dry_run and status not in ("skipped", "fetch_fail") and args.sleep > 0:
            time.sleep(args.sleep)

    # Print results
    print(f"\n{'='*65}")
    print("  Stats:")
    for k, v in stats.items():
        print(f"    {k:<15}: {v}")
    print(f"{'='*65}")

    if rejected_log:
        print(f"\n  Rejected words ({len(rejected_log)}):")
        for r in rejected_log:
            print(f"    {r['word']:20} -> {r.get('rejection_reason','')}")

    if args.dry_run:
        print("\n[DRY-RUN] No files modified.")
        return 0

    # ── Save ──
    write_json(WORDS_PATH, data)
    print(f"\n[APPLY] words.json saved ({len(data['words'])} words)")

    # Rebuild derived index
    full_words = data["words"]
    derived_items = build_derived_index(full_words)
    derived_data = {
        "_note": "Auto-generated by migrate_v1_1.py. Do not edit manually.",
        "items": derived_items,
    }
    write_json(DERIVED_PATH, derived_data)
    print(f"[APPLY] {DERIVED_PATH.name} written ({len(derived_items)} items)")

    # Rebuild normalize index
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    _build_normalize_index(full_words, derived_items, apply=True)

    print("\n[DONE] Migration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
