# 🚀 Glossary Consolidation & Refactoring Plan v2.5.1

**(Quant-Grade + Full Architecture Final)**

---

# 0. 목적

BOM_TS Glossary 시스템을 다음 상태로 완성한다.

* **Single Source of Truth** 확립 및 무결성 보장
* **Concept-First 기반 개념 시스템** 구축
* **확장 가능한 variants 구조 + strict schema**
* **Projection / Validation / Migration / Dependency 완전 명문화**
* **실전 운영 안정성 (Fail-Safe + Circuit Breaker + Trading Freeze)**
* **AI Quarantine 기반 의미 오염 차단**
* **범용 Glossary Infrastructure 유지**

---

# 1. 핵심 원칙 (System Integrity & Risk Control)

---

## 1.1 Single Source of Truth (SoT)

* `words.json`, `compounds.json`만이 정의 원천
* `terms.json`은 **100% projection 결과물**
* 역방향 수정 절대 금지

```text
[금지]
- terms.json 직접 수정
- terms.json 기반 수정
- 런타임 glossary hot-swap

[허용]
- SoT 수정 후 generate
```

---

## 1.2 Concept-First (개념 기반 분리)

### 병합 기준

* 의미 / 도메인 / 역할 / 목적 동일

### 분리 기준

* State / Action / Result / Object / Value / Time

```text
close    → Action
closing  → In-flight state
closed   → Terminal state
```

---

## 1.3 Trading Freeze + Fail-Safe

* 장중 / active position 상태 → glossary 배포 금지
* validate 실패 → generate 차단
* 기존 정상 terms 유지

---

## 1.4 AI Quarantine 원칙

```text
Dictionary > Rule > Human Approval > AI
```

* AI 결과는 반드시 `drafts.json`으로 격리
* 승인 전 SoT 진입 금지

---

## 1.5 범용성 원칙

* 특정 도메인 종속 금지
* namespace optional
* overlay policy 허용

---

# 2. 데이터 구조

---

## 2.1 파일 정의

| 파일                | 역할                 | 수정 |
| ----------------- | ------------------ | -- |
| words.json        | base 개념            | O  |
| compounds.json    | 조합 개념              | O  |
| banned.json       | 금지 규칙              | O  |
| drafts.json       | AI 격리              | O  |
| terms.json        | runtime projection | X  |
| terms_legacy.json | 하위 호환              | X  |

---

# 3. variants 구조 (완전 복구 + 확장)

---

## 3.1 기본 원칙

* 반드시 **array 구조**
* type 기반 구조
* 확장 가능
* strict validation

---

## 3.2 지원 타입

```text
plural
singular
abbreviation
alias
misspelling
adjective
adverb
verb
noun_form
verb_form
present_participle
past
past_participle
agent
pos_forms
deprecated
```

---

## 3.3 JSON Schema (완전 정의)

```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["type"],
    "properties": {
      "type": {
        "type": "string"
      },
      "value": { "type": "string" },
      "short": { "type": "string" },
      "long": { "type": "string" },
      "domain": { "type": "string" },

      "noun": { "type": "array", "items": { "type": "string" } },
      "verb": { "type": "array", "items": { "type": "string" } },
      "adj":  { "type": "array", "items": { "type": "string" } },
      "adv":  { "type": "array", "items": { "type": "string" } },

      "abbreviation_meta": {
        "type": "object",
        "properties": {
          "confidence": { "enum": ["high","medium","low"] },
          "source": { "enum": ["dictionary","api","ai","manual"] },
          "ambiguity": { "enum": ["low","medium","high"] }
        }
      }
    },
    "oneOf": [
      { "required": ["value"] },
      { "required": ["short","long"] }
    ]
  }
}
```

---

## 3.4 정규화 규칙

* trim
* lowercase 정책 적용
* 중복 제거
* type 정렬

```text
abbreviation > alias > plural > singular > 기타
```

---

