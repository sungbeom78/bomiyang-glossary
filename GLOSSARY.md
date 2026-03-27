# BOM_TS – 용어 사전 (Glossary)

> BOM_TS 전체 용어 사전. 코드·DB·설정·문서에서 용어 통일의 기준.
>
> **버전:** 2.0.0  |  **최종 수정:** 2026-03-27
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
| `ASNAP` | `account_snapshot`, `cls_account_snapshot`, `db_account_snapshots` |
| `CFG` | `cls_settings`, `mod_config` |
| `DIR` | `signal_direction`, `cls_signal_direction` |
| `ENV` | `mod_env`, `env_var` |
| `MT5B` | `mt5_bridge`, `cls_mt5_bridge` |
| `MT5P` | `mt5_proxy`, `env_mt5_proxy_url` |
| `NODE` | `node_name`, `env_node_name` |
| `OI` | `order_intent`, `cls_order_intent` |
| `OS` | `order_status`, `cls_order_status` |
| `SEC_RNK` | `sector_ranking`, `cls_sector_ranker` |
| `SIG` | `signal`, `mod_signals` |
| `SYM_RNK` | `symbol_ranking`, `cls_symbol_ranker` |
| `TG_BOT` | `telegram_bot`, `cls_telegram_bot` |
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
| 외환선물 | `FX Futures` | `fxFutures` | `FX_FUT` | `market` | 외환을 기초자산으로 하는 선물 상품. 접근 툴은 MT5이나, 시장 자체는 MT5가 아님. ❌ NOT: `MT5`, `mt5Futures`, `MT5_FUT` *(⚠️ MT5는 툴(플랫폼)이며 시장명이 아님. 반드시 fxFutures/FX_FUT 사용.)* |
| 코스닥 | `KOSDAQ` | `kosdaq` | `KOSDAQ` | `market`, `data` | 한국 코스닥 시장 ❌ NOT: `KOSPI` |
| 코스피 | `KOSPI` | `kospi` | `KOSPI` | `market`, `data` | 한국 종합주가지수 (Korea Composite Stock Price Index) ❌ NOT: `KOSDAQ` |
| 코인거래 | `Cryptocurrency` | `crypto` | `CRYPTO` | `market` | 암호화폐 거래 시장 (업비트 KRW 마켓) |
| 한국주식 | `Korean Stock` | `krStock` | `KR_STOCK` | `market` | 한국 주식 시장 (KRX) ❌ NOT: `KIS`, `KOSPI`, `KOSDAQ` |

---

## 🔧 툴 / 플랫폼 (Tools & Platforms)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| KIS API | `Korea Investment & Securities API` | `kis` | `KIS` | `tool` | 한국투자증권 REST API. 한국주식·미국주식 주문/시세 브로커. ❌ NOT: `KR_STOCK`, `krStock` |
| MT5 | `MetaTrader 5` | `mt5` | `MT5` | `tool` | 해외선물 접근 플랫폼. Windows 전용. 시장명이 아닌 툴명. ❌ NOT: `fxFutures`, `FX_FUT` |
| MT5 브릿지 | `MT5 Bridge` | `mt5Bridge` | `MT5B` | `tool`, `infra` | WSL에서 MT5 프록시로 RPC 호출하는 클라이언트 모듈 |
| MT5 프록시 | `MT5 Proxy` | `mt5Proxy` | `MT5P` | `tool`, `infra`, `config` | WSL Python → Windows MT5 연결을 중계하는 FastAPI 서버 |
| 업비트 | `Upbit` | `upbit` | `UPBIT` | `tool` | 암호화폐 거래소. crypto 마켓의 브로커. |
| 인증 | `Authentication` | `auth` | `AUTH` | `tool`, `system` | 브로커 API 인증 토큰 발급·갱신 (KIS OAuth, Upbit JWT 등) |

---

## 🏗️  인프라 (Infrastructure)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| PostgreSQL | `PostgreSQL` | `postgresql` | `PG_DB` | `infra` | System of Record. 모든 거래·시세·계좌 데이터의 최종 진실 저장소. *(⚠️ v2: abbr_short를 PG_DB로 변경 (process_guard의 PGD와 구분))* |
| Redis | `Redis` | `redis` | `REDIS` | `infra` | 실시간 캐시 + 이벤트 스트림. DB가 원본이며 Redis는 파생값. |
| 노드명 | `Node Name` | `nodeName` | `NODE` | `infra`, `config` | 서버 식별자. 멀티노드 배포 시 노드 구분에 사용. |
| 서비스 매니저 | `Service Manager` | `serviceManager` | `SVC_MGR` | `infra`, `system` | 멀티서비스(DB/LOG/FX/KR/US/Crypto) 시작·중지·상태 관리 |
| 오케스트레이터 | `Orchestrator` | `orchestrator` | `ORCH` | `infra`, `system` | 전체 거래 루프를 조율하는 최상위 실행 컨트롤러 |
| 워치독 | `Watchdog` | `watchdog` | `WDG` | `infra`, `system` | 서비스 비정상 종료 감지 및 자동 재시작 |
| 태스크 스케줄러 | `Task Scheduler` | `taskScheduler` | `SCHED` | `infra`, `system` | 일별/시간별 예약 작업 실행 (리부트, 리포트 생성 등) |
| 프로세스 가드 | `Process Guard` | `processGuard` | `PGD` | `infra`, `system` | 중복 프로세스 실행 방지 (PID 파일 기반) *(⚠️ v2: abbr_short를 PGD로 변경 (postgresql의 PG_DB와 구분))* |
| 하트비트 | `Heartbeat` | `heartbeat` | `HB` | `infra`, `system` | 시스템 생존 신호. 주기적으로 Telegram system 봇에 전송. |

---

