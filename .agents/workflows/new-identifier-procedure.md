---
description: glossary 신규 식별자(단어/복합어) 등록 절차 — 어떤 main 프로젝트에서도 동일하게 동작.
---

# Glossary 신규 식별자 등록 절차

> 이 파일은 glossary 서브모듈 자체의 신규 식별자 등록 절차를 정의한다.

## 언제 사용하는가

- 새 파일, 클래스, 함수, 변수 이름에 미등록 단어가 포함될 때
- `python generate_glossary.py check-id <identifier>` → `[ERROR] 미등록` 출력 시

---

## 절차

### Step 1 — check-id 실행

```bash
cd <glossary_root>
python generate_glossary.py check-id <new_identifier>
```

출력 확인:
- `[OK]` 또는 `[INFO]` → 등록된 단어. 진행 가능.
- `[ERROR] 미등록` → **개발 중단. Step 2로 이동.**

---

### Step 2 — 미등록 단어 제안

`[ERROR] 미등록` 단어마다 아래 표 형식으로 제안 요청:

```
[신규 용어 제안]
| word         | type  | 의미                       | 위치 (식별자)     |
|--------------|-------|----------------------------|-------------------|
| <word>       | noun  | <한국어 의미>              | <identifier>      |
```

---

### Step 3 — 결정 대기

사용자(또는 관리자) 결정:
- **승인(Approve)** → Step 4로 이동
- **보류(Pending)** → `dictionary/pending_words.json`에 추가 후 개발 재개 (QA에서 WARN)
- **거부(Reject)** → 이름 변경 후 Step 1 재실행

---

### Step 4 — 등록 실행

#### 단어 등록 (GlossaryWriter 사용)

```python
import sys
sys.path.insert(0, "<glossary_root>")
from core.writer import GlossaryWriter

with GlossaryWriter() as gw:
    gw.add_word({
        "id": "<word>",
        "canonical_pos": "<noun|verb|adj|adv>",
        "domain": "<trading|system|infra|market|general>",
        "lang": {"en": "<word>", "ko": "<한국어>"},
        "description_i18n": {
            "en": "<English definition>",
            "ko": "<한국어 정의>"
        },
        "variants": []  # wikt_sense 파이프라인으로 자동 채우기 권장
    })
```

#### Wiktionary + AI 파이프라인 사용 (권장)
```python
import sys
sys.path.insert(0, "<glossary_root>/bin")
from wikt_sense import fetch_and_process, _load_ai_env

word_stub = {"id": "<word>", "canonical_pos": "<pos>", "domain": "<domain>"}
ai_env = _load_ai_env()
url, result = fetch_and_process("<word>", word_stub, ai_env=ai_env)

if result and result.status == "ok":
    with GlossaryWriter() as gw:
        gw.add_word({
            "id": "<word>",
            "canonical_pos": result.selected_pos,
            "domain": "<domain>",
            "lang": {"en": "<word>", "ko": "<번역>"},
            "description_i18n": {"en": result.description_en},
            "variants": result.variants,
            "source_urls": [url],
        })
```

---

### Step 5 — 검증

```bash
python generate_glossary.py validate   # FATAL 0건 필수
python generate_glossary.py generate   # 인덱스 재생성
python generate_glossary.py check-id <new_identifier>  # [OK] 또는 [INFO] 확인
```

---

### Step 6 — 문서 업데이트

- `doc/change_log.md` 최상단에 추가 항목 기록
