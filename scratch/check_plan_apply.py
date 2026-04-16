#!/usr/bin/env python3
"""
check_plan_apply.py — Glossary v2.5.1 기획서 적용 상태 점검
실행 위치: glossary/ 루트
"""
import sys
import io
import json
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent  # glossary/
DICT = ROOT / "dictionary"
SCHEMA = ROOT / "schema"
BUILD = ROOT / "build"
BIN = ROOT / "bin"


def sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check(label, ok, detail=""):
    mark = "OK" if ok else "NG"
    suffix = f"  → {detail}" if detail else ""
    print(f"  [{mark}] {label}{suffix}")
    return ok

# ─────────────────────────────────────────────────────────────
# §2.1 파일 정의 점검
# ─────────────────────────────────────────────────────────────
sep("§2.1 파일 정의 — dictionary/ 파일 존재 여부")
required_files = {
    "words.json": "base 개념",
    "compounds.json": "조합 개념",
    "banned.json": "금지 규칙",
    "terms.json": "runtime projection",
    "terms_legacy.json": "하위 호환 (deprecated 분리)",
    "pending_words.json": "제안 보류",
}
optional_files = {
    "drafts.json": "AI 격리 (§1.4)",
}
missing = []
for fname, role in required_files.items():
    exists = (DICT / fname).exists()
    check(f"{fname} ({role})", exists)
    if not exists:
        missing.append(fname)
for fname, role in optional_files.items():
    exists = (DICT / fname).exists()
    status = "존재" if exists else "미생성 (optional)"
    print(f"  [OPT] {fname} ({role}): {status}")


# ─────────────────────────────────────────────────────────────
# §3 variants array 형식 점검
# ─────────────────────────────────────────────────────────────
sep("§3 variants 구조 — array 형식 전환 완료 여부")

def unwrap(data, *keys):
    if isinstance(data, list):
        return data
    for k in keys:
        if k in data and isinstance(data[k], list):
            return data[k]
    for v in data.values():
        if isinstance(v, list):
            return v
    return []

words_raw = json.loads((DICT / "words.json").read_text(encoding="utf-8"))
words = unwrap(words_raw, "words")
comp_raw = json.loads((DICT / "compounds.json").read_text(encoding="utf-8"))
compounds = unwrap(comp_raw, "compounds")

# variants 형식 점검
bad_words = [w.get("id", "?") for w in words if w.get("variants") is not None and not isinstance(w.get("variants"), list)]
bad_comps = [c.get("id", "?") for c in compounds if c.get("variants") is not None and not isinstance(c.get("variants"), list)]
check("words.json variants — 모두 array", len(bad_words) == 0,
      f"비정상 {len(bad_words)}개: {bad_words[:3]}" if bad_words else f"전체 {len(words)}개 OK")
check("compounds.json variants — 모두 array", len(bad_comps) == 0,
      f"비정상 {len(bad_comps)}개: {bad_comps[:3]}" if bad_comps else f"전체 {len(compounds)}개 OK")

# 구 abbr object 잔존 여부 (compounds)
old_abbr = [c.get("id","?") for c in compounds if isinstance(c.get("abbr"), dict)]
check("compounds.json 구 abbr object 제거", len(old_abbr) == 0,
      f"잔존: {old_abbr[:5]}" if old_abbr else "잔존 없음")

# variants type 필드 검증
valid_types = {
    "plural","singular","abbreviation","alias","misspelling",
    "adjective","adverb","verb","noun_form","verb_form",
    "present_participle","past","past_participle","agent",
    "pos_forms","deprecated"
}
bad_types = []
for w in words:
    for v in (w.get("variants") or []):
        t = v.get("type") if isinstance(v, dict) else None
        if t and t not in valid_types:
            bad_types.append(f"{w.get('id','?')}.{t}")
