---
description: glossary 명령 자동 실행 안전 정책 — validate/generate/check-id는 자동 승인, write는 GlossaryWriter 경유 필수.
---

# Glossary Safe Command Policy

> 이 파일은 glossary 서브모듈 내의 명령 실행 자동 승인 정책을 정의한다.
> main 프로젝트의 safe-command-policy와 **별개**로 관리된다.

---

## Grade A — 항상 자동 실행 허용 (SafeToAutoRun: true)

아래 명령은 read-only이거나 안전한 빌드 산출물 생성이며, 데이터를 변경하지 않는다.

| 명령 패턴 | 비고 |
|-----------|------|
| `python generate_glossary.py validate` | 읽기 전용 검증 |
| `python generate_glossary.py generate` | 빌드 산출물 생성 (dictionary/*.json은 건드리지 않음) |
| `python generate_glossary.py check-id <id>` | 읽기 전용 식별자 조회 |
| `python -m py_compile <file>` | 문법 검사 |
| `python -c "import json; ..."` | 인라인 데이터 조회 |
| `Get-Content <file>` | 파일 읽기 |

---

## Grade B — 조건부 자동 실행 (SafeToAutoRun: false, 확인 후 실행)

데이터를 변경하지만 GlossaryWriter를 사용하거나 백업이 자동 생성되는 경우.

| 명령 패턴 | 조건 |
|-----------|------|
| `python <script>.py` (GlossaryWriter 사용 확인된 스크립트) | 백업 자동 생성 시 허용 |
| `python generate_glossary.py migrate` | 데이터 변경 → 사용자 확인 필요 |

---

## Grade C — 절대 자동 실행 금지 (항상 사용자 승인 필요)

| 명령 패턴 | 이유 |
|-----------|------|
| `words_path.write_text(...)` 직접 호출 | GlossaryWriter bypass로 금지 |
| dictionary/*.json 직접 수정 (vim, notepad 등) | 정합성 보장 불가 |
| `git reset --hard`, `git clean -fd` | 복구 불가 |
| DB 삭제/초기화 명령 | 비가역적 |

---

## 원칙

1. **read-only = 자동 허용**: 파일을 읽기만 하는 명령은 항상 자동 실행.
2. **GlossaryWriter = 안전**: `core/writer.py`를 사용하는 스크립트는 backup이 자동 생성되므로 실행 안전.
3. **직접 write = 금지**: dictionary 파일을 GlossaryWriter 없이 직접 수정하는 명령은 실행 금지.
