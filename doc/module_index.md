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

## migrate_v1_2.py
- Path: bin/migrate_v1_2.py
- Classes: N/A
- Responsibility: 기존 JSON 데이터를 v1.2 스키마 구격(Sparse, Enum 규칙 포함)에 맞춰 자동 마이그레이션 (`--dry-run` 모드 지원)
- Entry Point: `main()`
- Related Modules: N/A
- Config: N/A
