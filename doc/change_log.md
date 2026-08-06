# Glossary Change Log

## [2026-08-03 21:40:00]
### Added
- 사용자 승인과 G-0 유사어 검토에 따라 기존 코드 식별자 `force_threshold`의 누락 root `threshold`를 general noun으로 등록.
- `limit`(한도/지정가), `boundary`(구간 경계), `trigger`(실행 조건)는 수치 비교 기준값과 의미가 달라 대체하지 않음.
- `GlossaryWriter` 저장 후 projection/index를 재생성.

### Verification
- `python generate_glossary.py validate` FATAL 0.
- `python generate_glossary.py check-id force_threshold` PASS.

## [2026-07-31 21:34:00]
### Fixed
- 미등록 식별자 감사가 외부 Dictionary API 상태에 따라 승인되거나 장시간 대기하던 비결정적 경로를 제거하고 로컬 glossary만 SoT로 사용.
- `GlossaryWriter` 추가 시 기존 레거시 순서를 전체 재정렬하지 않고 삽입 지점만 결정하며, JSON 최종 LF를 보장.
- projection generator가 `terms.json`/`terms_legacy.json` 생성 후에도 최종 LF를 보장.
- 서브모듈 루트와 main project 루트 모두에서 test import가 동일하게 동작하도록 테스트 경로를 고정.
- File: core/auditor.py
- File: core/writer.py
- File: generate_glossary.py
- File: test/conftest.py
- File: test/test_token_rules.py
- File: test/test_writer.py

### Verification
- 수정 전 full identifier audit가 외부 API poll에서 3분 이상 대기함을 재현.
- 수정 후 targeted test, validate, generate, standalone/root 테스트로 검증.

## [2026-07-31 12:04:00]
### Added
- 사용자 승인에 따라 기존 알림 식별자 `notify_activity`가 외부 Dictionary API 가용성에 의존하지 않도록 `activity`를 system noun으로 등록.
- `GlossaryWriter`를 통해 저장하고 projection/index를 재생성.
- File: dictionary/words.json
- File: dictionary/terms.json
- File: dictionary/terms_legacy.json
- File: GLOSSARY.md

### Verification
- `python generate_glossary.py validate` FATAL 0.
- `python generate_glossary.py check-id notify_activity` PASS.

## [2026-07-31 11:40:00]
### Fixed
- 외부 Dictionary API의 단일 타임아웃을 미등록 단어로 확정하고 실패 결과까지 LRU 캐시에 저장해 이후 감사가 계속 FATAL 처리되는 문제를 수정.
- HTTP 오류, 200 응답 JSON 오류, 404 이외 상태를 최대 3회 재시도하고 네트워크 실패 결과는 캐시하지 않도록 변경.
- 실제 404와 품사 부적합 응답은 기존처럼 미등록으로 판정해 naming gate를 약화하지 않음.
- File: core/token_rules.py
- File: test/test_token_rules.py
- File: doc/module_index.md

### Verification
- 수정 전 재시도·실패 캐시 회귀 테스트 2 FAIL.
- 수정 후 `pytest test/test_token_rules.py` 2 PASS.
- `python generate_glossary.py validate` FATAL 0.

## [2026-04-21 11:54:00]
### Fixed / Modified
- `web/server.py`의 `_inject_metadata` 함수에 존재하던 대소문자 정규화 로직이 fallback으로만 동작하여, `GlossaryWriter` 사용 시 정규화가 누락되는 "로직 이중화" 문제를 해결.
- `core/writer.py`에 `_normalize_entry` 헬퍼 함수를 추가하여 모든 `add_`/`update_` 연산 시 `id`, `lang`, `variants`, `abbreviation` 등을 소문자로 일괄 정규화하도록 중앙화.
- `web/server.py`에서 불필요하게 이중화된 소문자 정규화 로직 삭제.
- `dictionary/words.json`에 대문자로 잘못 등록된 `MB`를 `mb`로 수정.
- File: `core/writer.py`, `web/server.py`, `dictionary/words.json`

