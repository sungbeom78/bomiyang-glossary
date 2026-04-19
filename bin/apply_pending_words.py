#!/usr/bin/env python3
"""
apply_pending_words.py — pending_words.json 잔여 15개를 words.json에 적용
위치: glossary/bin/apply_pending_words.py

처리 방침:
  1. words.json에 단어 추가 (완전한 스키마 포함)
  2. variant 충돌 처리:
     - adapt: adapter.variants에서 adapt 관련 제거, from 필드로 명시
     - authenticate: auth.variants에서 authenticate 제거
     - volatile: volatility.variants에서 volatile 제거
     - low: lower 는 별개 canonical (low < lower), 충돌 없음 → 그대로 추가
  3. 추가 후 pending_words.json에서 제거
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

GLOSSARY_DIR = Path(__file__).parent.parent.resolve()
DICT_DIR     = GLOSSARY_DIR / "dictionary"
WORDS_PATH   = DICT_DIR / "words.json"
PENDING_PATH = DICT_DIR / "pending_words.json"

# GlossaryWriter import (glossary package root에서)
sys.path.insert(0, str(GLOSSARY_DIR))
try:
    from core.writer import GlossaryWriter
except ImportError:
    GlossaryWriter = None  # fallback

NOW = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

# 추가할 단어 정의 (완전한 스키마)
NEW_WORDS = [
    {
        "id": "adapt",
        "domain": "system",
        "status": "active",
        "lang": {"en": "adapt", "ko": "적응", "ja": "適応", "zh_hans": "适应"},
        "description_i18n": {
            "ko": "특정 인터페이스나 환경에 맞게 구조나 동작을 변환하는 행위.",
            "en": "To modify or adjust a structure or behavior to fit a specific interface or environment."
        },
        "canonical_pos": "verb",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "verb_form", "value": "adapts"},
            {"type": "present_participle", "value": "adapting"},
            {"type": "past", "value": "adapted"},
            {"type": "noun_form", "value": "adaptation"},
        ]
    },
    {
        "id": "authenticate",
        "domain": "infra",
        "status": "active",
        "lang": {"en": "authenticate", "ko": "인증하다", "ja": "認証する", "zh_hans": "认证"},
        "description_i18n": {
            "ko": "사용자 또는 시스템의 신원을 검증하는 행위.",
            "en": "To verify the identity of a user or system."
        },
        "canonical_pos": "verb",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "verb_form", "value": "authenticates"},
            {"type": "present_participle", "value": "authenticating"},
            {"type": "past", "value": "authenticated"},
            {"type": "noun_form", "value": "authentication"},
        ]
    },
    {
        "id": "low",
        "domain": "market",
        "status": "active",
        "lang": {"en": "low", "ko": "저가", "ja": "安値", "zh_hans": "低价"},
        "description_i18n": {
            "ko": "일정 기간 내 가격의 최저점.",
            "en": "The lowest price reached within a specific period."
        },
        "canonical_pos": "adj",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "comparative", "value": "lower"},
            {"type": "superlative", "value": "lowest"},
            {"type": "noun_form", "value": "low"},
        ]
    },
    {
        "id": "manage",
        "domain": "system",
        "status": "active",
        "lang": {"en": "manage", "ko": "관리", "ja": "管理", "zh_hans": "管理"},
        "description_i18n": {
            "ko": "자원이나 프로세스를 제어·감독하는 행위.",
            "en": "To control and oversee resources or processes."
        },
        "canonical_pos": "verb",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "verb_form", "value": "manages"},
            {"type": "present_participle", "value": "managing"},
            {"type": "past", "value": "managed"},
            {"type": "noun_form", "value": "management"},
            {"type": "agent", "value": "manager"},
        ]
    },
    {
        "id": "notify",
        "domain": "system",
        "status": "active",
        "lang": {"en": "notify", "ko": "알림", "ja": "通知", "zh_hans": "通知"},
        "description_i18n": {
            "ko": "이벤트나 상태 변경을 외부 채널(텔레그램, 이메일 등)로 전달하는 행위.",
            "en": "To send event or status change information to an external channel (Telegram, email, etc.)."
        },
        "canonical_pos": "verb",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "verb_form", "value": "notifies"},
            {"type": "present_participle", "value": "notifying"},
            {"type": "past", "value": "notified"},
            {"type": "noun_form", "value": "notification"},
        ]
    },
    {
        "id": "orchestrate",
        "domain": "system",
        "status": "active",
        "lang": {"en": "orchestrate", "ko": "오케스트레이트", "ja": "オーケストレート", "zh_hans": "编排"},
        "description_i18n": {
            "ko": "여러 모듈이나 서비스의 실행 흐름을 중앙에서 조율하는 행위.",
            "en": "To centrally coordinate the execution flow of multiple modules or services."
        },
        "canonical_pos": "verb",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "verb_form", "value": "orchestrates"},
            {"type": "present_participle", "value": "orchestrating"},
            {"type": "past", "value": "orchestrated"},
            {"type": "noun_form", "value": "orchestration"},
        ]
    },
    {
        "id": "real",
        "domain": "market",
        "status": "active",
        "lang": {"en": "real", "ko": "실시간", "ja": "リアル", "zh_hans": "实时"},
        "description_i18n": {
            "ko": "실제 시장 환경 또는 실시간 데이터를 의미하는 접두사 개념.",
            "en": "Referring to actual market conditions or live data, often used as a prefix concept."
        },
        "canonical_pos": "adj",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": []
    },
    {
        "id": "scan",
        "domain": "system",
        "status": "active",
        "lang": {"en": "scan", "ko": "스캔", "ja": "スキャン", "zh_hans": "扫描"},
        "description_i18n": {
            "ko": "소스 코드나 데이터를 순차적으로 검색·추출하는 행위.",
            "en": "To sequentially search through or extract items from source code or data."
        },
        "canonical_pos": "verb",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "verb_form", "value": "scans"},
            {"type": "present_participle", "value": "scanning"},
            {"type": "past", "value": "scanned"},
            {"type": "agent", "value": "scanner"},
        ]
    },
    {
        "id": "schedule",
        "domain": "system",
        "status": "active",
        "lang": {"en": "schedule", "ko": "스케줄", "ja": "スケジュール", "zh_hans": "计划"},
        "description_i18n": {
            "ko": "특정 시간 또는 조건에 맞춰 작업을 예약·실행하는 행위.",
            "en": "To plan or execute tasks at a specific time or based on a condition."
        },
        "canonical_pos": "verb",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "verb_form", "value": "schedules"},
            {"type": "present_participle", "value": "scheduling"},
            {"type": "past", "value": "scheduled"},
            {"type": "noun_form", "value": "scheduling"},
        ]
    },
    {
        "id": "select",
        "domain": "system",
        "status": "active",
        "lang": {"en": "select", "ko": "선택", "ja": "選択", "zh_hans": "选择"},
        "description_i18n": {
            "ko": "조건에 맞는 항목을 선별·조회하는 행위.",
            "en": "To filter or query items that meet specific conditions."
        },
        "canonical_pos": "verb",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "verb_form", "value": "selects"},
            {"type": "present_participle", "value": "selecting"},
            {"type": "past", "value": "selected"},
            {"type": "noun_form", "value": "selection"},
            {"type": "agent", "value": "selector"},
        ]
    },
    {
        "id": "slip",
        "domain": "trading",
        "status": "active",
        "lang": {"en": "slip", "ko": "슬리피지", "ja": "スリッページ", "zh_hans": "滑点"},
        "description_i18n": {
            "ko": "주문 가격과 실제 체결 가격 간의 차이(슬리피지).",
            "en": "The difference between the intended order price and the actual fill price (slippage)."
        },
        "canonical_pos": "noun",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "plural", "value": "slips"},
            {"type": "present_participle", "value": "slipping"},
            {"type": "past", "value": "slipped"},
            {"type": "noun_form", "value": "slippage"},
        ]
    },
    {
        "id": "snap",
        "domain": "system",
        "status": "active",
        "lang": {"en": "snap", "ko": "스냅샷", "ja": "スナップ", "zh_hans": "快照"},
        "description_i18n": {
            "ko": "특정 시점의 상태를 즉시 캡처하는 행위 또는 그 결과.",
            "en": "The act of immediately capturing a state at a specific point in time, or its result."
        },
        "canonical_pos": "verb",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "verb_form", "value": "snaps"},
            {"type": "present_participle", "value": "snapping"},
            {"type": "past", "value": "snapped"},
            {"type": "noun_form", "value": "snapshot"},
        ]
    },
    {
        "id": "store",
        "domain": "infra",
        "status": "active",
        "lang": {"en": "store", "ko": "저장", "ja": "保存", "zh_hans": "存储"},
        "description_i18n": {
            "ko": "데이터를 DB, 파일, 메모리 등에 영구 또는 임시로 보관하는 행위.",
            "en": "To persistently or temporarily save data to a database, file, or memory."
        },
        "canonical_pos": "verb",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "verb_form", "value": "stores"},
            {"type": "present_participle", "value": "storing"},
            {"type": "past", "value": "stored"},
            {"type": "noun_form", "value": "storage"},
        ]
    },
    {
        "id": "volatile",
        "domain": "trading",
        "status": "active",
        "lang": {"en": "volatile", "ko": "변동성 있는", "ja": "不安定な", "zh_hans": "波动的"},
        "description_i18n": {
            "ko": "가격 변동이 크고 불안정한 시장 상태.",
            "en": "A market condition characterized by large and rapid price fluctuations."
        },
        "canonical_pos": "adj",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "noun_form", "value": "volatility"},
            {"type": "adv_form", "value": "volatilely"},
        ]
    },
    {
        "id": "watch",
        "domain": "system",
        "status": "active",
        "lang": {"en": "watch", "ko": "감시", "ja": "ウォッチ", "zh_hans": "监控"},
        "description_i18n": {
            "ko": "파일, 소켓 또는 이벤트를 지속적으로 모니터링하는 행위.",
            "en": "To continuously monitor a file, socket, or event for changes."
        },
        "canonical_pos": "verb",
        "created_at": NOW,
        "updated_at": NOW,
        "variants": [
            {"type": "verb_form", "value": "watches"},
            {"type": "present_participle", "value": "watching"},
            {"type": "past", "value": "watched"},
            {"type": "agent", "value": "watcher"},
        ]
    },
]

# variant 충돌 해결: 부모 word에서 해당 surface 제거
REMOVE_VARIANT_FROM_PARENT: list[tuple[str, str]] = [
    # (parent_id, variant_value_to_remove)
    ("volatility", "volatile"),   # volatile은 독립 단어로 분리
    ("auth",       "authenticate"), # authenticate는 독립 단어로 분리
    # adapt: adapter.variants에 adapt가 variant로 있으면 제거
    ("adapter",    "adapt"),
    # lower: lower는 low의 comparative — low를 독립 추가하므로 lower.variants에서 low 제거 (있다면)
    ("lower",      "low"),
]


def apply_pending():
    if GlossaryWriter:
        gw = GlossaryWriter()
        words = gw.words
    else:
        data = json.loads(WORDS_PATH.read_text(encoding='utf-8'))
        words = data.get('words', [])

    existing_ids = {w['id'] for w in words}

    # Step 1: variant 충돌 해결 (부모에서 제거)
    variant_removed = []
    if GlossaryWriter:
        for pid, val in REMOVE_VARIANT_FROM_PARENT:
            w = gw.get_word(pid)
            if not w:
                continue
            before_v = list(w.get('variants', []))
            new_variants = [
                v for v in before_v
                if (v.get('value') or v.get('short') or '').lower().strip() != val
            ]
            if len(new_variants) < len(before_v):
                gw.update_word(pid, {'variants': new_variants})
                variant_removed.append(f"  [{pid}] {len(before_v)} -> {len(new_variants)}의")
    else:
        for w in words:
            wid = w.get('id', '')
            targets = [val for (pid, val) in REMOVE_VARIANT_FROM_PARENT if pid == wid]
            if not targets:
                continue
            before = len(w.get('variants', []))
            new_variants = [
                v for v in w.get('variants', [])
                if (v.get('value') or v.get('short') or '').lower().strip() not in targets
            ]
            if before != len(new_variants):
                w['variants'] = new_variants
                variant_removed.append(f"  [{wid}] {before} -> {len(new_variants)}의")

    # Step 2: 신규 단어 추가
    added = []
    skipped = []
    for w in NEW_WORDS:
        if w['id'] in existing_ids:
            skipped.append(w['id'])
        else:
            if GlossaryWriter:
                gw.add_word(w, skip_duplicate=True)
            else:
                words.append(w)
            added.append(w['id'])

    # 저장
    if GlossaryWriter:
        gw.save()
        words = gw.words
    else:
        words.sort(key=lambda x: x['id'])
        data['words'] = words
        WORDS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    # Step 3: pending_words.json에서 적용된 것 제거
    pw_data = json.loads(PENDING_PATH.read_text(encoding='utf-8'))
    applied_ids = set(added) | set(skipped)
    before_pending = len(pw_data.get('words', []))
    pw_data['words'] = [w for w in pw_data.get('words', []) if w['id'] not in applied_ids]
    after_pending = len(pw_data['words'])
    PENDING_PATH.write_text(json.dumps(pw_data, ensure_ascii=False, indent=2), encoding='utf-8')

    # 결과 출력
    print("=== pending_words 적용 결과 ===")
    if variant_removed:
        print("\n[variant 충돌 해결]")
        for r in variant_removed:
            print(r)
    print(f"\n[words.json 추가]")
    for wid in added:
        print(f"  + {wid}")
    if skipped:
        print(f"\n[이미 존재 (skip)]: {skipped}")
    print(f"\n[pending_words.json]: {before_pending} -> {after_pending}의")
    print(f"\n총 단어 수: {len(words)}")


if __name__ == "__main__":
    apply_pending()
