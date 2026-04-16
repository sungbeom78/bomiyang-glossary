#!/usr/bin/env python3
"""
test_regression.py — Glossary v2.5.1 regression test suite
Plan §8 Step 7: 추가 시나리오 테스트

실행:
    python test_regression.py
    python test_regression.py --verbose
"""

import json
import sys
import copy
import hashlib
import argparse
import io
from pathlib import Path
from datetime import datetime

# ── Windows stdout UTF-8 강제 설정 (cp949 UnicodeEncodeError 방지) ──────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
elif sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── 경로 설정 ─────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
# glossary/ 루트 탐색
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
BANNED_PATH    = DICT_DIR / "banned.json"
TERMS_PATH     = DICT_DIR / "terms.json"

# ── 색상 출력 ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):  print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}!{RESET} {msg}")
def header(msg): print(f"\n{BOLD}{'─'*52}{RESET}\n{BOLD}  {msg}{RESET}\n{'─'*52}")


# ── 데이터 로드 ────────────────────────────────────────────────────────
def _unwrap(data, *keys):
    """JSON이 {"words": [...]} 형태면 내부 list 꺼내기, 이미 list면 그대로 반환."""
    if isinstance(data, list):
        return data
    for k in keys:
        if k in data and isinstance(data[k], list):
            return data[k]
    # dict인데 첫 번째 값이 list인 경우 (키 이름 불명)
    for v in data.values():
        if isinstance(v, list):
            return v
    return data


def load_data():
    words_raw     = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
    compounds_raw = json.loads(COMPOUNDS_PATH.read_text(encoding="utf-8"))
    banned_raw    = json.loads(BANNED_PATH.read_text(encoding="utf-8")) if BANNED_PATH.exists() else []
    terms         = json.loads(TERMS_PATH.read_text(encoding="utf-8")) if TERMS_PATH.exists() else {}

    words     = _unwrap(words_raw,     "words")
    compounds = _unwrap(compounds_raw, "compounds")
    banned    = _unwrap(banned_raw,    "banned")

    return words, compounds, banned, terms


# ═══════════════════════════════════════════════════════════════════════
# TEST CASES
# ═══════════════════════════════════════════════════════════════════════

results = []

def test(name, passed, detail=""):
    results.append((name, passed, detail))
    if passed:
        ok(name + (f" — {detail}" if detail else ""))
    else:
        fail(name + (f" — {detail}" if detail else ""))
    return passed


# ────────────────────────────────────────────────────────────────────
# TC-01: validate — 정상 데이터 FATAL 없음
# ────────────────────────────────────────────────────────────────────
def tc_01_validate_clean(words, compounds, banned, verbose):
    header("TC-01  validate — 정상 데이터 FATAL 없음")
    try:
        from generate_glossary import validate
        fatals, warns = validate(words, compounds, banned, silent=True, skip_checksum=True)
        test("FATAL 0건", len(fatals) == 0, f"{len(fatals)}건 발생" if fatals else "")
        if verbose and warns:
            for w in warns[:5]:
                warn(f"WARN: {w}")
    except Exception as e:
        test("validate 실행", False, str(e))


# ────────────────────────────────────────────────────────────────────
# TC-02: generate — FATAL 없이 terms.json 생성
# ────────────────────────────────────────────────────────────────────
def tc_02_generate_terms(verbose):
    header("TC-02  generate — terms.json 정상 생성")
    try:
        if not TERMS_PATH.exists():
            test("terms.json 존재", False, "파일 없음")
            return
        terms = json.loads(TERMS_PATH.read_text(encoding="utf-8"))
        items = terms.get("terms", [])
        test("terms.json 파싱 성공", True)
        test("terms 항목 > 0", len(items) > 0, f"{len(items)}개")
        test("checksum 필드 존재", "checksum" in terms)
        test("generated_at 필드 존재", "generated_at" in terms)
    except Exception as e:
        test("terms.json 로드", False, str(e))


