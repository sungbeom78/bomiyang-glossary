## [2026-04-16 12:31:00]
### Added
- §5.3 Alerting 구현 — `web/notifier.py` 신설
  - Telegram: `TELEGRAM_SYSTEM_TOKEN` + `TELEGRAM_DEFAULT_CHAT_ID` (.env)
  - Slack 방식 1 (권장): `SLACK_WEBHOOK_URL` (Incoming Webhook)
  - Slack 방식 2: `SLACK_BOT_TOKEN` + `SLACK_DEFAULT_CHAT_ID` (xoxb- 필수)
  - `notify_info()` / `notify_warning()` / `notify_critical()` 편의 함수 제공
  - `notify()` 통합 함수: Telegram + Slack 동시 발송
- §1.3 Trading Freeze 구현 — `web/trading_freeze.py` 신설
  - `is_trading_freeze()` → (bool, reason) 반환
  - `check_freeze_or_raise()` → Flask 응답 dict 반환 (server.py 연동용)
  - `get_freeze_status()` → `/api/trading-freeze/status` 응답용
  - 차단 시간대: 한국 주식 09:00–15:30 / 해외 FX 21:00–02:00 / 코인 옵션
- `web/server.py` 연동 수정
  - `api_generate()`: Trading Freeze 게이트 추가 + generate 완료/실패 알림
  - `api_validate()`: FATAL 발생 시 `notify_critical()` 알림
  - `git_commit_push()`: Trading Freeze 게이트 추가 + commit 완료 알림
  - `GET /api/trading-freeze/status` 신규 엔드포인트 추가
  - `main()`: 서버 시작 시 Trading Freeze 상태 출력 (🔴/🟢 표시)
- `.env.example` 신규 키 추가: TELEGRAM_SYSTEM_TOKEN, TELEGRAM_DEFAULT_CHAT_ID,
  SLACK_WEBHOOK_URL, SLACK_BOT_TOKEN, SLACK_DEFAULT_CHAT_ID,
  TRADING_FREEZE_ENABLED, TRADING_FREEZE_CRYPTO
- File: web/notifier.py [NEW]
- File: web/trading_freeze.py [NEW]
- File: web/server.py
- File: .env.example
- File: doc/plan/Glossary Consolidation & Refactoring Plan v2.5.1 task.md (§5.3, §1.3 [x] 완료)
### Notes
- Telegram 전송: telegram=True 확인 완료 (2026-04-16 12:35 KST)
- Slack: 제공된 SLACK_SYSTEM_TOKEN이 Telegram 형식으로 Slack 사용 불가.
  SLACK_WEBHOOK_URL 또는 xoxb- Bot Token 발급 후 .env 설정 필요.
- Trading Freeze: 현재 KST 12:35 → "한국 주식 시장 운영 중" FREEZE 정상 감지 확인

## [2026-04-16 12:25:00]
### Modified
- Plan v2.5.1 task.md 상태 최신화
- 현재 상태 테이블에 build/report/, build/index/, bin/test_*.py, rollout_rollback_plan.md 항목 추가
- 잔여 검토 사항 → Plan §8 Migration 완료 현황으로 재구성
- Step 6~10 모두 [x] 완료 처리 (이전 [ ] 상태에서 갱신)
- File: doc/plan/Glossary Consolidation & Refactoring Plan v2.5.1 task.md
### Notes
- Step 7 (16/16 PASS), Step 8 (19/19 PASS), Step 9~10 (rollout_rollback_plan.md) 모두 완료 반영
- §5.3 Alerting, §1.3 Trading Freeze 는 범위 외 별도 작업으로 유지

