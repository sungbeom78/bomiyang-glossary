# antigravity – 용어 사전 (Glossary)

> 프로젝트 전체 용어 사전. 코드·DB·설정·문서에서 용어 통일의 기준.
>
> **버전:** 1.0.0  |  **최종 수정:** 2026-03-20
>
> ⚠️  이 파일은 `terms.json`으로부터 자동 생성됩니다. 직접 편집하지 마세요.

## 📌 약어 사용 규칙

| 약어 종류 | 사용 위치 |
|-----------|-----------|
| `abbr_long` | variable, table, column, class, function, module |
| `abbr_short` | env, filename, config_key |

## 🔄 기존 용어에서 수정된 사항

| 기존 (잘못된 용어) | 수정 후 | 이유 |
|-------------------|---------|------|
| `mt5Futures` / `MT5_FUT` | `fxFutures` / `FX_FUT` | MT5는 툴(플랫폼)이며 마켓이 아님 |

## ⚠️  abbr_short 중복 주의 (동일 개념 다계층)

아래 약어는 동일 개념의 다른 계층(도메인↔DB↔클래스↔모듈)에서 공유됩니다. 컨텍스트로 구분하세요.

| abbr_short | 공유 용어들 |
|------------|-------------|
| `ASNAP` | `db_account_snapshots`, `cls_account_snapshot` |
| `CFG` | `settings`, `mod_config`, `cls_settings` |
| `DIR` | `signal_direction`, `cls_signal_direction` |
| `ENV` | `env_var`, `mod_env` |
| `FILL` | `fill`, `db_fills` |
| `LOG` | `realtime_log`, `mod_logs` |
| `MKT` | `market_order`, `cls_market` |
| `MT5B` | `mt5_bridge`, `cls_mt5_bridge` |
| `MT5P` | `mt5_proxy`, `env_mt5_proxy_url` |
| `NODE` | `node_name`, `env_node_name` |
| `OFF` | `disabled`, `offline` |
| `OI` | `order_intent`, `cls_order_intent` |
| `ON` | `overnight`, `enabled`, `online` |
| `ORD` | `order`, `db_orders` |
| `OS` | `order_status`, `cls_order_status` |
| `RPT` | `mod_report`, `cfg_reporting` |
| `SEC_RNK` | `sector_ranking`, `cls_sector_ranker` |
| `SIG` | `signal`, `db_signals`, `mod_signals` |
| `SYM_RNK` | `symbol_ranking`, `cls_symbol_ranker` |
| `TK` | `tick`, `db_ticks` |

## 목차

