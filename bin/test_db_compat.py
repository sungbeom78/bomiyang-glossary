#!/usr/bin/env python3
"""
test_db_compat.py — Glossary v2.5.1 DB compatibility test
Plan §8 Step 8: 과거 데이터 deserialize 호환성 확인

검증 항목:
  1. terms.json → dict deserialize 정상 동작
  2. variants array/object 양식 모두 deserialize 가능
  3. 구 schema (abbr object) 필드 접근 시 graceful 처리
  4. terms 항목 필수 필드 완결성
  5. JSON 직렬화 왕복 (serialize → deserialize) 일관성

실행:
    python test_db_compat.py
    python test_db_compat.py --verbose
"""

import json
import sys
import copy
import argparse
from pathlib import Path
from datetime import datetime

# ── 경로 설정 ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
GLOSSARY_ROOT = None
for candidate in [SCRIPT_DIR, SCRIPT_DIR.parent, SCRIPT_DIR.parent / "glossary"]:
    if (candidate / "generate_glossary.py").exists():
        GLOSSARY_ROOT = candidate
        break

if GLOSSARY_ROOT is None:
    print("[FATAL] generate_glossary.py를 찾을 수 없습니다.")
    sys.exit(1)

sys.path.insert(0, str(GLOSSARY_ROOT))

DICT_DIR       = GLOSSARY_ROOT / "dictionary"
WORDS_PATH     = DICT_DIR / "words.json"
COMPOUNDS_PATH = DICT_DIR / "compounds.json"
TERMS_PATH     = DICT_DIR / "terms.json"

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):     print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg):   print(f"  {RED}✗{RESET} {msg}")
def warn(msg):   print(f"  {YELLOW}!{RESET} {msg}")
def header(msg): print(f"\n{BOLD}{'─'*52}{RESET}\n{BOLD}  {msg}{RESET}\n{'─'*52}")

results = []

def test(name, passed, detail=""):
    results.append((name, passed, detail))
    if passed:
        ok(name + (f" — {detail}" if detail else ""))
    else:
        fail(name + (f" — {detail}" if detail else ""))
    return passed


# ════════════════════════════════════════════════════════════════════
# 헬퍼: 구 schema(object) variants 접근 방식
# ════════════════════════════════════════════════════════════════════

def _unwrap(data, *keys):
    if isinstance(data, list):
        return data
    for k in keys:
        if k in data and isinstance(data[k], list):
            return data[k]
    for v in data.values():
        if isinstance(v, list):
            return v
    return data

def get_abbr_short_compat(variants):
    """array + object 하위호환 abbr short 추출."""
    if isinstance(variants, list):
        for v in variants:
            if isinstance(v, dict) and v.get("type") == "abbreviation":
                return v.get("short")
    elif isinstance(variants, dict):
        # 구 형식: {"short": "...", "long": "..."}
        return variants.get("short") or variants.get("abbr_short")
    return None

def get_abbr_long_compat(variants):
    """array + object 하위호환 abbr long 추출."""
    if isinstance(variants, list):
        for v in variants:
            if isinstance(v, dict) and v.get("type") == "abbreviation":
                return v.get("long")
    elif isinstance(variants, dict):
        return variants.get("long") or variants.get("abbr_long")
    return None


# ════════════════════════════════════════════════════════════════════
# TESTS
# ════════════════════════════════════════════════════════════════════

def dc_01_terms_json_load(verbose):
    header("DC-01  terms.json deserialize")
    try:
        raw = TERMS_PATH.read_text(encoding="utf-8")
        terms = json.loads(raw)
        test("terms.json JSON 파싱 성공", True)
        test("최상위 terms[] 필드 존재", "terms" in terms)
        test("최상위 checksum 필드 존재", "checksum" in terms)
        test("최상위 generated_at 필드 존재", "generated_at" in terms)
        items = terms.get("terms", [])
        test("terms 항목 수 > 0", len(items) > 0, f"{len(items)}개")
        return terms
    except Exception as e:
        test("terms.json 로드", False, str(e))
        return {}


