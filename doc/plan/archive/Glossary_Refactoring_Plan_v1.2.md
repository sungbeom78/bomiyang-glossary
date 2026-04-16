# Glossary System Management Plan v1.2
# (Concept-Based Normalization & AI-Agent Optimized)

## 1. 개요 및 목적
본 문서는 개발팀과 AI 코딩 어시스턴트(Cursor, Claude 등)가 프로젝트 전반에서 **동일한 비즈니스 언어**를 사용하도록 보장하는 용어 관리 표준 지침이다. 흩어진 단어들을 '개념(Concept)' 단위로 통합하여 코드 네이밍의 일관성을 확보하고, 다국어 환경 확장에 유연하게 대응하는 것을 목적으로 한다. **본 레포지토리는 타 프로젝트의 서브모듈(Submodule)로 동작하며, 현재는 내부 구조 변경 및 정규화 작업에 집중한다.**

## 2. 핵심 설계 원칙

### 2.1 개념 중심 정규화 (Normalization)
* **Root ID 중심 관리:** 표면적인 단어(Word)가 아닌 고유한 비즈니스 개념(`id`)을 엔트리의 최상위 기준으로 삼는다.
* **Variants 통합:** `report`(명사), `reports`(복수), `reporting`(동명사) 등을 별도 등록하지 않고, `report`라는 ID 하위의 `variants` 속성으로 통합 관리한다.

### 2.2 Sparse JSON (희소 저장 원칙)
* **최소 저장:** 값이 없는 필드는 `null`이나 `""`, `[]`로 저장하지 않고 필드 자체를 생략(Omit)한다. 이는 파일 크기를 줄이고 AI의 컨텍스트 해석 효율을 높인다.
* **필수 필드 강제:** `id`, `lang.en`, `domain`, `status`, `canonical_pos` 5개 항목은 시스템 안정성을 위해 반드시 포함한다.

