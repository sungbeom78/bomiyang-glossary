## [2026-04-18 18:05:00]
### Fixed / Refined (Glossary 2차 정제 — v3.2 적재 기준 통일)

#### 목적
마이그레이션과 신규 등록 간 variants 추출 기준 통일 + from/derived_terms 사용 규칙 확정

#### 1. 데이터 정제 (words.json)

**patch_domain_words.py (신규)**
- 19개 fetch_fail 도메인 단어에 수동 description_en 추가
  - kis, kosdaq, kospi, pnl, redis, url, vwap, mt5, postgresql 등
- url에 plural:urls variant 추가

**patch_upper.py (신규)**
- upper: uppermore, uppermost (잘못된 appendix 형태) 제거
- upper는 이미 comparative이므로 comparative variant 불필요

#### 2. 코드 개선

**normalize_build.py (MODIFY)**
- 모듈 헤더: v3.2 spec 완전 반영
  - 단어 검색 5단계 우선순위 명시
  - 용어 검색 원칙 (단어 단위 분해 → exact fallback) 명시
  - derived_terms 저장은 넓게, 조회는 exact fallback으로만 사용 명시

**batch_items.py (MODIFY)**
- process_auto() 주석: v1.2 통일 파이프라인 명시
  - "migration과 동일한 fetch_and_process() 사용" 명기

#### 3. 테스트

**bin/test_phase2.py (신규)** — 완료 조건 8카테고리 39개 테스트
- T1: more/most periphrastic variants 없음 ✅
- T2: from stage값 없음 ✅
- T3: noun plural 10개 샘플 ✅
- T4: verb 굴절 10개 샘플 ✅
- T5: comparative/superlative 복합표현 제외 ✅
- T6: derived_terms fallback 조회 6개 ✅
- T7: 신규 등록 = migration 동일 파이프라인 ✅
- T8: 도메인 단어 desc_en 9개 ✅
- **결과: 39 PASS / 0 FAIL**

#### 최종 데이터 상태
- words.json: 228 words
- desc_en 있음: 228/228 (100%)
- normalize_index: 955 entries
- derived_terms: 739 items

## [2026-04-17 12:26:00]
### Fixed (v1.2 Re-Migration — --only-incomplete 옵션 추가)

#### 문제
- `--resume`으로 migration 시 desc_en 있으면 skip → 169개 단어가 plural-only 상태로 남음
- 실질적으로 v1.2 형태소 패밀리 전략이 이전 단어들에 미적용

#### 해결
- `migrate_v1_1.py` : `--only-incomplete` 옵션 추가
  - plural-only 또는 variants=[] 인 단어만 선택 재처리
  - `--word-list ID,...` 옵션도 추가 (콤마 구분)
- 191개 단어 재처리: ok=172, fetch_fail=12, error=7
- derived_terms: 519 → **738 items**
- normalize_index: 752 → **954 entries**

#### 검증
- `verify_v1_1.py` : **11/11 PASS**
- `cancel` : cancelled(UK)/cancelling(UK) 수동 추가 (AI가 미국식만 반환)
- Only-plural 단어: 169 → **73** (73개는 진짜 plain noun)

## [2026-04-17 12:01:00]
### Major Refactor (Morphological Family Expansion — v1.2)

#### 핵심 문제 해결
- 기존: `canonical_pos` 기준 variants 필터 → "plural 수집기"로 전락
- 변경: **형태소 패밀리 최대 수집** (`active → activate, activation, actively, activating, activated`)

#### Architecture Changes

##### `bin/wikt_sense.py`
- `ALL_VARIANT_TYPES` 신규 상수: 16가지 타입 (inflection + morphological derivation)
  - inflection: `plural`, `singular`, `verb_form`, `past`, `past_participle`, `present_participle`, `comparative`, `superlative`
  - derivation: `noun_form`, `verb_derived`, `adj_form`, `adv_form`, `agent`, `gerund`
- AI 프롬프트 전면 교체: `CORE PHILOSOPHY = MAXIMIZE variants`
  - "FILTER only" 원칙: 완전히 다른 의미만 제거
  - `DERIVATION` 예시 6개 포함: `activate→activation`, `classify→classification` 등
- Hard Gate Gate-3: POS 제한 제거 → `ALL_VARIANT_TYPES` 포함 여부만 검증
- `_VTYPE_NORM` 확장: `adverb→adv_form`, `noun_derived→noun_form` 등 추가
- `STATUS_WORDS` 재정의: 병합 후 standalone 단어만 (`closed`, `pending`, `trading` 등)

