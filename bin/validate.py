#!/usr/bin/env python3
"""
validate.py
terms.json 유효성 검사 스크립트

사용법:
    python3 validate.py
    python3 validate.py --input terms.json
"""

import json
import argparse
from collections import defaultdict

REQUIRED_FIELDS = ["id", "ko", "en", "abbr_long", "abbr_short", "categories", "description"]


def validate(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    terms = data["terms"]
    errors = []
    warnings = []

    # 1. 필수 필드 검사
    for t in terms:
        for field in REQUIRED_FIELDS:
            if field not in t or not t[field]:
                errors.append(f"[{t.get('id','?')}] 필수 필드 누락: '{field}'")

    # 2. id 중복 검사
    id_map = defaultdict(list)
    for t in terms:
        id_map[t.get("id", "")].append(t)
    for id_, ts in id_map.items():
        if len(ts) > 1:
            errors.append(f"id 중복: '{id_}' ({len(ts)}건)")

    # 3. abbr_long 중복 검사
    long_map = defaultdict(list)
    for t in terms:
        long_map[t.get("abbr_long", "")].append(t["id"])
    for k, ids in long_map.items():
        if len(ids) > 1:
            errors.append(f"abbr_long 중복: '{k}' → {ids}")

    # 4. abbr_short 충돌 검사 (다른 개념끼리만)
    short_map = defaultdict(list)
    for t in terms:
        short_map[t.get("abbr_short", "")].append(t)
    for short, ts in short_map.items():
        if len(ts) > 1:
            # 카테고리가 전혀 겹치지 않으면 위험 경고
            all_cats = [set(t.get("categories", [])) for t in ts]
            has_overlap = any(
                all_cats[i] & all_cats[j]
                for i in range(len(all_cats))
                for j in range(i + 1, len(all_cats))
            )
            ids = [t["id"] for t in ts]
            if not has_overlap:
                errors.append(f"abbr_short 충돌 (카테고리 불일치): '{short}' → {ids}")
            else:
                warnings.append(f"abbr_short 공유 (동일개념 다계층, 허용): '{short}' → {ids}")

    # 5. categories 유효성 검사
    valid_cats = set(data["meta"]["categories"].keys())
    for t in terms:
        for cat in t.get("categories", []):
            if cat not in valid_cats:
                errors.append(f"[{t['id']}] 알 수 없는 category: '{cat}'")

    # 6. abbr_long camelCase 검사 (경고)
    for t in terms:
        al = t.get("abbr_long", "")
        if al and al[0].isupper() and not t.get("class_type"):
            warnings.append(f"[{t['id']}] abbr_long '{al}' 이 대문자 시작 (클래스가 아닌 경우 확인 필요)")

    # 결과 출력
    print(f"\n{'='*50}")
    print(f"📋 validate.py — {path}")
    print(f"{'='*50}")
    print(f"총 용어 수: {len(terms)}개")

    if errors:
        print(f"\n❌ 오류 {len(errors)}건:")
        for e in errors:
            print(f"  • {e}")
    else:
        print("\n✅ 오류 없음")

    if warnings:
        print(f"\n⚠️  경고 {len(warnings)}건:")
        for w in warnings:
            print(f"  • {w}")

    print(f"\n{'='*50}\n")
    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(description="terms.json 유효성 검사")
    parser.add_argument("--input", default="terms.json")
    args = parser.parse_args()

    ok = validate(args.input)
    exit(0 if ok else 1)


if __name__ == "__main__":
    main()