## 2026-04-19 15:35:00
### Modified - Refactored README files for generic usage
- Removed specific project references (e.g. BomTS) to make the Glossary submodule a generic naming enforcement tool.
- Restructured all README files (`README.md`, `README.ko.md`, `README.ja.md`, `README.zh.md`) to have a unified architecture and concepts.
- Added latest features (GlossaryWriter, wikt_sense.py pipeline, Variants instead of isolated words).
- Replaced legacy `.env` scan configuration instructions with `.scan_list` and `.scan_ignore`.
- Radically simplified the Korean README (`README.ko.md`) to match the structural flow of other languages.
- File: `README.md`, `README.ko.md`, `README.ja.md`, `README.zh.md`

## [2026-04-21 10:52:10]
### Fixed
- Updated `core/auditor.py` warning policy for targeted code audits:
- abbreviation variant warnings are now limited to strict naming surfaces (`module/class/db_table/db_column/env_key/config_key`)
- collection-semantic warnings are disabled for current parser-produced runtime identifier kinds
- numeric pattern checks are limited to strict naming surfaces

### Verification
- `python -m py_compile core/auditor.py` -> PASS
- `python ../script/operation/audit_identifiers.py --files src/notification/notification_event.py src/notification/notification_bridge.py src/notification/notification_history.py src/notification/notification_engine.py src/notification/notification_service.py src/notification/system_notifier.py src/notification/trade_notifier.py src/notification/command_router.py src/app.py run.py src/execution/orchestrator.py src/storage/redis_client.py` -> PASS (`WARN=0`)

## [2026-04-21 10:03:20]
### Fixed
- Resolved glossary validation blockers (`V-202`, `V-301`, and missing dependency word in `home_trading_system`).
- Applied user-approved message-system terminology registration so targeted identifier audit no longer returns fatal errors.
- Regenerated projection/index artifacts after dictionary updates.

### Changed Files
- `dictionary/words.json`
- `dictionary/terms.json`
- `build/index/word_min.json`
- `build/index/compound_min.json`
- `build/index/variant_map.json`

### Data flow impact
- No trading/runtime data flow change. Impact is limited to glossary validation/projection and identifier-audit resolution behavior.

### Verification
- `python generate_glossary.py validate` -> PASS (`FATAL=0`)
- `python generate_glossary.py generate` -> PASS
- `python ../script/operation/audit_identifiers.py --files src/notification/notification_event.py src/notification/notification_bridge.py src/notification/notification_history.py src/notification/notification_engine.py src/notification/notification_service.py src/notification/system_notifier.py src/notification/trade_notifier.py src/notification/command_router.py src/app.py run.py src/execution/orchestrator.py src/storage/redis_client.py ../lib_test/test_notification_engine.py` -> WARN (`FATAL=0`, `ERROR=0`)

> Archive: 이전 기록은 `doc/change_log_archive/202604_change_log.md` 참조

---

## [2026-04-20 16:33:00]
### Modified — AI 초안 입력 UX 개선 (v2)

#### 목적
AI 초안 입력 동작이 애매하다는 피드백을 받아 UI/UX를 명확하게 개선.

#### 변경 내용

**`web/index.html` (MODIFY)**

1. **마스터 체크박스 → 전체 선택/해제**
   - `ai-draft-chk` 체크박스 클릭 시 모든 `mc{i}` 체크박스 일괄 체크/해제
   - `DOMContentLoaded` 핸들러 로직 교체 (버튼 표시 제어 → mc토글)
   - 파일 렌더링 완료 시 마스터 체크된 경우 `mc{i}` 전체 체크 (자동실행 제거)

2. **RUN 버튼 항상 표시, 체크된 항목만 처리**
   - `ai-draft-run-btn`: `display:none` 제거 → 항상 표시 (`btn-ac` 스타일)
   - 텍스트: `"▷ AI 초안 실행"` → `"▷ RUN"`
   - `runAiDraftForAll()` 완전 삭제 → `runAiDraftForChecked()` 로 교체
   - `runAiDraftForChecked()`: 체크된 `mc{i}` 항목만 순회하여 AI 초안 실행
   - 미체크 항목은 "보류" 상태 유지

