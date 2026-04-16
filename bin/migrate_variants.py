#!/usr/bin/env python3
"""
migrate_variants.py  —  BOM_TS Glossary variants Object → Array 마이그레이션
위치: glossary/bin/migrate_variants.py

Plan v2.5.1 §3: variants 구조를 object 형식에서 type-based array 형식으로 전환.

변환 규칙:
  words.json variants (object):
    {"plural": ["items"], "abbreviation": ["ABR"], "alias": "x", ...}
  → array:
    [{"type": "plural", "value": "items"}, {"type": "abbreviation", "short": "ABR", "long": "..."}, ...]

  compounds.json:
    abbr: {"short": "ABR", "long": "..."} → variants array의 abbreviation 항목으로 통합
    variants (object) → array 동일 변환

정렬 순서 (§3.4):
  abbreviation > alias > plural > singular > 기타

사용법:
    python bin/migrate_variants.py --dry-run     # 변경 예상 결과 출력 (실제 저장 없음)
    python bin/migrate_variants.py               # 실제 마이그레이션 실행
"""

import sys
import io
import json
import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Windows 인코딩
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BIN_DIR    = Path(__file__).parent.resolve()
ROOT       = BIN_DIR.parent
DICT_DIR   = ROOT / "dictionary"
WORDS_PATH = DICT_DIR / "words.json"
COMPOUNDS_PATH = DICT_DIR / "compounds.json"
BACKUP_DIR = ROOT / "backup"

# §3.4 정렬 순서: abbreviation > alias > plural > singular > 기타
VARIANT_SORT_ORDER = {
    "abbreviation":     0,
    "alias":            1,
    "plural":           2,
    "singular":         3,
    "misspelling":      4,
    "adjective":        5,
    "adverb":           6,
    "verb":             7,
    "noun_form":        8,
    "verb_form":        9,
    "present_participle": 10,
    "past":             11,
    "past_participle":  12,
    "agent":            13,
    "pos_forms":        14,
    "deprecated":       15,
}


def _sort_key(variant: dict) -> int:
    return VARIANT_SORT_ORDER.get(variant.get("type", ""), 99)


