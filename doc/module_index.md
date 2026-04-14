# Module Index

## generate_glossary.py
- Path: generate_glossary.py
- Classes: N/A
- Responsibility: glossary source(`dictionary/*.json`)를 검증하고 `terms.json`, `GLOSSARY.md`, `build/index/word_min.json`, `build/index/compound_min.json`, `build/index/variant_map.json`을 생성하며 `check-id` naming gate를 제공
- Entry Point: `main()`
- Related Modules: `bin/run.py`, `web/server.py`, `bin/scan_items.py`
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

## enrich_items.py
- Path: bin/enrich_items.py
- Classes: N/A
- Responsibility: 사전 API 및 번역 API(Google GTX)를 통해 words.json 내 빈 다국어 항목 및 영문/한글 정의(설명)를 식별해 일괄 보완(backfill)
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