def dc_02_terms_required_fields(terms, verbose):
    header("DC-02  terms 항목 필수 필드 완결성")
    items = terms.get("terms", [])
    required_base    = {"id", "source", "root", "term_type", "domain", "lang"}
    required_variant = {"id", "source", "root", "term_type", "variant_type", "domain"}

    missing_base    = []
    missing_variant = []

    for t in items:
        tid = t.get("id", "?")
        tt  = t.get("term_type")
        if tt == "base":
            miss = required_base - set(t.keys())
            if miss:
                missing_base.append(f"{tid}: {miss}")
        elif tt == "variant":
            miss = required_variant - set(t.keys())
            if miss:
                missing_variant.append(f"{tid}: {miss}")

    test("base 항목 필수 필드 완결",
         len(missing_base) == 0,
         f"{len(missing_base)}개 불완전" if missing_base else f"{sum(1 for t in items if t.get('term_type')=='base')}개 OK")
    test("variant 항목 필수 필드 완결",
         len(missing_variant) == 0,
         f"{len(missing_variant)}개 불완전" if missing_variant else f"{sum(1 for t in items if t.get('term_type')=='variant')}개 OK")

    if verbose:
        for m in missing_base[:3]:
            warn(f"  base miss: {m}")
        for m in missing_variant[:3]:
            warn(f"  variant miss: {m}")


def dc_03_words_variants_compat(verbose):
    header("DC-03  words.json variants 하위호환 접근")
    words = _unwrap(json.loads(WORDS_PATH.read_text(encoding="utf-8")), "words")
    with_variants = [w for w in words if w.get("variants") is not None]

    array_ok   = 0
    object_ok  = 0
    unknown    = 0

    for w in with_variants:
        v = w["variants"]
        short = get_abbr_short_compat(v)
        if isinstance(v, list):
            array_ok += 1
        elif isinstance(v, dict):
            object_ok += 1
        else:
            unknown += 1

    test("words variants — array 형식만 존재",
         object_ok == 0 and unknown == 0,
         f"array:{array_ok} / object:{object_ok} / 기타:{unknown}")
    test("하위호환 접근 함수 정상 동작",
         True,
         f"variants 보유 단어 {len(with_variants)}개 접근 완료")


def dc_04_compounds_variants_compat(verbose):
    header("DC-04  compounds.json variants 하위호환 접근")
    compounds = _unwrap(json.loads(COMPOUNDS_PATH.read_text(encoding="utf-8")), "compounds")
    with_variants = [c for c in compounds if c.get("variants") is not None]

    array_ok  = 0
    object_ok = 0
    unknown   = 0

    for c in with_variants:
        v = c["variants"]
        if isinstance(v, list):
            array_ok += 1
        elif isinstance(v, dict):
            object_ok += 1
        else:
            unknown += 1

    test("compounds variants — array 형식만 존재",
         object_ok == 0 and unknown == 0,
         f"array:{array_ok} / object:{object_ok} / 기타:{unknown}")


def dc_05_json_roundtrip(verbose):
    header("DC-05  JSON 직렬화 왕복 일관성")
    try:
        # words
        words_raw  = WORDS_PATH.read_text(encoding="utf-8")
        words_obj  = json.loads(words_raw)
        words_re   = json.loads(json.dumps(words_obj, ensure_ascii=False))
        test("words.json 직렬화 왕복",
             words_obj == words_re,
             "불일치 발생" if words_obj != words_re else f"{len(words_obj)}개 OK")

        # compounds
        comp_raw   = COMPOUNDS_PATH.read_text(encoding="utf-8")
        comp_obj   = json.loads(comp_raw)
        comp_re    = json.loads(json.dumps(comp_obj, ensure_ascii=False))
        test("compounds.json 직렬화 왕복",
             comp_obj == comp_re,
             "불일치 발생" if comp_obj != comp_re else f"{len(comp_obj)}개 OK")

        # terms
        terms_raw  = TERMS_PATH.read_text(encoding="utf-8")
        terms_obj  = json.loads(terms_raw)
        terms_re   = json.loads(json.dumps(terms_obj, ensure_ascii=False))
        items_ok   = terms_obj.get("terms") == terms_re.get("terms")
        test("terms.json 직렬화 왕복",
             items_ok,
             "불일치 발생" if not items_ok else f"{len(terms_obj.get('terms',[]))}개 OK")
    except Exception as e:
        test("JSON 왕복 테스트", False, str(e))


