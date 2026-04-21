# Glossary AI Guideline

> glossary 서브모듈 전용 AI 운영 가이드라인.
> 어떤 main 프로젝트에 연결되어도 이 파일의 규칙이 우선 적용된다.

---

## 1. 데이터 아키텍처 개요

```
glossary/
├── dictionary/                    ← AUTHORITATIVE DATA (Source of Truth)
│   ├── words.json                 ← 단어 사전 (root words + variants)
│   ├── compounds.json             ← 복합어 사전
│   ├── banned.json                ← 금지어 목록
│   ├── pending_words.json         ← 승인 대기 단어
│   └── terms.json                 ← 자동 생성 (generate로 생성, 직접 편집 금지)
├── build/
│   └── index/
│       ├── word_min.json          ← 자동 생성 — check-id 런타임 인덱스
│       ├── compound_min.json      ← 자동 생성
│       └── variant_map.json       ← 자동 생성 — 형태소 → root 매핑
├── core/
│   └── writer.py                  ← GlossaryWriter (words/compounds 단일 저장 진입점)
├── generate_glossary.py           ← validate / generate / check-id 진입점
├── bin/
│   ├── wikt_sense.py              ← Wiktionary + AI 파이프라인
│   ├── batch_items.py             ← LLM 배치 처리
│   ├── scan_items.py              ← 소스 코드 스캔
│   └── apply_pending_words.py     ← pending → words.json 적용
└── web/
    └── server.py                  ← glossary 웹 UI 서버
```

---

## 2. 핵심 규칙 요약

### Rule G-1: GlossaryWriter 사용 의무
`words.json` / `compounds.json`을 직접 write하는 것은 **절대 금지**.
반드시 `core/writer.py`의 `GlossaryWriter`를 경유.

### Rule G-2: validate 우선
데이터 수정 전/후 반드시 `python generate_glossary.py validate` → FATAL 0건 확인.

### Rule G-3: check-id 먼저
신규 식별자 생성 전 반드시 `python generate_glossary.py check-id <identifier>` 실행.
`[ERROR] 미등록` 시 개발 중단 → 등록 절차 진행.

### Rule G-4: 복수형/파생형은 root variant로
- 복수형(seconds, formats 등)은 독립 root word로 등록 금지 → 단수형의 `plural` variant
- 약어(csv, api 등)는 word로 독립 등록 금지 → compound의 `abbreviation` variant
- 파생형(reached, reachable 등)은 독립 word로 등록 금지 → 동사 root의 `past`/`adj_form` variant

---

## 3. validate 규칙 (V-코드)

| V-코드 | 수준 | 룰 |
|--------|------|-----|
| V-104 | FATAL | compound.words 참조 단어가 words.json에 없음 |
| V-202 | FATAL | word로 등록된 항목이 compound의 abbreviation으로도 존재 (중복) |
| V-301 | FATAL | 복수형이 독립 root word로 등록됨 (단수형의 variant여야 함) |
| V-303 | WARN | plural variant가 자기 자신을 참조 (self-referential) |
| V-352 | WARN | ko 언어 표현이 집합형(복수)으로만 표현됨 |

---

## 4. GlossaryWriter API

| 메서드 | 역할 |
|--------|------|
| `add_word(word, skip_duplicate=False)` | 단어 추가 |
| `update_word(word_id, patch)` | 단어 수정 (patch 병합) |
| `remove_word(word_id)` | 단어 삭제 |
| `add_word_variant(word_id, vtype, vval)` | 단어에 variant 추가 |
| `add_compound(compound, skip_duplicate=False)` | 복합어 추가 |
| `update_compound(cid, patch)` | 복합어 수정 |
| `remove_compound(cid)` | 복합어 삭제 |
| `validate()` | 저장 전 validate 실행 (FATAL 목록 반환) |
| `save()` | 파일 저장 (자동 backup 생성) |
| `rollback()` | 스냅샷으로 메모리 상태 복원 |

---

## 5. PROJECTION_VARIANT_TYPES (generate_glossary.py)

`variant_map.json` 빌드 시 포함되는 variant type 목록.
`check-id` 에서 파생형이 root로 resolve되려면 아래 타입에 포함되어야 함.

```python
PROJECTION_VARIANT_TYPES = {
    # 기존 (abbreviation/alias 계열)
    "abbreviation", "alias", "plural", "misspelling",
    # 굴절형 (inflection)
    "singular", "verb_form", "past", "past_participle",
    "present_participle", "comparative", "superlative",
    # 형태론적 파생형 (morphological derivation)
    "noun_form", "verb_derived", "adj_form", "adv_form",
    "agent", "gerund",
}
```

---

## 6. 환경 설정

### .env 필수 항목

```
# API 키 (AI 파이프라인 사용 시)
API_KEY_TYPE=google           # google | claude | openai
GOOGLE_API_KEY=...
# ANTHROPIC_API_KEY=...
# OPENAI_API_KEY=...

API_MODEL=gemini-2.0-flash
MAX_OUTPUT_TOKENS=1000
BATCH_CHUNK_SIZE=20
```

### 설정 원칙
- 환경 변수 및 인증 정보는 코드에 절대 하드코딩 금지
- `.env` 파일을 통해서만 로드 (`bin/batch_items.py`의 `get_env()` 또는 `wikt_sense._load_ai_env()`)
- 절대 경로는 `Path(__file__).resolve().parent` 등 상대 경로로 구성

---

## 7. 명명 표준

| 대상 | 규칙 |
|------|------|
| 파일/모듈 | `snake_case.py` |
| 클래스 | `PascalCase` |
| 함수/메서드 | `snake_case` |
| 상수 | `UPPER_SNAKE_CASE` |
| 디렉토리 | singular form (`log/`, `test/`, `schema/`) |
| DB 테이블 | singular form |

모든 식별자는 `python generate_glossary.py check-id <identifier>` 통과 필수.

---

## 8. Wiktionary + AI 파이프라인 사용법

```python
import sys
sys.path.insert(0, "<glossary_root>/bin")
from wikt_sense import fetch_and_process, _load_ai_env
from core.writer import GlossaryWriter

word_stub = {
    "id": "<word>",
    "canonical_pos": "verb",   # 예상 품사
    "domain": "system",        # core | system | infra | ui | network | general
}

ai_env = _load_ai_env()
url, result = fetch_and_process("<word>", word_stub, ai_env=ai_env)

if result and result.status == "ok":
    entry = {
        "id": "<word>",
        "canonical_pos": result.selected_pos,
        "domain": "system",
        "lang": {"en": "<word>", "ko": "<번역>"},
        "description_i18n": {"en": result.description_en},
        "variants": result.variants,
        "source_urls": [url],
    }
    with GlossaryWriter() as gw:
        gw.add_word(entry)
```

---

## 9. 변경 이력 관리

- `doc/change_log.md` — glossary 전용 변경 이력 (main 프로젝트와 별도 관리)
- 항목 형식: 최상단 APPEND (덮어쓰기 금지)
- 500줄 초과 또는 월 1일 → `doc/change_log_archive/YYYYMM_change_log.md` 아카이브
