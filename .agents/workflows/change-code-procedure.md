---
description: Glossary 데이터 수정 절차 — 이 워크플로우는 glossary 서브모듈 내에서만 동작한다.
             어떤 main 프로젝트에서 사용해도 동일하게 적용된다.
---

# Glossary 코드 변경 절차

> 이 파일은 glossary 서브모듈 자체의 변경 절차를 정의한다.
> main 프로젝트의 change-code-procedure.md와 **별개**로 관리된다.

## Source of Truth
이 절차가 참조하는 규칙 소스:
- `doc/README_AI_GUIDELINE.md` — glossary 핵심 규칙 및 Frozen Zone
- `doc/module_index.md` — 모듈 책임 및 금지행위
- `doc/glossary_rule.md` — 단어/복합어 등록 정책
- `doc/change_log.md` — 변경 이력 (glossary 전용)

---

## §DATA — 데이터 파일 수정 (words.json / compounds.json)

> words.json / compounds.json을 **직접 write하는 것은 금지**. 반드시 GlossaryWriter를 사용.

### 수정 전 확인

- [ ] 직접 write(words_path.write_text, json.dump 등)를 사용하려 하는가?
  - ✅ YES → `core/writer.py`의 `GlossaryWriter` 사용 필수. 직접 write 금지.
  - ❌ NO (read-only) → 통과

### GlossaryWriter 사용 규칙

```python
# ✅ 올바른 방법
import sys
sys.path.insert(0, "glossary")  # 또는 서브모듈의 절대 경로
from core.writer import GlossaryWriter

with GlossaryWriter() as gw:
    gw.add_word({"id": "example", "canonical_pos": "noun", ...})
    gw.update_word("example", {"lang": {"ko": "예시"}})
    gw.add_word_variant("example", "plural", "examples")
    gw.add_compound({"id": "example_case", ...})
# with 블록 종료 시 자동 save() + backup 생성

# ❌ 금지
words_path.write_text(...)            # 절대 금지
json.dump(data, open(path, "w", ...)) # 절대 금지
```

### 레거시 파일 (점진적 통합 대상)
> 아래 파일들은 직접 write를 사용하는 레거시. 수정 시 GlossaryWriter로 전환 권장.
> **신규 작성은 반드시 GlossaryWriter 사용.**
- `bin/fix_*.py` — 정합성 수정 스크립트
- `bin/migrate_*.py` — 마이그레이션 스크립트
- `bin/batch_items.py` — 배치 처리

---

## §VALIDATE — 변경 후 필수 검증

// turbo-all

### 데이터(words.json / compounds.json) 변경 시
1. `python generate_glossary.py validate` → **FATAL 0건** 필수
2. `python generate_glossary.py generate` → 정상 생성 확인
3. 식별자 추가/변경 시: `python generate_glossary.py check-id <identifier>` → ERROR 없음 확인

### 코드(*.py) 변경 시
1. `python -m py_compile <수정파일>` — 문법 검증
2. `python generate_glossary.py validate` — 데이터 정합성 유지 확인

---

## §IDENTIFIER — 신규 식별자 등록 절차

> 새로운 식별자(파일명, 클래스, 함수, 변수 등)를 만들기 전에 반드시 수행.

1. `python generate_glossary.py check-id <new_identifier>` 실행
2. `[ERROR] 미등록` 출력 시 → **개발 즉시 중단**
3. 미등록 단어 → `/new-identifier-procedure` 워크플로우에 따라 등록 신청
4. 승인 후 개발 재개

---

## §DOCS — 변경 후 문서 업데이트 의무

// turbo-all
1. `doc/module_index.md` — 모듈/클래스/파일 추가·변경 시 업데이트
2. `doc/change_log.md` — 모든 의미 있는 변경 후 **최상단**에 항목 추가 (APPEND, 덮어쓰기 금지)

### change_log.md 형식
```
## YYYY-MM-DD HH:MM:SS
### Added / Modified / Fixed / Removed
- 설명
- File: path/to/file.py
### Notes
- (선택) 후속 작업 또는 주의사항
```

---

## §FAILURE — 실패 시 처리

| 단계 | 실패 유형 | 조치 |
|------|-----------|------|
| `py_compile` | 문법 오류 | 즉시 수정 후 재시도 |
| `validate` FATAL | 데이터 정합성 오류 | 오류 분석 → 수정 → validate 재실행 |
| `validate` 2회 연속 실패 | 반복 실패 | 즉시 중단, 현황 보고 |
| GlossaryWriter.validate() 실패 | 저장 전 사전 검증 실패 | rollback() 호출, 수동 수정 후 재시도 |