def convert_word_variants(word: dict) -> dict:
    """
    word의 variants object → type-based array 변환.
    §3.2 지원 타입 전체 처리.
    §3.3 JSON Schema:
      - value: 단순 문자열 variant (plural, alias, misspelling, singular 등)
      - short/long: abbreviation
    """
    old_variants = word.get("variants", {})
    if not isinstance(old_variants, dict):
        # 이미 array이거나 비정상 데이터: 그대로 유지
        return word

    new_variants = []

    for vtype, vval in old_variants.items():
        if vtype == "abbreviation":
            # abbreviation: list of strings → 각각 {"type": "abbreviation", "short": val}
            vals = [vval] if isinstance(vval, str) else (vval if isinstance(vval, list) else [])
            for v in vals:
                if v and isinstance(v, str):
                    new_variants.append({"type": "abbreviation", "short": v.strip()})
        elif isinstance(vval, list):
            # plural, agent 등 배열 타입
            for v in vval:
                if v and isinstance(v, str):
                    new_variants.append({"type": vtype, "value": v.strip()})
        elif isinstance(vval, str) and vval.strip():
            # singular, alias, misspelling, adjective, adverb, verb, noun_form 등 단일 문자열
            new_variants.append({"type": vtype, "value": vval.strip()})

    # §3.4 정렬
    new_variants.sort(key=_sort_key)

    result = dict(word)
    if new_variants:
        result["variants"] = new_variants
    else:
        result.pop("variants", None)

    # updated_at 갱신
    result["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return result


def convert_compound_variants(compound: dict) -> dict:
    """
    compound의 variants object + abbr object → type-based array 통합 변환.
    - abbr.short/long → {"type": "abbreviation", "short": ..., "long": ...}
    - variants object → array (convert_word_variants와 동일 규칙)
    """
    new_variants = []

    # 기존 abbr 객체 → abbreviation variant로 통합
    old_abbr = compound.get("abbr", {})
    if isinstance(old_abbr, dict) and old_abbr.get("short"):
        abbr_entry = {"type": "abbreviation", "short": old_abbr["short"]}
        if old_abbr.get("long"):
            abbr_entry["long"] = old_abbr["long"]
        new_variants.append(abbr_entry)

    # 기존 variants object 처리
    old_variants = compound.get("variants", {})
    if isinstance(old_variants, dict):
        for vtype, vval in old_variants.items():
            if vtype == "abbreviation":
                vals = [vval] if isinstance(vval, str) else (vval if isinstance(vval, list) else [])
                for v in vals:
                    if v and isinstance(v, str):
                        # abbr에서 이미 추가된 short와 중복 방지
                        short_val = v.strip()
                        if not any(
                            e.get("type") == "abbreviation" and e.get("short") == short_val
                            for e in new_variants
                        ):
                            new_variants.append({"type": "abbreviation", "short": short_val})
            elif isinstance(vval, list):
                for v in vval:
                    if v and isinstance(v, str):
                        new_variants.append({"type": vtype, "value": v.strip()})
            elif isinstance(vval, str) and vval.strip():
                new_variants.append({"type": vtype, "value": vval.strip()})

    # §3.4 정렬
    new_variants.sort(key=_sort_key)

    result = dict(compound)
    # abbr 필드 제거 (variants array로 통합)
    result.pop("abbr", None)
    if new_variants:
        result["variants"] = new_variants
    else:
        result.pop("variants", None)

    result["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return result


def migrate_words(dry_run: bool = False) -> tuple:
    """words.json 마이그레이션. 반환: (변경 수, 전체 수)"""
    data = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
    words = data.get("words", [])

    changed, total = 0, len(words)
    new_words = []
    for w in words:
        converted = convert_word_variants(w)
        if converted != w:
            changed += 1
        new_words.append(converted)

    if not dry_run:
        data["words"] = new_words
        # version 업데이트
        data["version"] = "2.5.1"
        WORDS_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return changed, total


def migrate_compounds(dry_run: bool = False) -> tuple:
    """compounds.json 마이그레이션. 반환: (변경 수, 전체 수)"""
    data = json.loads(COMPOUNDS_PATH.read_text(encoding="utf-8"))
    compounds = data.get("compounds", [])

    changed, total = 0, len(compounds)
    new_compounds = []
    for c in compounds:
        converted = convert_compound_variants(c)
        if converted != c:
            changed += 1
        new_compounds.append(converted)

    if not dry_run:
        data["compounds"] = new_compounds
        data["version"] = "2.5.1"
        COMPOUNDS_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return changed, total


def backup_files():
    """마이그레이션 전 백업 생성."""
    BACKUP_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for src in [WORDS_PATH, COMPOUNDS_PATH]:
        dst = BACKUP_DIR / f"{src.stem}_{ts}{src.suffix}"
        shutil.copy2(src, dst)
        print(f"  [BACKUP] {src.name} → backup/{dst.name}")


def main():
    parser = argparse.ArgumentParser(
        description="BOM_TS Glossary variants Object→Array 마이그레이션 (Plan v2.5.1 §3)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="실제 저장 없이 변경 예상 결과만 출력"
    )
    args = parser.parse_args()

    print(f"\n{'='*52}")
    print(f"  migrate_variants  —  Plan v2.5.1 §3")
    print(f"  {'[DRY-RUN]' if args.dry_run else '[LIVE]'}")
    print(f"{'='*52}")

    if not args.dry_run:
        print("\n백업 생성 중...")
        backup_files()

    print("\nwords.json 마이그레이션...")
    w_changed, w_total = migrate_words(dry_run=args.dry_run)
    print(f"  변경: {w_changed}/{w_total}개")

    print("\ncompounds.json 마이그레이션...")
    c_changed, c_total = migrate_compounds(dry_run=args.dry_run)
    print(f"  변경: {c_changed}/{c_total}개")

    if args.dry_run:
        print("\n[DRY-RUN] 실제 파일 변경 없음. --dry-run 없이 다시 실행하면 적용됩니다.")
    else:
        print("\n마이그레이션 완료.")
        print("다음 명령으로 검증하세요:")
        print("  python generate_glossary.py validate")
        print("  python generate_glossary.py generate")

    print(f"\n{'='*52}\n")


if __name__ == "__main__":
    main()
