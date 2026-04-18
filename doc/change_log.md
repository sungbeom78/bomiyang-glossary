# Glossary Change Log

> **Archive**: 이전 기록은 `doc/change_log_archive/202604_change_log.md` 에 보관.

---

## [2026-04-18 21:00:00]
### Modified — 웹 대시보드 기능 확장 (v3.4)

#### 목적
1. JSON에 있는 모든 필드를 UI에서 조회·수정 가능하도록 확장
2. 언어 전환 버튼(한/EN/JA/ZH) 추가
3. 환경설정 모달에서 기본 언어·시간대를 localStorage에 저장

#### 변경 파일

**web/index.html (MODIFY)**
- `topbar`: `lang-sel` 드롭다운 추가 (한국어/English/日本語/中文), `⚙ 설정` 버튼 추가
- 단어 수정 모달(`word-ov`) 전면 개편
  - **기본 정보**: id, pos, status, domain
  - **다국어 번역**: en, ko, ja, zh_hans
  - **설명**: ko (필수), en (선택)
  - **형태소/관계어**: abbr, from, variants (type:value 줄바꿈), synonyms, antonyms, source_urls, not
  - 중복 `wf-status` 제거 (기존 버그 수정)
  - 복합어 모달(`compound-ov`)의 중복 `wf-status` 제거
- 환경설정 모달(`settings-ov`) 신규 추가
  - 기본 표시 언어, 기본 시간대 선택 → localStorage 저장
- `renderWords()`:
  - `window.LANG` 값에 따라 번역 열(한국어/영어/일본어/중국어) 동적 전환
  - 설명(description) 열도 선택 언어로 자동 전환
  - 확장 행(xrow) 전체 필드 표시: lang.ja, lang.zh_hans, description(en), from, variants 칩, synonyms, antonyms, source_urls 링크
- `openWordForm()`: 신규 필드 9개 추가 채움
- `saveWord()`: 신규 필드를 JSON body에 포함 (ja, zh_hans, descEn, from, variants, synonyms, antonyms, source_urls)
- `variantsToText()` / `textToVariants()` 헬퍼 함수 추가
- `changeLang(lang)`, `openSettings()`, `saveSettings()` 함수 추가
- `boot()`: localStorage에서 저장된 언어·시간대 복원
- Escape 핸들러에 `settings-ov` 추가

#### 검증
- 브라우저 렌더링 확인: account 확장 행에서 lang.ja(アカウント), lang.zh_hans(帐户), description(en), variants 칩, source_url 링크 정상 표시
- 수정 모달: 9개 신규 필드 모두 정상 표시 및 기존 데이터 채움 확인
- 설정 모달: 저장 시 언어 즉시 전환, localStorage 반영 확인
- 228개 전체 렌더링 유지

---

## [2026-04-18 20:09:00]
### Modified — 웹 대시보드 렌더링 성능 최적화 (v3.3)

#### 목적
228개 전체 단어 항목의 완전한 출력 보장 및 1초 내 페이지 로딩 달성

#### 변경 내용

**web/server.py (MODIFY)**
- `_load_json()`: mtime 기반 인메모리 캐시 추가
  - 파일 변경 없을 때 파일 I/O 완전 제거 (매 GET 마다 208KB JSON 재파싱 방지)
  - `_cache: dict` 전역 캐시 딕셔너리 도입
  - `_invalidate_cache(path)` — save 시 캐시 무효화
- `/api/words` GET: ETag + If-None-Match 지원
  - md5 기반 ETag 생성 → 304 Not Modified 응답으로 클라이언트 중복 전송 방지

**web/index.html (MODIFY)**
- `boot()` 재구조화: words를 먼저 로드해 첫 페인트를 앞당김 (진행성 렌더)
  - 나머지 compounds/banned/drafts는 병렬 fetch
- `renderWords()` 전면 최적화:
  - `DocumentFragment` 사용으로 DOM 삽입 1회로 집약
  - `for` 루프로 교체 (`forEach` → 미세 오버헤드 제거)
  - HTML 문자열을 짧은 세그먼트 연결로 분할 (가독성 + 엔진 최적화)
  - 이벤트 위임(event delegation): 개별 `addEventListener` 228개 제거,
    tbody 단위 click/dblclick 핸들러 1개로 대체
  - 삭제 버튼: `onclick` 인라인 → `data-del-word`, `data-del-ko` 속성으로 분리
  - 수정 링크: `onclick` 인라인 → `data-edit-word` 속성으로 분리
- `reloadWords()`: ETag 캐시 헤더 지원 (304 응답 시 불필요한 JSON 파싱 스킵)
- `_wordsETag` 전역 변수 추가

#### 검증 결과
- 단어 228개 전체 정상 렌더링 확인
- 페이지 로딩 1초 이내
- 서버 문법 검사: `py_compile` PASS

### Notes
- 기존 change_log.md 515줄 → 500줄 초과로 `doc/change_log_archive/202604_change_log.md` 아카이빙 수행
