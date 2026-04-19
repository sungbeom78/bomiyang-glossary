#!/usr/bin/env python3
"""
fix_v301_conflicts.py — V-301: variant surface == word.id 충돌 해결
위치: glossary/bin/fix_v301_conflicts.py

처리 방침:
  사용자가 독립 단어로 명시적으로 추가한 케이스는 독립 word로 유지.
  해당 단어를 variant로 참조하는 부모 word에서 variant를 제거.

대상:
  ranking   : rank.variants에서 type in (present_participle, noun_form) value='ranking' 제거
  realized  : realize.variants에서 {type:past, value:realized} 제거
  extended  : extend.variants에서 {type:past, value:extended} 제거
  tracking  : track.variants에서 {type:present_participle, value:tracking} 제거
  used      : use.variants에서 {type:past, value:used} 제거
  runner    : run.variants에서 {type:agent, value:runner} 제거
  scoring   : score.variants에서 value='scoring' 제거   (scoring은 독립 단어 score 존재)
  reporting : report.variants에서 value='reporting' 제거

  아래는 구조적 설계 이슈 — 이번에는 제거하지 않음 (별도 검토 필요):
  classify <-> classification 상호 참조
  closed -> close (adj_form — close에서 closed는 의도적 포함 가능)
  entry -> reentry (다른 의미, 구조적 이슈)
  execution -> exec (exec의 noun_form이 execution — 의도적 참조)
  trading -> trade (동명사 형태 — 독립 단어로 사용)
  realize -> unrealized (unrealized의 from:'realize' variant — 구조적)
"""
import json
from pathlib import Path

GLOSSARY_DIR = Path(__file__).parent.parent.resolve()
WORDS_PATH = GLOSSARY_DIR / "dictionary" / "words.json"

# (word_id, variant_value_to_remove) — value 기준 제거
REMOVE_VARIANTS: list[tuple[str, str]] = [
    ("rank",    "ranking"),   # ranking은 독립 word
    ("realize", "realized"),  # realized는 독립 word
    ("extend",  "extended"),  # extended는 독립 word
    ("track",   "tracking"),  # tracking는 독립 word
    ("use",     "used"),      # used는 독립 word
    ("run",     "runner"),    # runner는 독립 word
]


def fix_v301():
    data = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
    words = data.get("words", [])
    report = []

    for w in words:
        wid = w.get("id", "")
        targets = [val for (wid2, val) in REMOVE_VARIANTS if wid2 == wid]
        if not targets:
            continue

        variants = w.get("variants", [])
        before = len(variants)
        new_variants = []
        removed = []
        for v in variants:
            val = (v.get("value") or v.get("short") or "").lower().strip()
            if val in targets:
                removed.append(f"{v.get('type')}:{val}")
            else:
                new_variants.append(v)
        after = len(new_variants)
        if removed:
            w["variants"] = new_variants
            report.append(f"  [{wid}] 제거: {removed}  ({before} -> {after}개)")

    data["words"] = words
    WORDS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=== V-301 variant 제거 결과 ===")
    for r in report:
        print(r)
    print(f"\n  처리 건수: {len(report)}")


if __name__ == "__main__":
    fix_v301()