##### `bin/merge_inflected_words.py` (신규)
- `-ed`/`-ing` canonical ID를 base verb로 병합
- MERGE: 21개 (`cancelled→cancel.past`, `failed→fail.past_participle` 등)
- KEEP: 7개 도메인 명사 (`trading`, `reporting`, `scoring`, `setting`, `trailing`, `closed`, `pending`)
- 234 → 228 단어 (21 removed, 15 new bases created)

#### Migration Results
- 228 words total (21 inflected IDs removed, 15 new base verbs added)
- Verbs with 0 variants: **234 → 0** (완전 해결)
- Top variant richness: classify(6v), reject(6v), run(6v), active(5v), disable(5v)
- derived_terms index: 519 items | normalize_index: 752 entries

## [2026-04-17 11:24:00]
### Major Refactor (Hard Gate Spec v1.1 — AI-Centric Architecture)

#### Architecture Change
- 기존: rule-based score → AI optional fallback (실제 AI 미실행)
- 변경: **AI가 중심, Hard Gate가 막는 구조**
  - Wiktionary HTML → Parser → Dict Score → AI 판단 → Hard Gate 검증 → 저장

#### Modified Files
- File: `bin/wikt_sense.py` — v1.1 완전 재설계
  - AI 프롬프트: 도메인 앵커링, 명시적 DO/DON'T 예시, variant type 제약
  - Hard Gate: 6단계 검증 (description_en, pos, variants, from, status word, variant type)
  - variant type 정규화 (`third_person_singular` → `verb_form`)
  - INFL_MAP에 comparative/superlative 추가 (adj variants 파싱)
  - `PipelineResult` 통합 반환 구조
- File: `bin/normalize_build.py` — `enrich_word_variants()` v1.1 연동
  - description_en, selected_pos, from 모두 反映
- File: `bin/batch_items.py` — `process_auto()` 전면 교체
  - dictionaryapi.dev 제거 → Wiktionary 단일 소스
  - v1.1 파이프라인 (fetch_and_process) 직접 호출
  - Hard Gate 통과 시에만 recommended=True

#### New Files
- File: `bin/migrate_v1_1.py` — v1.1 AI migration 스크립트
  - `--apply`, `--resume`, `--word`, `--dry-run` 지원
  - 단어별: variants/from 리셋 → AI 판단 → Hard Gate → 저장
- File: `bin/post_clean_v1_1.py` — post-migration 잔존 이상 정리

#### Migration Results (234 words)
- OK: 215 (AI 사용 207)
- Gate Rejected: 2 (lower, us — 수동 처리)
- Fetch Fail: 12 (도메인 전용 단어: KIS, KOSDAQ, mt5 등)
- Error: 5 (redis, url, pnl 등 — Wiktionary 미등재)

#### Data Quality (Before → After)
- desc_en 없음: 234 → **19** (fetch_fail/error 단어만 남음)
- 잘못된 from (bot→bottom 등): **17 → 0**
- more/most 형태 variants: **존재 → 전부 제거**
- adj variants 비어있던 문제: 해결 (Gate에서 adj exempt)

### Notes
- 신규 등록 경로와 migration 경로 **완전 통일** (동일 파이프라인)
- dictionaryapi.dev 의존성 완전 제거
- AI 프롬프트 핵심 설계: variant type EXACT name 지정 + from DO/DON'T 6개 예시

## [2026-04-17 09:19:00]
### Modified (Registration Path Parity Fix - batch_items.py)
- File: `bin/batch_items.py` — 신규 단어 등록 경로 v3.2 정합성 수정
  - `process_auto()`: dead-code comparative/superlative 필터 제거
    (이미 `enrich_word_variants()` -> `wikt_sense` 레벨에서 pos 필터 처리)
  - `process_auto()`: from 품질 필터 추가 (`is_bad_from()` 호출)
  - `process_auto()`: enriched dict에 `"from"` 필드 포함
  - `_apply_to_words_json()`: enriched 데이터 실제 반영 (기존: 버려짐)
    - `canonical_pos`, `description_i18n`, `source_urls`, `variants`, `from` 모두 적용
    - ko lang label을 LLM 번역 결과로 설정 (기존: word id 그대로)
- File: `bin/test_registration_parity.py` — 신규: 경로 정합성 테스트 21개
### Notes
- 신규 등록 경로 vs migration 경로 동일 함수 사용 확인:
  - enrich_word_variants() -> wikt_sense.fetch_and_process()
  - filter_variants_by_pos() (pos별 variant 필터)
  - post_clean_from.is_bad_from() (from 품질 필터)
