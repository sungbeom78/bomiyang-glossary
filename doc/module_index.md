# Module Index

## generate_glossary.py
- Path: generate_glossary.py
- Classes: N/A
- Responsibility: glossary source(`dictionary/*.json`)를 검증하고 `terms.json`, `GLOSSARY.md`, `build/index/word_min.json`, `build/index/compound_min.json`, `build/index/variant_map.json`을 생성하며 `check-id` naming gate를 제공
- Entry Point: `main()`
- Related Modules: `bin/run.py`, `web/server.py`, `bin/scan_terms.py`
- Config: N/A

## batch_terms.py
- Path: bin/batch_terms.py
- Classes: N/A
- Responsibility: 스캔된 용어 후보들을 LLM API를 통해 필터링하고 JSON 포맷으로 저장
- Entry Point: `main()`
- Related Modules: `scan_terms`
- Config: `.env`

## scan_terms.py
- Path: bin/scan_terms.py
- Classes: `TermScanner`
- Responsibility: 프로젝트 소스 코드를 스캔하여 용어 후보를 추출
- Entry Point: `main()`
- Related Modules: `batch_terms`
- Config: `.env`

## migrate_v1_2.py
- Path: bin/migrate_v1_2.py
- Classes: N/A
- Responsibility: 기존 JSON 데이터를 v1.2 스키마 구격(Sparse, Enum 규칙 포함)에 맞춰 자동 마이그레이션 (`--dry-run` 모드 지원)
- Entry Point: `main()`
- Related Modules: N/A
- Config: N/A

## web/server.py
- Path: web/server.py
- Classes: N/A
- Responsibility: glossary 웹 UI API를 제공하고 `generate_glossary.py`를 호출해 validate/generate/check-id 흐름을 노출
- Entry Point: `main()`
- Related Modules: `generate_glossary.py`, `web/index.html`
- Config: `.env`
