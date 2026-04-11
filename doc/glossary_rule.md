# glossary_rule.md — BOM_TS Glossary 서브모듈 이용 지침

> 위치: `glossary/glossary_rule.md`
> 대상: BOM_TS 프로젝트에 참여하는 개발자 및 AI 에이전트
> 상위 지침: `AGENTS.md Rule 8-B`, `doc/guidelines/06_glossary_rules.md`

---

## ★ 절대 규칙 (ABSOLUTE RULES)

> 아래 규칙은 예외 없이 반드시 준수한다.
> AI 에이전트는 이 규칙을 workflow로 인식하고 자동 실행한다.

```
1. 모든 식별자는 glossary/dictionary/words.json 에 등록된 단어의 조합으로만 생성한다.
2. 신규 식별자 생성 전 반드시 check-id 를 실행한다.
3. 사전에 없는 단어는 사용자 승인 후 등록한다.
4. dictionary/terms.json 은 자동 생성 파일이다 — 수동 편집 절대 금지.
5. 복합어는 5가지 조건 중 하나 이상을 충족할 때만 등록한다.
6. words.json 의 단어 id 는 반드시 단수형이며 언더스코어 없이 영소문자+숫자만 허용한다.
   형식: ^[a-z][a-z0-9]*$  예) order(O)  orders(X)  order_intent(X)
7. 복수형은 코드에서 컬렉션 표현 시 사용 가능하나, words.json 에는 단수형만 등록한다.
```

---

## 1. 사전 구조

| 파일 | 역할 | 편집 |
|------|------|------|
| `glossary/dictionary/words.json` | 단어 원자 단위 (최소 단위, **단수형+언더스코어 없음**) | ✅ 수동 |
| `glossary/dictionary/compounds.json` | 복합어 (조건부 등록) | ✅ 수동 |
| `glossary/dictionary/banned.json` | 금지표현 | ✅ 수동 |
| `glossary/dictionary/terms.json` | 하위호환 통합본 | ❌ 자동 생성 |
| `glossary/GLOSSARY.md` | 사람이 읽는 사전 | ❌ 자동 생성 |

---

## 2. 식별자 생성 절차 (MANDATORY WORKFLOW)

### 2-1. 신규 식별자가 필요할 때

```bash
# Step 1: 단어 분해 + 등록 여부 확인
python glossary/generate_glossary.py check-id <식별자>

# 예시
python glossary/generate_glossary.py check-id entry_decision_logger
```

**결과 해석:**

```
식별자: entry_decision_logger
분해:   ['entry', 'decision', 'logger']

  entry     → [OK]   words.json (trading, noun, "진입")
  decision  → [미등록]
  logger    → [OK]   words.json (system, noun, "로거")

미등록 단어 1개: ['decision']
```

### 2-2. 미등록 단어가 있을 때

```bash
# Step 2: 등록 제안 생성
python glossary/generate_glossary.py suggest entry_decision_logger
```

→ JSON 제안 출력됨 → 사용자 승인 → `words.json`에 추가

```bash
# Step 3: 복합어 등록 여부 판단 (아래 §4 참조)
# 조건 미충족이면 등록 없이 단어 조합으로 식별자 생성

# Step 4: generate 실행
python glossary/generate_glossary.py generate
```

### 2-3. AI 에이전트 자동 실행 규칙

```
신규 식별자 생성 전:
  → python glossary/generate_glossary.py check-id <식별자> 실행 필수

미등록 단어 발견 시:
  → 즉시 작업 중단
  → 사용자에게 미등록 단어 보고
  → 등록 제안 출력
  → 승인 받기 전 식별자 생성 금지

완료 후:
  → python glossary/generate_glossary.py validate 실행
  → FATAL 없음 확인 후 커밋
```

---

## 3. 식별자 포맷 규칙

### 3-1. 단어 조합 포맷

