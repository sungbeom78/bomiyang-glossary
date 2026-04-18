#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# post_clean_v1_1.py -- Post-migration quality cleanup
# Fixes residual data issues after v1.1 AI migration
import json, sys
from pathlib import Path

GLOSSARY_DIR = Path(__file__).parent.parent
WORDS_PATH   = GLOSSARY_DIR / "dictionary" / "words.json"

sys.path.insert(0, str(Path(__file__).parent))
from wikt_sense import STATUS_WORDS, VARIANTS_KEEP_BY_POS, FROM_BANNED

def main():
    data = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
    words = data["words"]
    fixes = 0

    for w in words:
        wid = w["id"]
        pos = w.get("canonical_pos", "")
        variants = w.get("variants") or []

        # Fix 1: Remove "more X" / "most X" variants (adj)
        clean_variants = []
        for v in variants:
            val = v.get("value", "")
            if val.startswith("more ") or val.startswith("most "):
                print(f"  [FIX] {wid}: removed variant '{val}' (periphrastic)")
                fixes += 1
                continue
            clean_variants.append(v)

        # Fix 2: Remove wrong-type variants for POS
        allowed = VARIANTS_KEEP_BY_POS.get(pos)
        final_variants = []
        if allowed is not None:
            for v in clean_variants:
                if v.get("type") in allowed:
                    final_variants.append(v)
                else:
                    print(f"  [FIX] {wid}: removed variant type={v.get('type')} (not in {allowed})")
                    fixes += 1
        else:
            final_variants = clean_variants

        # Fix 3: Status words should have no variants
        if wid in STATUS_WORDS and final_variants:
            print(f"  [FIX] {wid}: cleared {len(final_variants)} variants (status word)")
            fixes += len(final_variants)
            final_variants = []

        # Fix 4: Validate from field
        from_val = w.get("from")
        if from_val:
            fl = from_val.lower()
            if fl in FROM_BANNED or len(fl) <= 3 or fl == wid or fl == wid + "s":
                print(f"  [FIX] {wid}: removed from='{from_val}' (banned/short/self)")
                w.pop("from", None)
                fixes += 1

        # Fix 5: noun variants - auth should have "auths" not "authentications"
        if pos == "noun" and final_variants:
            # Check if any plural is actually related to the word
            for i, v in enumerate(final_variants):
                if v.get("type") == "plural":
                    plural_val = v["value"].lower()
                    # If plural doesn't start with the word id, it's wrong
                    if not plural_val.startswith(wid[:3]):
                        print(f"  [FIX] {wid}: removed wrong plural '{v['value']}'")
                        final_variants[i] = None
                        fixes += 1
            final_variants = [v for v in final_variants if v is not None]

            # Re-add rule plural if needed
            if not any(v.get("type") == "plural" for v in final_variants):
                if wid.endswith(("s", "x", "z", "ch", "sh")):
                    pl = wid + "es"
                elif wid.endswith("y") and len(wid) > 1 and wid[-2] not in "aeiou":
                    pl = wid[:-1] + "ies"
                else:
                    pl = wid + "s"
                if pl != wid:
                    final_variants.append({"type": "plural", "value": pl})
                    print(f"  [FIX] {wid}: added rule plural '{pl}'")
                    fixes += 1

        w["variants"] = final_variants

    # Fix special cases manually
    for w in words:
        if w["id"] == "lower" and not w.get("description_i18n", {}).get("en"):
            w.setdefault("description_i18n", {})["en"] = "The lower boundary or limit value in a range comparison."
            w.pop("from", None)
            print(f"  [FIX] lower: manual description + from=null")
            fixes += 1
        if w["id"] == "us" and not w.get("description_i18n", {}).get("en"):
            w["canonical_pos"] = "noun"
            w.setdefault("description_i18n", {})["en"] = "Abbreviation for domestic/Korean market context."
            print(f"  [FIX] us: manual pos=noun + description")
            fixes += 1

    WORDS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n  Total fixes: {fixes}")
    print(f"  words.json saved.")

if __name__ == "__main__":
    main()