- 테스트 21/21 PASS
- 주요 수정 전 문제: enriched 데이터가 words.json에 반영 안 됨 (dead code)

## [2026-04-17 09:16:00]
### Modified (v3.2 Full Data Migration - 234 words)
- File: `dictionary/words.json` — 전체 234개 단어 re-migration
  - variants clean: 362개 wrong-type variant 제거 (canonical_pos 불일치)
  - from clean: 18개 잘못된 from 값 제거 (자기참조, 복수형, meta-term, stage word)
  - Wiktionary enrichment: 35개 from 신규 설정, 3개 variants 추가
  - fetch_fail: 12개 (kisses/kosdaq/kospi/goldenkey 등 도메인 고유어)
- File: `dictionary/words__derived_terms.json` — 487 items 재생성
- File: `build/index/normalize_index.json` — 757 entries 재생성
- File: `bin/migrate_v3_2.py` — 신규: 완전 migration 스크립트
- File: `bin/post_clean_from.py` — 신규: from 품질 필터 스크립트
### Notes
- FATAL 0건, WARN 6건(기존 유지)
- terms.json 744개 생성
- normalize() 정규화 인덱스 757 entries
- pos별 variants 필터 적용 완료 (noun:plural만, verb:verb_form+past+pp만, adj:comparative+superlative만)

## [2026-04-17 08:58:00]
### Added (Wiktionary Sense Selection & From Extraction Spec v1.0)
- File: `bin/wikt_sense.py` — 신규 모듈 (274라인)
  - `parse_wiktionary_full()`: 전체 HTML 파싱 (etymologies + pos_blocks + inflections)
  - `score_candidate()`: 점수 기반 의미 선택 (pos match, description kw, domain kw, rare penalty)
  - `extract_from()`: lexical base 추출 (deny regex, allow pattern, fallback)
  - `filter_variants_by_pos()`: canonical_pos 기준 variants 필터링
  - `process_word()`: 7단계 메인 파이프라인
  - `fetch_and_process()`: Wiktionary fetch + process 통합
  - AI fallback 연동 (score < 5, 다의 어원, POS 중복 시 호출)
- File: `bin/normalize_build.py` — enrich_word_variants() wikt_sense 재사용 연동
- File: `bin/test_wikt_sense.py` — 단위 테스트 19개 (spec §10) + live 테스트 5케이스
### Notes
- 단위 19/19 PASS
- Live: bot(noun✅, from='bottom'*), execute(verb✅), drama(from=None✅), watch(plural✅), standard(adj✅)
- *bot.from='bottom' — Wiktionary에 "Clipping of bottom" 실제 존재. AI fallback 시 null로 교정됨
- FROM_DENY_PATTERNS: "From Late Latin" 패턴 regex로 처리 (이전 startswith 방식 교체)
- "Shortening of", "Back-formation from" allow 패턴 추가
- variants deduplication 추가

## [2026-04-17 07:51:00]
### Modified (Glossary Normalization System v3.2 - Policy Unification)
- File: `bin/normalize_build.py` — v3.2로 업그레이드
  - HEADWORD_INFLECTION_MAP에서 comparative/superlative 제거 (more X, most X 생성 차단)
  - `is_lexical_from()` 신설: from 필드를 lexical base vs etymology-stage로 분류
  - `_build_normalize_index()` 5단계 우선순위 재정립: id > variants > synonyms > from(lexical) > derived_terms
  - `enrich_word_variants()` public API 분리: 마이그레이션/신규 등록 공용 함수
  - from 필드: 삭제 아닌 보존, canonical 판단 시만 is_lexical_from()으로 분류
- File: `dictionary/words.json` — comparative/superlative 복합형 52건 제거 (more/most 패턴)
- File: `bin/batch_items.py` — process_auto()에서 신규 단어 등록 시 `enrich_word_variants()` 재사용 (경로 통일)
- File: `bin/clean_variants.py` — 복합 comparative 제거 스크립트 신설
### Notes
- normalize() 6개 테스트 모두 OK
- is_lexical_from() 6개 테스트 모두 OK
- comparative/superlative 0건 확인 (52건 제거 완료)
- FATAL 0건 유지, terms.json 762개

