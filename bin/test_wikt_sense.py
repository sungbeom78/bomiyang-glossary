#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_wikt_sense.py -- Spec v1.0 section 10 test cases.

Usage:
  python bin/test_wikt_sense.py
  python bin/test_wikt_sense.py --live  (fetches from Wiktionary)
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from wikt_sense import (
    extract_from,
    filter_variants_by_pos,
    score_candidate,
    SenseCandidate,
    Etymology,
    _is_lexical_token,
)

PASS = 0
FAIL = 0


def check(label: str, result, expected, note: str = ""):
    global PASS, FAIL
    ok = result == expected
    tag = "[OK]" if ok else "[FAIL]"
    suffix = f" ({note})" if note else ""
    print(f"  {tag} {label}: got {result!r}{suffix}")
    if ok:
        PASS += 1
    else:
        FAIL += 1
        print(f"       expected: {expected!r}")


def section(title: str):
    print(f"\n=== {title} ===")


# ---------------------------------------------------------------------------
# Unit tests (no network)
# ---------------------------------------------------------------------------

def test_is_lexical_token():
    section("is_lexical_token")
    check("latin -> False",     _is_lexical_token("latin"), False)
    check("greek -> False",     _is_lexical_token("greek"), False)
    check("robot -> True",      _is_lexical_token("robot"), True)
    check("adapt -> True",      _is_lexical_token("adapt"), True)
    check("ab -> False (short)",_is_lexical_token("ab"),    False)
    check("X -> False (short)", _is_lexical_token("X"),     False)
    check("bottom -> True",     _is_lexical_token("bottom"), True)


def test_extract_from():
    section("extract_from")

    # bot: two etymologies -- "From robot." and "Clipping of bottom."
    # Should return "robot" from the first allowed etymology
    etyms = [
        Etymology(text="From robot.", tokens=["robot"]),
        Etymology(text="Clipping of bottom.", tokens=["bottom"]),
    ]
    check("bot -> robot", extract_from(etyms), "robot")

    # Language-stage etymology should be rejected
    etyms2 = [
        Etymology(text="From Latin activus.", tokens=["latin", "activus"]),
    ]
    check("From Latin ... -> None", extract_from(etyms2), None)

    # Borrowed from should be rejected
    etyms3 = [
        Etymology(text="Borrowed from French balance.", tokens=["french", "balance"]),
    ]
    check("Borrowed from ... -> None", extract_from(etyms3), None)

    # Clean "From verb X" should work
    etyms4 = [
        Etymology(text="From the verb execute.", tokens=["execute"]),
    ]
    check("From the verb execute -> execute", extract_from(etyms4), "execute")

    # drama: "From Ancient Greek..." -> None
    etyms5 = [
        Etymology(text="From Ancient Greek drama.", tokens=["ancient", "greek", "drama"]),
    ]
    check("drama: From Ancient Greek ... -> None", extract_from(etyms5), None)

    # No from
    check("empty -> None", extract_from([]), None)


def test_filter_variants():
    section("filter_variants_by_pos")

    all_variants = [
        {"type": "plural",              "value": "bots"},
        {"type": "verb_form",           "value": "bots"},
        {"type": "present_participle",  "value": "botting"},
        {"type": "past",                "value": "botted"},
        {"type": "comparative",         "value": "more botted"},
    ]

    # noun: only plural
    noun_result = filter_variants_by_pos(all_variants, "noun")
    noun_types = [v["type"] for v in noun_result]
    check("noun keeps plural only", noun_types, ["plural"])

    # verb: verb_form, past, present_participle, past_participle
    verb_result = filter_variants_by_pos(all_variants, "verb")
    verb_types = [v["type"] for v in verb_result]
    check(
        "verb keeps verb_form+past+pp",
        sorted(verb_types),
        sorted(["verb_form", "present_participle", "past"]),
    )

    # adj: comparative/superlative
    adj_variants = [
        {"type": "comparative",  "value": "closer"},
        {"type": "superlative",  "value": "closest"},
        {"type": "plural",       "value": "closes"},
    ]
    adj_result = filter_variants_by_pos(adj_variants, "adj")
    adj_types = [v["type"] for v in adj_result]
    check("adj keeps comparative+superlative", sorted(adj_types), ["comparative", "superlative"])


def test_score_candidate():
    section("score_candidate")

    # bot + noun candidate -> should score high
    word_entry = {"id": "bot", "canonical_pos": "noun", "description": "automated program"}
    c_noun = SenseCandidate(pos="noun", definition="An automated program that performs tasks.")
    s = score_candidate(c_noun, word_entry)
    check("bot noun automated -> score >= 5", s >= 5, True, f"score={s}")

    # bot + verb candidate -> should score lower (pos mismatch)
    c_verb = SenseCandidate(pos="verb", definition="To fish for bot larvae.")
    s_v = score_candidate(c_verb, word_entry)
    check("bot verb mismatch -> lower than noun", s_v < s, True, f"verb={s_v} < noun={s}")

    # obsolete definition -> penalty
    c_obs = SenseCandidate(pos="noun", definition="(Obsolete) A type of parasitic larva.")
    s_obs = score_candidate(c_obs, word_entry)
    check("obsolete definition gets penalty", s_obs < s, True, f"obs={s_obs}")


# ---------------------------------------------------------------------------
# Live tests (fetch real Wiktionary)
# ---------------------------------------------------------------------------

def test_live(words):
    try:
        import requests
        from bs4 import BeautifulSoup
        from wikt_sense import process_word, parse_wiktionary_full
    except ImportError as e:
        print(f"  [SKIP] missing dependency: {e}")
        return

    section("Live Wiktionary Tests")
    for word_entry in words:
        wid = word_entry["id"]
        try:
            url, result = __import__("wikt_sense").fetch_and_process(wid, word_entry)
            if result is None:
                print(f"  [WARN] {wid}: fetch failed")
                continue
            print(f"  {wid}:")
            print(f"    pos      = {result.pos}")
            print(f"    from     = {result.from_word!r}")
            print(f"    variants = {result.variants}")
            print(f"    ai_used  = {result.ai_used}")
            print(f"    confidence = {result.confidence}")
        except Exception as e:
            print(f"  [ERR] {wid}: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Run live Wiktionary tests")
    args = parser.parse_args()

    print("Wiktionary Sense Selection Spec v1.0 -- Test Suite")
    print("=" * 55)

    test_is_lexical_token()
    test_extract_from()
    test_filter_variants()
    test_score_candidate()

    if args.live:
        live_cases = [
            {"id": "bot",      "canonical_pos": "noun",  "description": "automated program",  "domain": "infra"},
            {"id": "execute",  "canonical_pos": "verb",  "description": "run or carry out",    "domain": "general"},
            {"id": "drama",    "canonical_pos": "noun",  "description": "narrative expression", "domain": "general"},
            {"id": "watch",    "canonical_pos": "noun",  "description": "monitoring device",   "domain": "general"},
            {"id": "standard", "canonical_pos": "adj",   "description": "normal or default",   "domain": "general"},
        ]
        test_live(live_cases)

    print(f"\n{'='*55}")
    print(f"Unit tests: {PASS} passed, {FAIL} failed")
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    main()
