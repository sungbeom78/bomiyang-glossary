# 🔥 결론 (먼저)

## 1. 약어는 어디에 속하나?

👉 **Concept(= root) 기준 + variant로 관리 (정답)**

## 2. 약어는 필수 속성인가?

👉 **❌ 필수 아님 / ⭕ “존재 시 필수 수준으로 관리”**

---

# 🧠 왜 “필수”가 아니냐 (중요)

### ❌ 모든 개념에 약어가 있는 건 아니다

* `order` → 없음
* `risk` → 없음
* `log` → 없음

👉 강제하면:

* 의미 없는 약어 생성됨
* 품질 급락

---

### ⭕ 대신 이렇게 가야 한다

👉 **“약어가 존재하는 개념은 반드시 등록해야 한다”**

---

# 📄 Glossary Abbreviation Policy v0.1 (최종 지침)

👉 이거 그대로 md로 써도 된다

---

````md
# Glossary Abbreviation Policy v0.1

> 목적: BOM_TS Glossary에서 약어(abbreviation)를 일관되게 관리하기 위한 기준 정의

---

# 1. 핵심 원칙 (Core Principles)

## 1.1 Concept 기반

- 약어는 단어(word)가 아니라 **개념(concept)의 표현이다**
- 모든 약어는 반드시 root concept에 종속된다

---

## 1.2 Variant 통합

- 약어는 variant의 한 종류이다

```json
"variants": {
  "abbreviation": ["rpt"]
}
````

---

## 1.3 독립 word 금지

❌ 금지:

```json
{"id": "rpt"}
```

⭕ 허용:

```json
"report": {
  "variants": {
    "abbreviation": ["rpt"]
  }
}
```

---

# 2. 적용 범위

## 2.1 단일 개념 (word)

```json
{
  "id": "report",
  "variants": {
    "abbreviation": ["rpt"]
  }
}
```

---

## 2.2 복합 개념 (compound)

```json
{
  "id": "stop_loss",
  "abbr": {
    "short": "SL",
    "long": "STOP_LOSS"
  }
}
```

---

# 3. 필수성 규칙

## 3.1 기본 원칙

* 약어는 **필수 필드가 아니다**

---

## 3.2 강화 규칙 (중요)

다음 조건을 만족하면 반드시 등록해야 한다:

### RULE A — 도메인 표준 약어

| 개념          | 약어 |
| ----------- | -- |
| stop_loss   | SL |
| take_profit | TP |
| fx_futures  | FX |

---

### RULE B — 시스템에서 실제 사용되는 약어

* ENV 변수
* API 필드
* DB 컬럼

---

### RULE C — 반복적으로 사용되는 축약 표현

예:

* rpt (report)
* cfg (config)

---

👉 위 조건 충족 시:

**abbreviation 등록은 필수**

---

# 4. Naming 규칙

## 4.1 식별자 생성 시

* 약어 사용은 제한적으로 허용

GOOD:

* report_log
* order_queue

조건부:

* rpt_log (ENV, API 등 제한적)

---

## 4.2 ENV / API 규칙

약어는 다음 영역에서 적극 사용 가능:

* ENV 변수
* API response
* 외부 인터페이스

---

# 5. check-id 처리 규칙

## 5.1 입력 처리

```text
input: rpt_log
```

처리:

* rpt → report (abbreviation)
* log → log

결과:

```json
{
  "normalized": ["report", "log"],
  "variant": ["abbreviation"]
}
```

---

## 5.2 검증 정책

| 상황              | 결과    |
| --------------- | ----- |
| root 존재         | OK    |
| abbreviation 사용 | WARN  |
| root 없음         | ERROR |

---

# 6. Validation 규칙

## FATAL

* abbreviation이 word로 독립 존재
* abbreviation → root 매핑 없음

---

## WARN

* 약어 존재하지만 미등록
* 약어 중복 정의

---

# 7. Runtime Index

## variant_map.json

```json
{
  "rpt": {"root": "report", "type": "abbreviation"},
  "SL": {"root": "stop_loss", "type": "abbreviation"}
}
```

---

# 8. Migration 전략

## Step 1

* 기존 abbr 필드 → variants.abbreviation 이동

## Step 2

* rpt, sl 등 단독 word 제거

## Step 3

* compound abbr 유지

---

# 9. 금지 사항

* 약어를 독립 word로 등록
* 의미 없는 약어 생성
* root 없는 약어 사용

---

# 10. 결론

👉 약어는 optional 필드가 아니다

👉 “존재할 경우 반드시 정의해야 하는 필드”다

---

# 11. 한 줄 정의

👉 abbreviation = concept의 또 다른 이름이다

```

---

# 🔥 채친 최종 코멘트

너가 던진 질문 이거 👇

> "약어 필수 아니냐?"

👉 이건 설계 감각 제대로 들어온 질문이다

---

# 💥 진짜 핵심

| 잘못된 생각 | 올바른 생각 |
|------------|------------|
| 모든 개념에 약어 필요 | ❌ |
| 약어 있으면 반드시 등록 | ⭕ |

---

# 🚀 다음 단계 추천 (진짜 중요)

이제 순서:

1. **abbreviation 정책 반영**
2. **variant_map 생성 (abbr 포함)**
3. **check-id 엔진 구현**