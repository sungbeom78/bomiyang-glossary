## Module Index

## generate_glossary.py
- Path: generate_glossary.py
- Classes: N/A
- Responsibility: glossary source(`dictionary/*.json`)를 검증하고 다음 산출물을 생성:
  - `dictionary/terms.json` (projection, sha256 checksum 포함)
  - `dictionary/terms_legacy.json` (deprecated 항목)
  - `GLOSSARY.md`
  - `build/index/word_min.json`, `compound_min.json`, `variant_map.json`
  - `build/report/dependency_missing.json`, `projection_skipped.json`, `merge_candidates.json`, `banned_autofix_report.json`
  - `check-id` naming gate 제공
- Validation Gate: V-001/V-004/V-008/V-010/V-011/V-013
- Entry Point: `main()`
- Related Modules: `bin/run.py`, `web/server.py`, `bin/scan_items.py`, `bin/validate.py`
- Config: N/A

## batch_items.py
- Path: bin/batch_items.py
- Classes: N/A
- Responsibility: 스캔된 용어 후보들을 LLM 및 외부 사전 API를 통해 필터링하고 JSON 포맷으로 저장
- Entry Point: `main()`
- Related Modules: `scan_items`
- Config: `.env`

## scan_items.py
- Path: bin/scan_items.py
- Classes: `ItemScanner`
- Responsibility: 프로젝트 소스 코드를 스캔하여 단어 및 식별자 후보를 추출
- Entry Point: `main()`
- Related Modules: `batch_items`
- Config: `.env`
- Notes (v1.1):
  - `load_existing_words_and_tokens()`: variants를 `list[{type,value|short}]`로 올바르게 처리
  - `words__derived_terms.json` surface도 exclusion token에 포함 (underscore 없는 것만)
  - exclusion 토큰: ~228개(v1.0) → ~900+개(v1.1)

## enrich_items.py
- Path: bin/enrich_items.py
- Classes: N/A
- Responsibility: 사전 API 및 번역 API(Google GTX)를 통해 words.json 내 빈 다국어 항목 및 영문/한글 정의(설명)를 식별해 일괄 보완(backfill)
- Entry Point: `main()`
- Related Modules: N/A
- Config: N/A

## clean_derived_terms.py
- Path: bin/clean_derived_terms.py
- Classes: N/A
- Responsibility: `words__derived_terms.json` synonym 품질 정제
  - synonym 중 words.id/variants 충돌 제거
  - underscore/공백 포함 비자연어 표현 제거
  - 도메인 무관 동의어 제거
- Entry Point: `clean_derived_terms()`, `__main__`
- Related Modules: `dictionary/words__derived_terms.json`
- Config: N/A

## fix_missing_words.py
- Path: bin/fix_missing_words.py
- Classes: N/A
- Responsibility: V-104 FATAL 해결용 — compounds가 참조하지만 words.json에 없는 단어 추가
  - 대상: ranking, realized, tracking, extended, used
- Entry Point: `fix_missing_words()`, `__main__`
- Related Modules: `dictionary/words.json`
- Config: N/A
- Notes: 1회성 마이그레이션 스크립트. 이후 재실행해도 skip 처리됨.

## web/server.py
- Path: web/server.py
- Classes: N/A
- Responsibility: glossary 웹 UI API를 제공하고 `generate_glossary.py`를 호출해 validate/generate/check-id 흐름을 노출
- Entry Point: `main()`
- Related Modules: `generate_glossary.py`, `web/index.html`, `core/writer.py`
- Config: `.env`
- Notes: words/compounds write API는 GlossaryWriter 경유 (직접 write 금지)

## core/writer.py
- Path: core/writer.py
- Classes: GlossaryWriter
- Responsibility: words.json / compounds.json 의 단일 저장 진입점. 직접 write 금지 정책 시행.
- Entry Point: add_word(), add_compound(), update_word(), remove_word(), save(), validate()
- Related Modules: generate_glossary.py (validate 호출), web/server.py (write API), bin/apply_pending_words.py
- Config: dictionary/words.json, dictionary/compounds.json
- Notes:
  - context manager 지원 (with GlossaryWriter() as gw:)
  - save() 시 자동 backup 생성 (build/backup/)
  - rollback() 으로 스냅샷 기반 복원 가능
  - validate() 로 저장 전 FATAL 오류 확인 가능

## generate_glossary.py (Projection)
- Path: generate_glossary.py
- Responsibility: words.json + compounds.json → terms.json / variant_map.json / word_min.json 등 빌드 산출물 생성 및 validate
- Entry Point: cmd_generate(), cmd_validate(), cmd_check_id()
- Key Config:
  - PROJECTION_VARIANT_TYPES: variant_map에 포함할 타입 목록
    (abbreviation, alias, plural, misspelling + 굴절형 + 파생형 전체 — §4.4 확장)
  - PROJECTION_EXCLUDE_TYPES: variant_map 제외 타입 목록