# ────────────────────────────────────────────────────────────────────
# TC-03: checksum 무결성 검증
# ────────────────────────────────────────────────────────────────────
def tc_03_checksum(verbose):
    header("TC-03  checksum 무결성")
    try:
        from generate_glossary import verify_checksum
        terms = json.loads(TERMS_PATH.read_text(encoding="utf-8"))
        ok_flag, stored, computed = verify_checksum(terms)
        test("checksum 일치", ok_flag,
             f"stored={stored[:20]}..." if not ok_flag else "")
        if verbose and not ok_flag:
            warn(f"  stored  : {stored}")
            warn(f"  computed: {computed}")
    except ImportError:
        warn("verify_checksum 미정의 — skip")
    except Exception as e:
        test("checksum 검증", False, str(e))


# ────────────────────────────────────────────────────────────────────
# TC-04: variants array 형식 전수 검증
# ────────────────────────────────────────────────────────────────────
def tc_04_variants_array(words, compounds, verbose):
    header("TC-04  variants — array 형식 전수 검증")
    bad_words = []
    for w in words:
        if not isinstance(w, dict):
            bad_words.append(f"(비정상 항목: {type(w).__name__})")
            continue
        v = w.get("variants")
        if v is not None and not isinstance(v, list):
            bad_words.append(f"{w.get('id','?')} ({type(v).__name__})")

    bad_compounds = []
    for c in compounds:
        if not isinstance(c, dict):
            bad_compounds.append(f"(비정상 항목: {type(c).__name__})")
            continue
        v = c.get("variants")
        if v is not None and not isinstance(v, list):
            bad_compounds.append(f"{c.get('id','?')} ({type(v).__name__})")

    test("words.json variants 모두 array",
         len(bad_words) == 0,
         f"비정상: {bad_words[:3]}" if bad_words else f"{len(words)}개 OK")
    test("compounds.json variants 모두 array",
         len(bad_compounds) == 0,
         f"비정상: {bad_compounds[:3]}" if bad_compounds else f"{len(compounds)}개 OK")


# ────────────────────────────────────────────────────────────────────
# TC-05: terms.json projection — base/variant term_type 검증
# ────────────────────────────────────────────────────────────────────
def tc_05_projection_term_type(verbose):
    header("TC-05  projection — term_type 완결성")
    try:
        terms = json.loads(TERMS_PATH.read_text(encoding="utf-8"))
        items = terms.get("terms", [])
        valid_types = {"base", "variant"}
        invalid = [t["id"] for t in items if t.get("term_type") not in valid_types]
        test("모든 term_type 유효",
             len(invalid) == 0,
             f"미설정: {invalid[:5]}" if invalid else f"{len(items)}개 OK")

        # base 항목에 lang 필드 존재 여부
        no_lang = [t["id"] for t in items if t.get("term_type") == "base" and not t.get("lang")]
        test("base 항목 lang 필드 존재",
             len(no_lang) == 0,
             f"lang 없음: {no_lang[:5]}" if no_lang else "")
    except Exception as e:
        test("projection 검증", False, str(e))


# ────────────────────────────────────────────────────────────────────
# TC-06: duplicate id 주입 → validate FATAL 발생 확인
# ────────────────────────────────────────────────────────────────────
def tc_06_duplicate_id_injection(words, compounds, banned, verbose):
    header("TC-06  duplicate id 주입 → FATAL 감지")
    try:
        from generate_glossary import validate
        if not words:
            warn("words 비어있음 — skip")
            return
        # 첫 번째 단어 id 복제
        first = words[0] if isinstance(words[0], dict) else {}
        words_dup = words + [dict(first)]
        fatals, _ = validate(words_dup, compounds, banned, silent=True, skip_checksum=True)
        has_v001 = any("V-001" in f for f in fatals)
        test("V-001 (id 중복) FATAL 발생", has_v001,
             f"발생 안 함: {fatals[:2]}" if not has_v001 else "")
    except Exception as e:
        test("중복 id 주입 테스트", False, str(e))


# ────────────────────────────────────────────────────────────────────
# TC-07: dependency 깨진 compound → validate FATAL 발생 확인
# ────────────────────────────────────────────────────────────────────
def tc_07_broken_dependency(words, compounds, banned, verbose):
    header("TC-07  broken dependency → FATAL 감지")
    try:
        from generate_glossary import validate
        if not compounds:
            warn("compounds 비어있음 — skip")
            return
        # 존재하지 않는 단어 참조 주입
        src = compounds[0] if isinstance(compounds[0], dict) else {}
        bad_compound = copy.deepcopy(dict(src))
        bad_compound["id"] = "__test_broken__"
        bad_compound["words"] = ["__nonexistent_word_xyz__"]
        compounds_bad = compounds + [bad_compound]
        fatals, _ = validate(words, compounds_bad, banned, silent=True, skip_checksum=True)
        has_v104 = any("V-104" in f for f in fatals)
        test("V-104 (dependency 오류) FATAL 발생", has_v104,
             f"발생 안 함: {fatals[:2]}" if not has_v104 else "")
    except Exception as e:
        test("broken dependency 테스트", False, str(e))


