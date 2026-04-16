# Glossary 통합 지침 v1.2
# (Abbreviation + Meaning/POS + pos_forms + Search Unified Policy)

## 문서 성격
이 문서는 Glossary 시스템의 핵심 관리 규칙을 통합한 최종 실행 지침이다.

본 버전(v1.2)은 기존 v1.1에 다음을 추가 반영한다.

1. `pos_forms` 도입 및 기존 words.json 전체 보강
2. 신규 단어 등록 시 `pos_forms` 기반 중복 방지
3. 검색 기능에서 `id + pos_forms` 동시 검색 강제
4. 웹/시스템 검색 인덱스 정책 추가

---

# 1. 핵심 원칙

## 1.1 Word-first, Concept-first
- 모든 관리는 word 기준으로 수행한다
- 품사가 아니라 개념(concept)을 기준으로 관리한다

## 1.2 Non-destructive
- 기존 값은 덮어쓰지 않는다
- 자동 보완은 추가/정리만 수행한다

## 1.3 Dictionary → Abbreviation → AI
모든 검증 및 보완은 아래 우선순위를 따른다.

1. Dictionary
2. Abbreviation API
3. AI fallback

---

# 2. 약어 처리 정책

## 2.1 약어는 variants로 관리한다

```json
"variants": [
  {
    "type": "abbreviation",
    "short": "oms",
    "long": "order_management_system",
    "abbreviation_meta": {
                           "confidence": "high | medium | low",
                           "source": "dictionary | abbreviation_api | ai | inferred",
                           "ambiguity": "low | medium | high"
                         }
  }
]
````

## 2.2 금지 구조

```json
"abbreviation": ["OMS"]
"abbreviation": { "long": [], "short": [] }
```

## 2.3 terms.json 약어 처리 및 source of truth

* terms.json에서도 동일한 variants projection 구조를 사용한다
* terms.json에만 존재하는 약어는 허용하지 않는다.
* 약어는 반드시 words 또는 compounds의 variants에서 정의되어야 하며,
terms.json에는 그 결과가 projection으로만 나타나야 한다.

예:
- `SL` → `stop_loss`
- `TP` → `take_profit`
- `BTS` → `beyond_the_sun`

즉, 약어의 source of truth는 terms.json이 아니라 words/compounds이다.

## 2.4 1글자 정책

* 1글자 word 금지
* 1글자 abbreviation 금지
* suffix라도 금지
* 예: `"m"` → 삭제 대상

## 2.5 terms 기반 약어 처리 (Detection 단계)

terms.json에만 존재하는 약어 형태가 발견될 수 있다.

이 경우 terms는 정의(source of truth)가 아니라
"후보 탐지(detection source)"로만 사용한다.

처리 방식:

1. 해당 약어를 "신규 후보"로 등록한다
2. 반드시 words 또는 compounds에 정의를 생성한다
3. terms.json에는 직접 반영하지 않는다

즉:

- terms → 후보 발견
- words/compounds → 실제 정의
- terms → 다시 projection

이 흐름을 반드시 유지한다.

---

중요:

terms.json에 존재하는 약어를 그대로 사용하는 것은 금지한다.
항상 words/compounds를 거쳐 재정의해야 한다.

## 2.6 약어 상태 필드를 추가한다.

- 애매한 약어도 등록 가능
- 대신 위험도 관리 가능
- 나중에 cleansing에서 자동 정리 가능

```json
"abbreviation_meta": {
  "confidence": "high | medium | low",
  "source": "dictionary | abbreviation_api | ai | inferred",
  "ambiguity": "low | medium | high"
}
```

---

# 3. 의미 / 품사 관리 정책

## 3.1 개념 기준 관리

Glossary는 품사 기준이 아니라 개념 기준으로 관리한다.

## 3.2 병합 기준

다음 조건을 만족하면 하나의 entry로 관리한다.

* 의미 동일
* domain 동일 또는 실질적으로 동일
* usage 동일
* `id` / `pos_forms` 기준으로 같은 lemma 계열

## 3.3 분리 기준

다음 중 하나라도 만족하면 분리한다.

* 의미 다름
* domain 다름
* 상태 / 행위 / 값 / 객체가 갈림

예:

* `close` = 종가 / 마지막 가격
* `closed` = 종료 상태

---

# 4. canonical_pos 정책

## 4.1 canonical_pos는 하나만 유지한다

대표 품사 하나만 유지한다.

## 4.2 선택 우선순위

여러 품사가 가능할 경우 아래 우선순위로 선택한다.

```text
noun > verb > adj > adv > proper > mixed > 기타
```

## 4.3 기존 데이터 처리

* 여러 entry가 병합될 경우 canonical_pos는 위 우선순위 기준으로 하나를 선택한다
* 기존 값이 유효하면 유지 가능하나, cleansing 시 일관성 우선

---

# 5. pos_forms 정책 (신규 핵심)

## 5.1 목적

`pos_forms`는 하나의 lemma/개념에 대해 품사별 형태를 관리하기 위한 구조다.

예:

```json
"pos_forms": {
  "noun": ["account", "accounts"],
  "verb": ["account", "accounts", "accounting", "accounted"]
}
```

## 5.2 데이터 소스

* dictionary API의 `sourceUrls`
* sourceUrls에서 조회 가능한 Etymology 정보
* Etymology에 나타나는 품사별 형태 정보

예:

* `Noun account (plural accounts)`
* `Verb account (third-person singular simple present accounts, present participle accounting, simple past and past participle accounted)`

## 5.3 적용 규칙

* 기존 words.json 전체에 대해 `pos_forms`를 채운다
* 신규 단어 등록 시 `pos_forms`를 반드시 함께 채운다
* pos_forms가 비어 있으면 enrich/cleanse 대상이다

## 5.4 저장 규칙

* 품사 키는 canonical schema 값과 맞춘다: `noun`, `verb`, `adj`, `adv`, `proper`, `mixed`
* 값은 배열로 저장한다
* 중복 제거
* 소문자 기준 normalize
* 1글자 토큰은 제외

## 5.5 pos_forms 중복 해석 원칙

pos_forms 확장 이후 동일 form이 여러 entry에서 발견될 수 있다.

이 경우 즉시 오류로 판단하지 않는다.
먼저 아래 두 가지를 구분한다.

1. 형태 중복 (form overlap)
   - 같은 lemma 또는 굴절형이 여러 entry에 걸쳐 나타나는 경우
   - 허용 가능
   - cleansing 및 병합 후보 탐지 대상으로만 본다

2. 개념 중복 (concept duplication)
   - 실제 의미/도메인/용도가 같은데 entry가 중복된 경우
   - 정리 대상
   - 병합 후보로 처리한다

즉, pos_forms 중복은 곧바로 금지하지 않고,
개념 중복인지 여부를 기준으로 판단한다.

---

# 6. description_i18n 정책

## 6.1 배열 금지

`description_i18n`은 배열을 사용하지 않는다.

```json
"description_i18n": {
  "ko": "..."
}
```

## 6.2 생성 규칙

1. dictionary의 첫 번째 definition 사용
2. 길어도 그대로 유지 가능
3. dictionary 실패 시 AI가 하나 선택
4. 구현 설명이 아니라 개념 설명을 사용

## 6.3 금지

* 여러 개념을 한 description에 혼합
* 배열로 의미를 여러 개 저장
* 기존 값 덮어쓰기

---

# 7. 신규 단어 등록 정책 (강화)

## 7.1 신규 단어 등록 전 중복 확인

신규 단어 추가 시 아래를 모두 확인한다.

1. `words.id`에 동일 항목이 없는지
2. 기존 `pos_forms` 안에 동일 형태가 없는지
3. variants.abbreviation에 동일 short/long 매핑이 이미 존재하는지
4. terms projection에서만 존재하는 약어를 신규 source로 삼지 않는지
즉:

* `id` 중복 확인 필수
* `pos_forms` 중복 확인 필수

## 7.1.1 약어 처리 예외 규칙

약어는 일반 단어와 동일한 수준의 사전 기반 중복 검증을 강제하지 않는다.

이유:
- 약어는 다중 의미를 가지며
- 도메인 및 맥락에 따라 의미가 달라질 수 있기 때문이다

따라서 약어는 다음과 같이 처리한다:

1. 신규 등록은 허용한다
2. 대신 아래 분류 정보를 반드시 추가한다:
   - domain
   - description
   - (가능한 경우) abbreviation mapping

3. 중복 여부는 등록 시 차단하지 않고,
   cleansing 및 validation 단계에서 후보로 처리한다

## 7.2 등록 흐름

1. dictionary API 검색
2. sourceUrls 조회
3. Etymology에서 품사별 형태 추출
4. 기본 정보 채움
5. `pos_forms` 채움
6. canonical_pos 선택
7. words.json 등록

## 7.3 중복 판정

다음 중 하나면 신규 등록 금지 또는 병합 후보 처리:

* 동일 `id`
* 동일 lemma
* 동일 form이 기존 `pos_forms`에 포함됨

---

# 8. 데이터 정리 (Cleansing) 정책

## 8.0 선행 작업

cleansing의 첫 단계는 기존 words.json 전체에 대해 pos_forms를 보강하는 것이다.

순서:
1. dictionary API 조회
2. sourceUrls 확보
3. sourceUrls의 Etymology에서 품사별 형태 추출
4. 모든 기존 word에 pos_forms 반영
5. 그 이후에 병합 후보 / 삭제 후보 / canonical_pos 정리를 수행

즉, pos_forms 보강은 cleansing의 일부가 아니라 cleansing의 선행 조건이다.

## 8.1 전체 words.json 검수 필요

다음 항목을 전수 점검한다.

### 제거 대상

* 1글자 word
* 의미 불명
* dictionary/AI 모두 실패
* pos_forms 없이 중복 존재하는 항목

### 병합 후보

* 같은 lemma 계열
* 의미 동일
* domain 실질 동일
* pos_forms 기준 동일 군집

### 분리 유지

* 의미 다름
* domain 다름
* 상태/행위/값/객체 구분 명확

## 8.1.1 중복 판단 보충

pos_forms 기준 중복이 탐지되더라도 자동 병합하지 않는다.
중복은 병합 후보 신호로만 사용하며,
최종 판단은 개념 동일성(meaning/domain/usage) 기준으로 수행한다.

## 8.2 약어 정리

* 기존 abbreviation 필드 제거
* variants 기반으로 변환

## 8.3 canonical_pos 정리

* 병합 시 우선순위 기준으로 하나만 남긴다

---

# 9. 검색 정책 (신규 핵심)

## 9.1 시스템 검색

시스템 검색 기능은 최소한 아래를 동시에 검색해야 한다.

* `id`
* `pos_forms.*`

즉, 단어 찾기(search word)는 `id + pos_forms` 기반이다.

## 9.2 웹 검색

웹 검색은 가능한 모든 필드를 검색 대상으로 한다.

검색 대상:

* `id`
* `domain`
* `status`
* `lang.*`
* `description_i18n.*`
* `canonical_pos`
* `pos_forms.*`
* `variants.*`
* `sourceUrls`
* `created_at`
* `updated_at`
* `deprecated_at`

## 9.3 인덱싱

검색 성능을 위해 인덱싱이 필요하다.

### 시스템용 인덱스

* `id_index`
* `pos_form_index`
* `lemma_index`

### 웹용 인덱스

* full-text 스타일 검색용 flattened index
* 모든 searchable field를 normalize한 문자열 인덱스

---

# 10. 운영 정책

## 10.1 자동 보완

```bash
python bin/enrich_items.py
```

## 10.2 검증

```bash
python glossary/generate_glossary.py validate
```

## 10.3 cleansing

words.json 전체에 대해 정기적 cleansing 수행

## 10.4 약어 검증 정책

약어는 strict validation 대상이 아니다.

검증 시:

- 중복 발견 → ERROR가 아니라 WARN
- ambiguity → WARN
- 의미 불명 → WARN

약어 관련 오류는 차단이 아니라
후속 정리 대상(signal)로 취급한다

---

# 11. 최종 선언

Glossary는 단어 사전이 아니라 개념 시스템이다.

* 약어는 의미 매핑이다
* 품사는 대표값 하나만 가진다
* 모든 형태는 pos_forms로 관리한다
* 신규 등록은 id와 pos_forms 모두 중복 검사를 거친다
* 검색은 id만이 아니라 pos_forms까지 포함해야 한다

````

---

# 2. words.json 자동 cleansing 스크립트 설계

```md
# words.json 자동 cleansing 스크립트 설계
# (Design for Automated words.json Cleansing)