## 📐 도메인 개념 (Domain Concepts)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 거래대금 점수 | `Trading Value Score` | `tradingValueScore` | `TVS` | `domain`, `selector` | 거래대금 기반 유동성 점수 |
| 거래량 가중 평균가 | `VWAP` | `vwap` | `VWAP` | `domain`, `data` | Volume Weighted Average Price. 시가총액 가중 평균 체결가. |
| 계좌 스냅샷 | `Account Snapshot` | `accountSnapshot` | `ASNAP` | `domain`, `account` | 특정 시점의 계좌 잔고·포지션 상태 스냅샷 |
| 눌림 | `Pullback` | `pullback` | `PB` | `domain`, `selector` | 상승 추세 중 일시적으로 되돌리는 구간에서 진입하는 패턴 |
| 당일 거래 | `Intraday` | `intraday` | `INTRA` | `domain`, `session` | 당일 내 진입·청산을 완료하는 거래 (데이트레이딩) |
| 대장주 | `Leader Stock` | `leaderStock` | `LEAD` | `domain`, `selector` | 섹터를 이끄는 핵심 종목. 조건식 기반 스캔으로 선정. |
| 대장주 후보 | `Leader Candidates` | `leaderCandidates` | `LCAND` | `domain`, `selector` | 대장주 선정 전 1차 필터링된 후보 종목 목록 |
| 돌파 | `Breakout` | `breakout` | `BRK` | `domain`, `selector` | 직전 N봉 고가를 현재가가 상향 돌파하는 진입 패턴 |
| 롱 | `Long` | `long` | `LONG` | `domain` | 매수 포지션 방향 (가격 상승 기대) |
| 리부트 시각 | `Reboot Time` | `rebootTime` | `RBT` | `domain`, `session`, `system` | 일일 정기 프로세스 재시작 시각 |
| 리스크 매니저 | `Risk Manager` | `riskManager` | `RM` | `domain`, `risk` | 일일 손실 한도, 포지션 한도, 킬스위치 판단 담당 |
| 마켓 스캐너 | `Market Scanner` | `marketScanner` | `SCAN` | `domain`, `selector` | 조건식 기반 대장주 스캔 실행 모듈 |
| 매도 | `Sell` | `sell` | `SELL` | `domain`, `order` | 매도 주문 |
| 매수 | `Buy` | `buy` | `BUY` | `domain`, `order` | 매수 주문 |
| 모멘텀 점수 | `Momentum Score` | `momentumScore` | `MOM` | `domain`, `selector` | 가격 모멘텀(추세 강도) 점수 |
| 모의 거래 | `Mock Trading` | `mockTrading` | `MOCK` | `domain`, `system` | 실제 자금 없이 시뮬레이션으로 진행하는 거래 |
| 미실현 손익 | `Unrealized PnL` | `unrealizedPnl` | `UPNL` | `domain`, `account` | 현재 보유 중인 포지션의 평가 손익 |
| 반등 불발 청산 | `No Bounce Exit` | `noBounceExit` | `NBE` | `domain`, `risk` | 반등 신호 없이 일정 시간 경과 시 청산 |
| 변동성 점수 | `Volatility Score` | `volatilityScore` | `VOLS` | `domain`, `selector`, `risk` | 가격 변동성 점수. 높을수록 리스크 높음. |
| 봉 | `Bar` | `bar` | `BAR` | `domain`, `data` | OHLCV 캔들(봉) 데이터. M1 기준. |
| 분할 매도 | `Split Sell` | `splitSell` | `SSELL` | `domain`, `order` | 분할 매도 (여러 번 나눠서 청산) |
| 분할 매수 | `Split Buy` | `splitBuy` | `SBUY` | `domain`, `order` | 분할 매수 (여러 번 나눠서 진입) |
| 사용 증거금 | `Margin Used` | `marginUsed` | `MRG` | `domain`, `account`, `risk` | 현재 포지션 유지에 사용 중인 증거금 |
| 섹터 강도 점수 | `Sector Strength Score` | `sectorStrengthScore` | `SSS` | `domain`, `selector` | 섹터 내 비교 강도 점수 |
| 섹터 랭킹 | `Sector Ranking` | `sectorRanking` | `SEC_RNK` | `domain`, `selector` | 섹터별 강도 점수 순위 |
| 섹터 점수 | `Sector Score` | `sectorScore` | `SS` | `domain`, `selector` | 섹터 강도를 수치화한 점수 |
| 손절 | `Stop Loss` | `stopLoss` | `SL` | `domain`, `risk` | 손실 한도 도달 시 강제 청산. Hard Stop. |
| 숏 | `Short` | `short` | `SHORT` | `domain` | 매도 포지션 방향 (가격 하락 기대) |
| 수수료 | `Commission` | `commission` | `COMM` | `domain`, `account` | 거래 수수료 (거래당 비용) |
| 슬리피지 | `Slippage` | `slippage` | `SLIP` | `domain`, `order`, `risk` | 주문 가격과 실제 체결 가격의 차이 |
| 시간외 시작 | `Extended Market Start` | `extendedMarketStart` | `EXT_ST` | `domain`, `session` | 시간외 거래 시작 시각 |
| 시간외 종료 | `Extended Market End` | `extendedMarketEnd` | `EXT_END` | `domain`, `session` | 시간외 거래 종료 시각 |
| 시그널 | `Signal` | `signal` | `SIG` | `domain`, `module` | 진입 또는 청산 판단 결과. signals 모듈만 생성 가능. |
| 시그널 방향 | `Signal Direction` | `signalDirection` | `DIR` | `domain`, `status` | LONG / SHORT / FLAT — 시그널이 제안하는 포지션 방향 |
| 시그널 엔진 | `Signal Engine` | `signalEngine` | `SIG_ENG` | `domain` | 진입·청산 조건을 판단하는 핵심 로직 단위 |
| 시장 강도 | `Market Strength` | `marketStrength` | `MS` | `domain`, `selector`, `data` | 전체 시장(코스피·코스닥) 상승/하락 강도 지표 |
| 시장가 주문 | `Market Order` | `marketOrder` | `MKT_ORD` | `domain`, `order` | 현재 시장가로 즉시 체결되는 주문 *(⚠️ v2: abbr_short를 MKT_ORD로 변경 (cls_market의 MKT와 충돌 해소))* |
| 실시간 로그 | `Realtime Log` | `realtimeLog` | `RLOG` | `domain`, `data`, `system` | Redis 스트림 기반 실시간 이벤트 로그 *(⚠️ v2: abbr_short를 RLOG로 변경 (파일 로그 mod_logs의 LOG와 충돌 해소))* |
| 실전 거래 | `Live Trading` | `liveTrading` | `LIVE` | `domain`, `system` | 실제 자금으로 진행하는 거래 |
| 실현 손익 | `Realized PnL` | `realizedPnl` | `RPNL` | `domain`, `account` | 청산 완료된 거래의 확정 손익 |
| 아랫꼬리 | `Lower Wick` | `lowerWick` | `LW` | `domain`, `data` | 캔들 저가에서 몸통까지의 꼬리 (매수 지지 지표) |
| 업무 시작 | `Work Start` | `workStart` | `WS` | `domain`, `session` | 일일 업무 시작 시각 (사전 준비 포함) |
| 연속 손절 횟수 | `Consecutive Stops` | `consecutiveStops` | `CS` | `domain`, `risk` | 연속 손절 한도. 도달 시 당일 진입 차단. |
| 오버나이트 | `Overnight` | `overnight` | `OVNT` | `domain`, `session` | 당일 청산하지 않고 다음날까지 보유하는 거래 *(⚠️ v2: abbr_short를 OVNT로 변경 (enabled/online의 ON과 충돌 해소))* |
| 윗꼬리 | `Upper Wick` | `upperWick` | `UW` | `domain`, `data` | 캔들 고가에서 몸통까지의 꼬리 (매도 압력 지표) |
| 익절 | `Take Profit` | `takeProfit` | `TP` | `domain`, `risk` | 목표 수익 도달 시 청산 |
| 일일 최대 손실 | `Max Daily Loss` | `maxDailyLoss` | `MDL` | `domain`, `risk` | 당일 허용 최대 손실액. 도달 시 전량 청산 + 진입 차단. |
| 장 시작 | `Market Open` | `marketOpen` | `MO` | `domain`, `session` | 해당 마켓의 거래 시작 시각 |
| 장 종료 | `Market Close` | `marketClose` | `MC` | `domain`, `session` | 해당 마켓의 거래 종료 시각 |
| 장 종료 전량 청산 | `End-of-Day Flatten` | `eodFlatten` | `EODF` | `domain`, `order`, `session`, `risk` | 세션 종료 시각에 모든 포지션을 강제 청산 |
| 종목 랭킹 | `Symbol Ranking` | `symbolRanking` | `SYM_RNK` | `domain`, `selector` | 종목별 점수 순위 |
| 종목 점수 | `Stock Score` | `stockScore` | `STS` | `domain`, `selector` | 개별 종목 강도를 수치화한 점수 |
| 주문 | `Order` | `order` | `ORD` | `domain`, `order` | 브로커에 전송된 실제 주문 객체 |
| 주문 상태 | `Order Status` | `orderStatus` | `OS` | `domain`, `status`, `order` | 주문 생명주기 상태: pending→submitted→filled/cancelled/rejected |
| 주문 의도 | `Order Intent` | `orderIntent` | `OI` | `domain`, `order` | 주문 실행 전 의사결정 내용. execution이 생성하여 adapter에 전달. |
| 지정가 주문 | `Limit Order` | `limitOrder` | `LMT` | `domain`, `order` | 지정 가격 이하(매수) 또는 이상(매도)에서만 체결되는 주문 |
| 진입 | `Entry` | `entry` | `ENT` | `domain`, `order` | 포지션 진입 (매수/매도 시작) |
| 진입 차단 시각 | `No Entry After` | `noEntryAfter` | `NEA` | `domain`, `session`, `risk` | 이 시각 이후 신규 진입 차단 |
| 청산 | `Exit` | `exit` | `EXIT` | `domain`, `order` | 포지션 청산 (반대매매로 종료) |
| 청산 거래 | `Closed Trade` | `closedTrade` | `CT` | `domain`, `order` | 청산 완료된 거래. 손익이 확정된 상태. |
| 체결 | `Fill` | `fill` | `FILL` | `domain`, `order` | 주문이 실제 체결된 결과 (가격·수량·시간 포함) |
| 체결 강도 | `Execution Strength` | `execStrength` | `ES` | `domain`, `data` | 실시간 매수/매도 체결 강도 원본값 |
| 체결 강도 점수 | `Execution Strength Score` | `execStrengthScore` | `ESS` | `domain`, `selector` | 매수 체결 강도 점수 (매수강도/매도강도 비율) |
| 최대 동시 보유 수 | `Max Open Positions` | `maxOpenPositions` | `MOP` | `domain`, `risk` | 동시에 보유 가능한 최대 포지션 수 |
| 캔들 성격 | `Candle Personality` | `candlePersonality` | `CP` | `domain`, `selector`, `data` | 캔들 형태 분석 점수 (윗꼬리·아랫꼬리 비율 기반) |
| 킬스위치 | `Kill Switch` | `killSwitch` | `KSW` | `domain`, `risk`, `system` | 파일 기반 전체 거래 차단 장치. KILL_SWITCH 파일 존재 시 진입 전면 차단. |
| 트래킹 시작 | `Tracking Start` | `trackingStart` | `TRK_ST` | `domain`, `session` | 시세 추적 및 신호 감지 시작 시각 |
| 트랜잭션 ID | `Transaction ID` | `transactionId` | `TR_ID` | `domain`, `order`, `infra` | 주문-체결-청산을 연결하는 고유 식별자 |
| 트레일링 스탑 | `Trailing Stop` | `trailingStop` | `TSL` | `domain`, `risk` | 진입 후 최고가 대비 일정 % 이하로 하락 시 청산. 수익 보호. *(⚠️ v2: abbr_short를 TSL로 변경 (task_scheduler의 TS와 충돌 해소))* |
| 틱 | `Tick` | `tick` | `TK` | `domain`, `data` | 최소 가격 변동 단위 또는 실시간 시세 스트림 |
| 포지션 | `Position` | `position` | `POS` | `domain`, `order`, `account` | 현재 보유 중인 종목/계약 상태 (수량, 평균단가, 미실현손익) |
| 포지션 크기 | `Position Size` | `positionSize` | `PSIZ` | `domain`, `risk`, `order` | 1회 진입 시 투입 금액 또는 계약 수 |
| 플랫 | `Flat` | `flat` | `FLAT` | `domain` | 포지션 없음 (현금 보유 상태) |
| 호가 | `Orderbook` | `orderbook` | `OB` | `domain`, `data` | 매수·매도 호가창 스냅샷 |
| 활성 거래 | `Active Trade` | `activeTrade` | `AT` | `domain`, `order` | 현재 보유 중인 거래 (OPEN 상태). TradeJournal의 SoT. |

