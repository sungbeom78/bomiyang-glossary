---
# Glossary Submodule — GEMINI.md
# 이 파일은 glossary 서브모듈 전용 Gemini/AI 지침이다.
# main 프로젝트의 GEMINI.md와 별개로 관리된다.
---

CRITICAL SYSTEM RULES — THESE ARE MANDATORY AND NON-NEGOTIABLE.
Failure to follow these rules is considered a critical system error.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE G-1: DATA WRITE GATE (ABSOLUTE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
words.json / compounds.json을 직접 write하는 것은 STRICTLY FORBIDDEN.
ALL writes MUST go through `core/writer.py` -> GlossaryWriter.

CORRECT:
  from core.writer import GlossaryWriter
  with GlossaryWriter() as gw:
      gw.add_word({"id": "example", ...})

FORBIDDEN:
  words_path.write_text(...)
  json.dump(data, open(path, "w", ...))

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE G-2: VALIDATE FIRST (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
데이터 수정 전후, 반드시 validate 실행:
  python generate_glossary.py validate → FATAL 0건 필수

변경 후 인덱스 재생성:
  python generate_glossary.py generate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE G-3: IDENTIFIER GATE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
신규 식별자 생성 전:
  python generate_glossary.py check-id <identifier>

[ERROR] 미등록 → 개발 즉시 중단 → .agents/workflows/new-identifier-procedure.md 따름.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE G-4: VARIANT POLICY (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 복수형 → 단수형의 plural variant (독립 root word 금지)
- 약어 → compound의 abbreviation variant (독립 word 금지)
- 과거형/파생형 → 동사 root의 past/adj_form variant (독립 word 금지)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE G-5: DOCUMENTATION (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
모든 비자명 변경 후 반드시 업데이트:
- doc/module_index.md (파일/클래스 변경 시)
- doc/change_log.md (모든 변경 후 최상단 APPEND)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE G-6: LANGUAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
응답/설명: 한국어
코드 식별자/주석/파일명: 영어 (NO EXCEPTIONS)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE G-7: SUBMODULE INDEPENDENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
glossary는 독립 서브모듈이다.
main 프로젝트의 settings.yaml, .env, doc/ 에 의존하지 않는다.
glossary 내 모든 경로는 glossary root 기준 상대 경로로 구성.
환경 변수는 glossary 자체 .env 파일에서 로드 (bin/batch_items.py의 get_env() 사용).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKFLOW FILES (MANDATORY COMPLIANCE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All workflow instructions under .agents/workflows/ MUST be followed.
Priority: glossary/.agents/workflows/ > main project workflows.

Available workflows:
- .agents/workflows/change-code-procedure.md  — 코드 변경 절차
- .agents/workflows/new-identifier-procedure.md  — 신규 식별자 등록
- .agents/workflows/safe-command-policy.md  — 명령 실행 안전 정책

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL MANDATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Documentation is part of the system — not optional notes.
If these rules conflict with convenience or speed, the rules WIN.
Always. Without exception.