## 문서 성격
이 문서는 words.json을 자동 정리(cleanse)하기 위한 스크립트 설계 문서다.

목표는 다음과 같다.

1. 기존 words.json의 품사/형태/중복 문제를 정리한다
2. pos_forms를 전체 항목에 보강한다
3. 같은 단어 계열을 병합 후보로 식별한다
4. 이후 신규 등록 시 품질 저하를 방지한다

---

# 1. 스크립트 목표

자동 cleansing 스크립트는 다음을 수행한다.

1. 기존 words.json 전체 스캔
2. 각 word에 대해 dictionary/sourceUrls/Etymology 조회
3. `pos_forms` 생성
4. 동일 lemma/형태 기반으로 병합 후보 탐지
5. canonical_pos 정규화
6. description 보강 후보 탐지
7. 삭제/병합/유지 결과를 리포트화

---

# 2. 스크립트 형태

## 추천 파일명
```text
bin/cleanse_words.py
````

## 실행 예시

```bash
python bin/cleanse_words.py --dry-run
python bin/cleanse_words.py --apply
```

---

# 3. 동작 모드

## 3.1 dry-run

* 파일 수정 없음
* 병합 후보 / 삭제 후보 / 보강 후보 리포트 출력
* JSON patch 또는 report 파일 생성

## 3.2 apply

* 승인된 규칙에 따라 words.json 반영
* 백업 파일 생성 후 적용

---

# 4. 입력 / 출력

## 입력

* `dictionary/words.json`

## 보조 입력

* dictionary API
* sourceUrls
* Etymology
* abbreviation API
* AI fallback

## 출력

* 수정된 `words.json`
* 리포트 파일 예:

```text
tmp/cleansing/words_cleansing_report_YYYYMMDD_HHMM.json
```

---

# 5. 처리 단계

## Step 1. words 로드

* 전체 words.json 로드
* id 기준 맵 생성
* 기초 validation 수행

## Step 2. 전체 pos_forms 보강

기존 words.json의 모든 entry에 대해 dictionary/sourceUrls/Etymology를 조회하여
pos_forms를 먼저 채운다.

이 단계가 완료되기 전에는
병합 후보 탐지, 중복 판단, canonical_pos 정규화를 수행하지 않는다.

예:

```json
"pos_forms": {
  "noun": ["account", "accounts"],
  "verb": ["account", "accounts", "accounting", "accounted"]
}
```

## Step 3. 노이즈 탐지

다음 항목 탐지:

* 1글자 id
* 숫자 포함 이상치
* invalid canonical_pos
* 중복 의미 의심 항목

## Step 4. lemma / form 인덱스 생성

* `id -> entry`
* `form -> [entry_ids]`
* `lemma_group -> [entry_ids]`

## Step 5. 병합 후보 탐지

다음 조건이면 병합 후보:

* 동일 form 공유
* description 유사
* domain 동일 또는 유사
* 같은 lemma 계열

## Step 6. 분리 유지 판정

다음이면 분리 유지:

* description 차이 큼
* domain 차이 큼
* state / value / action / object 구분 명확

예:

* close / closed → 분리 유지

## Step 7. canonical_pos 정규화

병합 시 대표 canonical_pos를 선택:

```text
noun > verb > adj > adv > proper > mixed
```

## Step 8. description 보강

* 비어 있으면 dictionary 첫 번째 definition 사용
* 실패 시 AI fallback
* 기존 값은 덮어쓰지 않음

## Step 9. 리포트 생성

리포트 항목:

* keep
* merge_candidate
* remove_candidate
* invalid_candidate
* enriched
* updated_pos_forms

---

# 6. 병합 규칙

## 병합 대상

* 같은 lemma 계열
* pos_forms 공유
* 의미/도메인 실질 동일

## 병합 방법

* 대표 entry 1개 선택
* 나머지는 제거 후보 또는 deprecated 후보로 표시
* merged source를 리포트에 남김

## 대표 entry 선택 기준

1. id가 lemma 원형에 가까운 것
2. domain이 더 일반적인 것
3. canonical_pos 우선순위가 높은 것
4. description이 더 명확한 것

---

# 7. 삭제 규칙

## 삭제 후보

* 1글자 id
* dictionary/AI 모두 실패
* description 없음 + 의미 불명
* pos_forms 생성 불가
* variants/abbreviation 구조 위반

## 주의

즉시 삭제하지 말고 dry-run에서는 `remove_candidate`로만 표시한다.

---

# 8. 검색 인덱스 생성

스크립트는 cleansing 후 검색용 인덱스를 함께 만들 수 있다.

## 8.1 시스템용

```json
{
  "id_index": {...},
  "pos_form_index": {...},
  "lemma_index": {...}
}
```

## 8.2 웹용

모든 필드를 flatten한 searchable text index 생성

---

# 9. 신규 단어 등록과의 연결

신규 단어 추가 시, 동일 로직을 재사용해야 한다.

즉 신규 등록 전에:

1. id 중복 검사
2. pos_forms 중복 검사
3. lemma 그룹 충돌 검사

신규 등록 로직과 cleansing 로직은 가능한 한 같은 helper를 공유한다.

---

# 10. helper 함수 권장

## 추천 함수

* `fetch_dictionary_entry(word)`
* `fetch_source_urls(word)`
* `extract_etymology_pos_forms(url)`
* `build_pos_forms(entry, etymology)`
* `select_canonical_pos(pos_forms)`
* `detect_merge_candidates(entries)`
* `detect_remove_candidates(entries)`
* `build_search_indices(entries)`

---

# 11. 예외 처리

## dictionary 실패

* WARN
* AI fallback

## sourceUrls 실패

* WARN
* dictionary meanings만 사용

## etymology 파싱 실패

* WARN
* pos_forms 일부만 채움

## AI 실패

* WARN
* 기존 값 유지

---

# 12. 검증 기준

스크립트 실행 후 아래를 만족해야 한다.

* words.json validate PASS
* 1글자 id 제거 후보 식별 완료
* pos_forms 전체 보강 완료 또는 보강 불가 리포트 완료
* 중복 후보 리포트 생성
* 검색 인덱스 생성 가능

---

# 13. 최종 권장 흐름

```text
cleanse_words --dry-run
→ report 검토
→ 승인
→ cleanse_words --apply
→ generate_glossary validate
→ generate_glossary generate
```

---

# 14. 최종 선언

이 스크립트의 목적은 단순 정리가 아니다.

words.json을

* 단어 목록
  에서
* 개념 + 형태 + 검색 가능한 어휘 시스템
  으로 바꾸는 것이다.

```

---

# 정리

이번 버전의 핵심은 이거다.

- `pos_forms`를 전체 words에 채운다
- 신규 등록 때도 `pos_forms`를 함께 채운다
- 신규 등록 전에 `id`와 `pos_forms`를 함께 중복 검사한다
- 검색도 `id`만이 아니라 `pos_forms`까지 포함한다