# ────────────────────────────────────────────────────────────────────
# TC-08: check-id — 등록된 단어 조합 → 모두 OK
# ────────────────────────────────────────────────────────────────────
def tc_08_check_id_registered(words, verbose):
    header("TC-08  check-id — 등록 단어 인식")
    try:
        from generate_glossary import cmd_check_id
        if not words:
            warn("words 비어있음 — skip")
            return
        # 첫 번째 단어 id로 테스트
        wid = words[0]["id"] if isinstance(words[0], dict) else str(words[0])
        import io as _io
        from contextlib import redirect_stdout
        buf = _io.StringIO()
        with redirect_stdout(buf):
            cmd_check_id(wid)
        output = buf.getvalue()
        registered = "[OK]" in output or "OK" in output
        test(f"check-id '{wid}' → OK 인식", registered,
             output[:100] if not registered else "")
    except Exception as e:
        test("check-id 실행", False, str(e))


# ────────────────────────────────────────────────────────────────────
# TC-09: stats — 카운트 일치
# ────────────────────────────────────────────────────────────────────
def tc_09_stats_count(words, compounds, verbose):
    header("TC-09  stats — words/compounds 카운트 정합")
    try:
        from generate_glossary import cmd_stats
        import io as _io
        from contextlib import redirect_stdout
        buf = _io.StringIO()
        with redirect_stdout(buf):
            cmd_stats()
        output = buf.getvalue()
        test("stats 실행 성공", True)
        # 카운트 검증
        active_words = [w for w in words if isinstance(w, dict) and w.get("status", "active") == "active"]
        count_str = str(len(active_words))
        test(f"stats에 words 수({len(active_words)}) 포함",
             count_str in output,
             "출력에 없음" if count_str not in output else "")
        if verbose:
            print(output[:300])
    except Exception as e:
        test("stats 실행", False, str(e))


# ────────────────────────────────────────────────────────────────────
# TC-10: terms.json — source 필드 정합 (word/compound)
# ────────────────────────────────────────────────────────────────────
def tc_10_terms_source_field(words, compounds, verbose):
    header("TC-10  terms.json — source 필드 정합")
    try:
        terms_data = json.loads(TERMS_PATH.read_text(encoding="utf-8"))
        items = terms_data.get("terms", [])
        word_ids = {w["id"] for w in words}
        compound_ids = {c["id"] for c in compounds}

        bad_source = []
        for t in items:
            src = t.get("source")
            if src not in ("word", "compound"):
                bad_source.append(t["id"])

        test("모든 source 필드 유효",
             len(bad_source) == 0,
             f"비정상: {bad_source[:5]}" if bad_source else f"{len(items)}개 OK")
    except Exception as e:
        test("source 필드 검증", False, str(e))


# ════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Glossary v2.5.1 regression test")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print(f"\n{'═'*52}")
    print(f"  Glossary v2.5.1  Regression Test Suite")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  glossary: {GLOSSARY_ROOT}")
    print(f"{'═'*52}")

    words, compounds, banned, terms = load_data()
    print(f"\n  로드 완료 — words:{len(words)} / compounds:{len(compounds)} / banned:{len(banned)}")

    tc_01_validate_clean(words, compounds, banned, args.verbose)
    tc_02_generate_terms(args.verbose)
    tc_03_checksum(args.verbose)
    tc_04_variants_array(words, compounds, args.verbose)
    tc_05_projection_term_type(args.verbose)
    tc_06_duplicate_id_injection(words, compounds, banned, args.verbose)
    tc_07_broken_dependency(words, compounds, banned, args.verbose)
    tc_08_check_id_registered(words, args.verbose)
    tc_09_stats_count(words, compounds, args.verbose)
    tc_10_terms_source_field(words, compounds, args.verbose)

    # ── 결과 요약 ──
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