1. [🌐 시장 / 마켓 (Markets)](#시장--마켓-markets)
2. [🔧 툴 / 플랫폼 (Tools & Platforms)](#툴--플랫폼-tools--platforms)
3. [🏗️  인프라 (Infrastructure)](#인프라-infrastructure)
4. [📐 도메인 개념 (Domain Concepts)](#도메인-개념-domain-concepts)
5. [📋 거래 / 주문 (Trading & Orders)](#거래--주문-trading--orders)
6. [🛡️  리스크 관리 (Risk Management)](#리스크-관리-risk-management)
7. [📊 시장 데이터 (Market Data)](#시장-데이터-market-data)
8. [💰 계좌 / 잔고 (Account & Balance)](#계좌--잔고-account--balance)
9. [⚙️  시스템 운영 (System Operation)](#시스템-운영-system-operation)
10. [🔑 설정 / 환경변수 (Config & Env)](#설정--환경변수-config--env)
11. [📈 리포트 / 알림 (Report & Notification)](#리포트--알림-report--notification)
12. [📁 모듈 / 디렉토리 (Modules & Directories)](#모듈--디렉토리-modules--directories)
13. [🧩 클래스 / 열거형 (Classes & Enums)](#클래스--열거형-classes--enums)
14. [🕐 세션 / 시간 (Sessions & Time)](#세션--시간-sessions--time)
15. [🔍 종목 선정 / 스코어링 (Selector & Scoring)](#종목-선정--스코어링-selector--scoring)
16. [🚦 상태값 (Status Values)](#상태값-status-values)

---

## 🌐 시장 / 마켓 (Markets)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 미국주식 | `US Stock` | `usStock` | `US_STOCK` | `market` | 미국 주식 시장 (NYSE, NASDAQ 등) |
| 외환선물 | `FX Futures` | `fxFutures` | `FX_FUT` | `market` | 외환을 기초자산으로 하는 선물 상품. 접근 툴은 MT5이나, 시장 자체는 MT5가 아님. ❌ NOT: `MT5`, `mt5Futures`, `MT5_FUT` *(⚠️ 기존 glossary.md의 mt5Futures/MT5_FUT는 툴명이 혼입된 것으로 fxFutures/FX_FUT로 정정)* |
| 코스닥 | `KOSDAQ` | `kosdaq` | `KOSDAQ` | `market`, `data` | 코스닥 시장 지수 ❌ NOT: `KOSPI` |
| 코스피 | `KOSPI` | `kospi` | `KOSPI` | `market`, `data` | 한국 종합주가지수 (Korea Composite Stock Price Index) ❌ NOT: `KOSDAQ` |
| 코인거래 | `Cryptocurrency` | `crypto` | `CRYPTO` | `market` | 암호화폐 거래 시장 |
| 한국주식 | `Korean Stock` | `krStock` | `KR_STOCK` | `market` | 한국 주식 시장 (KRX) ❌ NOT: `KIS`, `KOSPI`, `KOSDAQ` |

---

## 🔧 툴 / 플랫폼 (Tools & Platforms)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| MT5 브릿지 | `MT5 Bridge` | `mt5Bridge` | `MT5B` | `tool`, `infra`, `class` | MT5와 자동매매 시스템을 연결하는 브릿지 컴포넌트 |
| MT5 프록시 | `MT5 Proxy Server` | `mt5Proxy` | `MT5P` | `tool`, `infra` | MT5 브로커와의 통신을 중계하는 프록시 서버 |
| 메타트레이더5 | `MetaTrader 5` | `mt5` | `MT5` | `tool`, `infra` | 외환선물 거래를 위한 브로커 연결 플랫폼. 마켓이 아닌 툴. ❌ NOT: `fxFutures`, `FX_FUT` |
| 앱 시크릿 | `App Secret` | `appSecret` | `AS` | `tool`, `config` | API 애플리케이션 시크릿 키 |
| 앱 키 | `App Key` | `appKey` | `AK` | `tool`, `config` | API 애플리케이션 키 |
| 인증 | `Authentication` | `auth` | `AUTH` | `tool`, `infra`, `system` | API 접근을 위한 인증 처리 |
| 접근 토큰 | `Access Token` | `accessToken` | `TOKEN` | `tool`, `config` | API 호출에 사용하는 OAuth 토큰 |
| 한국투자증권 API | `KIS API` | `kisApi` | `KIS` | `tool`, `infra` | 한국투자증권(Korea Investment & Securities) 연동 API |

---

## 🏗️  인프라 (Infrastructure)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 노드명 | `Node Name` | `nodeName` | `NODE` | `infra`, `config` | 분산 환경에서 각 머신/컨테이너를 식별하는 이름 |
| 대시보드 | `Dashboard` | `dashboard` | `DASH` | `infra`, `report` | 시스템 상태 및 거래 현황 모니터링 UI |
| 데이터베이스 | `Database` | `database` | `DB` | `infra`, `data` | PostgreSQL 기반 영구 저장소 ❌ NOT: `Redis`, `realtimeLog` |
| 서비스 관리자 | `Service Manager` | `serviceManager` | `SVC_MGR` | `infra`, `system`, `class` | 개별 서비스의 기동·중지·상태를 관리 |
| 설정 | `Settings / Configuration` | `settings` | `CFG` | `infra`, `config` | 시스템 설정값. settings.yaml 기반 Singleton 객체 |
| 실시간 로그 | `Real-time Log` | `realtimeLog` | `LOG` | `infra`, `system` | Redis 기반 실시간 로그 스트림 ❌ NOT: `database`, `DB` |
| 역할 | `Role` | `role` | `ROLE` | `infra`, `system`, `config` | 노드 또는 서비스에 부여된 역할 (예: master, worker) |
| 오케스트레이터 | `Orchestrator` | `orchestrator` | `ORCH` | `infra`, `system`, `class` | 전체 거래 흐름을 조율하는 최상위 제어 컴포넌트 |
| 워치독 | `Watchdog` | `watchdog` | `WDG` | `infra`, `system` | 하트비트 누락 등 이상 감지 시 조치를 취하는 감시 컴포넌트 |
| 작업 스케줄러 | `Task Scheduler` | `taskScheduler` | `SCHED` | `infra`, `system` | 특정 시간 또는 주기로 작업을 실행하는 스케줄러 |
| 프로세스 가드 | `Process Guard` | `processGuard` | `PG` | `infra`, `system` | 프로세스 비정상 종료 감지 및 재기동 담당 |
| 프로젝트 루트 | `Project Root` | `projectRoot` | `PROJ` | `infra`, `config` | 프로젝트 최상위 디렉토리 경로 |
| 하트비트 | `Heartbeat` | `heartbeat` | `HB` | `infra`, `system` | 서비스 생존 여부를 주기적으로 알리는 신호 |
| 환경변수 | `Environment Variable` | `envVar` | `ENV` | `infra`, `config` | 런타임 환경변수 (.env 파일 또는 시스템 환경변수) |

---

## 📐 도메인 개념 (Domain Concepts)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 눌림목 | `Pullback` | `pullback` | `PB` | `domain`, `selector` | 상승 추세 중 일시적 하락 후 재상승하는 진입 패턴 |
| 돌파 | `Breakout` | `breakout` | `BRK` | `domain`, `selector` | 저항선/지지선을 돌파하는 가격 움직임 패턴 |
| 롱 | `Long` | `long` | `LONG` | `domain`, `order` | 가격 상승을 기대하는 매수 포지션 방향 ❌ NOT: `short` |
| 숏 | `Short` | `short` | `SHORT` | `domain`, `order` | 가격 하락을 기대하는 매도 포지션 방향 ❌ NOT: `long` |
| 시그널 | `Signal` | `signal` | `SIG` | `domain`, `class` | 매매 진입/청산 판단의 근거가 되는 신호 |
| 시그널 방향 | `Signal Direction` | `signalDirection` | `DIR` | `domain`, `class`, `status` | 시그널의 방향 (Long / Short / Flat) |
| 시그널 엔진 | `Signal Engine` | `signalEngine` | `SIG_ENG` | `domain`, `class`, `module` | 시그널 생성 로직의 핵심 컴포넌트 |
| 플랫 | `Flat` | `flat` | `FLAT` | `domain`, `status` | 포지션 없음 상태 (중립) |

---

## 📋 거래 / 주문 (Trading & Orders)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 거래 ID | `Transaction ID` | `transactionId` | `TR_ID` | `order`, `tool` | API 거래 요청 식별자 |
| 거절 | `Rejected` | `rejected` | `RJCT` | `order`, `status` | 브로커 또는 리스크 로직에 의해 거절된 상태 |
| 대기 | `Pending` | `pending` | `PEND` | `order`, `status` | 주문이 아직 제출되지 않은 대기 상태 |
| 매도 | `Sell` | `sell` | `SELL` | `order`, `domain` | 매도 방향 주문 |
| 매수 | `Buy` | `buy` | `BUY` | `order`, `domain` | 매수 방향 주문 |
| 부분 체결 | `Partial Fill` | `partialFill` | `PART` | `order`, `status` | 주문 수량의 일부만 체결된 상태 |
| 분할 매도 | `Split Sell` | `splitSell` | `SSELL` | `order`, `domain` | 포지션을 여러 번에 나눠 매도하는 전략 |
| 분할 매수 | `Split Buy` | `splitBuy` | `SBUY` | `order`, `domain` | 포지션을 여러 번에 나눠 매수하는 전략 |
| 시장가 | `Market Order` | `marketOrder` | `MKT` | `order`, `domain` | 현재 시장가로 즉시 체결하는 주문 유형 ❌ NOT: `limitOrder` |
| 실패 | `Failed` | `failed` | `FAIL` | `order`, `status`, `system` | 기술적 오류로 주문 처리 실패 |
| 오버나이트 | `Overnight` | `overnight` | `ON` | `order`, `session`, `domain` | 장 마감 후 다음날까지 포지션을 보유하는 거래 ❌ NOT: `intraday` |
| 장중 | `Intraday` | `intraday` | `INTRA` | `order`, `session`, `domain` | 당일 장 시간 내에 진입과 청산이 완료되는 거래 |
| 제출됨 | `Submitted` | `submitted` | `SUBM` | `order`, `status` | 브로커에 주문이 제출된 상태 |
| 종료된 거래 | `Closed Trade` | `closedTrade` | `CT` | `order`, `domain` | 청산 완료된 거래 ❌ NOT: `activeTrade` |
| 주문 | `Order` | `order` | `ORD` | `order`, `domain`, `class` | 브로커에 제출하는 매수/매도 요청 단위 |
| 주문 (DB) | `orders` | `orders` | `ORD` | `order`, `data`, `infra` | 주문 이력 저장 테이블 |
| 주문 상태 | `Order Status` | `orderStatus` | `OS` | `order`, `status`, `class` | 주문의 현재 처리 상태 (Enum) |
| 주문의도 | `Order Intent` | `orderIntent` | `OI` | `order`, `domain`, `class` | 시그널로부터 생성된 주문 의사결정 객체. 실제 주문 제출 전 단계. ❌ NOT: `order`, `ORD` |
| 지정가 | `Limit Order` | `limitOrder` | `LMT` | `order`, `domain` | 지정된 가격 이하(매수) 또는 이상(매도)에서만 체결하는 주문 유형 ❌ NOT: `marketOrder` |
| 진입 | `Entry` | `entry` | `ENT` | `order`, `domain`, `config` | 새 포지션을 여는 행위 또는 관련 설정 |
| 청산 | `Exit / Close` | `exit` | `EXIT` | `order`, `domain`, `config` | 보유 포지션을 닫는 행위 또는 관련 설정 |
| 체결 | `Fill / Execution` | `fill` | `FILL` | `order`, `domain`, `class` | 주문이 실제로 체결된 결과 |
| 체결 (DB) | `fills` | `fills` | `FILL` | `order`, `data`, `infra` | 체결 이력 저장 테이블 |
| 체결 완료 | `Filled` | `filled` | `FLLD` | `order`, `status` | 주문 전량이 체결 완료된 상태 |
| 취소 | `Cancelled` | `cancelled` | `CNCL` | `order`, `status` | 주문이 취소된 상태 |
| 포지션 | `Position` | `position` | `POS` | `order`, `domain`, `class`, `account` | 현재 보유 중인 종목/방향/수량 상태 |
| 활성 거래 | `Active Trade` | `activeTrade` | `AT` | `order`, `domain` | 현재 진행 중인(미청산) 거래 ❌ NOT: `closedTrade` |

---

## 🛡️  리스크 관리 (Risk Management)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 리스크 관리자 | `Risk Manager` | `riskManager` | `RM` | `risk`, `class` | 거래 전후 리스크 규칙을 검사하고 집행하는 컴포넌트 |
| 미반등 청산 | `No-Bounce Exit` | `noBounceExit` | `NBE` | `risk`, `domain`, `config` | 일정 시간 내 반등이 없을 경우 청산하는 규칙 |
| 손절 | `Stop Loss` | `stopLoss` | `SL` | `risk`, `domain` | 손실 한도 도달 시 포지션을 강제 청산하는 규칙 |
| 수수료 | `Commission` | `commission` | `COMM` | `risk`, `account` | 거래 시 브로커에게 지불하는 수수료 |
| 슬리피지 | `Slippage` | `slippage` | `SLIP` | `risk`, `domain` | 주문 예상가와 실제 체결가의 차이 |
| 연속 손절 | `Consecutive Stops` | `consecutiveStops` | `CS` | `risk` | 연속으로 손절이 발생한 횟수 기반 거래 중단 조건 |
| 익절 | `Take Profit` | `takeProfit` | `TP` | `risk`, `domain` | 목표 수익 달성 시 포지션을 청산하는 규칙 |
| 일일 최대 손실 | `Max Daily Loss` | `maxDailyLoss` | `MDL` | `risk`, `account` | 하루 손실 한도 초과 시 당일 신규 진입 금지 |
| 최대 포지션 수 | `Max Open Positions` | `maxOpenPositions` | `MOP` | `risk`, `account` | 동시에 보유할 수 있는 최대 포지션 개수 제한 |
| 트레일링 스탑 | `Trailing Stop` | `trailingStop` | `TS` | `risk`, `domain`, `config` | 수익이 늘어남에 따라 손절가를 자동으로 올려가는 방식 |
| 포지션 비중 | `Position Size` | `positionSize` | `PSIZ` | `risk`, `account` | 개별 거래에 투입할 자금 비중 또는 수량 |

---

## 📊 시장 데이터 (Market Data)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 1분봉 | `bars_1m` | `bars1m` | `B1M` | `data`, `infra` | 1분봉 OHLCV 데이터 테이블 |
| 가중평균가 | `VWAP` | `vwap` | `VWAP` | `data`, `domain` | 거래량 가중 평균 가격 (Volume Weighted Average Price) |
| 거래대금 | `Trading Value` | `tradingValue` | `TV` | `data` | 봉 기간 내 체결된 금액 (가격 × 거래량) |
| 거래량 | `Volume` | `volume` | `VOL` | `data` | 봉 기간 내 거래된 수량 *(⚠️ abbr_short VOL은 volatilityScore와 혼동 주의. 컨텍스트로 구분.)* |
| 거래정지 | `is_suspended` | `isSuspended` | `SUSP` | `data`, `status` | 거래정지 여부 플래그 |
| 계좌 스냅샷 | `account_snapshots` | `accountSnapshots` | `ASNAP` | `data`, `infra`, `account` | 주기적 계좌 상태 스냅샷 저장 테이블 |
| 고가 | `High` | `high` | `H` | `data` | 봉의 최고 가격 |
| 관리종목 | `is_managed` | `isManaged` | `MGND` | `data`, `status` | 관리종목 지정 여부 플래그 |
| 리스크 이벤트 | `risk_events` | `riskEvents` | `REVT` | `data`, `infra`, `risk` | 리스크 규칙 발동 이벤트 로그 테이블 |
| 변동폭 | `Range` | `range` | `RNG` | `data` | 봉의 고가 - 저가 값 |
| 봉 (1분봉) | `Bar (1-min)` | `bar` | `BAR` | `data`, `class` | 일정 시간 단위(기본 1분)로 집계된 OHLCV 데이터 |
| 상장일 | `listing_date` | `listingDate` | `LSTD` | `data` | 종목 상장 날짜 |
| 상장주수 | `listed_shares` | `listedShares` | `LSHR` | `data` | 상장된 전체 주식 수 |
| 섹터 랭킹 | `sector_rankings` | `sectorRankings` | `SR` | `data`, `infra`, `selector` | 섹터 랭킹 결과 저장 테이블로 사용됨 |
| 시가 | `Open` | `open` | `O` | `data` | 봉의 시작 가격 |
| 시가총액 | `market_cap` | `marketCap` | `MCAP` | `data` | 종목의 시가총액 |
| 시그널 (DB) | `signals` | `signals` | `SIG` | `data`, `infra` | 생성된 시그널 이력 저장 테이블 |
| 액면가 | `face_value` | `faceValue` | `FV` | `data` | 주식 액면가 |
| 업종 마스터 | `sector_master` | `sectorMaster` | `SECM` | `data`, `infra` | 업종 분류 마스터 테이블 |
| 업종명 | `sector_name` | `sectorName` | `SECN` | `data` | 업종 분류 이름 |
| 업종코드 | `sector_code` | `sectorCode` | `SECC` | `data` | 업종 분류 코드 |
| 저가 | `Low` | `low` | `L` | `data` | 봉의 최저 가격 |
| 종가 | `Close` | `close` | `C` | `data` | 봉의 마지막 가격 |
| 종목 마스터 | `symbols` | `symbols` | `SYM` | `data`, `infra` | 전 종목 기본 정보 테이블 |
| 종목 마스터 (KIS) | `stock_master` | `stockMaster` | `SM` | `data`, `infra`, `tool` | 한국투자증권(KIS) 기준 종목 마스터 테이블 |
| 종목명 | `stock_name` | `stockName` | `SN` | `data` | 종목의 한글 이름 |
| 종목코드 (PK) | `stock_code` | `stockCode` | `SC` | `data` | 종목 고유 식별 코드 (Primary Key) |
| 체결강도 | `Execution Strength` | `execStrength` | `ES` | `data`, `selector` | 매수 체결 강도 (매수 체결량 / 전체 체결량) |
| 틱 | `Tick` | `tick` | `TK` | `data`, `class` | 개별 체결 이벤트 단위 데이터 |
| 틱 데이터 | `ticks` | `ticks` | `TK` | `data`, `infra` | 체결 틱 데이터 테이블 |
| 표준코드 | `std_code` | `stdCode` | `STDC` | `data` | 거래소 표준 종목 코드 |
| 활성 | `is_active` | `isActive` | `ACT` | `data`, `status` | 활성 종목 여부 플래그 |

---

## 💰 계좌 / 잔고 (Account & Balance)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 계좌번호 | `Account Number` | `accountNo` | `ACCT` | `account`, `config` | 브로커 계좌 번호 |
| 모의투자 | `Mock Trading` | `mockTrading` | `MOCK` | `account`, `system` | 실제 자금 없이 시뮬레이션하는 거래 모드 ❌ NOT: `liveTrading` |
| 미실현 손익 | `Unrealized P&L` | `unrealizedPnl` | `UR_PNL` | `account` | 보유 포지션의 평가 손익 (아직 청산 전) |
| 상품코드 | `Account Product` | `accountProduct` | `APROD` | `account`, `config` | 계좌 상품 유형 코드 |
| 순자산 | `Equity` | `equity` | `EQ` | `account` | 잔고 + 미실현 손익의 총 순자산 |
| 승률 | `Win Rate` | `winRate` | `WR` | `account`, `report` | 전체 거래 중 수익 거래의 비율 |
| 승리 | `Win` | `win` | `W` | `account`, `status` | 수익이 발생한 거래 결과 |
| 실전투자 | `Live Trading` | `liveTrading` | `LIVE` | `account`, `system` | 실제 자금으로 진행하는 거래 모드 ❌ NOT: `mockTrading` |
| 실현 손익 | `Realized P&L` | `realizedPnl` | `R_PNL` | `account`, `report` | 청산 완료된 거래의 확정 손익 |
| 예수금 | `Deposit` | `deposit` | `DEP` | `account` | 계좌에 예치된 현금 (미결제 주문 제외 사용 가능 금액) |
| 일일 손익 | `Daily P&L` | `dailyPnl` | `D_PNL` | `account`, `report` | 당일 실현 + 미실현 손익 합계 |
| 잔고 | `Balance` | `balance` | `BAL` | `account` | 계좌의 현금 잔고 |
| 증거금 | `Margin Used` | `marginUsed` | `MRG` | `account`, `risk` | 현재 포지션 유지를 위해 사용 중인 증거금 |
| 패배 | `Loss` | `loss` | `LOSS` | `account`, `status` | 손실이 발생한 거래 결과 *(⚠️ abbr_short 충돌 해소: L → LOSS)* |

---

## ⚙️  시스템 운영 (System Operation)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 킬스위치 | `Kill Switch` | `killSwitch` | `KSW` | `system`, `risk` | 긴급 시 전체 거래 즉시 중단 스위치 |

---

## 🔑 설정 / 환경변수 (Config & Env)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| DB 접속 | `PG_DSN` | `pgDsn` | `PG_DSN` | `config`, `infra` | PostgreSQL 접속 DSN 환경변수 *(⚠️ abbr_short 충돌 해소: PG → PG_DSN)* |
| KIS 계좌번호 | `KIS_ACCOUNT_NO` | `kisAccountNo` | `KIS_ACCT` | `config`, `account` | 한국투자증권 계좌번호 환경변수 |
| KIS 모의 앱키 | `KIS_MOCK_APP_KEY` | `kisMockAppKey` | `KIS_MAK` | `config`, `tool` | 한국투자증권 모의투자 앱키 환경변수 |
| KIS 앱시크릿 | `KIS_APP_SECRET` | `kisAppSecret` | `KIS_AS` | `config`, `tool` | 한국투자증권 API 앱시크릿 환경변수 |
| KIS 앱키 | `KIS_APP_KEY` | `kisAppKey` | `KIS_AK` | `config`, `tool` | 한국투자증권 API 앱키 환경변수 |
| MT5 프록시 URL | `MT5_PROXY_URL` | `mt5ProxyUrl` | `MT5P` | `config`, `tool` | MT5 프록시 서버 URL 환경변수 |
| MT5 활성 | `ENABLE_MT5` | `enableMt5` | `E_MT5` | `config`, `tool` | MT5 연결 활성화 여부 환경변수 |
| Redis 접속 | `REDIS_URL` | `redisUrl` | `REDIS` | `config`, `infra` | Redis 접속 URL 환경변수 |
| 노드명 환경변수 | `NODE_NAME` | `nodeNameEnv` | `NODE` | `config`, `infra` | 현재 실행 노드를 식별하는 환경변수 |
| 대시보드 포트 | `DASHBOARD_PORT` | `dashboardPort` | `DASH_P` | `config`, `infra` | 대시보드 웹서버 포트 환경변수 |
| 리포트 설정 | `reporting` | `reporting` | `RPT` | `config`, `report` | 리포트 생성 설정 섹션 |
| 모의투자 사용 | `KIS_TEST_USE_MOCK_TRADING` | `kisTestUseMock` | `KIS_MOCK` | `config`, `account` | 모의투자 모드 활성화 환경변수 |
| 미국시장 활성 | `ENABLE_US` | `enableUs` | `E_US` | `config`, `market` | 미국주식 시장 활성화 여부 환경변수 |
| 백테스트 | `backtest` | `backtest` | `BT` | `config`, `system` | 백테스트 실행 설정 섹션 |
| 세션 | `sessions` | `sessions` | `SESS` | `config`, `session` | 장 세션 시간 설정 섹션 |
| 스코어링 | `scoring` | `scoring` | `SCR_CFG` | `config`, `selector` | 종목 스코어링 가중치 설정 섹션 *(⚠️ abbr_short 충돌 해소: SCR → SCR_CFG)* |
| 시스템 | `system` | `system` | `SYS` | `config`, `system` | settings.yaml 최상위 system 섹션 |
| 진입 거부 | `entry_deny` | `entryDeny` | `ED` | `config`, `risk` | 진입 금지 조건 설정 섹션 |
| 한국시장 활성 | `ENABLE_KR` | `enableKr` | `E_KR` | `config`, `market` | 한국주식 시장 활성화 여부 환경변수 |
| 한국주식 셀렉터 | `kr_selector` | `krSelector` | `KR_SEL` | `config`, `selector` | 한국주식 종목 선정 설정 섹션 |
| 한국주식 전략 | `kr_strategy` | `krStrategy` | `KR_STR` | `config`, `domain` | 한국주식 매매 전략 설정 섹션 |

---

## 📈 리포트 / 알림 (Report & Notification)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| AI 평가 | `AI Evaluation` | `aiEvaluation` | `AI_EVAL` | `report` | AI가 생성한 거래 전략 평가 및 개선 제안 |
| 거래 알림 | `Trade Notification` | `tradeNotifier` | `TRD_NTF` | `report`, `order` | 주문·체결 이벤트 알림 발송 |
| 시스템 알림 | `System Notification` | `systemNotifier` | `SYS_NTF` | `report`, `system` | 시스템 이벤트(에러, 경고 등) 알림 발송 |
| 월간 리포트 | `Monthly Report` | `monthlyReport` | `MR` | `report` | 월간 거래 결과 요약 리포트 |
| 일간 리포트 | `Daily Report` | `dailyReport` | `DR` | `report` | 당일 거래 결과 및 계좌 현황 요약 리포트 |
| 주간 리포트 | `Weekly Report` | `weeklyReport` | `W_RPT` | `report` | 주간 거래 결과 요약 리포트 *(⚠️ abbr_short WR은 winRate와 동일. 컨텍스트로 구분. [수정: WR → W_RPT])* |
| 텔레그램 봇 | `Telegram Bot` | `telegramBot` | `TG` | `report`, `infra`, `class` | 텔레그램을 통한 알림 발송 컴포넌트 |

---

## 📁 모듈 / 디렉토리 (Modules & Directories)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 공통 | `common` | `common` | `COM` | `module` | 전 모듈이 공유하는 공통 유틸·모델 디렉토리 |
| 데이터 | `data` | `data` | `DATA` | `module`, `data` | 정적 데이터 파일 디렉토리 |
| 로그 | `logs` | `logs` | `LOG` | `module`, `infra` | 로그 파일 저장 디렉토리 |
| 리스크 | `risk` | `risk` | `RSK` | `module`, `risk` | 리스크 관리 로직 디렉토리 |
| 리포트 | `report` | `report` | `RPT` | `module`, `report` | 리포트 생성 디렉토리 |
| 리플레이 | `replay` | `replay` | `RPL` | `module`, `system` | 과거 데이터 기반 시뮬레이션(리플레이) 디렉토리 |
| 문서 | `doc` | `doc` | `DOC` | `module` | 프로젝트 문서 디렉토리 |
| 설정 파일 | `config` | `config` | `CFG` | `module`, `config` | settings.yaml 등 설정 파일 디렉토리 |
| 수집기 | `collectors` | `collectors` | `COL` | `module` | 시장 데이터 수집 컴포넌트 디렉토리 |
| 스크립트 | `scripts` | `scripts` | `SCR` | `module` | 유틸리티 스크립트 디렉토리 *(⚠️ abbr_short SCR은 sectorScore의 scoring(SCR) config key와 혼동 주의)* |
| 시그널 | `signals` | `signalsModule` | `SIG` | `module`, `domain` | 시그널 생성 로직 디렉토리 |
| 실행 엔진 | `execution` | `execution` | `EXEC` | `module`, `order` | 주문 실행 엔진 디렉토리 |
| 알림 | `notifications` | `notifications` | `NTF` | `module`, `report` | 알림 발송 컴포넌트 디렉토리 |
| 어댑터 | `adapters` | `adapters` | `ADP` | `module` | 외부 브로커/API 연결 어댑터 디렉토리 |
| 저장소 | `storage` | `storage` | `STR` | `module`, `infra` | DB·파일 저장 추상화 레이어 디렉토리 |
| 종목 선정 | `selector` | `selector` | `SEL` | `module`, `selector` | 대장주 선정 및 스코어링 로직 디렉토리 |
| 환경 파일 | `env` | `env` | `ENV` | `module`, `config` | .env 환경변수 파일 디렉토리 |

---

## 🧩 클래스 / 열거형 (Classes & Enums)

| 한글명 | 클래스명 | abbr_long | abbr_short | 유형 | 모듈 | 설명 |
|--------|---------|-----------|------------|------|------|------|
| DB 엔진 | `DBEngine` | `DBEngine` | `DB_ENG` | Class | `storage/` | DB 연결 및 쿼리 추상화 Class (storage/) |
| FX 시그널 엔진 | `FxSignalEngine` | `FxSignalEngine` | `FX_SIG` | Class | `signals/` | 외환선물 시그널 생성 엔진 Class (signals/) |
| KIS 모의 인증 | `KisMockAuth` | `KisMockAuth` | `KIS_MAUTH` | Class | `adapters/kr/kis_auth` | 한국투자증권 모의투자 인증 Class (adapters/kr/kis_auth) |
| KIS 어댑터 | `KisAdapter` | `KisAdapter` | `KIS_ADP` | Class | `adapters/kr/kis_adapter` | KIS API 연동 어댑터 Class (adapters/kr/kis_adapter) |
| KIS 인증 | `KisAuth` | `KisAuth` | `KIS_AUTH` | Class | `adapters/kr/kis_auth` | 한국투자증권 실전 인증 Class (adapters/kr/kis_auth) |
| KR 시그널 엔진 | `KrSignalEngine` | `KrSignalEngine` | `KR_SIG` | Class | `signals/` | 한국주식 시그널 생성 엔진 Class (signals/) |
| MT5 브릿지 클래스 | `MT5Bridge` | `MT5Bridge` | `MT5B` | Class | `adapters/mt5/` | MT5 연결 브릿지 Class (adapters/mt5/) |
| 거래 기록 | `TradeRecord` | `TradeRecord` | `TR` | Class | `execution/` | 개별 거래 이력 기록 Class (execution/) |
| 거래 오케스트레이터 | `TradingOrchestrator` | `TradingOrchestrator` | `T_ORCH` | Class | `execution/` | 전체 거래 흐름 오케스트레이터 Class (execution/) |
| 계좌 스냅샷 | `AccountSnapshot` | `AccountSnapshot` | `ASNAP` | Model | `common/models` | 계좌 상태 스냅샷 Model (common/models) |
| 리포트 생성기 | `ReportGenerator` | `ReportGenerator` | `RPT_GEN` | Class | `report/` | 리포트 생성 Class (report/) |
| 리플레이 실행기 | `ReplayRunner` | `ReplayRunner` | `RPL_RUN` | Class | `replay/` | 과거 데이터 리플레이 실행기 Class (replay/) |
| 서비스 상태 열거형 | `ServiceStatus` | `ServiceStatus` | `SVC_S` | Enum | `common/service_manager` | 서비스 상태 Enum (common/service_manager) |
| 서비스 유형 | `ServiceType` | `ServiceType` | `SVC_T` | Enum | `common/service_manager` | 서비스 유형 Enum (common/service_manager) |
| 서비스 정보 | `ServiceInfo` | `ServiceInfo` | `SVC_I` | Class | `common/service_manager` | 서비스 메타정보 Class (common/service_manager) |
| 설정 싱글톤 | `Settings` | `Settings` | `CFG` | Singleton | `common/config` | 전역 설정 Singleton (common/config) |
| 섹터 랭커 | `SectorRanker` | `SectorRanker` | `SEC_RNK` | Class | `selector/` | 섹터 순위 산정 Class (selector/) |
| 시그널 방향 열거형 | `SignalDirection` | `SignalDirection` | `DIR` | Enum | `common/models` | 시그널 방향 Enum: Long / Short / Flat (common/models) |
| 시그널 이벤트 | `SignalEvent` | `SignalEvent` | `SIG_EVT` | Model | `common/models` | 시그널 발생 이벤트 Model (common/models) |
| 시장 열거형 | `Market` | `Market` | `MKT` | Enum | `common/models` | 거래 시장 종류 Enum (common/models) |
| 실행 엔진 | `ExecutionEngine` | `ExecutionEngine` | `EXEC_ENG` | Class | `execution/` | 주문 실행 엔진 Class (execution/) |
| 유효기간 | `TimeInForce` | `TimeInForce` | `TIF` | Enum | `common/models` | 주문 유효기간 Enum (common/models) |
| 종목 랭커 | `SymbolRanker` | `SymbolRanker` | `SYM_RNK` | Class | `selector/` | 종목 순위 산정 Class (selector/) |
| 주문 방향 | `OrderSide` | `OrderSide` | `OSIDE` | Enum | `common/models` | 주문 방향 Enum: Buy / Sell (common/models) *(⚠️ abbr_short 충돌 해소: OS → OSIDE)* |
| 주문 상태 열거형 | `OrderStatus` | `OrderStatus` | `OS` | Enum | `common/models` | 주문 상태 Enum (common/models) |
| 주문 유형 | `OrderType` | `OrderType` | `OT` | Enum | `common/models` | 주문 유형 Enum: Market / Limit (common/models) |
| 주문 의도 | `OrderIntent` | `OrderIntent` | `OI` | Model | `common/models` | 주문 의도 Model (common/models) |
| 텔레그램 봇 클래스 | `TelegramBot` | `TelegramBot` | `TG_BOT` | Class | `notifications/` | 텔레그램 알림 봇 Class (notifications/) |

---

## 🕐 세션 / 시간 (Sessions & Time)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 리부팅 시간 | `Reboot Time` | `rebootTime` | `RBT` | `session`, `system` | 시스템 정기 재시작 시각 |
| 작업 시작 | `Work Start` | `workStart` | `WS` | `session`, `system` | 일과 시작 시각 (데이터 수집, 초기화 등) |
| 장 마감 | `Market Close` | `marketClose` | `MC` | `session`, `domain` | 거래소 장 마감 시각 |
| 장 마감 청산 | `EOD Flatten` | `eodFlatten` | `EODF` | `session`, `order`, `risk` | 장 마감 시 잔존 포지션 전량 청산 |
| 장 시작 | `Market Open` | `marketOpen` | `MO` | `session`, `domain` | 거래소 장 시작 시각 |
| 진입 금지 시간 | `No Entry After` | `noEntryAfter` | `NEA` | `session`, `risk` | 이 시각 이후 신규 진입 금지 |
| 추적 시작 | `Tracking Start` | `trackingStart` | `TRK_ST` | `session`, `system` | 종목 추적 시작 시각 *(⚠️ abbr_short TS는 trailingStop과 동일. 컨텍스트로 구분. [수정: TS → TRK_ST])* |

---

## 🔍 종목 선정 / 스코어링 (Selector & Scoring)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 거래대금 점수 | `Trading Value Score` | `tradingValueScore` | `TVS` | `selector`, `data` | 거래대금 수준을 수치화한 점수 |
| 대장주 | `Leader Stock` | `leaderStock` | `LEAD` | `selector`, `domain` | 섹터 또는 시장을 주도하는 종목 |
| 대장주 스캐너 | `Market Scanner` | `marketScanner` | `SCAN` | `selector`, `class` | 조건에 맞는 대장주 후보를 자동 탐색하는 컴포넌트 |
| 대장주 후보 | `Leader Candidates` | `leaderCandidates` | `LCAND` | `selector`, `domain` | 대장주로 선정되기 위한 후보 종목 목록 |
| 모멘텀 점수 | `Momentum Score` | `momentumScore` | `MOM` | `selector`, `data` | 가격 추세 강도를 수치화한 점수 |
| 변동성 점수 | `Volatility Score` | `volatilityScore` | `VOLS` | `selector`, `data`, `risk` | 종목의 가격 변동성을 수치화한 점수 *(⚠️ abbr_short VOL은 시장 데이터의 volume(거래량)과 혼동 주의. 컨텍스트로 구분. [수정: VOL → VOLS])* |
| 봉 성격 | `Candle Personality` | `candlePersonality` | `CP` | `selector`, `data`, `domain` | 캔들스틱의 형태적 특성 분류 |
| 섹터 강도 점수 | `Sector Strength Score` | `sectorStrengthScore` | `SSS` | `selector`, `data` | 섹터 전체의 강도를 수치화한 점수 |
| 섹터 랭킹 | `Sector Ranking` | `sectorRanking` | `SEC_RNK` | `selector`, `data` | 강세/약세 섹터를 순위화한 결과 |
| 섹터 점수 | `Sector Score` | `sectorScore` | `SS` | `selector`, `data`, `class` | 개별 섹터의 종합 점수 |
| 시장 강도 | `Market Strength` | `marketStrength` | `MS` | `selector`, `data`, `config` | 전체 시장의 상승/하락 강도 지표 |
| 아랫꼬리 | `Lower Wick` | `lowerWick` | `LW` | `selector`, `data` | 캔들의 저가-몸통 하단 사이 꼬리 |
| 윗꼬리 | `Upper Wick` | `upperWick` | `UW` | `selector`, `data` | 캔들의 고가-몸통 상단 사이 꼬리 |
| 종목 랭킹 | `Symbol Ranking` | `symbolRanking` | `SYM_RNK` | `selector`, `data` | 스코어 기반 종목 순위 |
| 종목 점수 | `Stock Score` | `stockScore` | `STS` | `selector`, `data`, `class` | 개별 종목의 종합 점수 |
| 체결강도 점수 | `Execution Strength Score` | `execStrengthScore` | `ESS` | `selector`, `data` | 매수 체결 강도를 수치화한 점수 |

---

## 🚦 상태값 (Status Values)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 비활성 | `Disabled` | `disabled` | `OFF` | `status`, `config` | 기능·서비스가 비활성화된 상태 *(⚠️ abbr_short OFF는 offline과 동일. 컨텍스트로 구분.)* |
| 시작 중 | `Starting` | `starting` | `START` | `status`, `system` | 서비스가 초기화 중인 상태 |
| 실행 중 | `Running` | `running` | `RUN` | `status`, `system` | 서비스가 정상적으로 실행 중인 상태 |
| 오류 | `Error` | `error` | `ERR` | `status`, `system` | 오류가 발생한 상태 |
| 오프라인 | `Offline` | `offline` | `OFF` | `status`, `infra` | 서비스·연결이 오프라인 상태 *(⚠️ abbr_short OFF는 disabled와 동일. 컨텍스트로 구분.)* |
| 온라인 | `Online` | `online` | `ON` | `status`, `infra` | 서비스·연결이 온라인 상태 *(⚠️ abbr_short ON은 overnight, enabled와 동일. 컨텍스트로 구분.)* |
| 중지됨 | `Stopped` | `stopped` | `STOP` | `status`, `system` | 서비스가 중지된 상태 |
| 활성 | `Enabled` | `enabled` | `ON` | `status`, `config` | 기능·서비스가 활성화된 상태 *(⚠️ abbr_short ON은 overnight과 동일. 컨텍스트로 구분.)* |

---

## 🔤 전체 색인 (abbr_short 알파벳순)

| abbr_short | abbr_long | 한글명 | 영문명 |
|------------|-----------|--------|--------|
| `ACCT` | `accountNo` | 계좌번호 | `Account Number` |
| `ACT` | `isActive` | 활성 | `is_active` |
| `ADP` | `adapters` | 어댑터 | `adapters` |
| `AI_EVAL` | `aiEvaluation` | AI 평가 | `AI Evaluation` |
| `AK` | `appKey` | 앱 키 | `App Key` |
| `APROD` | `accountProduct` | 상품코드 | `Account Product` |
| `AS` | `appSecret` | 앱 시크릿 | `App Secret` |
| `ASNAP` | `accountSnapshots` | 계좌 스냅샷 | `account_snapshots` |
| `ASNAP` | `AccountSnapshot` | 계좌 스냅샷 | `AccountSnapshot` |
| `AT` | `activeTrade` | 활성 거래 | `Active Trade` |
| `AUTH` | `auth` | 인증 | `Authentication` |
| `B1M` | `bars1m` | 1분봉 | `bars_1m` |
| `BAL` | `balance` | 잔고 | `Balance` |
| `BAR` | `bar` | 봉 (1분봉) | `Bar (1-min)` |
| `BRK` | `breakout` | 돌파 | `Breakout` |
| `BT` | `backtest` | 백테스트 | `backtest` |
| `BUY` | `buy` | 매수 | `Buy` |
| `C` | `close` | 종가 | `Close` |
| `CFG` | `settings` | 설정 | `Settings / Configuration` |
| `CFG` | `config` | 설정 파일 | `config` |
| `CFG` | `Settings` | 설정 싱글톤 | `Settings` |
| `CNCL` | `cancelled` | 취소 | `Cancelled` |
| `COL` | `collectors` | 수집기 | `collectors` |
| `COM` | `common` | 공통 | `common` |
| `COMM` | `commission` | 수수료 | `Commission` |
| `CP` | `candlePersonality` | 봉 성격 | `Candle Personality` |
| `CRYPTO` | `crypto` | 코인거래 | `Cryptocurrency` |
| `CS` | `consecutiveStops` | 연속 손절 | `Consecutive Stops` |
| `CT` | `closedTrade` | 종료된 거래 | `Closed Trade` |
| `DASH` | `dashboard` | 대시보드 | `Dashboard` |
| `DASH_P` | `dashboardPort` | 대시보드 포트 | `DASHBOARD_PORT` |
| `DATA` | `data` | 데이터 | `data` |
| `DB` | `database` | 데이터베이스 | `Database` |
| `DB_ENG` | `DBEngine` | DB 엔진 | `DBEngine` |
| `DEP` | `deposit` | 예수금 | `Deposit` |
| `DIR` | `signalDirection` | 시그널 방향 | `Signal Direction` |
| `DIR` | `SignalDirection` | 시그널 방향 열거형 | `SignalDirection` |
| `DOC` | `doc` | 문서 | `doc` |
| `DR` | `dailyReport` | 일간 리포트 | `Daily Report` |
| `D_PNL` | `dailyPnl` | 일일 손익 | `Daily P&L` |
| `ED` | `entryDeny` | 진입 거부 | `entry_deny` |
| `ENT` | `entry` | 진입 | `Entry` |
| `ENV` | `envVar` | 환경변수 | `Environment Variable` |
| `ENV` | `env` | 환경 파일 | `env` |
| `EODF` | `eodFlatten` | 장 마감 청산 | `EOD Flatten` |
| `EQ` | `equity` | 순자산 | `Equity` |
| `ERR` | `error` | 오류 | `Error` |
| `ES` | `execStrength` | 체결강도 | `Execution Strength` |
| `ESS` | `execStrengthScore` | 체결강도 점수 | `Execution Strength Score` |
| `EXEC` | `execution` | 실행 엔진 | `execution` |
| `EXEC_ENG` | `ExecutionEngine` | 실행 엔진 | `ExecutionEngine` |
| `EXIT` | `exit` | 청산 | `Exit / Close` |
| `E_KR` | `enableKr` | 한국시장 활성 | `ENABLE_KR` |
| `E_MT5` | `enableMt5` | MT5 활성 | `ENABLE_MT5` |
| `E_US` | `enableUs` | 미국시장 활성 | `ENABLE_US` |
| `FAIL` | `failed` | 실패 | `Failed` |
| `FILL` | `fill` | 체결 | `Fill / Execution` |
| `FILL` | `fills` | 체결 (DB) | `fills` |
| `FLAT` | `flat` | 플랫 | `Flat` |
| `FLLD` | `filled` | 체결 완료 | `Filled` |
| `FV` | `faceValue` | 액면가 | `face_value` |
| `FX_FUT` | `fxFutures` | 외환선물 | `FX Futures` |
| `FX_SIG` | `FxSignalEngine` | FX 시그널 엔진 | `FxSignalEngine` |
| `H` | `high` | 고가 | `High` |
| `HB` | `heartbeat` | 하트비트 | `Heartbeat` |
| `INTRA` | `intraday` | 장중 | `Intraday` |
| `KIS` | `kisApi` | 한국투자증권 API | `KIS API` |
| `KIS_ACCT` | `kisAccountNo` | KIS 계좌번호 | `KIS_ACCOUNT_NO` |
| `KIS_ADP` | `KisAdapter` | KIS 어댑터 | `KisAdapter` |
| `KIS_AK` | `kisAppKey` | KIS 앱키 | `KIS_APP_KEY` |
| `KIS_AS` | `kisAppSecret` | KIS 앱시크릿 | `KIS_APP_SECRET` |
| `KIS_AUTH` | `KisAuth` | KIS 인증 | `KisAuth` |
| `KIS_MAK` | `kisMockAppKey` | KIS 모의 앱키 | `KIS_MOCK_APP_KEY` |
| `KIS_MAUTH` | `KisMockAuth` | KIS 모의 인증 | `KisMockAuth` |
| `KIS_MOCK` | `kisTestUseMock` | 모의투자 사용 | `KIS_TEST_USE_MOCK_TRADING` |
| `KOSDAQ` | `kosdaq` | 코스닥 | `KOSDAQ` |
| `KOSPI` | `kospi` | 코스피 | `KOSPI` |
| `KR_SEL` | `krSelector` | 한국주식 셀렉터 | `kr_selector` |
| `KR_SIG` | `KrSignalEngine` | KR 시그널 엔진 | `KrSignalEngine` |
| `KR_STOCK` | `krStock` | 한국주식 | `Korean Stock` |
| `KR_STR` | `krStrategy` | 한국주식 전략 | `kr_strategy` |
| `KSW` | `killSwitch` | 킬스위치 | `Kill Switch` |
| `L` | `low` | 저가 | `Low` |
| `LCAND` | `leaderCandidates` | 대장주 후보 | `Leader Candidates` |
| `LEAD` | `leaderStock` | 대장주 | `Leader Stock` |
| `LIVE` | `liveTrading` | 실전투자 | `Live Trading` |
| `LMT` | `limitOrder` | 지정가 | `Limit Order` |
| `LOG` | `realtimeLog` | 실시간 로그 | `Real-time Log` |
| `LOG` | `logs` | 로그 | `logs` |
| `LONG` | `long` | 롱 | `Long` |
| `LOSS` | `loss` | 패배 | `Loss` |
| `LSHR` | `listedShares` | 상장주수 | `listed_shares` |
| `LSTD` | `listingDate` | 상장일 | `listing_date` |
| `LW` | `lowerWick` | 아랫꼬리 | `Lower Wick` |
| `MC` | `marketClose` | 장 마감 | `Market Close` |
| `MCAP` | `marketCap` | 시가총액 | `market_cap` |
| `MDL` | `maxDailyLoss` | 일일 최대 손실 | `Max Daily Loss` |
| `MGND` | `isManaged` | 관리종목 | `is_managed` |
| `MKT` | `marketOrder` | 시장가 | `Market Order` |
| `MKT` | `Market` | 시장 열거형 | `Market` |
| `MO` | `marketOpen` | 장 시작 | `Market Open` |
| `MOCK` | `mockTrading` | 모의투자 | `Mock Trading` |
| `MOM` | `momentumScore` | 모멘텀 점수 | `Momentum Score` |
| `MOP` | `maxOpenPositions` | 최대 포지션 수 | `Max Open Positions` |
| `MR` | `monthlyReport` | 월간 리포트 | `Monthly Report` |
| `MRG` | `marginUsed` | 증거금 | `Margin Used` |
| `MS` | `marketStrength` | 시장 강도 | `Market Strength` |
| `MT5` | `mt5` | 메타트레이더5 | `MetaTrader 5` |
| `MT5B` | `mt5Bridge` | MT5 브릿지 | `MT5 Bridge` |
| `MT5B` | `MT5Bridge` | MT5 브릿지 클래스 | `MT5Bridge` |
| `MT5P` | `mt5Proxy` | MT5 프록시 | `MT5 Proxy Server` |
| `MT5P` | `mt5ProxyUrl` | MT5 프록시 URL | `MT5_PROXY_URL` |
| `NBE` | `noBounceExit` | 미반등 청산 | `No-Bounce Exit` |
| `NEA` | `noEntryAfter` | 진입 금지 시간 | `No Entry After` |
| `NODE` | `nodeName` | 노드명 | `Node Name` |
| `NODE` | `nodeNameEnv` | 노드명 환경변수 | `NODE_NAME` |
| `NTF` | `notifications` | 알림 | `notifications` |
| `O` | `open` | 시가 | `Open` |
| `OFF` | `disabled` | 비활성 | `Disabled` |
| `OFF` | `offline` | 오프라인 | `Offline` |
| `OI` | `orderIntent` | 주문의도 | `Order Intent` |
| `OI` | `OrderIntent` | 주문 의도 | `OrderIntent` |
| `ON` | `overnight` | 오버나이트 | `Overnight` |
| `ON` | `enabled` | 활성 | `Enabled` |
| `ON` | `online` | 온라인 | `Online` |
| `ORCH` | `orchestrator` | 오케스트레이터 | `Orchestrator` |
| `ORD` | `order` | 주문 | `Order` |
| `ORD` | `orders` | 주문 (DB) | `orders` |
| `OS` | `orderStatus` | 주문 상태 | `Order Status` |
| `OS` | `OrderStatus` | 주문 상태 열거형 | `OrderStatus` |
| `OSIDE` | `OrderSide` | 주문 방향 | `OrderSide` |
| `OT` | `OrderType` | 주문 유형 | `OrderType` |
| `PART` | `partialFill` | 부분 체결 | `Partial Fill` |
| `PB` | `pullback` | 눌림목 | `Pullback` |
| `PEND` | `pending` | 대기 | `Pending` |
| `PG` | `processGuard` | 프로세스 가드 | `Process Guard` |
| `PG_DSN` | `pgDsn` | DB 접속 | `PG_DSN` |
| `POS` | `position` | 포지션 | `Position` |
| `PROJ` | `projectRoot` | 프로젝트 루트 | `Project Root` |
| `PSIZ` | `positionSize` | 포지션 비중 | `Position Size` |
| `RBT` | `rebootTime` | 리부팅 시간 | `Reboot Time` |
| `REDIS` | `redisUrl` | Redis 접속 | `REDIS_URL` |
| `REVT` | `riskEvents` | 리스크 이벤트 | `risk_events` |
| `RJCT` | `rejected` | 거절 | `Rejected` |
| `RM` | `riskManager` | 리스크 관리자 | `Risk Manager` |
| `RNG` | `range` | 변동폭 | `Range` |
| `ROLE` | `role` | 역할 | `Role` |
| `RPL` | `replay` | 리플레이 | `replay` |
| `RPL_RUN` | `ReplayRunner` | 리플레이 실행기 | `ReplayRunner` |
| `RPT` | `report` | 리포트 | `report` |
| `RPT` | `reporting` | 리포트 설정 | `reporting` |
| `RPT_GEN` | `ReportGenerator` | 리포트 생성기 | `ReportGenerator` |
| `RSK` | `risk` | 리스크 | `risk` |
| `RUN` | `running` | 실행 중 | `Running` |
| `R_PNL` | `realizedPnl` | 실현 손익 | `Realized P&L` |
| `SBUY` | `splitBuy` | 분할 매수 | `Split Buy` |
| `SC` | `stockCode` | 종목코드 (PK) | `stock_code` |
| `SCAN` | `marketScanner` | 대장주 스캐너 | `Market Scanner` |
| `SCHED` | `taskScheduler` | 작업 스케줄러 | `Task Scheduler` |
| `SCR` | `scripts` | 스크립트 | `scripts` |
| `SCR_CFG` | `scoring` | 스코어링 | `scoring` |
| `SECC` | `sectorCode` | 업종코드 | `sector_code` |
| `SECM` | `sectorMaster` | 업종 마스터 | `sector_master` |
| `SECN` | `sectorName` | 업종명 | `sector_name` |
| `SEC_RNK` | `sectorRanking` | 섹터 랭킹 | `Sector Ranking` |
| `SEC_RNK` | `SectorRanker` | 섹터 랭커 | `SectorRanker` |
| `SEL` | `selector` | 종목 선정 | `selector` |
| `SELL` | `sell` | 매도 | `Sell` |
| `SESS` | `sessions` | 세션 | `sessions` |
| `SHORT` | `short` | 숏 | `Short` |
| `SIG` | `signal` | 시그널 | `Signal` |
| `SIG` | `signals` | 시그널 (DB) | `signals` |
| `SIG` | `signalsModule` | 시그널 | `signals` |
| `SIG_ENG` | `signalEngine` | 시그널 엔진 | `Signal Engine` |
| `SIG_EVT` | `SignalEvent` | 시그널 이벤트 | `SignalEvent` |
| `SL` | `stopLoss` | 손절 | `Stop Loss` |
| `SLIP` | `slippage` | 슬리피지 | `Slippage` |
| `SM` | `stockMaster` | 종목 마스터 (KIS) | `stock_master` |
| `SN` | `stockName` | 종목명 | `stock_name` |
| `SR` | `sectorRankings` | 섹터 랭킹 | `sector_rankings` |
| `SS` | `sectorScore` | 섹터 점수 | `Sector Score` |
| `SSELL` | `splitSell` | 분할 매도 | `Split Sell` |
| `SSS` | `sectorStrengthScore` | 섹터 강도 점수 | `Sector Strength Score` |
| `START` | `starting` | 시작 중 | `Starting` |
| `STDC` | `stdCode` | 표준코드 | `std_code` |
| `STOP` | `stopped` | 중지됨 | `Stopped` |
| `STR` | `storage` | 저장소 | `storage` |
| `STS` | `stockScore` | 종목 점수 | `Stock Score` |
| `SUBM` | `submitted` | 제출됨 | `Submitted` |
| `SUSP` | `isSuspended` | 거래정지 | `is_suspended` |
| `SVC_I` | `ServiceInfo` | 서비스 정보 | `ServiceInfo` |
| `SVC_MGR` | `serviceManager` | 서비스 관리자 | `Service Manager` |
| `SVC_S` | `ServiceStatus` | 서비스 상태 열거형 | `ServiceStatus` |
| `SVC_T` | `ServiceType` | 서비스 유형 | `ServiceType` |
| `SYM` | `symbols` | 종목 마스터 | `symbols` |
| `SYM_RNK` | `symbolRanking` | 종목 랭킹 | `Symbol Ranking` |
| `SYM_RNK` | `SymbolRanker` | 종목 랭커 | `SymbolRanker` |
| `SYS` | `system` | 시스템 | `system` |
| `SYS_NTF` | `systemNotifier` | 시스템 알림 | `System Notification` |
| `TG` | `telegramBot` | 텔레그램 봇 | `Telegram Bot` |
| `TG_BOT` | `TelegramBot` | 텔레그램 봇 클래스 | `TelegramBot` |
| `TIF` | `TimeInForce` | 유효기간 | `TimeInForce` |
| `TK` | `tick` | 틱 | `Tick` |
| `TK` | `ticks` | 틱 데이터 | `ticks` |
| `TOKEN` | `accessToken` | 접근 토큰 | `Access Token` |
| `TP` | `takeProfit` | 익절 | `Take Profit` |
| `TR` | `TradeRecord` | 거래 기록 | `TradeRecord` |
| `TRD_NTF` | `tradeNotifier` | 거래 알림 | `Trade Notification` |
| `TRK_ST` | `trackingStart` | 추적 시작 | `Tracking Start` |
| `TR_ID` | `transactionId` | 거래 ID | `Transaction ID` |
| `TS` | `trailingStop` | 트레일링 스탑 | `Trailing Stop` |
| `TV` | `tradingValue` | 거래대금 | `Trading Value` |
| `TVS` | `tradingValueScore` | 거래대금 점수 | `Trading Value Score` |
| `T_ORCH` | `TradingOrchestrator` | 거래 오케스트레이터 | `TradingOrchestrator` |
| `UR_PNL` | `unrealizedPnl` | 미실현 손익 | `Unrealized P&L` |
| `US_STOCK` | `usStock` | 미국주식 | `US Stock` |
| `UW` | `upperWick` | 윗꼬리 | `Upper Wick` |
| `VOL` | `volume` | 거래량 | `Volume` |
| `VOLS` | `volatilityScore` | 변동성 점수 | `Volatility Score` |
| `VWAP` | `vwap` | 가중평균가 | `VWAP` |
| `W` | `win` | 승리 | `Win` |
| `WDG` | `watchdog` | 워치독 | `Watchdog` |
| `WR` | `winRate` | 승률 | `Win Rate` |
| `WS` | `workStart` | 작업 시작 | `Work Start` |
| `W_RPT` | `weeklyReport` | 주간 리포트 | `Weekly Report` |
