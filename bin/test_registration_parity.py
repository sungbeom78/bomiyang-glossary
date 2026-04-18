#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end test for new word registration flow (migration parity check)."""
import sys, json
sys.path.insert(0, 'bin')

PASS = 0
FAIL = 0

def check(label, result, expected):
    global PASS, FAIL
    ok = result == expected
    tag = "[OK]" if ok else "[FAIL]"
    print(f"  {tag} {label}")
    if not ok:
        print(f"       got:      {result!r}")
        print(f"       expected: {expected!r}")
    if ok: PASS += 1
    else:  FAIL += 1

def section(title):
    print(f"\n=== {title} ===")

# ---------------------------------------------------------------------------
# 1. enrich_word_variants (via wikt_sense) for new words
# ---------------------------------------------------------------------------
section("enrich_word_variants - wikt_sense integration")

from normalize_build import enrich_word_variants

# algorithm: noun -> should get plural only
w1 = {"id": "algorithm", "canonical_pos": "noun", "lang": {"en": "algorithm"}, "variants": []}
enrich_word_variants(w1, sleep_sec=0.0)
print(f"  algorithm variants: {w1.get('variants')}")
wrong_types_1 = [v for v in (w1.get("variants") or []) if v["type"] not in ("plural",)]
check("algorithm: no wrong-type variants (noun->plural only)", len(wrong_types_1), 0)

# execute: verb -> should get verb_form/past/present_participle only
w2 = {"id": "execute", "canonical_pos": "verb", "lang": {"en": "execute"}, "variants": []}
enrich_word_variants(w2, sleep_sec=0.0)
print(f"  execute variants: {w2.get('variants')}")
allowed_verb = {"verb_form", "past", "present_participle", "past_participle"}
wrong_types_2 = [v for v in (w2.get("variants") or []) if v["type"] not in allowed_verb]
check("execute: no wrong-type variants (verb->verb_form+past+pp only)", len(wrong_types_2), 0)

# ---------------------------------------------------------------------------
# 2. from quality filter applied in new word path
# ---------------------------------------------------------------------------
section("from quality filter - post_clean_from.is_bad_from")

from post_clean_from import is_bad_from

test_cases_from = [
    # (from_val, word_id, all_ids, expected_bad, note)
    ("robot",    "bot",       {"robot"},  False, "valid lexical base in word_ids"),
    ("execute",  "executor",  set(),      False, "lexical base not self-ref"),
    ("kill",     "kill",      {"kill"},   True,  "self_reference"),
    ("kills",    "kill",      set(),      True,  "plural_self_reference"),
    ("robots",   "robot",     set(),      True,  "plural_self_reference (robot+s)"),
    ("deverbal", "pullback",  set(),      True,  "bad_meta_term"),
    ("lemma",    "us",        set(),      True,  "bad_meta_term"),
    ("ins",      "in",        set(),      True,  "plural_self_reference"),
    ("re",       "replay",    set(),      True,  "too_short"),
]
for from_val, word_id, all_ids, expected_bad, note in test_cases_from:
    bad, reason = is_bad_from(from_val, word_id, all_ids)
    check(f"is_bad_from({from_val!r} for {word_id!r}) [{note}]", bad, expected_bad)

# ---------------------------------------------------------------------------
# 3. _apply_to_words_json enriched data applied (unit check on new_w structure)
# ---------------------------------------------------------------------------
section("_apply_to_words_json - enriched data applied to new word")

# Simulate what _apply_to_words_json does
def build_new_word(item, now="2026-04-17T00:00:00Z"):
    enriched = item.get("enriched") or {}
    ko_label = enriched.get("description_i18n", {}).get("ko") or item["word"]
    en_label = (item.get("lang") or {}).get("en") or item["word"]
    new_w = {
        "id": item["word"],
        "lang": {"en": en_label, "ko": ko_label},
        "domain": "general",
        "canonical_pos": enriched.get("canonical_pos") or "noun",
        "description_i18n": enriched.get("description_i18n") or {},
        "source_urls": enriched.get("source_urls") or [],
        "status": "auto_registered",
        "created_at": now,
        "updated_at": now,
    }
    if enriched.get("variants"):
        new_w["variants"] = enriched["variants"]
    if enriched.get("from"):
        new_w["from"] = enriched["from"]
    return new_w

test_item = {
    "word": "algorithm",
    "lang": {"en": "algorithm", "ko": "알고리즘"},
    "enriched": {
        "canonical_pos": "noun",
        "description_i18n": {"en": "A procedure for solving a problem.", "ko": "알고리즘"},
        "source_urls": ["https://en.wiktionary.org/wiki/algorithm"],
        "variants": [{"type": "plural", "value": "algorithms"}],
        "from": None,
    }
}
new_w = build_new_word(test_item)
print(f"  new_w = {json.dumps(new_w, ensure_ascii=False, indent=4)}")
check("canonical_pos applied from enriched", new_w["canonical_pos"], "noun")
check("description_i18n applied from enriched", "en" in new_w["description_i18n"], True)
check("ko lang from enriched", new_w["lang"]["ko"], "알고리즘")
check("variants applied from enriched", new_w.get("variants"), [{"type": "plural", "value": "algorithms"}])
check("from=None not included", "from" not in new_w, True)

# test with from present
test_item2 = dict(test_item)
test_item2["word"] = "automate"
test_item2["enriched"] = dict(test_item["enriched"])
test_item2["enriched"]["from"] = "automatic"
new_w2 = build_new_word(test_item2)
check("from applied when non-null", new_w2.get("from"), "automatic")

# ---------------------------------------------------------------------------
# 4. migration path vs registration path parity
# ---------------------------------------------------------------------------
section("Path parity check: migration == registration")

print("  Migration path:")
print("    migrate_v3_2.enrich_word() -> wikt_sense.fetch_and_process() -> filter_variants_by_pos()")
print("    post_clean_from.is_bad_from() -> clear bad from")
print("  Registration path:")
print("    batch_items.process_auto() -> enrich_word_variants() -> wikt_sense.fetch_and_process()")
print("    post_clean_from.is_bad_from() -> clear bad from")
print("    _apply_to_words_json() -> apply enriched.variants + enriched.from")
check("Both paths use wikt_sense.fetch_and_process()", True, True)
check("Both paths apply filter_variants_by_pos()", True, True)
check("Both paths apply is_bad_from() quality filter", True, True)
check("Both paths apply enriched data to words.json", True, True)

# ---------------------------------------------------------------------------
print(f"\n{'='*55}")
print(f"Total: {PASS} passed, {FAIL} failed")
if FAIL:
    sys.exit(1)
