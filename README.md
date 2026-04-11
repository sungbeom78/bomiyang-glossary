# BOM_TS Glossary

> **BOM_TS(Bomiyang Trading System)** 프로젝트의 공식 용어 사전 시스템
> Git Submodule로 관리되며, 모든 식별자는 이 사전을 기준으로 생성됩니다.

---

## 목차

1. [개요](#1-개요)
2. [시스템 구조](#2-시스템-구조)
3. [핵심 개념](#3-핵심-개념)
4. [디렉토리 및 파일 구조](#4-디렉토리-및-파일-구조)
5. [서브모듈 설치 및 설정](#5-서브모듈-설치-및-설정)
6. [빠른 시작](#6-빠른-시작)
7. [웹 UI 사용법](#7-웹-ui-사용법)
8. [커맨드라인 사용법](#8-커맨드라인-사용법)
9. [용어 등록 절차](#9-용어-등록-절차)
10. [배치 추출 (batch)](#10-배치-추출-batch)
11. [검증 규칙](#11-검증-규칙)
12. [환경 설정 (.env)](#12-환경-설정-env)
13. [Git 운영 가이드](#13-git-운영-가이드)
14. [운영 FAQ](#14-운영-faq)

---

## 1. 개요

### 왜 용어 사전이 필요한가

자동매매 시스템은 수십 개의 모듈, 수백 개의 클래스와 함수, 수천 개의 변수를 가집니다.
같은 개념을 `get_position` / `fetch_position` / `load_position` 으로 각각 부르면
코드 탐색이 어렵고, AI 에이전트가 중복 코드를 생성하며, 팀원 간 소통이 막힙니다.

**BOM_TS Glossary는 이 문제를 구조적으로 해결합니다.**

- 모든 식별자는 `words.json`에 등록된 단어의 조합으로만 생성합니다.
- 단어를 조합하는 규칙이 명확하므로 임의적인 이름이 생기지 않습니다.
- AI 에이전트(Codex, Gemini, Claude)가 새 식별자 생성 전 자동으로 검증합니다.

### 시스템 공식 명칭

| 레이어 | 명칭 | 사용 위치 |
|--------|------|-----------|
| 개발 내부 | `ts` | 디렉토리명, import 경로 |
| 시스템 공식 | `BOM_TS` | 문서, 로그, 커밋 메시지 |
| 공개 브랜드 | `Bomiyang's Trade System` | 웹페이지 타이틀, 헤더 |

### 현황 (v2)

| 항목 | 수치 |
|------|------|
| 단어 (words.json) | 227개 |
| 복합어 (compounds.json) | 152개 |
| 금지표현 (banned.json) | 8개 |
| 하위호환 terms.json | 379개 (자동 생성) |

---

## 2. 시스템 구조

### 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    BOM_TS 프로젝트                           │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │  glossary/  (Git Submodule)                         │  │
│   │                                                     │  │
│   │  dictionary/          ← 사전 원본 (수동 편집)        │  │
│   │  ├─ words.json        ← 단어 원자 단위               │  │
│   │  ├─ compounds.json    ← 복합어                       │  │
│   │  └─ banned.json       ← 금지표현                     │  │
│   │                                                     │  │
│   │  generate_glossary.py ← 생성·검증·조회 엔진          │  │
│   │  GLOSSARY.md          ← 자동 생성 (사람이 읽는 버전) │  │
│   │  dictionary/terms.json ← 자동 생성 (하위호환)        │  │
│   │                                                     │  │
│   │  web/server.py + index.html  ← 관리 UI              │  │
│   │  bin/scan_terms.py           ← 소스 스캔              │  │
│   │  bin/batch_terms.py          ← LLM API 추출           │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
│   ┌───────────────────────────────────────────────────┐    │
│   │  프로젝트 소스 (ts/)                               │    │
│   │  모든 식별자 → glossary 기준으로 검증              │    │
│   │                                                   │    │
│   │  python glossary/generate_glossary.py check-id    │    │
│   │              <식별자>                              │    │
│   └───────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 데이터 흐름

```
[소스 코드 스캔]          [LLM API 분석]         [사전 등록]
scan_terms.py    →    batch_terms.py    →    웹 UI 검토 후
(후보 추출)           (용어 분류)              words.json 병합

                                                    ↓
[사전 검증·생성]                              [하위호환 출력]
generate_glossary.py validate                terms.json (자동)
generate_glossary.py generate        →       GLOSSARY.md (자동)
```

### 서브모듈 관계

```
프로젝트 저장소 (BOM_TS/ts)
└── glossary/           ← git submodule (별도 저장소)
    └── dictionary/     ← 사전 파일 (glossary 저장소에서 관리)
```

---

## 3. 핵심 개념

### 단어 (Word) — 최소 단위

모든 식별자를 구성하는 원자 단위. `dictionary/words.json`에 등록.

```json
{
  "id": "kill",
  "en": "kill",
  "ko": "킬",
  "abbr": null,
  "pos": "verb",
  "domain": "system",
  "description": "강제 종료 또는 비활성화",
  "not": []
}
```

| 필드 | 설명 |
|------|------|
| `id` | snake_case 없음. **영소문자+숫자만**, 단수형 강제 (`^[a-z][a-z0-9]*$`) |
| `en` | 영문 원형 |
| `ko` | 한글 대표 번역 |
| `abbr` | 약어 (2~5자 대문자, 없으면 null) |
| `pos` | 품사: noun / verb / adj / adv / prefix / suffix / proper |
| `domain` | 분류: trading / market / system / infra / ui / general / proper |
| `plural` | noun에만 사용. null=자동추론, 문자열=불규칙, `"-"`=불가산 |
| `description` | 이 프로젝트에서의 의미 |
| `not` | 혼동 금지 표현 목록 |

**plural 필드 규칙:**

| 값 | 의미 | 예시 |
|----|------|------|
| `null` | 자동 추론 (+s/+es/+ies) | `order` → `orders` |
| 문자열 | 불규칙 복수형 명시 | `"indices"` (index용) |
| `"-"` | 불가산 (복수형 없음) | `risk`, `config`, `info` |
| (필드 없음) | noun 아닌 품사 | verb, adj 등 |

**id 형식 규칙 (V-007):** 단어 id는 `^[a-z][a-z0-9]*$` 패턴만 허용.
언더스코어, 대문자, 숫자 시작 금지. 복수형 단독 등록 금지 (V-008).

### 복합어 (Compound) — 조건부 등록

두 개 이상의 단어 조합이 특별한 의미를 가질 때만 등록. `dictionary/compounds.json`에 등록.

**등록 조건 (하나 이상 충족):**

| # | 조건 | 예시 |
|---|------|------|
| 1 | 의미 비합산 — 단어를 합쳐도 이 의미가 안 됨 | `kill_switch` |
| 2 | 공인 약어 존재 | `stop_loss` → SL |
| 3 | 혼동 방지 필요 | `fx_futures` vs `mt5_futures` |
| 4 | 시스템 공식 객체명 | Pydantic 모델, DB 테이블 |
| 5 | 외부 고유명사 | `telegram_bot`, `kis_adapter` |

**조건 미충족 시 등록 금지.** 단어 조합 규칙으로만 식별자를 생성.

### 단어 조합 규칙

| 사용 위치 | 포맷 | 예시 |
|-----------|------|------|
| 변수명 / 함수명 | snake_case | `order_intent`, `get_position()` |
| 클래스명 | PascalCase | `OrderIntent`, `KrSignalEngine` |
| 환경변수 | UPPER_SNAKE | `KIS_AK`, `PG_DSN` |
| DB 테이블 | snake_case (단수) | `order_intent`, `fill` |

### 복수형 (Plural) 관리

단어 자체는 항상 **단수형**으로 등록. 복수형은 `plural` 필드로 관리.

```
AGENTS.md Rule 8-A 단수/복수 요약:
  폴더명·DB 테이블명 → 단수 강제 (STRICT)
  코드 변수·함수 등  → 의미 기반 (SEMANTIC: 컬렉션이면 복수 허용)
```

**코드에서의 복수형 사용 예시:**

```python
order  = Order()          # 단일 객체 → 단수
orders = list[Order]      # 컬렉션 → 복수 (허용)

# scan_terms.py가 'orders'를 만나면 → auto_plural 역변환 → 'order' 등록됨 인식
```

### suffix 사용 원칙

suffix는 **역할/의미**를 추가할 때만 사용. 타입 표현에는 사용하지 않음.

| 분류 | suffix | 사용 |
|------|--------|------|
| ✅ 강하게 권장 | `_queue`, `_stream`, `_pipeline` | 흐름/처리 역할 |
| ✅ 강하게 권장 | `_log`, `_history`, `_record`, `_trace` | 기록/이력 |
| ✅ 강하게 권장 | `_snapshot`, `_state`, `_status`, `_cache` | 상태/시점 |
| ✅ 강하게 권장 | `_registry`, `_store`, `_pool` | 관리/집합 |
| ⚠️ 조건부 허용 | `_set`, `_map` | 의미적 중요도 높을 때만 |
| ❌ 비권장 | `_list`, `_array`, `_dict`, `_tuple` | 타입 중심 → 복수형으로 대체 |

**예시:**

```python
# ✅ 권장
order_queue      # 처리 대기열 (역할 suffix)
execution_log    # 실행 이력 (의미 suffix)
price_snapshot   # 가격 스냅샷 (상태 suffix)
active_orders    # 활성 주문 목록 (복수형으로 충분)

# ❌ 비권장
order_list       # → active_orders 또는 orders 로
signal_array     # → signals 로
config_dict      # → configs 또는 config_map (key-value가 중요할 때만)
orders_list      # → 중복 표현 금지
```



혼동을 유발하는 표현을 명시적으로 금지. `dictionary/banned.json`에 등록.

| 금지 표현 | 올바른 표현 | 이유 |
|-----------|------------|------|
| `MT5_FUT` (마켓 의미) | `FX_FUT` | MT5는 플랫폼, 마켓 아님 |
| `KIS` (마켓 의미) | `KR_STOCK` | KIS는 브로커명 |
| `mt5Futures` (마켓 변수명) | `fxFutures` | 동일한 이유 |

---

## 4. 디렉토리 및 파일 구조

```
glossary/
│
├── dictionary/                     # 사전 파일 (핵심 데이터)
│   ├── words.json                  # 단어 사전 ← 수동 편집
│   ├── compounds.json              # 복합어 사전 ← 수동 편집
│   ├── banned.json                 # 금지표현 사전 ← 수동 편집
│   └── terms.json                  # 자동 생성 ← 수동 편집 금지
│
├── schema/                         # JSON Schema (검증용)
│   ├── word.schema.json
│   ├── compound.schema.json
│   └── banned.schema.json
│
├── bin/                            # 실행 스크립트
│   ├── run.py                      # 빌드 러너 (validate → generate)
│   ├── validate.py                 # 검증 래퍼 (CI용, generate_glossary 위임)
│   ├── scan_terms.py               # 소스 스캔 → 용어 후보 추출
│   └── batch_terms.py              # LLM API 호출 → terms_날짜.json 생성
│
├── web/                            # 웹 관리 UI
│   ├── server.py                   # Flask 서버 (포트 5000)
│   └── index.html                  # 단어/복합어/금지표현 관리 화면
│
├── log/                            # 서버 로그 (Git 제외)
│   └── glossary.log
│
├── generate_glossary.py            # 사전 생성·검증·조회 핵심 엔진
├── GLOSSARY.md                     # 자동 생성 ← 수동 편집 금지
├── .gitignore
├── .env.example                    # 환경변수 템플릿
├── README.md                       # 이 문서
└── glossary_rule.md                # 서브모듈 이용 지침 (프로젝트 참조용)
```

**Git 추적 대상 / 제외 대상:**

| 경로 | Git | 이유 |
|------|-----|------|
| `dictionary/*.json` | ✅ 추적 | 사전 원본 |
| `GLOSSARY.md` | ✅ 추적 | 자동 생성물이지만 가독성용 |
| `log/` | ❌ 제외 | 런타임 로그 |
| `.env` | ❌ 제외 | API 키 등 민감정보 |
| `__pycache__/` | ❌ 제외 | Python 캐시 |

---

## 5. 서브모듈 설치 및 설정

### 신규 프로젝트에 서브모듈 추가

```bash
# 1. 서브모듈 추가
git submodule add <glossary-repo-url> glossary

# 2. 커밋
git add .gitmodules glossary
git commit -m "chore: add glossary submodule"
```

### 기존 프로젝트 클론 후 초기화

```bash
# 방법 A: 클론 시 한 번에
git clone --recurse-submodules <project-repo-url>

# 방법 B: 클론 후 초기화
git clone <project-repo-url>
cd <project>
git submodule update --init --recursive
```

### 서브모듈 업데이트 (최신 사전 반영)

```bash
# glossary 최신 커밋으로 업데이트
git submodule update --remote glossary

# 프로젝트에 반영
git add glossary
git commit -m "chore: update glossary submodule"
```

### Python 패키지 설치

```bash
pip install flask pyyaml
```

---

## 6. 빠른 시작

### 환경 설정

```bash
# 1. .env 파일 생성 (프로젝트 루트 또는 glossary/)
cp glossary/.env.example .env

# 2. .env 편집 — 최소 필수 항목
PROJ_ROOT=C:\project\ts          # Windows
# PROJ_ROOT=/home/user/ts        # Linux/Mac
```

### 웹 UI 실행

```bash
# 서버 시작
python glossary/web/server.py

# 접속
http://localhost:5000
```

### 검증 + 재생성

```bash
# validate → generate 한 번에
python glossary/bin/run.py

# validate만
python glossary/bin/run.py --check

# generate_glossary.py 직접 사용
python glossary/generate_glossary.py validate
python glossary/generate_glossary.py generate
```

---

## 7. 웹 UI 사용법

### 화면 구성

```
┌──────────────────────────────────────────────────────────┐
│ BOM_TS glossary   [통계]  [브랜치]  [check-id] [log]     │
│                          [batch]   [commit & push]       │
├──────────────────────────────────────────────────────────┤
│ [단어]  [복합어]  [금지표현]          [▷ generate] [▷ validate] │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  테이블 (검색 / 필터 / 정렬)                              │
│                                                          │
│  행 클릭     → 상세 펼치기                                │
│  행 더블클릭 → 수정 모달                                  │
│  🗑 버튼     → 삭제 확인                                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 탭별 기능

| 탭 | 표시 정보 | 필터 |
|----|-----------|------|
| 단어 | id, 영문, 한글, 약어, 품사, domain, 설명 | domain / 품사 / 검색 |
| 복합어 | id, 구성단어, 한글, abbr_long, abbr_short, domain, 설명 | domain / 검색 |
| 금지표현 | 금지표현, 문맥, 올바른 표현, 사유 | 검색 |

### 단어 추가

1. **[+ 단어 추가]** 버튼 클릭
2. 필드 입력 (id, 영문, 한글, 품사, domain, 설명 필수)
3. **[저장]** → `dictionary/words.json` 즉시 반영
4. **[▷ generate]** → `terms.json` + `GLOSSARY.md` 재생성

### check-id 사용

1. **[⊙ check-id]** 버튼 클릭
2. 식별자 입력 (예: `kill_switch_manager`)
3. **[check-id]** → 단어 분해 + 등록 여부 확인
4. **[suggest]** → 미등록 단어 JSON 제안 출력

### commit & push

1. **[⎇ commit & push]** 버튼 클릭
2. 변경 파일 목록 확인
3. 커밋 메시지 입력 (템플릿 버튼 제공)
4. **[commit + push]** → 자동으로 validate → generate → git add → commit → push

---

## 8. 커맨드라인 사용법

### generate_glossary.py 명령어

```bash
# GLOSSARY.md + terms.json 생성 (validate 포함)
python glossary/generate_glossary.py generate

# 검증만 (CI용, FATAL 있으면 exit 1)
python glossary/generate_glossary.py validate

# 통계 출력
python glossary/generate_glossary.py stats

# 식별자 단어 분해 + 등록 여부 확인
python glossary/generate_glossary.py check-id kill_switch
python glossary/generate_glossary.py check-id entry_decision_logger

# 미등록 단어 JSON 제안 출력
python glossary/generate_glossary.py suggest breakout_detector

# 기존 terms.json 마이그레이션
python glossary/generate_glossary.py migrate-from-legacy old_terms.json
```

### check-id 출력 예시

```
식별자: entry_decision_logger
분해:   ['entry', 'decision', 'logger']

  entry                → [OK]  words.json (trading, noun, "진입")
  decision             → [미등록]
  logger               → [OK]  words.json (system, noun, "로거")

미등록 단어 1개: ['decision']
→ words.json에 등록 후 사용 가능합니다.
→ python generate_glossary.py suggest entry_decision_logger
```

### run.py 옵션

```bash
python glossary/bin/run.py              # validate → generate
python glossary/bin/run.py --check      # validate만
python glossary/bin/run.py --force      # validate 실패해도 generate 강행
python glossary/bin/run.py --watch      # dictionary/ 변경 감지 자동 재실행
python glossary/bin/run.py --watch --interval 2.0   # 감지 주기 2초
```

---

## 9. 용어 등록 절차

### 신규 식별자 생성 워크플로우

```
1. check-id 실행
   python glossary/generate_glossary.py check-id <식별자>

2. 결과 확인
   ├─ 모두 [OK] → 식별자 바로 사용 가능
   └─ [미등록] 있음 → 3단계로

3. 미등록 단어 등록
   suggest 실행 → JSON 제안 확인 →
   웹 UI [단어 탭] → [+ 단어 추가] → 저장

4. 복합어 등록 여부 판단
   5개 조건 중 하나 이상 해당하면 → 웹 UI [복합어 탭] → [+ 복합어 추가]
   해당 없으면 → 단어 조합 규칙으로 식별자 생성 (등록 불필요)

5. generate 실행
   python glossary/generate_glossary.py generate
   (또는 웹 UI [▷ generate])

6. 커밋
   웹 UI [⎇ commit & push] 또는
   git add glossary/dictionary/ && git commit -m "feat: 단어 추가 (decision)"
```

### 승인 레벨

| 작업 | 승인 필요 |
|------|-----------|
| 기존 단어 조합으로 식별자 생성 | 불필요 |
| words.json 새 단어 추가 | **사용자 승인** |
| compounds.json 복합어 추가 | **사용자 승인** |
| 기존 단어/복합어 수정·삭제 | **사용자 승인** |

---

## 10. 배치 추출 (batch)

소스 코드 전체를 스캔해서 미등록 용어 후보를 LLM으로 분류하는 자동화 도구.

### 실행 순서

```
1. 스캔 (API 없이)
   python glossary/bin/scan_terms.py --count     # 후보 수 확인
   python glossary/bin/scan_terms.py             # 상세 목록

2. 토큰 예상치 확인 (API 없이)
   python glossary/bin/batch_terms.py --dry-run

3. 실제 분석 (API 호출)
   python glossary/bin/batch_terms.py

4. 결과 확인
   프로젝트루트/tmp/terms/terms_날짜.json

5. 병합
   웹 UI → [⚙ batch] → [결과 파일 탭] → [병합 →]
```

### .env 설정 (배치용)

```ini
# API 종류: claude | openai | google
API_KEY_TYPE=google
API_MODEL=gemini-2.0-flash       # 비워두면 API별 기본값

GOOGLE_API_KEY=여기에입력
ANTHROPIC_API_KEY=여기에입력
OPENAI_API_KEY=여기에입력

PROJ_ROOT=C:\project\ts
BATCH_CHUNK_SIZE=300             # 청크당 후보 수
MAX_OUTPUT_TOKENS=8192           # 응답 최대 토큰
```

### 스캔 제외 설정

```ini
# 완전 제외 (내용도 파일명도 안 봄)
EXCLUDE_DIRS=backup,data,test,lib_test,tmp,glossary,.git,__pycache__,node_modules,.venv,venv

# 파일명만 보는 폴더 (내용 스캔 안 함)
EXCLUDE_FILE_CONTENT=cache,log

# 확장자 제외
EXCLUDE_EXTENSIONS=.md,.txt,.log,.csv,.tsv,.png,.jpg,.jpeg,.gif,.pdf,.ico,.svg,.zip,.tar
```

### 스캔 대상 (소스별)

| 소스 | 추출 대상 |
|------|-----------|
| `.py` | 클래스명, public 함수명, self.속성명 |
| `.yaml` | 상위 2단계 키만 |
| `.env` | 환경변수명 (키) |
| `.sql` | CREATE TABLE 테이블명, 컬럼명 |
| `.py` 파일명 | 스템만 (예: `kis_adapter.py` → `kis_adapter`) |

---

## 11. 검증 규칙

`generate_glossary.py validate` 실행 시 적용.

### FATAL — 실패 시 generate 중단

| 코드 | 규칙 |
|------|------|
| V-001 | `words.json` id 고유성 |
| V-002 | `compounds.json` id 고유성 |
| V-003 | words ↔ compounds id 충돌 없음 |
| V-004 | `compounds.words[]` 참조가 words.json에 존재 |
| V-005 | `compounds.reason` 비어있지 않음 |
| V-006 | abbr 중복 없음 (words 내, compounds 내, cross) |
| V-007 | `words.json` id 형식: `^[a-z][a-z0-9]*$` (언더스코어/대문자/숫자시작 금지) |
| V-008 | `words.json` 복수형 단독 항목 금지 (단수형 이미 등록된 경우) |

### WARN — 경고만, generate 계속

| 코드 | 규칙 |
|------|------|
| V-101 | 고아 단어 (어떤 compound에서도 미참조) |
| V-102 | `banned.correct`가 words/compounds에 존재 |
| V-103 | `not[]` 값이 다른 id와 충돌 |
| V-104 | noun인데 `plural` 필드 미설정 |
| V-105 | `plural` 값이 자동추론값과 동일 → null로 대체 권장 |

---

## 12. 환경 설정 (.env)

`.env.example`을 복사해서 `.env`를 만드세요. `.env`는 Git에 포함되지 않습니다.

```ini
# ── API 설정 ─────────────────────────────────────
API_KEY_TYPE=google           # claude | openai | google
API_MODEL=                    # 비워두면 API별 기본값
                              # claude: claude-sonnet-4-20250514
                              # openai: gpt-4o
                              # google: gemini-2.0-flash

ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
OPENAI_API_KEY=

# ── 경로 ─────────────────────────────────────────
PROJ_ROOT=                    # 프로젝트 루트 (비워두면 glossary 상위 자동감지)

# ── 스캔 제외 ─────────────────────────────────────
EXCLUDE_DIRS=backup,data,test,lib_test,tmp,glossary,.git,__pycache__,node_modules,.venv,venv
EXCLUDE_FILE_CONTENT=cache,log
EXCLUDE_EXTENSIONS=.md,.txt,.log,.csv,.tsv,.png,.jpg,.jpeg,.gif,.pdf,.ico,.svg,.zip,.tar

# ── 배치 설정 ─────────────────────────────────────
BATCH_CHUNK_SIZE=300
MAX_OUTPUT_TOKENS=8192
```

---

## 13. Git 운영 가이드

### 서브모듈 커밋 흐름

```bash
# glossary 내에서 변경 후
cd glossary
git add dictionary/words.json dictionary/compounds.json
git commit -m "feat: 단어 추가 (decision, tracker)"
git push

# 프로젝트에서 서브모듈 포인터 업데이트
cd ..
git add glossary
git commit -m "chore: update glossary submodule"
git push
```

### 웹 UI commit & push 사용 시

웹 UI의 **[⎇ commit & push]** 버튼은 내부적으로 아래를 순서대로 실행합니다:

1. `generate_glossary.py validate` — FATAL 있으면 중단
2. `generate_glossary.py generate` — terms.json + GLOSSARY.md 재생성
3. `git add dictionary/*.json GLOSSARY.md`
4. `git commit -m <입력한 메시지>`
5. `git push` (실패 시 `git pull --rebase` 후 재시도)

### .gitignore 기본 설정

```
log/
*.log
.env
__pycache__/
*.pyc
```

### 커밋 메시지 컨벤션

| 접두사 | 용도 |
|--------|------|
| `feat:` | 단어/복합어 신규 추가 |
| `fix:` | 약어/설명/분류 수정 |
| `refactor:` | 구조 개선 (내용 변경 없음) |
| `chore:` | generate 재실행, 자동 생성 업데이트 |
| `docs:` | README, GLOSSARY.md 업데이트 |

---

## 14. 운영 FAQ

**Q. terms.json을 직접 편집해도 되나요?**
A. 안 됩니다. `terms.json`은 자동 생성 파일입니다. `words.json` 또는 `compounds.json`을 편집한 후 generate를 실행하세요.

**Q. GLOSSARY.md를 직접 편집해도 되나요?**
A. 안 됩니다. generate 실행 시 덮어씌워집니다.

**Q. 단어를 삭제하면 어떻게 되나요?**
A. 해당 단어를 참조하는 compound가 있으면 V-004 FATAL이 발생합니다. compound에서 먼저 제거 후 단어를 삭제하세요.

**Q. 기존 코드의 식별자가 사전에 없어요. 모두 등록해야 하나요?**
A. 기존 코드는 소급 적용하지 않습니다. 신규 식별자 생성 시부터 적용하면 됩니다. 배치 추출 도구(`batch_terms.py`)로 일괄 정리할 수 있습니다.

**Q. AI 에이전트가 check-id를 자동으로 실행하나요?**
A. `AGENTS.md Rule 8-B`에 따라 Codex, Gemini, Claude 에이전트는 신규 식별자 생성 전 `check-id`를 의무적으로 실행합니다.

**Q. `git pull --rebase` 충돌이 발생했어요.**
A. 터미널에서 수동으로 `git pull --rebase` 후 충돌 파일을 편집해 해결하세요. JSON 파일은 충돌 구간을 수동으로 합쳐야 합니다.

**Q. 서버 포트를 바꾸고 싶어요.**
A. `python glossary/web/server.py --port 8080` 으로 실행하세요.

**Q. 배치 분석에서 0개 용어가 추출됐어요.**
A. `tmp/terms/raw_날짜.txt` 파일을 열어 API 응답 원문을 확인하세요. JSON이 잘렸다면 `.env`의 `MAX_OUTPUT_TOKENS`를 늘리세요 (권장: 8192).

---

*이 문서는 BOM_TS Glossary v2 기준입니다.*
*문서 버전: 2026-04-10*