| 사용 위치 | 포맷 | 예시 |
|-----------|------|------|
| 변수명 | snake_case | `order_intent`, `kill_switch` |
| 함수명 | snake_case | `get_order_intent()`, `activate_kill_switch()` |
| 클래스명 | PascalCase | `OrderIntent`, `KrSignalEngine` |
| 모듈(파일)명 | snake_case | `order_intent.py`, `kis_adapter.py` |
| DB 테이블명 | snake_case **단수형** | `order`, `fill`, `position` |
| DB 컬럼명 | snake_case | `realized_pnl`, `order_id` |
| 환경변수명 | UPPER_SNAKE_CASE | `KIS_AK`, `PG_DSN`, `KR_STOCK` |
| config 키 | snake_case | `kr_strategy`, `stop_loss_rate` |
| JSON/API 필드 | snake_case | `order_intent`, `fill_price` |

### 3-2. words.json id 형식 (V-007 / V-008)

```
허용 패턴: ^[a-z][a-z0-9]*$
  - 영소문자로 시작
  - 영소문자 + 숫자만 허용
  - 언더스코어 금지 (단어 = 단일 토큰)
  - 복수형 단독 등록 금지

예시:
  ✅ order, fill, signal, kill, topn
  ❌ order_intent  (언더스코어 → compound에 등록)
  ❌ orders        (복수형 → 단수형 등록 후 plural 필드로 관리)
  ❌ 1m            (숫자 시작 → 사전 등록 불가)
```

### 3-3. plural 필드 (noun 전용)

| plural 값 | 의미 | 예시 |
|-----------|------|------|
| `null` | 자동 추론 (+s/+es/+ies) | `order` → `orders` |
| 문자열 | 불규칙 복수형 명시 | `index` → `"indices"` |
| `"-"` | 불가산 (복수형 없음) | `risk`, `config`, `info` |

```json
{"id": "order",    "pos": "noun", "plural": null,      ...}
{"id": "index",    "pos": "noun", "plural": "indices",  ...}
{"id": "risk",     "pos": "noun", "plural": "-",        ...}
{"id": "activate", "pos": "verb"                        ...}
```

### 3-4. 단수/복수 사용 원칙 (AGENTS.md Rule 8-A)

| 영역 | 규칙 | 예시 |
|------|------|------|
| 폴더명 | **단수 강제** | `log/`, `test/`, `script/` |
| DB 테이블명 | **단수 강제** | `order`, `fill`, `position` |
| 코드 변수/함수 | **의미 기반** | `orders = list[Order]` (컬렉션이면 복수 허용) |
| words.json id | **단수 강제** | `order`(O), `orders`(X) |

### 3-5. suffix 사용 원칙

suffix는 **역할/의미** 추가 시에만 사용. 타입 표현에는 사용 금지.

| 분류 | suffix 목록 | 사용 |
|------|-------------|------|
| ✅ 강하게 권장 | `_queue`, `_stream`, `_pipeline` | 흐름/처리 역할 |
| ✅ 강하게 권장 | `_log`, `_history`, `_record`, `_trace` | 기록/이력 |
| ✅ 강하게 권장 | `_snapshot`, `_state`, `_status`, `_cache` | 상태/시점 |
| ✅ 강하게 권장 | `_registry`, `_store`, `_pool` | 관리/집합 |
| ⚠️ 조건부 허용 | `_set`, `_map` | key-value/중복제거가 의미적으로 중요할 때 |
| ❌ 비권장 | `_list`, `_array`, `_dict`, `_tuple` | 타입 중심 → 복수형으로 대체 |

```python
# ✅ 권장
order_queue   = deque()          # 처리 대기열 (역할 suffix)
signal_log    = []               # 이력 (의미 suffix)
active_orders = list[Order]      # 컬렉션 (복수형으로 충분)

# ❌ 비권장
order_list    = []   # → active_orders 또는 orders 로
signal_array  = []   # → signals 로
orders_list   = []   # → 중복 표현 금지
```

### 3-6. 허용 문자 및 구분자 규칙

```
허용:  a-z, 0-9, underscore (_)
금지:  하이픈(-), 공백, 특수문자

snake_case  → 소문자 + underscore
PascalCase  → 영문 대소문자 (구분자 없음)
UPPER_SNAKE → 대문자 + underscore
```

### 3-7. 단어 순서 규칙