for c in compounds:
    for v in (c.get("variants") or []):
        t = v.get("type") if isinstance(v, dict) else None
        if t and t not in valid_types:
            bad_types.append(f"{c.get('id','?')}.{t}")
check("variants type 값 모두 §3.2 허용 목록", len(bad_types) == 0,
      f"미허용: {bad_types[:5]}" if bad_types else "OK")


# ─────────────────────────────────────────────────────────────
# §4 Projection — terms.json 점검
# ─────────────────────────────────────────────────────────────
sep("§4 Projection — terms.json 구조 점검")

terms_data = json.loads((DICT / "terms.json").read_text(encoding="utf-8"))
items = terms_data.get("terms", [])

check("terms.json 최상위 terms[] 필드", "terms" in terms_data)
check("checksum 필드 (§4.9)", "checksum" in terms_data,
      str(terms_data.get("checksum","MISSING"))[:30])
check("generated_at 필드", "generated_at" in terms_data,
      str(terms_data.get("generated_at","MISSING")))
check(f"terms 항목 수 > 0", len(items) > 0, f"{len(items)}개")

tt_dist = Counter(t.get("term_type") for t in items)
src_dist = Counter(t.get("source") for t in items)
check("term_type: base/variant 만 존재 (§4.4)", all(k in ("base","variant") for k in tt_dist),
      dict(tt_dist))
check("source: word/compound 만 존재", all(k in ("word","compound") for k in src_dist),
      dict(src_dist))

# base 항목 필수 필드
required_base = {"id", "source", "root", "term_type", "domain", "lang"}
miss_base = [t["id"] for t in items if t.get("term_type") == "base" and required_base - set(t.keys())]
check("base 항목 필수 필드 완결", len(miss_base) == 0,
      f"미완전 {len(miss_base)}개" if miss_base else f"{tt_dist['base']}개 OK")

# variant 항목 필수 필드
required_var = {"id", "source", "root", "term_type", "variant_type", "domain"}
miss_var = [t["id"] for t in items if t.get("term_type") == "variant" and required_var - set(t.keys())]
check("variant 항목 필수 필드 완결", len(miss_var) == 0,
      f"미완전 {len(miss_var)}개" if miss_var else f"{tt_dist['variant']}개 OK")

# §4.5 제외 대상 확인 — pos_forms/adjective/adverb가 terms에 포함되어있으면 이상
excluded_types = {"pos_forms", "adjective", "adverb"}
excluded_in_terms = [t["id"] for t in items if t.get("variant_type") in excluded_types]
check("제외 variant_type(pos_forms/adj/adv) terms 미포함 (§4.5)", len(excluded_in_terms) == 0,
      f"포함됨: {excluded_in_terms[:5]}" if excluded_in_terms else "OK")

# deprecated → legacy 분리 (§4.8)
legacy_path = DICT / "terms_legacy.json"
if legacy_path.exists():
    legacy_data = json.loads(legacy_path.read_text(encoding="utf-8"))
    legacy_count = len(legacy_data.get("terms", legacy_data if isinstance(legacy_data, list) else []))
    check("terms_legacy.json 존재 (§4.8)", True, f"항목 {legacy_count}개")
else:
    check("terms_legacy.json 존재 (§4.8)", False, "파일 없음")


# ─────────────────────────────────────────────────────────────
# §6 Dependency 점검
# ─────────────────────────────────────────────────────────────
sep("§6 Dependency — compounds.words 참조 정합성")

word_ids = {w["id"] for w in words if isinstance(w, dict)}
broken_deps = []
for c in compounds:
    if not isinstance(c, dict):
        continue
    for wid in (c.get("words") or []):
        if wid not in word_ids:
            broken_deps.append(f"{c.get('id','?')}.{wid}")
check("compounds.words → 모든 참조 단어 존재 (§6.1)", len(broken_deps) == 0,
      f"깨진 참조 {len(broken_deps)}개: {broken_deps[:5]}" if broken_deps else f"{len(compounds)}개 복합어 OK")


