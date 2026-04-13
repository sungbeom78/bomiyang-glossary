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
