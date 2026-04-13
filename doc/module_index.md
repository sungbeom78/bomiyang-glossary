# Module Index

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