| 패턴 | 예시 |
|------|------|
| 수식어 → 피수식어 | `kr_stock`, `daily_report` |
| 동사 → 목적어 | `get_position`, `close_trade` |
| 주체 → 역할 | `risk_manager`, `signal_engine` |
| 범위(대) → 범위(소) | `market_session`, `account_snapshot` |

### 3-8. 폴더명 단수형 강제

> `AGENTS.md Rule 8-A`: 모든 디렉토리명은 단수형을 사용한다.

| 금지 | 올바른 표현 |
|------|------------|
| `logs/` | `log/` |
| `tests/` | `test/` |
| `scripts/` | `script/` |
| `tools/` | `tool/` |

---

## 4. 복합어 등록 조건

아래 **5가지 조건 중 하나 이상**을 충족할 때만 `compounds.json`에 등록.
**조건 미충족 시 등록 금지** — 단어 조합 규칙으로 식별자를 만든다.

| # | 조건 | 판단 기준 | 예시 |
|---|------|----------|------|
| 1 | **의미 비합산** | 단어를 합쳐도 이 개념의 의미가 안 됨 | `kill_switch` |
| 2 | **공인 약어** | 도메인에서 통용되는 약어 존재 | `stop_loss` → SL |
| 3 | **혼동 방지** | 금지표현과 구분이 필요 | `fx_futures` vs `mt5_futures` |
| 4 | **시스템 객체** | Pydantic 모델, DB 테이블 등 공식 객체명 | `order_intent` |
| 5 | **고유명사** | 외부 시스템/서비스 고유 명칭 | `telegram_bot` |

### 등록 금지 예시

```
# 단어 조합만으로 의미 명확 → 등록 불필요
entry_price   = entry + price      (단순 조합, 의미 명확)
daily_limit   = daily + limit      (단순 조합, 의미 명확)
market_open   = market + open      (단순 조합, 의미 명확)

# 복합어 등록 필요
kill_switch   = kill + switch      (시스템 고유 메커니즘)
stop_loss     = stop + loss        (도메인 공인 약어 SL)
fx_futures    = fx + futures       (혼동 방지 — MT5_FUT 금지)
```

---

## 5. 금지표현 (Banned)

아래 표현은 사용이 금지됩니다. `dictionary/banned.json`에 정의.

| 금지 표현 | 문맥 | 올바른 표현 | 이유 |
|-----------|------|------------|------|
| `MT5_FUT` | 마켓 식별자 | `FX_FUT` | MT5는 플랫폼, 마켓 아님 |
| `mt5Futures` | 변수명 | `fxFutures` | 동일 |
| `KIS` | 한국주식 마켓 의미 | `KR_STOCK` | KIS는 브로커명 |
| `MT5` | 외환선물 마켓 의미 | `FX_FUT` | MT5는 MetaTrader5 플랫폼명 |
| `VOL` | 변동성(volatility) 단독 | `VOLS` 또는 context 명시 | volume과 혼동 |
| `TS` | trailing/tracking 단독 | 문맥에 따라 명시 | 두 개념 혼동 |

---

## 6. 약어 사용 기준

| 사용 위치 | 약어 종류 | 형식 |
|-----------|-----------|------|
| 변수명 / 함수명 / 클래스명 | `abbr_long` (camelCase) | `orderIntent`, `killSwitch` |
| 환경변수명 | `abbr_short` (UPPER_SNAKE) | `KIS_AK`, `KR_STOCK` |
| 설정 파일 키 | `abbr_short` (snake_case) | `kr_strategy` |

### 마켓별 약어

| 마켓 | abbr_long | abbr_short | 금지 |
|------|-----------|------------|------|
| 한국주식 | `krStock` | `KR_STOCK` | `KIS`, `KOSPI` |
| 미국주식 | `usStock` | `US_STOCK` | — |
| 외환선물 | `fxFutures` | `FX_FUT` | `MT5`, `MT5_FUT` |
| 암호화폐 | `crypto` | `CRYPTO` | `coin`, `virtual` |

---

## 7. 검증 명령어

