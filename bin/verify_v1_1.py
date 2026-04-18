#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Final quality verification for v1.1 migration
import json, sys
from pathlib import Path

WORDS_PATH = Path(__file__).parent.parent / "dictionary" / "words.json"
data = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
words = data["words"]

# Key test cases from spec
TEST_CASES = {
    "bot":       {"expect_from": "robot",         "expect_no_from": False},
    "bridge":    {"expect_from": None,             "expect_no_from": True},
    "fill":      {"expect_from": None,             "expect_no_from": True},
    "backtest":  {"expect_from": None,             "expect_no_from": True},
    "exec":      {"expect_from": "execute",        "expect_no_from": False},
    "app":       {"expect_from": "application",   "expect_no_from": False},
    "closed":    {"expect_plural": False},
    # v1.2: cancelled/completed merged into base verb
    "cancel":    {"check_variant_type": "past",      "check_variant_val": "cancelled"},
    "complete":  {"check_variant_type": "past_participle", "check_variant_val": "completed"},
    "active":    {"check_variant_type": "verb_derived",    "check_variant_val": "activate"},
    "classify":  {"check_variant_type": "noun_form",       "check_variant_val": "classification"},
}

wmap = {w["id"]: w for w in words}
PASS = 0
FAIL = 0

print("=" * 65)
print("  v1.1 Key Test Cases")
print("=" * 65)

for wid, checks in TEST_CASES.items():
    w = wmap.get(wid)
    if not w:
        print(f"  [MISS] {wid}: not in words.json")
        FAIL += 1
        continue

    from_val = w.get("from")
    variants = w.get("variants") or []
    desc_en = (w.get("description_i18n") or {}).get("en", "")
    has_plural = any(v.get("type") == "plural" for v in variants)

    issues = []

    if "expect_from" in checks:
        if checks["expect_from"] is not None:
            if from_val != checks["expect_from"]:
                issues.append(f"from={from_val!r}, expected={checks['expect_from']!r}")
        else:
            if from_val is not None:
                issues.append(f"from={from_val!r}, expected=None")

    if checks.get("expect_no_from") and from_val:
        issues.append(f"from should be None, got {from_val!r}")

    if "expect_plural" in checks:
        if checks["expect_plural"] != has_plural:
            issues.append(f"plural={has_plural}, expected={checks['expect_plural']}")

    if "check_variant_type" in checks:
        vtype = checks["check_variant_type"]
        vval  = checks["check_variant_val"]
        found = any(v.get("type") == vtype and v.get("value", "").lower() == vval.lower()
                    for v in variants)
        if not found:
            issues.append(f"missing variant type={vtype!r} value={vval!r}")

    if not desc_en:
        issues.append("no desc_en")

    if issues:
        print(f"  [FAIL] {wid:15} {'; '.join(issues)}")
        FAIL += 1
    else:
        print(f"  [OK]   {wid:15} from={from_val!r:20} desc={desc_en[:50]}")
        PASS += 1

# Global stats
print(f"\n{'='*65}")
print("  Global Quality Stats")
print(f"{'='*65}")

no_desc = [w for w in words if not (w.get("description_i18n") or {}).get("en")]
bad_from = []
for w in words:
    fv = w.get("from")
    if fv:
        fl = fv.lower()
        if fl == w["id"] or fl == w["id"] + "s" or len(fl) <= 3:
            bad_from.append((w["id"], fv))

no_variants_noun = [w for w in words if w.get("canonical_pos") == "noun"
                    and not (w.get("variants") or [])
                    and w["id"] not in ("fx", "kr", "us", "db", "dsn", "eod", "pnl", "mt5", "KIS", "KOSDAQ", "m")]

print(f"  Total words      : {len(words)}")
print(f"  With desc_en     : {len(words) - len(no_desc)}")
print(f"  No desc_en       : {len(no_desc)} {[w['id'] for w in no_desc[:10]]}")
print(f"  Bad from (self/short): {len(bad_from)} {bad_from}")
print(f"  Nouns without variants: {len(no_variants_noun)} {[w['id'] for w in no_variants_noun[:10]]}")

print(f"\n  Test Cases: {PASS} passed, {FAIL} failed")
print(f"{'='*65}")

# Show 5 sample complete entries
print("\n  Sample Entries:")
for wid in ["bot", "trade", "execute", "closed", "config"]:
    w = wmap.get(wid)
    if w:
        vs = [v["value"] for v in (w.get("variants") or [])]
        desc = (w.get("description_i18n") or {}).get("en", "")[:60]
        fv = w.get("from")
        print(f"    {wid:15} pos={w.get('canonical_pos',''):5} variants={vs}  from={fv!r}  desc={desc}")