## [2026-04-16 11:41:00]
### Modified
- Plan v2.5.1 §8 Step 7–10 대응 파일 수정 — Windows 호환성 및 경로 정확성 개선
- bin/test_regression.py: Windows cp949 터미널 UnicodeEncodeError 방지 위해 `sys.stdout.reconfigure(encoding='utf-8')` 추가, tc_08/tc_09 내 `import io as _io` alias 불일치 버그 수정
- bin/test_db_compat.py: 동일한 Windows stdout UTF-8 처리 추가, dc_05 JSON 왕복 테스트에서 `len(words_obj)` 가 dict 키 수를 반환하던 오류를 `_unwrap()` 적용 후 항목 수 계산으로 수정 (words:234개, compounds:154개 정상 표시)
- bin/rollout_rollback_plan.md: 모든 Linux 전용 명령어(bash/sh) → PowerShell 명령어로 대체
  - `cp -r` → `Copy-Item -Recurse`
  - `ln -sfn` → `Rename-Item` 기반 교체 절차 (mklink 주석 안내)
  - `date +%Y%m%d` → `Get-Date -Format 'yyyyMMdd'`
  - `cd glossary` / `cd ..` → `Push-Location ..` / `Pop-Location`
  - `cat` → `Get-Content`
  - git commit 문자열 내 이중 따옴표 → 단일 따옴표 (PowerShell 파싱 안전)
  - 코드 블럭 언어 태그 `bash` → `powershell`
  - 모든 명령 블럭에 실행 위치 주석(`# 실행 위치: glossary/ 루트`) 추가
- File: bin/test_regression.py
- File: bin/test_db_compat.py
- File: bin/rollout_rollback_plan.md
### Notes
- test_regression.py: 16/16 PASS (PYTHONIOENCODING 환경변수 없이도 정상 실행)
- test_db_compat.py: 19/19 PASS (words:234, compounds:154, terms:598 정상 표시)

## [2026-04-15 13:42:12]
### Added / Modified
- Plan v2.5.1 2단계 구현 완료 — variants Array 전환
- bin/migrate_variants.py 신설: words.json/compounds.json의 variants object → array 마이그레이션 (dry-run 지원)
- generate_glossary.py: `build_terms_json()` 내 compound variants projection을 array+object 하위호환으로 전환
- generate_glossary.py: `cmd_generate()` 내 `variant_map` 생성 로직을 array+object 하위호환으로 전환
- schema/word.schema.json: variants를 type-based array 형식으로 완전 재정의 (§3.3, oneOf[value|short])
- schema/compound.schema.json: variants array 형식 + abbr 객체 제거 (abbreviation type으로 통합)
- web/index.html:
  - `getVariantShort(variants)`, `getVariantLong(variants)`, `cAbbrShort(c)`, `cAbbrLong(c)` 헬퍼 추가
  - wFilter, renderWords, cFilter, renderCompounds → 헬퍼 사용으로 전환
  - openWordForm, saveWord → variants array [{type:'abbreviation',short}] 형식으로 저장
  - openCompoundForm, saveCompound → variants array [{type:'abbreviation',short,long}] 형식으로 저장
- words.json: 234개 단어 variants object → array 마이그레이션 완료
- compounds.json: 154개 복합어 variants object → array 마이그레이션 완료
- File: generate_glossary.py
- File: schema/word.schema.json
- File: schema/compound.schema.json
- File: bin/migrate_variants.py
- File: web/index.html
### Notes
- generate FATAL 없음, WARN 6건(V-401 기존 단어 4개 description 미등록, V-352 1건)
- terms.json 598개 checksum 포함 재생성 완료

## [2026-04-15 13:28:00]
### Added / Modified
- Plan v2.5.1 1단계 구현 완료 (Glossary Consolidation & Refactoring Plan v2.5.1)
- terms.json에 sha256 checksum 필드 추가 (`compute_checksum`, `verify_checksum` 함수 신설)
- V-010 (checksum CRITICAL), V-011 (schema ERROR), V-013 (banned exact-match ERROR) 검증 추가
- `validate()` 함수에 `skip_checksum` 파라미터 추가 — generate 전 호출 시 기존 terms.json checksum 검증 스킵
- deprecated 항목 → `dictionary/terms_legacy.json` 자동 분리 생성
- Projection 보강: alias / misspelling variant도 terms.json에 포함 (`PROJECTION_VARIANT_TYPES` 상수 신설)
- `_extract_word_variants()` 헬퍼 추가 — §4.4/§4.5 포함/제외 규칙 집중 처리
- `build_terms_json()` 반환 시그니처 변경: dict → tuple(active_data, legacy_data, skipped)
- `_register_term()` 내부 함수 추가 — id 충돌 시 skipped 기록 (§4.7)
- 운영 산출물 4종 자동 생성 (§11): `build/report/dependency_missing.json`, `projection_skipped.json`, `merge_candidates.json`, `banned_autofix_report.json`
- `REPORT_DIR`, `TERMS_LEGACY_PATH` 경로 상수 추가
- `PROJECTION_VARIANT_TYPES`, `PROJECTION_EXCLUDE_TYPES` 상수 추가 (§4.4, §4.5)
- `cmd_stats()` 내 `w["pos"]` → `w.get("canonical_pos")` 수정 (v1.2 스키마 정합)
- `doc/module_index.md` 갱신 — generate_glossary.py 산출물 및 Validation Gate 명시
- File: generate_glossary.py
- File: doc/module_index.md
### Notes
- V-010은 standalone `validate` 명령에서만 기존 terms.json 체크섬 검증. `generate` 전에는 skip_checksum=True로 우회.
- V-013은 case-sensitive exact match 적용 — KIS(banned)↔kis(id) 오탐 방지.
- WARN 6건 (V-401×5, V-352×1)은 기존 데이터 품질 이슈로 1단계 범위 외.

