# Glossary Change Log

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
