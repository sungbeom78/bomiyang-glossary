## [2026-04-14 14:22:08]
### Modified
- Glossary_Refactoring_Plan_v1.2_extra_01.md 에 정의된 abbreviation (약어) 스키마 변경 및 정책 반영
- schema 내 `variants.abbreviation` 타입을 string 배열 형태로 변경 및 기존 words.json 마이그레이션 (`cfg` 단어 제거 등)
- `generate_glossary.py` 내 `variant_map.json` 생성 로직 추가 및 `check-id` 명령에서 약어 파싱·매핑(WARN, JSON 출력 구조 등) 정책 적용
- 독립 word로 존재하는 단어와 약어가 겹치는 conflicts (start, stop 등) 해소
- File: schema/word.schema.json
- File: schema/compound.schema.json
- File: dictionary/words.json
- File: dictionary/compounds.json
- File: generate_glossary.py
### Notes
- 약어는 필수 필드가 아니되, 존재하는 경우 variants.abbreviation(또는 abbr)으로 관리되며, check-id 시 base concept으로 자동 normalize되도록 개선됨.
- cfg, sl, rpt 등 독립 word 배제 규칙 V-202 FATAL 검증 완료.

## [2026-04-14 13:38:00]
### Modified
- `scan_terms.py` 스캐너가 기존 `words.json`, `compounds.json` 내 데이터를 읽을 때 v1.2 체계에 맞게 `canonical_pos`, `lang`, `variants`를 파싱하도록 수정
- 웹 UI (`index.html`) 상의 병합 도구에서 AI가 추출한 임시 파일(`terms_*.json`)을 승인할 때, v1.2 규격의 Sparse 객체 형태로 조립되어 저장되도록 `doMergeProcessed`, `openWordForm`, `saveWord`, `wFilter`, `renderWords` 등 폼/테이블 구조 전면 교체
- File: bin/scan_terms.py
- File: web/index.html
### Notes
- 빈 객체나 배열을 보내지 않도록 강제. UI 상에서 데이터 시각화가 v1.2를 완벽하게 준수

## [2026-04-14 13:08:00]
### Added / Modified
- `words.json` 내 전 단어를 대상으로 `ja`, `zh_hans` (일본어, 중국어 간체) 필드 번역 및 일괄 추가 완료
- `banned.json` 및 `banned.schema.json` 파일 v1.2 체제(3.3절) 맞춤 리팩토링 (`reason_i18n` 다국어 확장, `severity` 필드 추가)
- `generate_glossary.py` 로직이 새로운 `banned` 객체 형식 처리하도록 수정 (Context 병합)
- File: dictionary/words.json
- File: dictionary/banned.json
- File: schema/word.schema.json
- File: schema/compound.schema.json
- File: schema/banned.schema.json
- File: generate_glossary.py
### Notes
- 커스텀 번역 스크립트(`bin/translate_lang_gtx.py`) 작성을 통해 GoogleTranslate 무인증 엔드포인트를 호출하여 총 235단어 자동 번역 수행.
- Sparse 특성 검사 및 `generate`/`validate`/`check-id` 검증 완료.

## [2026-04-14 12:16:00]
### Added / Modified
- Glossary_Refactoring_Plan_v1.2.md에 따른 Sparse JSON 스키마 적용 및 리팩토링 진행
- `words.json`, `compounds.json` 데이터를 v1.2 스키마에 맞게 마이그레이션하는 스크립트 작성 (lang, variants, description_i18n 분리 및 canonical_pos 적용)
- `generate_glossary.py` 내 Index(`word_min.json`, `compound_min.json`) 생성 기능 추가 및 `check-id` 명령의 Index 기반 조회 전환
- `generate_glossary.py` 의 V-104 검증 규칙을 강화하여 복합어 `words` 참조 검증 및 순환 참조(Circular Reference) 예방 추가
- File: schema/word.schema.json
- File: schema/compound.schema.json
- File: bin/migrate_v1_2.py
- File: generate_glossary.py
- File: dictionary/words.json
- File: dictionary/compounds.json
### Notes
- `terms.json`을 직접 의존하는 외부 스크립트(web/server.py 등)와의 하위호환을 위해 Phase 4 완료시까지 `terms.json` 자동 생성을 유지함.
- `reason`, `not` 필드는 컴파운드의 특수한 데이터로 판단하여 삭제하지 않고 Sparse한 속성으로 유지함.

## [2026-04-14 02:22:28]
### Modified
- 병합 대상 파일(`terms_*.json`) 파싱 시 대용량 배열의 렌더링 지연 속도를 시각화 및 최적화
- File: web/index.html
### Notes
- `selectBatchFile()` 함수에 `requestAnimationFrame`을 적용하여 1,000건 이상의 용어도 브라우저 멈춤 없이 Chunk 단위(40건)로 생성하도록 수정
- 화면 상단에 `<수치/전체수 (진행률%)>` 형식으로 "화면 생성 중" 상태를 실시간 수치화하여 표시

## [2026-04-14 02:04:53]
### Added / Modified
- 용어 배치 추출(병합 UI)에 사용자 선택 승인(Drafts) 로직 및 AI 기반 복합어 분절 자동화 탑재
- `dictionary/drafts.json` 데이터 계층 신설 (FIFO 100건 제한)
- 웹 UI에 '보류 (Drafts)' 탭 신설 및 병합 모달 뷰 대규모 개편 (구성 단어의 의미/주석을 직접 입력할 수 있는 표 형태 내장)
- `batch_terms.py`의 `SYSTEM_PROMPT` 업데이트를 통해 복합어 추출 및 누락 상태의 기본 단어 추출(plural 대응 포함) 지원
- File: web/server.py
- File: web/index.html
- File: bin/batch_terms.py
### Notes
- 2초 이내 렌더링 성능 요건에 맞게 UI 랜더링 시 동적 AI 호출을 피하고, 배치 단계에 선제적 텍스트 완성 모델을 포함하도록 개선.

## [2026-04-13 23:59:42]
### Fixed
- `load_existing_terms` 함수의 반환값이 3개로 변경됨에 따라 발생하는 unpacking ValueError 수정 (`n_patterns` 추가)
- File: bin/batch_terms.py
### Notes
- `TermScanner` 초기화 시 `n_patterns` 옵션 전달 추가