---

## 📋 거래 / 주문 (Trading & Orders)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 거래 알림 | `Trade Notifier` | `tradeNotifier` | `TRD_NTF` | `order`, `report` | 체결·청산 이벤트를 Telegram market 봇으로 발송 |
| 주문 테이블 | `Orders Table` | `dbOrders` | `ORD_DB` | `order`, `data`, `infra` | DB 주문 이력 테이블 *(⚠️ v2: abbr_long을 dbOrders로, abbr_short를 ORD_DB로 변경 (domain order와 구분))* |
| 체결 테이블 | `Fills Table` | `dbFills` | `FILL_DB` | `order`, `data`, `infra` | DB 체결 이력 테이블 *(⚠️ v2: abbr_long을 dbFills로, abbr_short를 FILL_DB로 변경 (domain fill과 구분))* |

---

## 📊 시장 데이터 (Market Data)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 1분봉 테이블 | `1-Minute Bars Table` | `bars1m` | `BAR1M` | `data`, `infra` | DB 1분 OHLCV 봉 데이터 |
| KR 호가 스냅샷 테이블 | `KR Orderbook Snapshot Table` | `krOrderbookSnapshot` | `KR_OB_DB` | `data`, `infra` | DB KR 주식 호가 스냅샷 (1초 주기) |
| 계좌 스냅샷 테이블 | `Account Snapshots Table` | `accountSnapshots` | `ASNAP` | `data`, `infra`, `account` | DB 계좌 스냅샷 이력 |
| 리스크 이벤트 테이블 | `Risk Events Table` | `riskEvents` | `REVT` | `data`, `infra`, `risk` | DB 리스크 이벤트 이력 (킬스위치·일손 등) |
| 섹터 랭킹 테이블 | `Sector Rankings Table` | `sectorRankings` | `SEC_RNK_DB` | `data`, `infra`, `selector` | DB 섹터 랭킹 스냅샷 *(⚠️ v2: abbr_short를 SEC_RNK_DB로 변경 (domain sector_ranking의 SEC_RNK와 구분))* |
| 섹터 마스터 테이블 | `Sector Master Table` | `sectorMaster` | `SEC_MST` | `data`, `infra` | DB 섹터 마스터 (섹터코드·이름) |
| 시그널 테이블 | `Signals Table` | `dbSignals` | `SIG_DB` | `data`, `infra` | DB 시그널 이력 저장 테이블 *(⚠️ v2: abbr_long을 dbSignals로 변경 (domain signal의 signals와 충돌 방지))* |
| 종목 마스터 테이블 | `Symbols Table` | `symbols` | `SYM` | `data`, `infra` | DB 종목 마스터 (코드·이름·마켓) |
| 주식 마스터 테이블 | `Stock Master Table` | `stockMaster` | `STK_MST` | `data`, `infra` | DB 한국주식 종목 마스터 |
| 틱 테이블 | `Ticks Table` | `ticks` | `TK` | `data`, `infra` | DB 실시간 틱 데이터 |

