# Glossary 개선 지침 v0.3
## (plural root cleanup finalization)

---

## 1. 배경

약어 규칙 개선(v0.2) 작업을 통해 다음은 이미 정리되었다.

- `terms.json`에서 임의의 `abbr_short`, `abbr_long` 자동 생성 제거
- 약어 source를 `word.variants.abbreviation` 및 `compound.abbr`로 단일화
- `terms.json` 내 variant 엔티티에 `root`와 `variant_type` 부여
- 웹 UI, 배치 프롬프트, 스캔 로직의 legacy 약어 필드 의존 제거

이제 남은 구조 리스크는 **복수형이 root key로 등록된 기존 word들**이다.

예:
- `candidates`
- `categories`
- `colors`

이 상태를 그대로 두면 glossary의 핵심 철학인
- root = concept
- plural = variant
원칙이 깨진다.

따라서 v0.3의 목표는 다음 하나로 정리된다.

> **words.json의 root를 단수형으로 정렬하고, 복수형은 variants.plural 또는 terms 파생 엔티티로 내린다.**

---

## 2. 목표

### 2.1 최종 상태

모든 `word root`는 다음 조건을 만족해야 한다.

1. root id는 **단수형 concept**이다
2. 복수형 표현은 `variants.plural`에 위치한다
3. `terms.json`에는 복수형 term이 존재할 수 있으나, 반드시 단수형 root를 가리킨다
4. `check-id`는 plural 입력을 단수 root로 normalize 한다

---

## 3. 절대 원칙

### RULE 1 — root는 concept 단위다
- `candidate`는 가능
- `candidates`는 root로 금지

### RULE 2 — plural은 variant다
- `variants.plural`로만 관리한다

### RULE 3 — terms는 파생물이다
- `terms.json`은 source of truth가 아니다
- plural term이 terms에 존재하는 것은 허용하지만, root를 반드시 가진다

### RULE 4 — legacy plural root는 모두 정리 대상이다
- “기존에 쓰고 있으니 유지” 금지
- 이미 정의가 틀어져 있으면 지금 바로 바로잡는다

---

## 4. 작업 범위

### 4.1 대상 파일
- `dictionary/words.json`
- `dictionary/terms.json` (자동 생성물)
- `generate_glossary.py`
- `word.schema.json`
- 필요 시 `scan_terms.py`
- 필요 시 `batch_terms.py`
- 필요 시 `web/index.html` 표시 로직

### 4.2 이번 단계에서 수정하지 않는 것
- 다국어 번역 품질 자체
- banned 표현 대규모 재정비
- compound 등록 기준 재설계
- abbreviation 정책 재변경

---

## 5. 실제 변경 지침

### 5.1 words.json 정리 규칙

#### 기존 잘못된 구조
```json
{
  "id": "candidates",
  "domain": "general",
  "lang": {
    "en": "candidates",
    "ko": "후보들"
  },
  "canonical_pos": "noun"
}
```

#### 변경 후 구조
```json
{
  "id": "candidate",
  "domain": "general",
  "status": "active",
  "lang": {
    "en": "candidate",
    "ko": "후보",
    "ja": "候補",
    "zh_hans": "候选"
  },
  "canonical_pos": "noun",
  "variants": {
    "plural": ["candidates"]
  }
}
```

#### 적용 원칙
- root id를 단수형으로 변경
- `lang.en`도 단수형으로 정리
- 한국어 표현도 가능하면 단수 개념 중심으로 정리
- `variants.plural`에 기존 복수형 추가
- 복수형 root 항목은 제거

---

### 5.2 terms.json 생성 규칙 변경

`terms.json`은 자동 생성물이므로 직접 수정하지 않는다.

#### base term 예시
```json
{
  "id": "candidate",
  "source": "word"
}
```

#### plural term 예시
```json
{
  "id": "candidates",
  "source": "word",
  "root": "candidate",
  "variant_type": "plural"
}
```

#### 원칙
- base term 1개 + plural variant term 1개
- plural term은 반드시 `root` 보유
- plural term이 독립 concept처럼 보이면 안 됨

---

### 5.3 generate_glossary.py 수정 포인트

#### 필수 수정
1. `words.json`의 `variants.plural`을 읽어 plural variant term을 배출
2. base term과 variant term을 명확히 구분
3. root 없는 variant term 생성 금지
4. 기존 plural root 감지 시 validate 또는 migration warning 추가

#### 권장 추가
- `stats` 출력 시 plural variant 개수 집계
- `check-id` 결과에 “plural normalized” 정보 표시

