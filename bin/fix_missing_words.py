#!/usr/bin/env python3
"""
fix_missing_words.py — V-104 FATAL 해결: compounds가 참조하는 미등록 단어 추가
위치: glossary/bin/fix_missing_words.py

대상:
  - ranking  (sector_ranking, symbol_ranking, db_sector_rankings 참조)
  - realized (realized_pnl 참조)
  - tracking (tracking_start 참조)
  - extended (extended_market_start, extended_market_end 참조)
  - used     (margin_used 참조)
"""
import json
from datetime import datetime, timezone
from pathlib import Path

GLOSSARY_DIR = Path(__file__).parent.parent.resolve()
WORDS_PATH   = GLOSSARY_DIR / "dictionary" / "words.json"

NOW = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

MISSING_WORDS = [
    {
        "id": "ranking",
        "domain": "trading",
        "status": "active",
        "lang": {"en": "ranking", "ko": "순위", "ja": "ランキング", "zh_hans": "排名"},
        "description_i18n": {
            "ko": "특정 기준에 따른 순위 또는 순위 목록.",
            "en": "An ordered list based on a specific criterion."
        },
        "canonical_pos": "noun",
        "variants": [
            {"type": "plural", "value": "rankings"},
            {"type": "present_participle", "value": "ranking"},
        ],
        "created_at": NOW,
        "updated_at": NOW,
    },
    {
        "id": "realized",
        "domain": "trading",
        "status": "active",
        "lang": {"en": "realized", "ko": "실현된", "ja": "実現済み", "zh_hans": "已实现"},
        "description_i18n": {
            "ko": "포지션을 청산하여 확정된 손익 상태.",
            "en": "Describing a gain or loss that has been confirmed by closing a position."
        },
        "canonical_pos": "adj",
        "from": "realize",
        "variants": [],
        "created_at": NOW,
        "updated_at": NOW,
    },
    {
        "id": "tracking",
        "domain": "system",
        "status": "active",
        "lang": {"en": "tracking", "ko": "추적", "ja": "トラッキング", "zh_hans": "追踪"},
        "description_i18n": {
            "ko": "대상의 상태나 위치를 지속적으로 기록·감시하는 행위.",
            "en": "The continuous monitoring or recording of a subject's state or position."
        },
        "canonical_pos": "noun",
        "from": "track",
        "variants": [],
        "created_at": NOW,
        "updated_at": NOW,
    },
    {
        "id": "extended",
        "domain": "market",
        "status": "active",
        "lang": {"en": "extended", "ko": "연장된", "ja": "拡張済み", "zh_hans": "延长的"},
        "description_i18n": {
            "ko": "정규 시장 시간 외의 프리마켓·애프터마켓 거래 시간을 가리킴.",
            "en": "Refers to pre-market or after-market trading sessions outside regular hours."
        },
        "canonical_pos": "adj",
        "from": "extend",
        "variants": [],
        "created_at": NOW,
        "updated_at": NOW,
    },
    {
        "id": "used",
        "domain": "trading",
        "status": "active",
        "lang": {"en": "used", "ko": "사용된", "ja": "使用済み", "zh_hans": "已使用"},
        "description_i18n": {
            "ko": "이미 소진되거나 활용된 수량·금액 (예: margin_used = 사용 증거금).",
            "en": "The portion of a quantity or amount that has already been consumed or allocated."
        },
        "canonical_pos": "adj",
        "from": "use",
        "variants": [],
        "created_at": NOW,
        "updated_at": NOW,
    },
]


def fix_missing_words():
    data = json.loads(WORDS_PATH.read_text(encoding='utf-8'))
    existing_ids = {w['id'] for w in data.get('words', [])}

    added = []
    skipped = []
    for w in MISSING_WORDS:
        if w['id'] in existing_ids:
            skipped.append(w['id'])
        else:
            data['words'].append(w)
            added.append(w['id'])

    # 알파벳 정렬
    data['words'].sort(key=lambda x: x['id'])
    WORDS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    print("=== V-104 FATAL 해결: missing words 추가 ===")
    print(f"  추가됨:  {added}")
    print(f"  이미 있음 (skip): {skipped}")
    print(f"  words.json 총 단어 수: {len(data['words'])}")


if __name__ == "__main__":
    fix_missing_words()