---

## ⚙️  시스템 운영 (System Operation)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 시스템 알림 | `System Notifier` | `systemNotifier` | `SYS_NTF` | `system`, `report` | 시스템 이벤트(장애·시작·종료)를 Telegram system 봇으로 발송 |
| 역할 | `Role` | `role` | `ROLE` | `system`, `config` | 서비스 또는 노드의 역할 (primary/replica 등) |

---

## 🔑 설정 / 환경변수 (Config & Env)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| FX 마켓 활성화 | `Enable FX Market Env` | `enableFx` | `E_FX` | `config`, `market` | .env > E_FX — 외환선물 마켓 활성화 여부 *(⚠️ v2: E_MT5 → E_FX로 변경 (MT5는 툴명이므로 마켓 활성화 키에 사용 부적절))* |
| KIS 계좌번호 | `KIS Account No Env` | `kisAccountNo` | `KIS_ACCT` | `config` | .env > KIS_ACCT — KIS 실전 계좌번호 |
| KIS 모의 앱키 | `KIS Mock App Key Env` | `kisMockAppKey` | `KIS_MAK` | `config` | .env > KIS_MAK — KIS 모의투자 앱키 |
| KIS 앱시크릿 | `KIS App Secret Env` | `kisAppSecret` | `KIS_AS` | `config` | .env > KIS_AS — KIS API 앱시크릿 |
| KIS 앱키 | `KIS App Key Env` | `kisAppKey` | `KIS_AK` | `config` | .env > KIS_AK — KIS API 앱키 |
| KR 마켓 활성화 | `Enable KR Market Env` | `enableKr` | `E_KR` | `config`, `market` | .env > E_KR — 한국주식 마켓 활성화 여부 |
| KR 셀렉터 설정 | `KR Selector Config` | `krSelector` | `KR_SEL` | `config`, `selector` | settings.yaml > kr_selector 섹션 |
| KR 전략 설정 | `KR Strategy Config` | `krStrategy` | `KR_STR` | `config` | settings.yaml > kr_strategy 섹션 |
| MT5 프록시 URL | `MT5 Proxy URL Env` | `mt5ProxyUrl` | `MT5P` | `config`, `infra` | .env > MT5P — MT5 프록시 서버 URL (툴 접속 설정이므로 MT5 유지) |
| PostgreSQL DSN | `PostgreSQL DSN Env` | `pgDsn` | `PG_DSN` | `config`, `infra` | .env > PG_DSN — PostgreSQL 접속 문자열 |
| Redis URL | `Redis URL Env` | `redisUrl` | `REDIS_URL` | `config`, `infra` | .env > REDIS_URL — Redis 접속 URL |
| US 마켓 활성화 | `Enable US Market Env` | `enableUs` | `E_US` | `config`, `market` | .env > E_US — 미국주식 마켓 활성화 여부 |
| 노드명 환경변수 | `Node Name Env` | `nodeNameEnv` | `NODE` | `config` | .env > NODE_NAME |
| 대시보드 포트 | `Dashboard Port Env` | `dashboardPort` | `DASH_P` | `config`, `infra` | .env > DASH_P — 대시보드 웹서버 포트 |
| 리포트 설정 | `Reporting Config` | `reporting` | `RPT_CFG` | `config`, `report` | settings.yaml > reporting 섹션 *(⚠️ v2: abbr_short를 RPT_CFG로 변경 (mod_report의 RPT와 구분))* |
| 백테스트 설정 | `Backtest Config` | `backtest` | `BT` | `config`, `system` | settings.yaml > backtest 섹션 |
| 세션 설정 | `Sessions Config` | `sessions` | `SESS` | `config`, `session` | settings.yaml > sessions 섹션 (마켓별 시간) |
| 스코어링 설정 | `Scoring Config` | `scoring` | `SCR_CFG` | `config`, `selector` | settings.yaml > scoring 섹션 (가중치 파라미터) |
| 시스템 설정 | `System Config` | `system` | `SYS` | `config` | settings.yaml > system 섹션 |
| 진입 차단 설정 | `Entry Deny Config` | `entryDeny` | `ED` | `config`, `risk` | settings.yaml > entry_deny 섹션 (진입 차단 조건) |
| 프로젝트 루트 | `Project Root Env` | `projectRoot` | `PROJECT_ROOT` | `config` | .env > PROJECT_ROOT — 프로젝트 절대 경로 기준 |
| 환경변수 | `Environment Variable` | `envVar` | `ENV` | `config` | .env 파일 환경변수 총칭 |

---

## 📈 리포트 / 알림 (Report & Notification)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 텔레그램 봇 | `Telegram Bot` | `telegramBot` | `TG_BOT` | `report`, `infra` | Telegram 알림·명령 처리 봇 (system/test/market 3종) |

---

## 📁 모듈 / 디렉토리 (Modules & Directories)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 공통 모듈 | `Common Module` | `common` | `CMN` | `module` | src/common/ — 모델, 설정, 로깅, 예외, 유틸 |
| 로그 디렉토리 | `Logs Directory` | `logs` | `LOG` | `module` | logs/ — 런타임 로그 파일 저장 |
| 리스크 모듈 | `Risk Module` | `risk` | `RSK` | `module` | src/risk/ — 리스크 관리 |
| 리포트 모듈 | `Report Module` | `report` | `RPT` | `module` | src/report/ — 리포트, 대시보드 |
| 리플레이 모듈 | `Replay Module` | `replay` | `RPL` | `module` | src/replay/ — 백테스트 |
| 설정 모듈 | `Config Module` | `config` | `CFG` | `module`, `config` | src/common/config.py — Settings 싱글턴 모듈 |
| 셀렉터 모듈 | `Selector Module` | `selector` | `SEL` | `module` | src/selector/ — 섹터·종목 선정 |
| 수집기 모듈 | `Collectors Module` | `collectors` | `COL` | `module` | src/collectors/ — 시세·데이터 수집 |
| 스토리지 모듈 | `Storage Module` | `storage` | `STG` | `module` | src/storage/ — DB ORM, Redis 클라이언트 |
| 시그널 모듈 | `Signals Module` | `signals` | `SIG` | `module`, `domain` | src/signals/ — 진입/청산 시그널 |
| 실행 모듈 | `Execution Module` | `execution` | `EXEC` | `module` | src/execution/ — 주문 실행, 오케스트레이터 |
| 알림 모듈 | `Notifications Module` | `notifications` | `NTF` | `module` | src/notifications/ — Telegram 봇 |
| 어댑터 모듈 | `Adapters Module` | `adapters` | `ADP` | `module` | src/adapters/ — 브로커 연동 (MT5/KIS/Upbit) |
| 환경변수 모듈 | `Env Module` | `env` | `ENV` | `module`, `config` | .env 파일 로더 모듈 |