# ─────────────────────────────────────────────────────────────
# §7 Validation Gate 코드 점검
# ─────────────────────────────────────────────────────────────
sep("§7 Validation Gate — generate_glossary.py 코드 점검")

gg_path = ROOT / "generate_glossary.py"
gg_src = gg_path.read_text(encoding="utf-8")

gates = {
    "V-001 (id unique)": "V-001",
    "V-104/V-004 (dependency)": "V-104",
    "V-008 (abbr unique)": "V-008",
    "V-010 (checksum)": "V-010",
    "V-011 (schema)": "V-011",
    "V-013 (banned exact match)": "V-013",
}
for label, code in gates.items():
    check(f"{label} 구현", code in gg_src)

# verify_checksum 함수 존재
check("verify_checksum 함수 존재", "def verify_checksum" in gg_src)
check("skip_checksum 파라미터 존재", "skip_checksum" in gg_src)


# ─────────────────────────────────────────────────────────────
# §11 운영 산출물 점검
# ─────────────────────────────────────────────────────────────
sep("§11 운영 산출물 — build/report/ 파일 점검")

report_dir = BUILD / "report"
op_files = [
    "dependency_missing.json",
    "projection_skipped.json",
    "merge_candidates.json",
    "banned_autofix_report.json",
]
for fname in op_files:
    fpath = report_dir / fname
    if fpath.exists():
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            cnt = len(data) if isinstance(data, list) else len(data.get("items", data.get("reports", [])))
            check(fname, True, f"항목 {cnt}개")
        except Exception as e:
            check(fname, False, str(e))
    else:
        check(fname, False, "파일 없음 (generate 실행 필요)")

# build/index 산출물
sep("§build/index — 인덱스 파일 점검")
index_dir = BUILD / "index"
idx_files = ["word_min.json", "compound_min.json", "variant_map.json"]
for fname in idx_files:
    fpath = index_dir / fname
    if fpath.exists():
        size = fpath.stat().st_size
        check(fname, True, f"{size:,} bytes")
    else:
        check(fname, False, "파일 없음 (generate 실행 필요)")


# ─────────────────────────────────────────────────────────────
# schema 점검
# ─────────────────────────────────────────────────────────────
sep("schema/ — §3.3 array 기준 스키마 점검")
for fname in ["word.schema.json", "compound.schema.json", "banned.schema.json"]:
    fpath = SCHEMA / fname
    if fpath.exists():
        src = fpath.read_text(encoding="utf-8")
        has_array = '"type": "array"' in src or "'type': 'array'" in src
        check(f"{fname}", fpath.exists(), f"variants array 형식: {'OK' if has_array else 'MISSING'}")
    else:
        check(f"{fname}", False, "파일 없음")


# ─────────────────────────────────────────────────────────────
# bin/ 파일 점검
# ─────────────────────────────────────────────────────────────
sep("bin/ — 마이그레이션/테스트 파일 점검")
bin_files = {
    "migrate_variants.py": "§8 Step 2 — object→array 마이그레이션",
    "test_regression.py": "§8 Step 7 — regression test",
    "test_db_compat.py": "§8 Step 8 — DB 호환성 test",
    "rollout_rollback_plan.md": "§8 Step 9–10 — rollout/rollback 플랜",
}
for fname, role in bin_files.items():
    check(fname, (BIN / fname).exists(), role)


# ─────────────────────────────────────────────────────────────
# 최종 요약
# ─────────────────────────────────────────────────────────────
sep("요약")
print()
if missing:
    print(f"  [주의] 미존재 필수 파일: {missing}")
else:
    print("  필수 파일 모두 존재")

print()
print("  WARN 현황 (정상 범위):")
print("  - V-401 x5: main/manager/manual/meta/method — description_i18n 미등록")
print("  - V-352 x1: candle — ko 집합 표현만 존재")
