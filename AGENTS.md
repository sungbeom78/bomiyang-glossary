# AGENTS.md — glossary submodule

> 이 파일은 glossary 서브모듈 전용 AI 에이전트 지침이다.
> 어떤 main 프로젝트에 연결되어도 **이 파일 내의 규칙이 우선** 적용된다.
> main 프로젝트의 AGENTS.md 중 glossary와 충돌하는 규칙은 이 파일이 override한다.

---

## 0. 서브모듈 독립 원칙

- glossary는 독립 Git 저장소이며 **자체 완결형** 지침으로 관리된다.
- main 프로젝트의 설정 파일(settings.yaml, .env 등)에 의존하지 않는다. 시스템의 절대/상대 경로 하드코딩을 절대 금지하며 호출하는 메인 모듈로부터 인자로 주입받아야 한다.
- glossary 내 작업은 이 AGENTS.md와 `.agents/workflows/` 를 Single Source of Truth로 삼는다.

> **[ABSOLUTE RULE]**
> 어떤 작업을 하던 다음 원칙은 무조건 지켜져야 합니다:
> ***Glossary is the single source of truth for naming across systems.***

---

## 1. 문서 우선 원칙 (MANDATORY)

코드 수정 전, 아래 순서로 문서를 반드시 확인한다:

1. `doc/README_AI_GUIDELINE.md` — 핵심 규칙 및 Frozen Zone
2. `doc/glossary_rule.md` — 단어/복합어 등록 정책
3. `doc/module_index.md` — 모듈 책임 및 금지행위
4. `doc/change_log.md` — 최근 변경 이력 확인

---

## 2. 데이터 수정 규칙 (ABSOLUTE — 절대 위반 금지)

### words.json / compounds.json 직접 write 금지

모든 데이터 수정은 반드시 `core/writer.py`의 `GlossaryWriter`를 통해야 한다.

```python
# ✅ 올바른 방법
import sys
sys.path.insert(0, ".")   # glossary root
from core.writer import GlossaryWriter

with GlossaryWriter() as gw:
    gw.add_word({"id": "example", "canonical_pos": "noun", ...})
    gw.add_compound({"id": "example_case", ...})
# with 블록 종료 시 자동 save + backup

# ❌ 금지
words_path.write_text(...)             # 절대 금지
json.dump(data, open(path,"w",...))    # 절대 금지
```

### 변경 후 필수 검증 순서

```bash
python generate_glossary.py validate   # FATAL 0건 필수
python generate_glossary.py generate   # 인덱스 재생성
```

---

## 3. 식별자 명명 규칙

- 신규 식별자 생성 전: `python generate_glossary.py check-id <identifier>` 실행
- `[ERROR] 미등록` → 개발 중단 → `.agents/workflows/new-identifier-procedure.md` 따름
- Wiktionary + AI 파이프라인(`bin/wikt_sense.py`)으로 단어 정보 자동 보완 권장

---

## 4. 코드 변경 절차

`.agents/workflows/change-code-procedure.md` 참조.

요약:
1. 수정 전: `doc/` 문서 검토
2. 수정 중: `/edit-file-procedure` 워크플로우 준수
3. 수정 후: `validate` → `generate` → `doc/` 업데이트

---

## 5. 명령 자동 실행 정책

`.agents/workflows/safe-command-policy.md` 참조.

핵심 원칙:
- **read-only 명령**: 항상 자동 실행 허용 (validate, generate, check-id)
- **GlossaryWriter 경유 스크립트**: 자동 실행 허용 (backup 자동 생성)
- **직접 write**: 절대 금지

---

## 6. 문서 업데이트 의무

비자명 코드 변경 후 반드시 업데이트:

| 파일 | 주기 |
|------|------|
| `doc/module_index.md` | 모듈/클래스/파일 추가·변경 시마다 |
| `doc/change_log.md` | 모든 의미 있는 변경 후 최상단에 추가 (APPEND 전용) |

---

## 7. 언어 규칙

- 응답/설명: **한국어**
- 코드 식별자(변수, 함수, 클래스, 파일명): **영어**
- 코드 주석: **영어**
- 문서 파일명: **영어**

---

## 8. 단일 연산 원칙 및 설계 제약 사항 (SSOC & Determinism)

- **SSOC (Single Source of Computation)**: 배열의 길이, 필터 카운트 등 파생 가능한 값은 별도의 변수로 분리저장하지 않고 원본 Collection에서 직접 연산한다.
- **결정론 (Determinism)**: 동일 입력 시 항상 동일한 반환값을 가지도록 구성해야 한다. 환경 변수와 하드코딩된 값에 기반하여 암묵적인 분기를 생성해서는 안된다.
- **외부 종속성 차단**: glossary의 모든 코드(검증 로직 포함)는 `os.environ` 또는 `config/settings.yaml` 처럼 특정 애플리케이션 종속적 상태 요소에 접근하면 안된다.

---

## 9. Auto 모드 등록 정책 (`batch_items.py --register-mode auto`)

아래 토큰은 노이즈로 간주하여 자동 등록 제외:
- 길이 1~2자 토큰
- 숫자 포함 토큰
- 특수문자 포함 토큰
- 식별자 분해 과정에서 생성된 비의미론적 토큰

일반 영어 단어라도 실제 시스템에서 반복 사용되는 단어만 등록 대상.

---

## 9. Frozen Zone

아래 파일은 수정 전 사용자 명시적 승인 필요:
- `dictionary/words.json` — 직접 write 금지, GlossaryWriter 경유 필수
- `dictionary/compounds.json` — 직접 write 금지, GlossaryWriter 경유 필수
- `dictionary/banned.json` — 금지어 목록, 임의 수정 금지
- `generate_glossary.py` 의 `PROJECTION_VARIANT_TYPES` — 변경 시 terms.json 생성 결과에 큰 영향

---

## 10. 완료 기준 (COMPLETION CONTRACT)

작업 완료는 아래 조건이 모두 충족되어야 한다:

| # | 조건 | 증거 |
|---|------|------|
| 1 | 구현 완료 | 코드 존재, placeholder 없음 |
| 2 | validate PASS | `[OK] FATAL 없음` 출력 |
| 3 | generate PASS | terms.json 정상 생성 확인 |
| 4 | 문서 업데이트 | module_index.md, change_log.md 갱신 |