---

## 🧩 클래스 / 열거형 (Classes & Enums)

| 한글명 | 클래스명 | abbr_long | abbr_short | 유형 | 모듈 | 설명 |
|--------|---------|-----------|------------|------|------|------|
| DB 엔진 | `DBEngine` | `DBEngine` | `DBA` | True | `-` | PostgreSQL 연결 풀 및 ORM 세션 관리 |
| FX 시그널 엔진 | `FxSignalEngine` | `FxSignalEngine` | `FX_SIG` | True | `-` | 외환선물 진입·청산 시그널 생성 엔진 |
| KIS 모의 인증 클래스 | `KisMockAuth` | `KisMockAuth` | `KIS_MAUTH` | True | `-` | KIS 모의투자 전용 인증 클래스 |
| KIS 미국주식 어댑터 | `KisUsAdapter` | `KisUsAdapter` | `KIS_US_ADP` | True | `-` | 미국주식 KIS API 어댑터 (이중계좌: 실전 데이터 + 모의 매매) |
| KIS 어댑터 | `KisAdapter` | `KisAdapter` | `KIS_ADP` | True | `-` | 한국주식 KIS API 연동 어댑터 (이중 계좌: 실전 데이터 + 모의 매매) |
| KIS 인증 클래스 | `KisAuth` | `KisAuth` | `KIS_AUTH` | True | `-` | KIS OAuth2 토큰 발급·갱신·캐싱 |
| KR 시그널 엔진 | `KrSignalEngine` | `KrSignalEngine` | `KR_SIG` | True | `-` | 한국주식 진입·청산 시그널 생성 엔진 |
| KR 호가 필터 | `KrOrderbookFilter` | `KrOrderbookFilter` | `KR_OBF` | True | `-` | KR 호가 기반 진입 정합성·매도 위험 점수 산출 |
| MT5 로컬 어댑터 | `MT5LocalAdapter` | `MT5LocalAdapter` | `MT5_ADP` | True | `-` | 로컬 MT5 어댑터 (BaseBrokerAdapter 구현, run.py 통합용) |
| MT5 브릿지 클래스 | `MT5Bridge` | `MT5Bridge` | `MT5B` | True | `-` | WSL → Windows MT5 RPC 클라이언트 클래스 |
| MT5 프록시 서버 | `MT5ProxyServer` | `MT5ProxyServer` | `MT5PS` | True | `-` | Windows에서 실행되는 FastAPI 기반 MT5 프록시 서버 |
| Market 열거형 | `Market Enum` | `Market` | `MKT` | True | `-` | 거래 마켓 열거형 (KR_STOCK, US_STOCK, FX_FUT, CRYPTO) |
| US 스윙 시그널 엔진 | `UsSwingSignalEngine` | `UsSwingSignalEngine` | `US_SIG` | True | `-` | 미국주식 스윙 시그널 엔진 (눌림/돌파 진입, 5단계 청산) |
| 거래 기록 모델 | `TradeRecord` | `TradeRecord` | `TR` | True | `-` | 거래 생명주기 전체(진입→청산) Pydantic 모델 |
| 계좌 스냅샷 모델 | `AccountSnapshot` | `AccountSnapshot` | `ASNAP` | True | `-` | 계좌 상태 스냅샷 Pydantic 모델 |
| 리포트 생성기 | `ReportGenerator` | `ReportGenerator` | `RPT_GEN` | True | `-` | 일간/주간/월간 거래 리포트 생성 클래스 |
| 리플레이 러너 | `ReplayRunner` | `ReplayRunner` | `RPL_RUN` | True | `-` | 과거 데이터 기반 백테스트 실행 클래스 |
| 서비스 상태 열거형 | `ServiceStatus Enum` | `ServiceStatus` | `SVC_S` | True | `-` | RUNNING / STOPPED / STARTING / ERROR |
| 서비스 유형 열거형 | `ServiceType Enum` | `ServiceType` | `SVC_T` | True | `-` | DB / LOG / FX / KR / US / CRYPTO / TEST |
| 서비스 정보 모델 | `ServiceInfo` | `ServiceInfo` | `SVC_I` | True | `-` | 서비스 상태·메타데이터 Pydantic 모델 |
| 설정 클래스 | `Settings` | `Settings` | `CFG` | True | `-` | settings.yaml + .env 통합 설정 싱글턴 |
| 섹터 랭커 | `SectorRanker` | `SectorRanker` | `SEC_RNK` | True | `-` | 섹터 강도 랭킹 계산 클래스 |
| 시그널 방향 열거형 | `SignalDirection Enum` | `SignalDirection` | `DIR` | True | `-` | LONG / SHORT / FLAT |
| 시그널 이벤트 | `SignalEvent` | `SignalEvent` | `SIG_EVT` | True | `-` | 시그널 엔진 출력 모델. signals 모듈만 생성 가능. |
| 실행 엔진 | `ExecutionEngine` | `ExecutionEngine` | `EXEC_ENG` | True | `-` | 주문 실행 담당 엔진 (OrderIntent → 브로커 API 호출) |
| 업비트 어댑터 | `UpbitAdapter` | `UpbitAdapter` | `UPB_ADP` | True | `-` | 업비트 REST API 어댑터 (잔고/캔들/주문/레이트리밋) |
| 업비트 인증 | `UpbitAuth` | `UpbitAuth` | `UPB_AUTH` | True | `-` | 업비트 JWT 인증/서명 (PyJWT + SHA512) |
| 종목 랭커 | `SymbolRanker` | `SymbolRanker` | `SYM_RNK` | True | `-` | 종목 점수 랭킹 계산 클래스 |
| 주문 방향 열거형 | `OrderSide Enum` | `OrderSide` | `OSIDE` | True | `-` | BUY / SELL |
| 주문 상태 열거형 | `OrderStatus Enum` | `OrderStatus` | `OS` | True | `-` | PENDING / SUBMITTED / PARTIAL_FILL / FILLED / CANCELLED / REJECTED / FAILED |
| 주문 유형 열거형 | `OrderType Enum` | `OrderType` | `OT` | True | `-` | MARKET / LIMIT |
| 주문 유효 기간 열거형 | `TimeInForce Enum` | `TimeInForce` | `TIF` | True | `-` | GTC / IOC / DAY |
| 주문 의도 모델 | `OrderIntent` | `OrderIntent` | `OI` | True | `-` | 실행 전 주문 의도 Pydantic 모델. execution 모듈만 생성 가능. |
| 코인 리스크 매니저 | `CryptoRiskManager` | `CryptoRiskManager` | `CRY_RM` | True | `-` | 코인 전용 리스크 관리 (연속손절·재진입 제한·일손 한도) |
| 크립토 시그널 엔진 | `CryptoSignalEngine` | `CryptoSignalEngine` | `CRY_SIG` | True | `-` | 암호화폐 추세 돌파 시그널 엔진 (2단계 진입) |
| 텔레그램 봇 클래스 | `TelegramBot` | `TelegramBot` | `TG_BOT` | True | `-` | Telegram 봇 기반 클래스 (system/test/market 공통) |
| 트레이딩 오케스트레이터 | `TradingOrchestrator` | `TradingOrchestrator` | `T_ORCH` | True | `-` | 전체 거래 루프를 조율하는 최상위 클래스 |