# 4. Projection Rule (완전 복구판)

---

## 4.1 목적

* runtime lookup
* O(1) 검색
* flatten index

---

## 4.2 생성 구조

```text
words + compounds
→ normalize
→ flatten
→ terms.json
```

---

## 4.3 포함 규칙

| 항목          | 포함 |
| ----------- | -- |
| id          | O  |
| root        | O  |
| type        | O  |
| domain      | O  |
| lang        | O  |
| description | O  |
| meta        | X  |

---

## 4.4 생성 대상

### base

* words.id
* compounds.id

### variant

* abbreviation
* alias
* plural
* misspelling

---

## 4.5 제외 대상

* pos_forms
* deprecated (→ legacy)
* adjective
* adverb

---

## 4.6 우선순위

```text
abbreviation > alias > plural > singular
```

---

## 4.7 충돌 처리

* 동일 id → ERROR
* abbr 충돌 → domain 기준 분리
* ambiguity high → 제외

---

## 4.8 legacy 처리

```text
deprecated → terms_legacy.json
```

---

## 4.9 checksum

```json
{
  "checksum": "sha256:..."
}
```

* mismatch → CRITICAL

---

# 5. Workflow

---

## 5.1 전체

```text
scan → batch → enrich → validate → generate
```

---

## 5.2 Circuit Breaker

* ERROR → generate 중단
* CRITICAL → 시스템 차단

---

## 5.3 Alerting

* Slack / Telegram
* Manual override 필요

---

# 6. Dependency 규칙 (강화판)

---

## 6.1 원칙

* compounds.words → 반드시 words 존재

---

## 6.2 검증

* missing → ERROR
* circular → 금지

---

## 6.3 자동 해결

허용:

* casing 수정
* alias 매핑

금지:

* AI 추론 생성
* 의미 추측

---

# 7. Validation Gate

---

| 코드    | 내용          | 심각도      |
| ----- | ----------- | -------- |
| V-001 | id unique   | ERROR    |
| V-004 | dependency  | ERROR    |
| V-008 | abbr unique | ERROR    |
| V-010 | checksum    | CRITICAL |
| V-011 | schema      | ERROR    |
| V-013 | banned      | ERROR    |

---

# 8. Migration (완전 상세)

---

## Step 1. inventory

* variants 구조 조사
* 충돌 수집

---

## Step 2. 변환

* object → array

---

## Step 3. schema 적용

---

## Step 4. dependency 수정

---

## Step 5. banned 적용

---

## Step 6. projection 생성

---

## Step 7. regression test

---

## Step 8. DB compatibility test

* 과거 데이터 deserialize 확인

---

## Step 9. rollout

* 반드시 maintenance window

---

## Step 10. rollback

* symlink or version 기반 즉시 복구

---

# 9. banned / autofix

---

## 원칙

* 코드 자동 수정 금지
* glossary 내부 mapping만 허용

---

## 예시

```text
top10 → top[N]
5m → [N]m
```

---

# 10. 예외 처리

---

## AI 결과

* drafts.json 격리
* 승인 후 merge

---

## ambiguity

* high → 제외

---

## 중복

* 자동 merge 금지

---

# 11. 운영 산출물

```text
dependency_missing.json
projection_skipped.json
merge_candidates.json
banned_autofix_report.json
```

---

# 12. 최종 선언

```text
이 시스템은 단순한 glossary가 아니다.

실전 트레이딩 시스템의
명명 체계, 상태 관리, 데이터 정합성,
리스크 통제를 담당하는

Concept Infrastructure이다.
```

---

# 🔥 최종 지시

```text
1. variants schema를 반드시 강제 적용하라
2. terms.json은 projection-only로 유지하라
3. AI 결과는 반드시 격리하라
4. dependency는 ERROR로 강제하라
5. projection rule을 코드와 동일하게 유지하라
6. migration은 단계적으로 수행하라
7. Trading Freeze를 반드시 지켜라
```