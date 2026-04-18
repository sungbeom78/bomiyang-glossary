# 🚀 Glossary Migration & Canonical Consolidation Plan v1.0 (최종)

---

# 0. 목적

Glossary를 다음 상태로 만든다.

* 동일 의미는 하나의 canonical word로 통합
* 파생형/형태소 분리 방지
* dictionary 기반 관계 정보 확보
* From(어원 기반) 규칙을 이용한 canonical 정렬
* migration을 통해 기존 words.json 재정비

---

# 1. 핵심 원칙

## 1.1 Canonical 단일화

* 동일 의미 → word 1개만 유지
* 파생형/활용형 → variants 또는 relation으로 흡수

---

## 1.2 variants 유지 (중요)

* 현재 variants 구조 유지
* 역할:

  * 검색
  * 형태 선택 (동사/형용사 등)

---

## 1.3 relation 추가 (필수)

```json
"synonyms": [],
"antonyms": [],
"derived_terms": []
```

---

## 1.4 From 기반 canonical 우선 규칙 (핵심)

```json
"from": "active"
```

* `from`은 canonical 재정렬 기준
* 강제 기준이 아니라 **최우선 후보 기준**

---

# 2. words 최종 구조

```json
{
  "id": "activate",
  "domain": "system",
  "status": "active",
  "canonical_pos": "verb",

  "lang": {
    "en": "activate",
    "ko": "활성화하다"
  },

  "from": "active",

  "variants": [
    { "type": "past", "value": "activated" },
    { "type": "present_participle", "value": "activating" }
  ],

  "synonyms": ["enable", "trigger"],
  "antonyms": ["disable", "deactivate"],
  "derived_terms": ["activation", "activator", "reactivate"],

  "description_i18n": {
    "ko": "상태를 활성화하는 동작"
  },

  "source_urls": [
    "https://en.wiktionary.org/wiki/activate"
  ]
}
```

---

# 3. From 규칙 (핵심 로직)

## 3.1 의미

* `from` = 해당 word의 기반 단어 (base word)
* Wiktionary `From X + suffix`에서 추출

---

## 3.2 적용 규칙

### Rule A — canonical 후보

* `from` 값은 **canonical 상위 후보**
* 동일 의미일 경우 반드시 `from` 우선

---

### Rule B — canonical 재정렬

조건 만족 시:

* `activate → active`
* `activation → active`

처리:

* `active`를 canonical 유지/승격
* 나머지는 variants 또는 derived_terms로 이동

---

### Rule C — 신규 등록

migration 시:

* `from` 값 존재하면 반드시 추출
* glossary에 없으면 **신규 등록 후보 생성**

---

### Rule D — 강제 금지

아래 경우는 강제 merge 금지:

* 의미 다름
* domain 다름
* usage 다름

→ manual_review

---

# 4. migration 전체 흐름

---

## Step 1. Dictionary 조회

각 word에 대해:

* From (Etymology)
* synonyms
* antonyms
* derived_terms
* inflections

---

## Step 2. From 추출

패턴:

```text
From X + suffix
From plural of X
From past participle of X
```

결과:

```json
"from": "X"
```

---

## Step 3. From candidate pool 생성

* 모든 `from` 값 수집
* 중복 제거
* 별도 리스트 생성

```text
from_candidates = unique(all from values)
```

---

## Step 4. from word 보강

각 from 값에 대해:

* glossary 존재 여부 확인
* 없으면 신규 word 생성

```json
{
  "id": "active",
  "status": "pending"
}
```

---

## Step 5. Canonical 재정렬

각 word에 대해:

### 조건

* from 존재
* 의미 동일

### 처리

* from을 canonical로 설정
* 현재 word는:

  * variants 이동 OR
  * derived_terms 연결

---

## Step 6. variants 재구성

모든 형태소 통합:

* past
* ing
* plural
* noun_form
* abbreviation

---

## Step 7. relation 추가

```json
synonyms
antonyms
derived_terms
```

---

## Step 8. 중복 제거 (마지막 단계)

중요:

> **모든 작업 끝난 후 마지막에 수행**

### 기준

* 같은 의미
* 같은 from root
* 같은 domain

### 처리

* 하나만 남김
* 나머지는 merge

---

## Step 9. validation

* id unique
* from 존재 유효성
* relation id 존재 여부
* variants 중복 제거

---

## Step 10. projection 재생성

```bash
generate_glossary.py generate
```

---

# 5. canonical 선택 규칙

우선순위:

1. from 존재 시 from
2. glossary 기존 word
3. 가장 단순한 형태 (lemma)
4. domain 적합성

---

# 6. AI 판정 규칙

입력:

* 기존 glossary
* 신규 단어
* from 값
* 파일 경로

출력:

```text
reuse_from
reuse_existing
merge
new
manual_review
```

---

# 7. 절대 금지

❌ etymology tree 저장
❌ variants에 의미 관계 저장
❌ 동일 의미 word 여러 개 유지
❌ from 무시
❌ dictionary 결과 그대로 저장