---

## 🚦 상태값 (Status Values)

| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |
|--------|--------|-----------|------------|----------|------|
| 거절 | `Rejected` | `rejected` | `RJCT` | `status`, `order` | 브로커에 의해 주문 거절됨 |
| 대기 | `Pending` | `pending` | `PEND` | `status` | 주문 생성 후 브로커 전송 전 대기 상태 |
| 부분 체결 | `Partial Fill` | `partialFill` | `PART` | `status`, `order` | 주문 수량의 일부만 체결된 상태 |
| 비활성화 | `Disabled` | `disabled` | `OFF` | `status`, `config` | 기능 비활성화 상태 |
| 시작 중 | `Starting` | `starting` | `START` | `status`, `system` | 서비스 시작 중 (초기화 진행 중) |
| 실패 | `Failed` | `failed` | `FAIL` | `status` | 시스템 오류로 처리 실패 |
| 실행 중 | `Running` | `running` | `RUN` | `status`, `system` | 서비스 실행 중 상태 |
| 오류 | `Error` | `error` | `ERR` | `status`, `system` | 오류 발생 상태 |
| 오프라인 | `Offline` | `offline` | `OFLN` | `status` | 네트워크/서비스 미연결 상태 *(⚠️ v2: abbr_short를 OFLN으로 변경 (disabled의 OFF와 충돌 해소))* |
| 온라인 | `Online` | `online` | `ONLN` | `status` | 네트워크/서비스 연결 상태 *(⚠️ v2: abbr_short를 ONLN으로 변경 (overnight의 ON과 충돌 해소))* |
| 접수 | `Submitted` | `submitted` | `SUBM` | `status` | 브로커에 주문 전송 완료 |
| 중지 | `Stopped` | `stopped` | `STOP` | `status`, `system` | 서비스 중지 상태 |
| 체결 완료 | `Filled` | `filled` | `FLLD` | `status`, `order` | 주문 전량 체결 완료 |
| 취소 | `Cancelled` | `cancelled` | `CNCL` | `status`, `order` | 주문 취소됨 |
| 활성화 | `Enabled` | `enabled` | `ON` | `status`, `config` | 기능 활성화 상태 |

---

## 🔤 전체 색인 (abbr_short 알파벳순)