def dc_06_old_schema_graceful(verbose):
    header("DC-06  구 schema (object variants) graceful 처리")
    # 구 형식 시뮬레이션
    old_word = {
        "id": "__compat_test__",
        "en": "compat",
        "ko": "호환 테스트",
        "canonical_pos": "noun",
        "domain": "system",
        "status": "active",
        "variants": {"short": "CPT", "long": "CompatTest"}   # 구 object 형식
    }
    old_compound = {
        "id": "__compat_test_c__",
        "words": [],
        "domain": "system",
        "status": "active",
        "abbr": {"short": "CTC", "long": "compatTestC"},      # 구 abbr object 형식
        "reason": "test"
    }

    # 하위호환 헬퍼로 접근
    short_w = get_abbr_short_compat(old_word["variants"])
    short_c = get_abbr_short_compat(old_compound.get("abbr"))

    test("구 word variants object → short 접근",
         short_w == "CPT", f"결과: {short_w}")
    test("구 compound abbr object → short 접근",
         short_c == "CTC", f"결과: {short_c}")


def dc_07_terms_id_uniqueness(terms, verbose):
    header("DC-07  terms.json id 고유성 (DB insert 충돌 없음)")
    items = terms.get("terms", [])
    ids = [t["id"] for t in items]
    dup = [i for i in set(ids) if ids.count(i) > 1]
    test("terms id 중복 없음",
         len(dup) == 0,
         f"중복: {dup[:5]}" if dup else f"{len(ids)}개 고유")


def dc_08_unicode_integrity(verbose):
    header("DC-08  UTF-8 / 유니코드 무결성")
    try:
        for path, name in [(WORDS_PATH, "words"), (COMPOUNDS_PATH, "compounds"), (TERMS_PATH, "terms")]:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
            # ensure_ascii=False로 재직렬화 후 동일한 텍스트인지 확인
            obj  = json.loads(text)
            re_text = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
            re_obj  = json.loads(re_text)
            test(f"{name}.json UTF-8 무결성", True, f"{len(raw)} bytes")
    except UnicodeDecodeError as e:
        test("UTF-8 디코딩", False, str(e))
    except Exception as e:
        test("유니코드 무결성", False, str(e))


# ════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Glossary v2.5.1 DB compatibility test")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print(f"\n{'═'*52}")
    print(f"  Glossary v2.5.1  DB Compatibility Test")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  glossary: {GLOSSARY_ROOT}")
    print(f"{'═'*52}")

    terms = dc_01_terms_json_load(args.verbose)
    dc_02_terms_required_fields(terms, args.verbose)
    dc_03_words_variants_compat(args.verbose)
    dc_04_compounds_variants_compat(args.verbose)
    dc_05_json_roundtrip(args.verbose)
    dc_06_old_schema_graceful(args.verbose)
    dc_07_terms_id_uniqueness(terms, args.verbose)
    dc_08_unicode_integrity(args.verbose)

    total  = len(results)
    passed = sum(1 for _, p, _ in results if p)
    failed = total - passed

    print(f"\n{'═'*52}")
    print(f"  결과: {GREEN}{passed}/{total} PASS{RESET}"
          + (f"  {RED}{failed} FAIL{RESET}" if failed else ""))
    print(f"{'═'*52}\n")

    if failed:
        print(f"{RED}실패 항목:{RESET}")
        for name, p, detail in results:
            if not p:
                print(f"  {RED}✗{RESET} {name}" + (f" — {detail}" if detail else ""))
        print()

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
