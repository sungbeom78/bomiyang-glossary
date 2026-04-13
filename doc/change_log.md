## [2026-04-13 23:59:42]
### Fixed
- `load_existing_terms` 함수의 반환값이 3개로 변경됨에 따라 발생하는 unpacking ValueError 수정 (`n_patterns` 추가)
- File: bin/batch_terms.py
### Notes
- `TermScanner` 초기화 시 `n_patterns` 옵션 전달 추가