| abbr_short | abbr_long | 한글명 | 영문명 |
|------------|-----------|--------|--------|
| `ADP` | `adapters` | 어댑터 모듈 | `Adapters Module` |
| `ASNAP` | `accountSnapshot` | 계좌 스냅샷 | `Account Snapshot` |
| `ASNAP` | `AccountSnapshot` | 계좌 스냅샷 모델 | `AccountSnapshot` |
| `ASNAP` | `accountSnapshots` | 계좌 스냅샷 테이블 | `Account Snapshots Table` |
| `AT` | `activeTrade` | 활성 거래 | `Active Trade` |
| `AUTH` | `auth` | 인증 | `Authentication` |
| `BAR` | `bar` | 봉 | `Bar` |
| `BAR1M` | `bars1m` | 1분봉 테이블 | `1-Minute Bars Table` |
| `BRK` | `breakout` | 돌파 | `Breakout` |
| `BT` | `backtest` | 백테스트 설정 | `Backtest Config` |
| `BUY` | `buy` | 매수 | `Buy` |
| `CFG` | `Settings` | 설정 클래스 | `Settings` |
| `CFG` | `config` | 설정 모듈 | `Config Module` |
| `CMN` | `common` | 공통 모듈 | `Common Module` |
| `CNCL` | `cancelled` | 취소 | `Cancelled` |
| `COL` | `collectors` | 수집기 모듈 | `Collectors Module` |
| `COMM` | `commission` | 수수료 | `Commission` |
| `CP` | `candlePersonality` | 캔들 성격 | `Candle Personality` |
| `CRYPTO` | `crypto` | 코인거래 | `Cryptocurrency` |
| `CRY_RM` | `CryptoRiskManager` | 코인 리스크 매니저 | `CryptoRiskManager` |
| `CRY_SIG` | `CryptoSignalEngine` | 크립토 시그널 엔진 | `CryptoSignalEngine` |
| `CS` | `consecutiveStops` | 연속 손절 횟수 | `Consecutive Stops` |
| `CT` | `closedTrade` | 청산 거래 | `Closed Trade` |
| `DASH_P` | `dashboardPort` | 대시보드 포트 | `Dashboard Port Env` |
| `DBA` | `DBEngine` | DB 엔진 | `DBEngine` |
| `DIR` | `signalDirection` | 시그널 방향 | `Signal Direction` |
| `DIR` | `SignalDirection` | 시그널 방향 열거형 | `SignalDirection Enum` |
| `ED` | `entryDeny` | 진입 차단 설정 | `Entry Deny Config` |
| `ENT` | `entry` | 진입 | `Entry` |
| `ENV` | `env` | 환경변수 모듈 | `Env Module` |
| `ENV` | `envVar` | 환경변수 | `Environment Variable` |
| `EODF` | `eodFlatten` | 장 종료 전량 청산 | `End-of-Day Flatten` |
| `ERR` | `error` | 오류 | `Error` |
| `ES` | `execStrength` | 체결 강도 | `Execution Strength` |
| `ESS` | `execStrengthScore` | 체결 강도 점수 | `Execution Strength Score` |
| `EXEC` | `execution` | 실행 모듈 | `Execution Module` |
| `EXEC_ENG` | `ExecutionEngine` | 실행 엔진 | `ExecutionEngine` |
| `EXIT` | `exit` | 청산 | `Exit` |
| `EXT_END` | `extendedMarketEnd` | 시간외 종료 | `Extended Market End` |
| `EXT_ST` | `extendedMarketStart` | 시간외 시작 | `Extended Market Start` |
| `E_FX` | `enableFx` | FX 마켓 활성화 | `Enable FX Market Env` |
| `E_KR` | `enableKr` | KR 마켓 활성화 | `Enable KR Market Env` |
| `E_US` | `enableUs` | US 마켓 활성화 | `Enable US Market Env` |
| `FAIL` | `failed` | 실패 | `Failed` |
| `FILL` | `fill` | 체결 | `Fill` |
| `FILL_DB` | `dbFills` | 체결 테이블 | `Fills Table` |
| `FLAT` | `flat` | 플랫 | `Flat` |
| `FLLD` | `filled` | 체결 완료 | `Filled` |
| `FX_FUT` | `fxFutures` | 외환선물 | `FX Futures` |
| `FX_SIG` | `FxSignalEngine` | FX 시그널 엔진 | `FxSignalEngine` |
| `HB` | `heartbeat` | 하트비트 | `Heartbeat` |
| `INTRA` | `intraday` | 당일 거래 | `Intraday` |
| `KIS` | `kis` | KIS API | `Korea Investment & Securities API` |
| `KIS_ACCT` | `kisAccountNo` | KIS 계좌번호 | `KIS Account No Env` |
| `KIS_ADP` | `KisAdapter` | KIS 어댑터 | `KisAdapter` |
| `KIS_AK` | `kisAppKey` | KIS 앱키 | `KIS App Key Env` |
| `KIS_AS` | `kisAppSecret` | KIS 앱시크릿 | `KIS App Secret Env` |
| `KIS_AUTH` | `KisAuth` | KIS 인증 클래스 | `KisAuth` |
| `KIS_MAK` | `kisMockAppKey` | KIS 모의 앱키 | `KIS Mock App Key Env` |
| `KIS_MAUTH` | `KisMockAuth` | KIS 모의 인증 클래스 | `KisMockAuth` |
| `KIS_US_ADP` | `KisUsAdapter` | KIS 미국주식 어댑터 | `KisUsAdapter` |
| `KOSDAQ` | `kosdaq` | 코스닥 | `KOSDAQ` |
| `KOSPI` | `kospi` | 코스피 | `KOSPI` |
| `KR_OBF` | `KrOrderbookFilter` | KR 호가 필터 | `KrOrderbookFilter` |
| `KR_OB_DB` | `krOrderbookSnapshot` | KR 호가 스냅샷 테이블 | `KR Orderbook Snapshot Table` |
| `KR_SEL` | `krSelector` | KR 셀렉터 설정 | `KR Selector Config` |
| `KR_SIG` | `KrSignalEngine` | KR 시그널 엔진 | `KrSignalEngine` |
| `KR_STOCK` | `krStock` | 한국주식 | `Korean Stock` |
| `KR_STR` | `krStrategy` | KR 전략 설정 | `KR Strategy Config` |
| `KSW` | `killSwitch` | 킬스위치 | `Kill Switch` |
| `LCAND` | `leaderCandidates` | 대장주 후보 | `Leader Candidates` |
| `LEAD` | `leaderStock` | 대장주 | `Leader Stock` |
| `LIVE` | `liveTrading` | 실전 거래 | `Live Trading` |
| `LMT` | `limitOrder` | 지정가 주문 | `Limit Order` |
| `LOG` | `logs` | 로그 디렉토리 | `Logs Directory` |
| `LONG` | `long` | 롱 | `Long` |
| `LW` | `lowerWick` | 아랫꼬리 | `Lower Wick` |
| `MC` | `marketClose` | 장 종료 | `Market Close` |
| `MDL` | `maxDailyLoss` | 일일 최대 손실 | `Max Daily Loss` |
| `MKT` | `Market` | Market 열거형 | `Market Enum` |
| `MKT_ORD` | `marketOrder` | 시장가 주문 | `Market Order` |
| `MO` | `marketOpen` | 장 시작 | `Market Open` |
| `MOCK` | `mockTrading` | 모의 거래 | `Mock Trading` |
| `MOM` | `momentumScore` | 모멘텀 점수 | `Momentum Score` |
| `MOP` | `maxOpenPositions` | 최대 동시 보유 수 | `Max Open Positions` |
| `MRG` | `marginUsed` | 사용 증거금 | `Margin Used` |
| `MS` | `marketStrength` | 시장 강도 | `Market Strength` |
| `MT5` | `mt5` | MT5 | `MetaTrader 5` |
| `MT5B` | `mt5Bridge` | MT5 브릿지 | `MT5 Bridge` |
| `MT5B` | `MT5Bridge` | MT5 브릿지 클래스 | `MT5Bridge` |
| `MT5P` | `mt5Proxy` | MT5 프록시 | `MT5 Proxy` |
| `MT5P` | `mt5ProxyUrl` | MT5 프록시 URL | `MT5 Proxy URL Env` |
| `MT5PS` | `MT5ProxyServer` | MT5 프록시 서버 | `MT5ProxyServer` |
| `MT5_ADP` | `MT5LocalAdapter` | MT5 로컬 어댑터 | `MT5LocalAdapter` |
| `NBE` | `noBounceExit` | 반등 불발 청산 | `No Bounce Exit` |
| `NEA` | `noEntryAfter` | 진입 차단 시각 | `No Entry After` |
| `NODE` | `nodeName` | 노드명 | `Node Name` |
| `NODE` | `nodeNameEnv` | 노드명 환경변수 | `Node Name Env` |
| `NTF` | `notifications` | 알림 모듈 | `Notifications Module` |
| `OB` | `orderbook` | 호가 | `Orderbook` |
| `OFF` | `disabled` | 비활성화 | `Disabled` |
| `OFLN` | `offline` | 오프라인 | `Offline` |
| `OI` | `orderIntent` | 주문 의도 | `Order Intent` |
| `OI` | `OrderIntent` | 주문 의도 모델 | `OrderIntent` |
| `ON` | `enabled` | 활성화 | `Enabled` |
| `ONLN` | `online` | 온라인 | `Online` |
| `ORCH` | `orchestrator` | 오케스트레이터 | `Orchestrator` |
| `ORD` | `order` | 주문 | `Order` |
| `ORD_DB` | `dbOrders` | 주문 테이블 | `Orders Table` |
| `OS` | `orderStatus` | 주문 상태 | `Order Status` |
| `OS` | `OrderStatus` | 주문 상태 열거형 | `OrderStatus Enum` |
| `OSIDE` | `OrderSide` | 주문 방향 열거형 | `OrderSide Enum` |
| `OT` | `OrderType` | 주문 유형 열거형 | `OrderType Enum` |
| `OVNT` | `overnight` | 오버나이트 | `Overnight` |
| `PART` | `partialFill` | 부분 체결 | `Partial Fill` |
| `PB` | `pullback` | 눌림 | `Pullback` |
| `PEND` | `pending` | 대기 | `Pending` |
| `PGD` | `processGuard` | 프로세스 가드 | `Process Guard` |
| `PG_DB` | `postgresql` | PostgreSQL | `PostgreSQL` |
| `PG_DSN` | `pgDsn` | PostgreSQL DSN | `PostgreSQL DSN Env` |
| `POS` | `position` | 포지션 | `Position` |
| `PROJECT_ROOT` | `projectRoot` | 프로젝트 루트 | `Project Root Env` |
| `PSIZ` | `positionSize` | 포지션 크기 | `Position Size` |
| `RBT` | `rebootTime` | 리부트 시각 | `Reboot Time` |
| `REDIS` | `redis` | Redis | `Redis` |
| `REDIS_URL` | `redisUrl` | Redis URL | `Redis URL Env` |
| `REVT` | `riskEvents` | 리스크 이벤트 테이블 | `Risk Events Table` |
| `RJCT` | `rejected` | 거절 | `Rejected` |
| `RLOG` | `realtimeLog` | 실시간 로그 | `Realtime Log` |
| `RM` | `riskManager` | 리스크 매니저 | `Risk Manager` |
| `ROLE` | `role` | 역할 | `Role` |
| `RPL` | `replay` | 리플레이 모듈 | `Replay Module` |
| `RPL_RUN` | `ReplayRunner` | 리플레이 러너 | `ReplayRunner` |
| `RPNL` | `realizedPnl` | 실현 손익 | `Realized PnL` |
| `RPT` | `report` | 리포트 모듈 | `Report Module` |
| `RPT_CFG` | `reporting` | 리포트 설정 | `Reporting Config` |
| `RPT_GEN` | `ReportGenerator` | 리포트 생성기 | `ReportGenerator` |
| `RSK` | `risk` | 리스크 모듈 | `Risk Module` |
| `RUN` | `running` | 실행 중 | `Running` |
| `SBUY` | `splitBuy` | 분할 매수 | `Split Buy` |
| `SCAN` | `marketScanner` | 마켓 스캐너 | `Market Scanner` |
| `SCHED` | `taskScheduler` | 태스크 스케줄러 | `Task Scheduler` |
| `SCR_CFG` | `scoring` | 스코어링 설정 | `Scoring Config` |
| `SEC_MST` | `sectorMaster` | 섹터 마스터 테이블 | `Sector Master Table` |
| `SEC_RNK` | `sectorRanking` | 섹터 랭킹 | `Sector Ranking` |
| `SEC_RNK` | `SectorRanker` | 섹터 랭커 | `SectorRanker` |
| `SEC_RNK_DB` | `sectorRankings` | 섹터 랭킹 테이블 | `Sector Rankings Table` |
| `SEL` | `selector` | 셀렉터 모듈 | `Selector Module` |
| `SELL` | `sell` | 매도 | `Sell` |
| `SESS` | `sessions` | 세션 설정 | `Sessions Config` |
| `SHORT` | `short` | 숏 | `Short` |
| `SIG` | `signal` | 시그널 | `Signal` |
| `SIG` | `signals` | 시그널 모듈 | `Signals Module` |
| `SIG_DB` | `dbSignals` | 시그널 테이블 | `Signals Table` |
| `SIG_ENG` | `signalEngine` | 시그널 엔진 | `Signal Engine` |
| `SIG_EVT` | `SignalEvent` | 시그널 이벤트 | `SignalEvent` |
| `SL` | `stopLoss` | 손절 | `Stop Loss` |
| `SLIP` | `slippage` | 슬리피지 | `Slippage` |
| `SS` | `sectorScore` | 섹터 점수 | `Sector Score` |
| `SSELL` | `splitSell` | 분할 매도 | `Split Sell` |
| `SSS` | `sectorStrengthScore` | 섹터 강도 점수 | `Sector Strength Score` |
| `START` | `starting` | 시작 중 | `Starting` |
| `STG` | `storage` | 스토리지 모듈 | `Storage Module` |
| `STK_MST` | `stockMaster` | 주식 마스터 테이블 | `Stock Master Table` |
| `STOP` | `stopped` | 중지 | `Stopped` |
| `STS` | `stockScore` | 종목 점수 | `Stock Score` |
| `SUBM` | `submitted` | 접수 | `Submitted` |
| `SVC_I` | `ServiceInfo` | 서비스 정보 모델 | `ServiceInfo` |
| `SVC_MGR` | `serviceManager` | 서비스 매니저 | `Service Manager` |
| `SVC_S` | `ServiceStatus` | 서비스 상태 열거형 | `ServiceStatus Enum` |
| `SVC_T` | `ServiceType` | 서비스 유형 열거형 | `ServiceType Enum` |
| `SYM` | `symbols` | 종목 마스터 테이블 | `Symbols Table` |
| `SYM_RNK` | `symbolRanking` | 종목 랭킹 | `Symbol Ranking` |
| `SYM_RNK` | `SymbolRanker` | 종목 랭커 | `SymbolRanker` |
| `SYS` | `system` | 시스템 설정 | `System Config` |
| `SYS_NTF` | `systemNotifier` | 시스템 알림 | `System Notifier` |
| `TG_BOT` | `telegramBot` | 텔레그램 봇 | `Telegram Bot` |
| `TG_BOT` | `TelegramBot` | 텔레그램 봇 클래스 | `TelegramBot` |
| `TIF` | `TimeInForce` | 주문 유효 기간 열거형 | `TimeInForce Enum` |
| `TK` | `tick` | 틱 | `Tick` |
| `TK` | `ticks` | 틱 테이블 | `Ticks Table` |
| `TP` | `takeProfit` | 익절 | `Take Profit` |
| `TR` | `TradeRecord` | 거래 기록 모델 | `TradeRecord` |
| `TRD_NTF` | `tradeNotifier` | 거래 알림 | `Trade Notifier` |
| `TRK_ST` | `trackingStart` | 트래킹 시작 | `Tracking Start` |
| `TR_ID` | `transactionId` | 트랜잭션 ID | `Transaction ID` |
| `TSL` | `trailingStop` | 트레일링 스탑 | `Trailing Stop` |
| `TVS` | `tradingValueScore` | 거래대금 점수 | `Trading Value Score` |
| `T_ORCH` | `TradingOrchestrator` | 트레이딩 오케스트레이터 | `TradingOrchestrator` |
| `UPBIT` | `upbit` | 업비트 | `Upbit` |
| `UPB_ADP` | `UpbitAdapter` | 업비트 어댑터 | `UpbitAdapter` |
| `UPB_AUTH` | `UpbitAuth` | 업비트 인증 | `UpbitAuth` |
| `UPNL` | `unrealizedPnl` | 미실현 손익 | `Unrealized PnL` |
| `US_SIG` | `UsSwingSignalEngine` | US 스윙 시그널 엔진 | `UsSwingSignalEngine` |
| `US_STOCK` | `usStock` | 미국주식 | `US Stock` |
| `UW` | `upperWick` | 윗꼬리 | `Upper Wick` |
| `VOLS` | `volatilityScore` | 변동성 점수 | `Volatility Score` |
| `VWAP` | `vwap` | 거래량 가중 평균가 | `VWAP` |
| `WDG` | `watchdog` | 워치독 | `Watchdog` |
| `WS` | `workStart` | 업무 시작 | `Work Start` |