### 2.3 데이터 이원화 (Source vs Index)
* **Source (dictionary/*.json):** 사람이 편집하는 원본 파일. 상세한 설명과 메타데이터를 포함한다.
* **Index (build/index/*.json):** AI 에이전트나 배포 도구가 읽는 최적화 파일. 주석과 비필수 필드를 제거하여 토큰 소모를 최소화한다.

---

## 3. 상세 데이터 규격 (Schema)

### 3.1 Word Entry 구조 (단일 개념)
| 필드명 | 타입 | 필수 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | string | **Y** | kebab-case 기반 고유 식별자 (예: `order-status`) |
| `domain` | string | **Y** | 비즈니스 영역 (예: `trading`, `common`, `auth`) |
| `status` | string | **Y** | 생명주기 (`active`, `deprecated`). **하드 삭제 대신 사용.** |
| `canonical_pos`| string | **Y** | 대표 품사 (`noun`, `verb`, `adj`, `adv`). 네이밍 규칙의 기준. |
| `lang` | object | **Y** | 언어별 표기명. `en`은 필수, `ko`, `ja` 등은 선택. |
| `variants` | object | N | 파생 형태 (아래 3.4의 Enum 규격 준수) |
| `description_i18n`| object | N | 언어별 상세 정의. AI가 맥락을 이해하는 핵심 데이터. |

### 3.2 Compound Entry 구조 (복합 용어)
| 필드명 | 타입 | 필수 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | string | **Y** | kebab-case 기반 고유 식별자 |
| `words` | string[] | **Y** | 구성 단어 ID 배열 (참조 무결성 검증 대상) |
| `lang` | object | **Y** | 언어별 표기명 (`en` 필수) |
| `domain` | string | **Y** | 비즈니스 영역 |
| `abbr` | object | N | 약어 (`long`, `short`) |
| `description_i18n`| object | N | 언어별 상세 정의 |

### 3.3 Banned Entry 구조 (금지 표현)
| 필드명 | 타입 | 필수 | 설명 |
| :--- | :--- | :--- | :--- |
| `expression` | string | **Y** | 사용을 금지할 문자열 또는 패턴 |
| `lang` | string | N | 특정 언어에 국한된 경우 ISO 코드 명시 |
| `correct` | string | N | 권장되는 대체 용어 또는 ID |
| `reason` | string | **Y** | 금지 사유 (예: 오해 소지, 비표준) |
| `severity` | string | **Y** | 위반 강도 (`error`: 빌드 차단, `warn`: 경고) |

### 3.4 Variant Enum 정의
AI 에이전트가 변체(Variant)를 오인하지 않도록 아래의 표준 Enum 값을 사용한다.
* **Core Variants:** `plural`, `verb`, `past`, `past_participle`, `present_participle`, `agent`, `abbreviation`
* **Optional Variants:** `adjective`, `adverb`, `alias`, `misspelling`, `singular`, `noun_form`, `verb_form`

### 3.5 다국어 처리 표준
* **표준 코드:** ISO 639-1 표준을 준수한다 (`ko`, `en`, `ja`, `zh_hans`, `zh_hant`).
* **Fallback:** 특정 언어 데이터가 없을 경우 `en` -> `id` 순으로 참조하도록 시스템을 구성한다.

---

## 4. 품질 관리(QA) 및 검증 규칙

개발 프로세스(CI/CD)에서 다음 규칙을 자동 검증하여 데이터 오염을 방지한다.

* **V-101 (Unique ID):** `id`는 전체 사전에서 유일해야 하며, `variants`에 등록된 단어가 다른 엔트리의 `id`와 중복될 수 없다.
* **V-102 (Naming Standard):** `id`는 소문자 kebab-case만 허용하며, 특수문자 사용을 금지한다.
* **V-103 (No Hard Delete):** 한 번 사용된 용어는 삭제하지 않고 `status: deprecated`로 전환하여 과거 데이터/코드와의 연결성을 유지한다.
* **V-104 (Reference Integrity):** 복합어(Compound) 구성 시 사용된 단어 ID가 실제로 `words.json`에 존재하는지 검사한다.
* **V-105 (Atomic Deployment):** 배포 시 원자적 교체 및 실패 시 자동 롤백을 보장하여 시스템 중단이나 불완전한 데이터 로딩을 방지한다.

---

## 5. AI 에이전트 활용 지침

이 지침의 최종 목적은 AI가 코드를 더 잘 짜게 만드는 것이다.

1.  **Context Injection:** AI(Claude/Cursor)에게 질문할 때 `build/index/word_min.json`의 내용을 시스템 프롬프트나 참고 문서로 제공한다.
2.  **Naming Consistency:** 새로운 함수나 클래스를 생성할 때 사전에 정의된 `canonical_pos`와 `id`를 조합하도록 지시한다.
    * *예: `report` (ID) + `status` (ID) -> `getReportStatus()` (CamelCase 변환)*
3.  **Variant Auto-Mapping:** 사용자가 "보고서 행위자"라고 입력하면 AI가 `variants.agent`에서 `reporter`를 찾아내어 코딩에 반영하게 한다.

---

## 6. 운영 리스크 관리

* **용어 충돌 리스크:** 서로 다른 도메인에서 같은 단어를 다른 의미로 쓸 경우, `id`에 도메인 접두사를 붙여 분리한다 (예: `trading:order` vs `system:order`).
* **과도한 세분화 방지:** 너무 지엽적인 단어까지 사전에 등록하면 유지보수 비용이 상승한다. 프로젝트 전반에서 3회 이상 재사용되는 용어 위주로 등록할 것을 권고한다.

---

## 7. 결론
v1.2 지침은 **"데이터는 엄격하게, 활용은 유연하게"**라는 원칙을 따른다. 과도한 프로그래밍 제약보다는 **데이터 무결성(QA Rules)**과 **AI 가독성(Sparse JSON)**에 집중함으로써, 개발자가 복잡한 설정 없이도 일관된 고품질의 코드를 생산할 수 있는 환경을 제공한다.

---

## 부록: 단계적 마이그레이션 로드맵
1.  **Phase 1 (Dual-Support):** 신규 스키마를 적용하되, 기존 필드(`ko`, `en`, `plural`)를 호환 필드로 유지 (Schema v0.4-beta).
2.  **Phase 2 (Conversion):** 자동 변환 스크립트를 통해 원본 JSON을 `lang` 및 `variants` 구조로 일괄 리팩토링.
3.  **Phase 3 (Index Shift):** `generate_glossary.py`를 수정하여 Runtime Index 생성을 활성화하고, `check-id` 로직을 인덱스 기반으로 전환.
4.  **Phase 4 (Deprecation):** Legacy 필드 지원을 완전히 중단하고 신규 QA 규칙을 엄격 적용.