---

### 5.4 check-id 규칙 보강

입력:
```text
candidates_log
```

처리:
1. tokenize → `["candidates", "log"]`
2. variant lookup → `candidates -> candidate (plural)`
3. normalize → `["candidate", "log"]`
4. validate → OK + warning/info

예시 결과:
```json
{
  "input": "candidates_log",
  "normalized": ["candidate", "log"],
  "variants_detected": ["plural"],
  "valid": true,
  "warnings": ["plural variant normalized to root"]
}
```

#### 원칙
- plural은 사용 금지가 아니라 **정규화 대상**
- 그러나 신규 식별자 생성 시에는 root 사용을 권장
- plural을 그대로 root처럼 쓰는 설계는 금지

---

### 5.5 schema 수정

현재 variants 하위의 다수 필드가 string으로 선언된 부분은 array 기반으로 통일하는 것이 바람직하다.

#### 권장 방향
```json
"variants": {
  "type": "object",
  "properties": {
    "plural": {
      "type": "array",
      "items": {"type": "string"}
    },
    "abbreviation": {
      "type": "array",
      "items": {"type": "string"}
    },
    "agent": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

#### 이유
- plural이 1개라고 가정해도 array가 더 일관적
- abbreviation은 이미 array 성격
- 향후 irregular plural / alias / multiple abbreviations 확장에 유리

---

## 6. validate 규칙 추가/보강

### 신규 FATAL 권장

#### V-301 — plural root 금지
- `words.json`에 복수형 root가 존재하면 실패
- 예: `candidates`, `categories`, `colors`

#### V-302 — plural variant root 누락 금지
- plural term 또는 plural mapping이 존재하는데 root가 없으면 실패

#### V-303 — singular/plural self-conflict 금지
- root가 `candidate`인데 plural에 `candidate` 등록 금지

### 신규 WARN 권장

#### V-351 — noun인데 plural 미정의
- 모든 noun에 plural이 반드시 필요한 것은 아니지만,
- countable noun이면 plural 검토 필요

#### V-352 — ko 표현이 집합 표현으로만 남아 있음
- 예: “후보들”, “색상들”
- 개념 단위 표현으로 정리 권장

---

## 7. Migration 순서

### Step 1. plural root 탐지
- `words.json` 전체에서 root가 복수형으로 보이는 항목 탐지
- 예시 목록 수집 후 검토

### Step 2. 단수형 root 생성/치환
- `candidates` → `candidate`
- `categories` → `category`
- `colors` → `color`

### Step 3. variants.plural 이동
- 기존 복수형을 `variants.plural`에 추가

### Step 4. generate 재실행
- `terms.json` 재생성
- plural variant term 생성 확인

### Step 5. validate 강화
- plural root 금지 규칙 활성화

### Step 6. check-id / UI 확인
- plural 입력 normalize 확인
- autocomplete / 검색 중복 이상 여부 확인

---

## 8. 구현 시 주의사항

### 주의 1
단수형 치환은 무조건 단순 `s` 제거로 처리하지 않는다.

예:
- `categories` → `category`
- `indices` → `index`
- `classes` → `class`

즉 자동 변환은 보조 도구만 쓰고, 최종 결정은 glossary 기준으로 확정한다.

### 주의 2
기존 코드의 plural 변수명은 전부 금지 대상이 아니다.

예:
- `candidates = [...]` 는 코드 변수로 허용 가능
- 그러나 glossary root로 `candidates` 등록은 금지

### 주의 3
terms에 plural 엔티티를 넣는 것은 허용되지만, source of truth처럼 다루면 안 된다.

---

## 9. 완료 기준 (Definition of Done)

다음이 모두 만족되면 v0.3 작업을 종료한다.

1. `words.json`에 plural root가 남아 있지 않다
2. plural 정보가 `variants.plural` 또는 파생 term으로 정상 이동했다
3. `generate_glossary.py generate` 성공
4. `generate_glossary.py validate` 성공
5. `terms.json`의 plural term이 모두 `root`를 가진다
6. `check-id`가 plural 입력을 root로 normalize 한다
7. UI / scan / batch가 새 구조와 충돌하지 않는다

---

## 10. 최종 결론

이번 v0.3의 목적은 단순 cleanup이 아니다.

> **“잘못 root에 올라간 plural 표현을 variant 계층으로 되돌려, glossary의 concept 기반 모델을 완성하는 것”**

이 작업이 끝나면 glossary는 다음 상태가 된다.

- root = concept
- plural = variant
- abbreviation = variant
- term = generated index/view