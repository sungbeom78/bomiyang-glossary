#!/usr/bin/env python3
"""
clean_pending_words.py — pending_words.json 정제
위치: glossary/bin/clean_pending_words.py

처리 내용:
1. words.json에 이미 등록된 항목 제거 (disable, rank, relax)
2. 도메인 무관/언어학/접두사 항목 제거 (latin, french, re 등)
3. 나머지 유지 (adapt, authenticate, manage 등 — 검토 대상)
"""
import json
from pathlib import Path

GLOSSARY_DIR = Path(__file__).parent.parent.resolve()
DICT_DIR     = GLOSSARY_DIR / "dictionary"
WORDS_PATH   = DICT_DIR / "words.json"
PENDING_PATH = DICT_DIR / "pending_words.json"

# words.json에 이미 있거나 도메인 무관해서 제거할 id 목록
REMOVE_IDS = {
    # 이미 words.json에 정식 등록됨
    "disable", "rank", "relax",
    # 도메인 무관: 언어학 용어
    "latin", "french", "italian", "ancient_greek", "middle_english",
    # 도메인 무관: 접두사/불용어
    "tele", "re", "un", "intra",
    # 일반어 / 불필요 (off, back, old, new, middle, heart, dash, bottom, earlier)
    "old", "new", "off", "back", "bottom", "middle", "heart", "dash", "earlier",
}


def clean_pending():
    with open(WORDS_PATH, encoding="utf-8") as f:
        wdata = json.load(f)
    word_ids = {w["id"] for w in wdata.get("words", [])}

    with open(PENDING_PATH, encoding="utf-8") as f:
        pw_data = json.load(f)

    original = pw_data.get("words", [])
    kept = []
    removed = []

    for w in original:
        wid = w["id"]
        if wid in REMOVE_IDS:
            removed.append((wid, "목록 기준 제거"))
        elif wid in word_ids:
            removed.append((wid, "words.json에 이미 등록됨"))
        else:
            kept.append(w)

    pw_data["words"] = kept
    with open(PENDING_PATH, "w", encoding="utf-8") as f:
        json.dump(pw_data, f, ensure_ascii=False, indent=2)

    print("=== pending_words.json 정제 결과 ===")
    print(f"  원본: {len(original)}개")
    print(f"  정제 후: {len(kept)}개")
    print(f"  제거됨: {len(removed)}개")
    print()
    print("  제거 항목:")
    for wid, reason in removed:
        print(f"    - {wid!r}: {reason}")
    print()
    print("  유지 (계속 검토 대상):")
    for w in kept:
        print(f"    - {w['id']!r} ({w.get('domain', '?')})")


if __name__ == "__main__":
    clean_pending()