3. **항목별 AI 상태 배지 표시**
   - 각 행의 "발견: n회" 와 miniDesc 스팬 사이에 `<span id="ai-status-{i}">` 배지 추가
   - 초기값: `보류` (회색 pill 스타일)
   - RUN 실행 후: `…` (진행 중, 파란색) → `성공` (녹색) / `실패` (빨간색)
   - `fillAiDraft`: 성공 시 배지 `성공`으로 업데이트
   - `runAiDraftForChecked`: 실패 시 배지 `실패`로 업데이트

#### Verification
- `verify_ai_v2.py` → 9개 항목 ALL PASS
- `python -m py_compile web/server.py` → PASS (server.py 변경 없음)

#### Affected Files
- `web/index.html` (MODIFY: 마스터 체크박스, RUN 버튼, 상태 배지, runAiDraftForChecked)

---


### Added — 배치 병합 탭 "AI 초안 입력" 기능

#### 목적
배치 스캔 결과를 병합할 때, 각 용어의 다국어 명칭(EN/KO/JA/ZH)·발음·한 줄 설명을
AI API를 통해 자동으로 채워주는 기능 추가.
이미지 참고: Google 검색 결과와 같은 형태(표기/읽기·발음·한 줄 설명)로 자동 입력.

#### 변경 내용

**1. `web/server.py` (MODIFY)**

- `POST /api/batch/ai_draft` 엔드포인트 추가
  - Request: `{ word, api_type(optional), model(optional) }`
  - Response: `{ ok, en, ko, ja, zh, pronunciation:{en,ko,ja,zh}, description }`
  - 기존 `.env`의 `API_KEY_TYPE` / `API_MODEL` / `*_API_KEY` 사용 (하드코딩 없음)
- `_call_ai_api(api_type, model, prompt)` 헬퍼 함수 추가
  - claude(anthropic) / openai / google 3종 지원
  - 마크다운 코드블록에 싸인 응답도 JSON 추출 (`_extract_json`)

**2. `web/index.html` (MODIFY)**

- 배치 병합(3. 병합) 탭에 "🤖 AI 초안 입력" 체크박스 UI 추가
  - API 종류 선택 드롭다운, 모델 선택 드롭다운 (스캔 탭과 동일 BATCH_MODELS 재활용)
  - 체크 시 파일 로드 완료 후 자동으로 `runAiDraftForAll()` 실행
  - 미체크 시 "▷ AI 초안 실행" 버튼 표시 (수동 실행)
- `onAiDraftApiChange()` 함수 추가 — API 선택 시 모델 목록 갱신
- `runAiDraftForAll()` 함수 추가
  - `_batchTerms` 전체를 순회하며 `fillAiDraft(i, word, ...)` 순차 호출
  - 진행 상태 바 표시 (성공/실패 카운트), API 과부하 방지 150ms 간격
- `fillAiDraft(i, word, apiType, model)` 함수 추가
  - `/api/batch/ai_draft` 호출 → EN/KO/JA/ZH 명칭 필드 자동 채우기
  - 설명(description) 필드가 비어 있는 경우에만 채우기
  - 발음 정보를 상세 패널(det{i})에 표시
  - `_batchTerms[i].lang` 업데이트 → `doMergeProcessed` 에서 즉시 반영
  - 행 왼쪽에 보라색 하이라이트 시각 피드백
- `renderChunk` else 블록에 AI 초안 자동 트리거 삽입
- `DOMContentLoaded` 이벤트에 체크박스 toggle 핸들러 등록

#### Verification
- `python -m py_compile web/server.py` → PASS
- `runAiDraftForAll` 4곳 정상 삽입 확인 (verify_patch.py)
- `ai-draft-chk` 체크박스 HTML 존재 확인
- `/api/batch/ai_draft` 엔드포인트 server.py 정상 삽입 확인
- `_call_ai_api` 헬퍼 정상 삽입 확인

#### Affected Files
- `web/server.py` (MODIFY: /api/batch/ai_draft, _call_ai_api 추가)
- `web/index.html` (MODIFY: AI 초안 체크박스 UI, runAiDraftForAll, fillAiDraft, 자동 트리거)

---