## [2026-04-17 00:09:00]
### Added (Glossary Normalization System v3.1)
- File: `bin/normalize_build.py` — v3.1 정규화 엔진 신설
  - `from` 필드 정제: `middle`, `latin`, `french` 등 언어 단계 값 115건 제거
  - Wiktionary headword-line 파서로 inflection 변형 635건 variants에 적용
  - `derived_terms` 제거 후 `words__derived_terms.json`으로 분리 (6,932건)
  - `normalize_index.json` 생성 (7,144 entries): surface → canonical_id
  - `normalize(word)` API: 의미 업룥나 적용 � 모든 표면형을 canonical id로 첫번에 환시
- File: `dictionary/words.json` — derived_terms 제거, variants 635건 보강, from 115건 정제 완료
- File: `dictionary/words__derived_terms.json` — 파생어 및 형태소 검색 인덱스 신설
### Notes
- terms.json 762건 (546에서 증가), FATAL 0건
- normalize('sectors') → 'sector', normalize('accounts') → 'account' 등 정상 확인

## [2026-04-16 23:17:00]
### Fixed / Added (Migration v2 성공)
- Wiktionary HTML 구조 변경(`mw-heading div`) 대응 파서 전면 재작성
- File: `bin/migrate_words_relations.py` — v2 전면 재작성. `_get_sections()` / `_find_english_subsections()` 로 기존 h2 anchor 변경에 대응. Etymology, Synonyms, Antonyms, Derived terms, Inflection 모두 정상 추출.
- File: `bin/fix_self_variants.py` — 문자 자체 값과 동일한 self-conflict variants 제거 유톸리티 신설
- File: `dictionary/words.json` — Migration v2 전진. `from` 150건(64%), `synonyms` 65건, `antonyms` 42건, `derived_terms` 195건(83%), `source_urls` 222건(95%) 자동 보강 완료
### Notes
- FATAL 0건, WARN 6건(기존)으로 validate 통과 확인
- pending_words.json 에 from 기반 신규 후보 36건 자동 등록됨

## [2026-04-16 21:12:00]
### Added / Modified
- Glossary Migration & Canonical Consolidation Plan v1.0 실행 완료
- File: `schema/word.schema.json` — `from`, `synonyms`, `antonyms`, `derived_terms` 관계형 속성 추가하여 검증 규칙 최신화.
- File: `bin/migrate_words_relations.py` — 지정된 소스에서 마이그레이션 스크립트를 추출해 `bin` 폴더에 배치 후 실행. Wiktionary API 기반으로 단어 234건 검사 완료 (`source_urls` 222건 신규 확보).
- `generate_glossary.py generate`를 실행하여 Projection(GLOSSARY.md 포함) 재생성 및 최종 완료.
### Notes
- Migration 과정 중 FATAL 에러나 파손 현상 없이 모두 정상 수행됨.

## [2026-04-16 18:22:00]
### Added / Modified
- Auto 모드 배치 추출 결과 UI 개선 및 한국어 LLM 번역 연동
- File: `web/index.html` — `renderChunk()` 내 UI 개선. 병합 리스트 출력 시 발견 횟수 외에 품사(pos), 한국어 뜻, 영어 정의 요약을 노출하도록 수정. `상세▼` 토글 버튼 통해 상세 뜻 및 source_urls 링크를 확인 가능.
- File: `bin/batch_items.py` — `process_auto()` 내 영문 사전 검색 후 `.env`의 API 키를 활용해 추출된 전체 단어 뜻을 LLM으로 일괄 한국어 번역(`description_i18n.ko`)하도록 로직 추가.
### Notes
- 사용자는 `API_KEY_TYPE` (claude, openai, google) 환경 변수 설정 후 Auto 모드를 재실행하여 한국어 정의까지 자동 매핑된 화면을 볼 수 있습니다.

## [2026-04-16 15:00:00]
### Fixed / Modified
- 배치 추출 결과물 병합 화면 오류 수정 및 Dictionary API 추출 고도화
- File: `web/index.html` — `d.terms` 오타를 `d.items`로 수정. `doMergeProcessed`에서 enriched 데이터 추출 방식 적용
- File: `bin/batch_items.py` — Auto 모드 추출 로직 수정. `partOfSpeech`를 `canonical_pos`로 매핑하고, `source_urls` 및 첫 번째 definition을 `description_i18n`으로 저장
- File: `schema/word.schema.json` — 엄격한 스키마 검증을 통과하기 위해 `source_urls` 필드 명세 추가
### Notes
- 사용자는 `batch_items.py` 기반의 Auto 모드를 재실행하여 단어 속성을 새로 추출해야 정상적으로 UI에 영단어의 품사/정의 등이 반영됩니다.

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