## [2026-04-14 20:01:59]

### Modified
- V-351 경고 규칙을 Sparse JSON 원칙에 맞게 정리 (명사 plural 미정의 일괄 WARN 제거)
- File: generate_glossary.py
### Notes
- 기존 V-351은 noun + plural 미정의 전체를 경고해 대부분 단어가 WARN으로 출력되는 과경고 상태였음
- v0.4의 Sparse 원칙(값 없는 필드 생략 허용)에 맞게 `variants.plural`이 "명시되어 있는데 비어 있는 경우"에만 V-351 경고를 발생하도록 조정
- plural root 금지(V-301), self-conflict 금지(V-303), check-id 정규화 동작에는 영향 없음

## [2026-04-14 18:28:48]
### Modified
- BOM_TS Glossary Integration Final v0.4 기준으로 AI runtime index 메타데이터 정합화 및 운영 문서 보강
- File: generate_glossary.py
- File: doc/README_AI_GUIDELINE.md
- File: doc/module_index.md
### Notes
- `word_min.json`에 `status`, `canonical_pos`를 포함해 AI 에이전트 naming gate가 sparse index만으로 품사/상태를 참조할 수 있도록 보강
- `compound_min.json`에도 `status`를 포함해 runtime index와 source lifecycle 정보 정합성을 맞춤
- glossary AI guideline에 `build/index/word_min.json`, `build/index/variant_map.json` 우선 사용 규칙 추가
- module index에 `generate_glossary.py`, `web/server.py` 책임과 생성 산출물 경로를 명시

## [2026-04-14 14:44:16]

## [2026-04-14 15:23:47]
### Modified
- Glossary_Refactoring_Plan_v1.2_extra_03.md 지침에 따라 root 단수형 정규화 및 validation 규칙 적용 완료
- File: schema/word.schema.json
- File: schema/compound.schema.json
- File: dictionary/words.json
- File: dictionary/compounds.json
- File: generate_glossary.py
- File: bin/scan_terms.py
### Notes
- 복수형이 root로 쓰이던 항목(candidates 등)을 단수형으로 치환하고 `variants.plural` 배열 구성
- V-301 (plural root 금지), V-303 (self-conflict 금지), V-351, V-352 등의 validation 코드 반영
- check-id 스크립트 실행 시 plural 입력을 root로 식별하고 정규화 정보 출력 지원
- scan_terms.py에서 plural / abbreviation이 배열화된 schema 호환 처리

### Modified / Removed
- terms.json에서 자동 생성되던 abbr_short 및 abbr_long 속성 전면 삭제 (BOM_TS 구조 개선 v0.2)
- terms.json 내 Base(source), Variant(variant_type, root) 구조 고도화 적용
- web/index.html UI에서 잔재하던 abbr_long, abbr_short 참조 버그 픽스 (abbr.long, abbr.short 참조로 수정 적용)
- bin/batch_terms.py, bin/scan_terms.py 내 하위호환 용 abbr 레거시 로직 제거
- File: generate_glossary.py
- File: web/index.html
- File: bin/batch_terms.py
- File: bin/scan_terms.py
### Notes
- 복합어 저장 및 생성 시 단일화된 abbr 객체 스키마 적용
- 약어에 대해선 root 값 필수 포함 원칙 적용 완료


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