```bash
# 검증 + 생성 (표준 워크플로우)
python glossary/bin/run.py

# 검증만 (CI/CD)
python glossary/generate_glossary.py validate

# 식별자 단어 분해 확인
python glossary/generate_glossary.py check-id <식별자>

# 미등록 단어 제안
python glossary/generate_glossary.py suggest <식별자>

# 통계
python glossary/generate_glossary.py stats
```

**검증 규칙 요약 (V-001 ~ V-105):**

| 코드 | 규칙 | 수준 |
|------|------|------|
| V-001 | words id 고유 | FATAL |
| V-002 | compounds id 고유 | FATAL |
| V-003 | words ↔ compounds id 충돌 없음 | FATAL |
| V-004 | compounds.words[] 참조가 words에 존재 | FATAL |
| V-005 | compounds.reason 비어있지 않음 | FATAL |
| V-006 | abbr 중복 없음 | FATAL |
| V-007 | words id 형식: `^[a-z][a-z0-9]*$` | FATAL |
| V-008 | words 복수형 단독 항목 금지 | FATAL |
| V-101 | 고아 단어 (compound 미참조) | WARN |
| V-102 | banned.correct 미등록 | WARN |
| V-103 | not[] 값이 id와 충돌 | WARN |
| V-104 | noun인데 plural 필드 없음 | WARN |
| V-105 | plural 값이 자동추론과 동일 → null 권장 | WARN |

---

## 8. 서브모듈 Git 운영

### 사전 변경 후 커밋

```bash
# 1. glossary 디렉토리에서 커밋
cd glossary
git add dictionary/words.json dictionary/compounds.json dictionary/banned.json
git commit -m "feat: 단어 추가 (decision)"
git push

# 2. 프로젝트에서 서브모듈 포인터 업데이트
cd ..
git add glossary
git commit -m "chore: update glossary"
git push
```

### 서브모듈 최신화

```bash
# 원격의 최신 사전 반영
git submodule update --remote glossary
git add glossary
git commit -m "chore: update glossary submodule"
```

### 커밋 메시지 컨벤션

```
feat:     단어/복합어 신규 추가
fix:      약어/설명/분류 수정
refactor: 구조 개선 (내용 변경 없음)
chore:    generate 재실행, 자동 생성 업데이트
```

---

## 9. domain 분류 기준

| domain | 대상 영역 | 예시 단어 |
|--------|-----------|-----------|
| `trading` | 매매·주문·포지션·리스크 | order, fill, stop, loss, profit, position |
| `market` | 시장·종목·가격·데이터 | bar, tick, candle, volume, sector, stock |
| `system` | 시스템 운영·상태·설정 | config, kill, switch, log, guard, status |
| `infra` | 외부 서비스·DB·인증 | redis, api, token, auth, proxy, bridge |
| `ui` | 대시보드·리포트·표시 | dashboard, chart, report, display |
| `general` | 범용 영어 단어 | get, set, max, min, daily, count |
| `proper` | 고유명사 | kis, mt5, upbit, telegram, gemini |

---

## 10. 위반 처리

| 위반 유형 | 처리 방법 |
|-----------|-----------|
| 미등록 단어로 식별자 생성 | 즉시 중단, 사용자 보고, 승인 후 등록 |
| 금지표현 사용 | 즉시 수정, 올바른 표현으로 교체 |
| 복합어 조건 미충족 등록 | 해당 compound 삭제, 단어 조합으로 대체 |
| terms.json 수동 편집 | 즉시 되돌리기, generate 재실행 |
| 폴더명 복수형 사용 | 즉시 수정 (logs → log, tests → test) |
| words.json id에 언더스코어 포함 | V-007 FATAL → 즉시 수정 (단어 = 단일 토큰) |
| words.json에 복수형 단독 등록 | V-008 FATAL → 삭제 후 단수형으로 등록 |
| plural 필드 누락 (noun) | V-104 WARN → plural 필드 추가 |
| `_list`, `_array`, `_dict` suffix 신규 사용 | 비권장 → 복수형 또는 의미 suffix로 대체 |
| `orders_list` 등 중복 표현 | 즉시 수정 → `orders` 또는 `order_queue` 등으로 |

---

*BOM_TS Glossary v2 | 2026-04-10*
