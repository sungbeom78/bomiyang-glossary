# BOM_TS 용어 사전

> 자동 생성 파일. 수동 편집 금지.
> 원본: `words.json` + `compounds.json` + `banned.json`
> 생성: 2026-04-14 14:20

## 통계
- 단어: 234개
- 복합어: 154개
- 금지 표현: 8개

---

## 단어 사전 (Words)

### trading

| 단어 | 한글 | 약어 | 품사 | 복수형 | 설명 |
|------|------|------|------|--------|------|
| `account` | 계좌 | — | noun | auto | 투자 계좌 정보 |
| `active` | 활성 | — | adj | — | 현재 진행 중이거나 활성화된 상태 |
| `balance` | 잔고 | — | noun | auto | 계좌의 현재 자산 잔고 |
| `bar` | 봉 | BAR | noun | auto | OHLCV 캔들(봉) 데이터. M1 기준. |
| `bounce` | 반등 | — | noun | auto | 하락 후 일시적 상승 |
| `breakout` | 돌파 | BRK | noun | auto | 직전 N봉 고가를 현재가가 상향 돌파하는 진입 패턴 |
| `buy` | 매수 | BUY | noun | auto | 매수 주문 |
| `capital` | 자본금 | — | noun | auto | 투자 시스템의 총 자본금 |
| `classify` | 분류 | — | noun | auto | 데이터를 분류하는 기능 |
| `commission` | 수수료 | COMM | noun | auto | 거래 수수료 (거래당 비용) |
| `condition` | 조건 | — | noun | auto | 매매 진입/청산 또는 필터링에 사용되는 조건 |
| `consecutive` | 연속 | — | adj | — | 연속으로 발생하는 |
| `contract` | 계약 | — | noun | auto | 선물 계약 단위 |
| `entry` | 진입 | ENT | noun | auto | 포지션 진입 (매수/매도 시작) |
| `eod` | 장마감 | — | noun | auto | End of Day 장 마감 시점 |
| `equity` | 자본 | — | noun | auto | 계좌의 현재 자본 값 |
| `exec` | 실행 | — | noun | auto | 실행 또는 체결 강도 |
| `execution` | 실행 | — | noun | auto | 주문 실행 및 관리 관련 시스템 |
| `exit` | 청산 | EXIT | noun | auto | 포지션 청산 (반대매매로 종료) |
| `fill` | 체결 | FILL | noun | auto | 주문이 실제 체결된 결과 (가격·수량·시간 포함) |
| `flat` | 플랫 | FLAT | noun | auto | 포지션 없음 (현금 보유 상태) |
| `flatten` | 청산 | — | verb | — | 모든 포지션을 닫는 행위 |
| `goldenkey` | 골든키 | — | noun | auto | 특정 종목 선정 기준 또는 신호 |
| `intraday` | 당일 거래 | INTRA | noun | auto | 당일 내 진입·청산을 완료하는 거래 (데이트레이딩) |
| `leader` | 대장 | — | noun | auto | 섹터를 주도하는 종목 |
| `limit` | 한도/지정가 | — | noun | auto | 가격 제한 또는 지정가 주문 |
| `live` | 실전 | — | adj | — | 실제 자금으로 진행하는 |
| `long` | 롱 | LONG | noun | auto | 매수 포지션 방향 (가격 상승 기대) |
| `loss` | 손실 | — | noun | auto | 거래에서 발생한 손실 |
| `margin` | 증거금 | — | noun | auto | 포지션 유지를 위한 담보금 |
| `mock` | 모의 | — | adj | — | 실제 자금 없이 시뮬레이션하는 |
| `momentum` | 모멘텀 | — | noun | auto | 가격 추세의 강도 |
| `order` | 주문 | ORD | noun | auto | 브로커에 전송된 실제 주문 객체 |
| `orderbook` | 호가 | OB | noun | auto | 매수·매도 호가창 스냅샷 |
| `overnight` | 오버나이트 | OVNT | noun | auto | 당일 청산하지 않고 다음날까지 보유하는 거래 |
| `partial` | 부분 | — | adj | — | 전체 중 일부만 처리된 |
| `pnl` | 손익 | — | noun | auto | Profit and Loss 손익 |
| `position` | 포지션 | POS | noun | auto | 현재 보유 중인 종목/계약 상태 (수량, 평균단가, 미실현손익) |
| `premium` | 프리미엄 | — | noun | auto | 프리미엄 가격/가치 |
| `profit` | 수익 | — | noun | auto | 거래에서 발생한 이익 |
| `pullback` | 눌림 | PB | noun | auto | 상승 추세 중 일시적으로 되돌리는 구간에서 진입하는 패턴 |
| `realized` | 실현 | — | adj | — | 청산 완료되어 확정된 |
| `reentry` | 재진입 | — | noun | auto | 거래에서 재진입할 수 있는지 여부를 결정하는 설정. |
| `risk` | 리스크 | — | noun | auto | 손실 가능성 또는 위험도 |
| `sell` | 매도 | SELL | noun | auto | 매도 주문 |
| `short` | 숏 | SHORT | noun | auto | 매도 포지션 방향 (가격 하락 기대) |
| `signal` | 시그널 | SIG | noun | auto | 진입 또는 청산 판단 결과. signals 모듈만 생성 가능. |
| `slippage` | 슬리피지 | SLIP | noun | auto | 주문 가격과 실제 체결 가격의 차이 |
| `split` | 분할 | — | verb | — | 수량을 여러 번에 나눠 처리 |
| `stop` | 정지/손절 | — | noun | auto | 손실 한도 도달 시 포지션 청산 |
| `swing` | 스윙 | — | noun | auto | 수일~수주에 걸친 중기 매매 |
| `take` | 취득 | — | verb | — | 목표 수익을 달성하여 청산 |
| `tick` | 틱 | TK | noun | auto | 최소 가격 변동 단위 또는 실시간 시세 스트림 |
| `trade` | 거래 | — | noun | auto | 개별 매매 거래 |
| `trading` | 거래 | — | noun | auto | 매매 거래 행위 또는 거래 관련 |
| `trailing` | 추적 | — | adj | — | 수익에 따라 이동하는 |
| `universe` | 유니버스 | — | noun | auto | 거래 대상이 되는 종목 또는 자산의 집합입니다. |
| `unrealized` | 미실현 | — | adj | — | 아직 청산되지 않은 |
| `volatility` | 변동성 | — | noun | auto | 가격 변동의 폭 |
| `vwap` | 거래량 가중 평균가 | VWAP | noun | auto | Volume Weighted Average Price. 시가총액 가중 평균 체결가. |

### market

| 단어 | 한글 | 약어 | 품사 | 복수형 | 설명 |
|------|------|------|------|--------|------|
| `candle` | 캔들 | — | noun | auto | 캔들스틱 차트 봉 |
| `categories` | 분류 | — | noun | auto | 종목 또는 테마의 분류 정보 |
| `classification` | 분류 | — | noun | auto | 종목 또는 시장 상황에 대한 분류 결과 |
| `close` | 종가 | — | noun | auto | 봉의 마지막 가격 |
| `code` | 코드 | CODE | noun | auto | 종목 코드 또는 기타 식별 코드 |
| `crypto` | 코인거래 | — | noun | auto | 암호화폐 거래 시장 (업비트 KRW 마켓) |
| `direction` | 방향 | — | noun | auto | 시그널의 매수/매도 방향 |
| `exchange` | 거래소 | — | noun | auto | 거래가 이루어지는 금융 거래소 |
| `futures` | 선물 | — | noun | auto | 선물 상품 |
| `fx` | 외환 | — | prefix | — | 외환 시장 prefix |
| `history` | 히스토리 | — | noun | auto | 과거 데이터 또는 이벤트 기록 |
| `kosdaq` | 코스닥 | — | noun | auto | 한국 코스닥 시장 |
| `kospi` | 코스피 | KOSPI | noun | auto | 한국 종합주가지수 (Korea Composite Stock Price Index) |
| `kr` | 한국 | — | prefix | — | 한국 시장 prefix |
| `lower` | 아래 | — | adj | — | 아래쪽에 위치한 |
| `m` | 분 | M | suffix | — | 분 단위 시간 접미사 (1m, 5m 등) |
| `market` | 시장 | — | noun | auto | 거래가 이루어지는 시장 |
| `meta` | 메타 정보 | META | noun | auto |  |
| `open` | 시가 | — | noun | auto | 봉의 시작 가격 |
| `personality` | 성격 | — | noun | auto | 봉의 형태적 특성 |
| `ranking` | 랭킹 | — | noun | auto | 순위 결과 |
| `realtime` | 실시간 | — | adj | — | 실시간으로 처리되는 |
| `score` | 점수 | — | noun | auto | 특정 지표의 수치화 결과 |
| `sector` | 섹터 | — | noun | auto | 산업 분류 업종 |
| `stock` | 주식 | — | noun | auto | 주식 종목 |
| `strength` | 강도 | — | noun | auto | 시장 또는 종목의 상승/하락 강도 |
| `symbol` | 종목 | — | noun | auto | 거래 종목 코드 |
| `theme` | 테마 | — | noun | auto | 종목 분류 테마 (테마주) |
| `upper` | 위 | — | adj | — | 위쪽에 위치한 |
| `us` | 미국 | — | prefix | — | 미국 시장 prefix |
| `value` | 거래대금 | — | noun | auto | 가격×수량의 거래 금액 |
| `wick` | 꼬리 | — | noun | auto | 캔들의 몸통 밖 선 |

### system

| 단어 | 한글 | 약어 | 품사 | 복수형 | 설명 |
|------|------|------|------|--------|------|
| `after` | 이후 | — | adv | — | 특정 시각 이후 |
| `backtest` | 백테스트 | — | noun | auto | 과거 데이터 기반 전략 검증 |
| `cancelled` | 취소 | CNCL | noun | auto | 주문 취소됨 |
| `chart` | 차트 | CHART | noun | auto | 시각화를 위한 차트 설정 |
| `closed` | 종료됨 | — | noun | auto | 주문, 거래 또는 프로세스가 종료되었음을 나타내는 상태 |
| `cluster` | 클러스터 | — | noun | auto | 데이터 클러스터링 결과 또는 구조 |
| `clustering` | 클러스터링 | — | noun | auto | 데이터를 클러스터로 그룹화하는 설정 |
| `collector` | 수집기 | — | noun | auto | 데이터를 수집하는 컴포넌트 |
| `colors` | 색상 | — | noun | auto | UI 또는 보고서에 사용되는 색상 설정 |
| `command` | 명령어 | — | noun | auto | 시스템 제어를 위한 명령어 설정 |
| `complete` | 완료 | — | noun | auto | 작업 또는 프로세스가 완료되었음을 나타내는 상태 |
| `completed` | 완료됨 | — | noun | auto | 주문, 작업 또는 프로세스가 완료되었음을 나타내는 상태 |
| `confidence` | 신뢰도 | — | noun | auto | 신호 또는 예측의 신뢰 수준 |
| `config` | 설정 | cfg | noun | auto | 시스템 설정값 |
| `confirmed` | 확인됨 | — | noun | auto | 어떤 이벤트나 상태가 최종적으로 확인되었음을 나타내는 플래그 |
| `connected` | 연결됨 | — | noun | auto | 서비스 또는 시스템과의 연결 상태 |
| `core` | 코어 | — | noun | auto | 공통 흐름의 중심 역할을 담당하는 핵심 구성요소 |
| `deny` | 거부 | — | verb | — | 진입 조건 불충족으로 거부 |
| `disabled` | 비활성화 | OFF | noun | auto | 기능 비활성화 상태 |
| `enabled` | 활성화 | ON | noun | auto | 기능 활성화 상태 |
| `end` | 종료 | — | noun | auto | 종료 시각 또는 동작 |
| `engine` | 엔진 | — | noun | auto | 시스템의 핵심 처리 로직을 담당하는 부분 |
| `error` | 오류 | ERR | noun | auto | 오류 발생 상태 |
| `event` | 이벤트 | — | noun | auto | 시스템 내 발생 사건 |
| `extended` | 확장 | — | adj | — | 기본 범위를 넘어 확장된 |
| `failed` | 실패 | FAIL | noun | auto | 시스템 오류로 처리 실패 |
| `filled` | 체결 완료 | FLLD | noun | auto | 주문 전량 체결 완료 |
| `filter` | 필터 | — | noun | auto | 조건에 맞게 거르는 컴포넌트 |
| `generator` | 생성기 | — | noun | auto | 결과물을 생성하는 컴포넌트 |
| `guard` | 가드 | — | noun | auto | 프로세스 보호 컴포넌트 |
| `halted` | 중단됨 | — | noun | auto | 거래 또는 시스템이 일시적으로 중단된 상태 |
| `handlers` | 핸들러 | — | noun | auto | 특정 이벤트를 처리하는 객체 또는 함수들의 집합 |
| `health` | 상태 | — | noun | auto | 시스템 컴포넌트의 정상 작동 여부 (헬스 체크) |
| `info` | 정보 | — | noun | auto | 메타 정보 |
| `intent` | 의도 | — | noun | auto | 실행 전 주문 의사결정 객체 |
| `interval` | 간격 | — | noun | auto | 데이터 수집, 분석 또는 작업 실행 간격 |
| `kill` | 킬 | — | verb | — | 강제 종료 또는 비활성화 |
| `local` | 로컬 | — | adj | — | 원격이 아닌 로컬 환경 |
| `log` | 로그 | — | noun | auto | 시스템 이벤트 기록 |
| `main` | 메인 실행 | MAIN | noun | auto |  |
| `manager` | 관리자 | — | noun | auto |  |
| `manual` | 수동 | — | noun | auto |  |
| `method` | 방법 | — | noun | auto |  |
| `module` | 모듈 | — | noun | auto | 특정 책임을 캡슐화한 코드 단위 |
| `no` | 금지 | — | prefix | — | 부정 또는 금지를 나타내는 접두사 |
| `node` | 노드 | — | noun | auto | 분산 환경의 개별 머신/컨테이너 |
| `notifier` | 알리미 | — | noun | auto | 알림 발송 컴포넌트 |
| `offline` | 오프라인 | OFLN | noun | auto | 네트워크/서비스 미연결 상태 |
| `online` | 온라인 | ONLN | noun | auto | 네트워크/서비스 연결 상태 |
| `pending` | 대기 | PEND | noun | auto | 주문 생성 후 브로커 전송 전 대기 상태 |
| `process` | 프로세스 | — | noun | auto | 실행 중인 프로그램 |
| `protocol` | 프로토콜 | — | noun | auto | 모듈 간 동작 계약(인터페이스) 규약 |
| `ranker` | 랭커 | — | noun | auto | 순위를 산정하는 컴포넌트 |
| `reboot` | 재시작 | — | noun | auto | 시스템 정기 재시작 |
| `record` | 기록 | — | noun | auto | 개별 거래 이력 |
| `registry` | 레지스트리 | — | noun | auto | 마켓별 모듈을 등록하고 조회하는 매핑 저장소 |
| `rejected` | 거절 | RJCT | noun | auto | 브로커에 의해 주문 거절됨 |
| `relaxed` | 완화된 | — | noun | auto | 특정 조건을 완화하여 적용하는 설정. |
| `replay` | 리플레이 | — | noun | auto | 과거 데이터 재생 시뮬레이션 |
| `report` | 리포트 | — | noun | auto | 보고서 |
| `reporting` | 리포팅 | — | noun | auto | 보고서 생성 설정 |
| `role` | 역할 | ROLE | noun | auto | 서비스 또는 노드의 역할 (primary/replica 등) |
| `runner` | 실행기 | — | noun | auto | 작업을 실행하는 컴포넌트 |
| `running` | 실행 중 | RUN | noun | auto | 서비스 실행 중 상태 |
| `runtime` | 런타임 | — | noun | auto | 프로그램이 실행되는 환경 또는 시간. |
| `scanner` | 스캐너 | — | noun | auto | 시장이나 종목을 탐색하고 분석하는 모듈 또는 기능. |
| `scheduler` | 스케줄러 | — | noun | auto | 작업 예약 및 관리를 담당하는 시스템 컴포넌트 또는 설정. |
| `scope` | 범위 | SCOPE | noun | auto | 설정이나 작업이 적용되는 범위를 정의하는 설정. |
| `scorer` | 스코어러 | — | noun | auto | 종목 또는 신호에 점수를 부여하는 모듈. |
| `scoring` | 스코어링 | — | noun | auto | 점수 산정 로직 |
| `selector` | 셀렉터 | — | noun | auto | 종목 선정 컴포넌트 |
| `server` | 서버 | — | noun | auto | 서버 프로세스 |
| `service` | 서비스 | — | noun | auto | 독립적으로 실행되는 프로세스 |
| `sessions` | 세션들 | — | noun | auto | 시장 세션 설정 모음 |
| `settings` | 설정들 | — | noun | auto | 시스템 설정값 모음 |
| `side` | 방향 | — | noun | auto | 매수/매도 방향 |
| `snapshot` | 스냅샷 | — | noun | auto | 특정 시점의 상태 저장본 |
| `start` | 시작 | — | noun | auto | 시작 시각 또는 동작 |
| `starting` | 시작 중 | — | noun | auto | 서비스 시작 중 (초기화 진행 중) |
| `status` | 상태 | — | noun | auto | 현재 처리 상태 |
| `stopped` | 중지 | — | noun | auto | 서비스 중지 상태 |
| `strategy` | 전략 | — | noun | auto | 매매 전략 설정 |
| `submitted` | 접수 | SUBM | noun | auto | 브로커에 주문 전송 완료 |
| `switch` | 스위치 | — | noun | auto | 기능 활성화/비활성화 제어 |
| `system` | 시스템 | — | noun | auto | 전체 소프트웨어 시스템 |
| `task` | 작업 | — | noun | auto | 스케줄링되는 실행 단위 |
| `time` | 시각 | — | noun | auto | 특정 시점 |
| `timeframe` | 타임프레임 | — | noun | auto | 차트 또는 데이터 분석에서 사용되는 시간 단위 (예: 1분, 5분, 1시간). |
| `timezone` | 시간대 | — | noun | auto | 시스템 또는 특정 작업에서 사용되는 표준 시간대 설정입니다. |
| `token` | 토큰 | TOKEN | noun | auto | 인증 또는 세션 관리에 사용되는 보안 토큰입니다. |
| `tracking` | 추적 | — | noun | auto | 종목 모니터링 시작 시각 |
| `tradability` | 거래 가능성 | — | noun | auto | 종목이나 상품의 거래 가능 여부 또는 수준을 나타내는 지표입니다. |
| `transaction` | 거래 ID | — | noun | auto | API 요청 식별자 |
| `transition` | 전환 | — | noun | auto | 상태 머신 등에서 한 상태에서 다른 상태로의 변화를 나타냅니다. |
| `trend` | 추세 | TREND | noun | auto | 시장 가격의 전반적인 방향성을 나타냅니다. |
| `type` | 유형 | — | noun | auto | 분류 유형 |
| `used` | 사용됨 | — | adj | — | 현재 사용 중인 |
| `var` | 변수 | — | noun | auto | 환경변수 |
| `work` | 작업 | — | noun | auto | 일과 시작 |

### infra

| 단어 | 한글 | 약어 | 품사 | 복수형 | 설명 |
|------|------|------|------|--------|------|
| `adapter` | 어댑터 | — | noun | auto | 외부 API 연결 어댑터 |
| `app` | 앱 | — | noun | auto | 애플리케이션 키 |
| `auth` | 인증 | AUTH | noun | auto | 브로커 API 인증 토큰 발급·갱신 (KIS OAuth, Upbit JWT 등) |
| `bot` | 봇 | — | noun | auto | 자동화 프로그램 |
| `bridge` | 브릿지 | — | noun | auto | 두 시스템을 연결하는 컴포넌트 |
| `cls` | 클래스 | — | noun | auto | 클래스 정의 접두사 |
| `common` | 공통 | — | adj | — | 전 모듈 공유 공통 코드 |
| `dashboard` | 대시보드 | — | noun | auto | 모니터링 UI |
| `db` | 데이터베이스 | — | noun | auto | 데이터베이스 접두사 |
| `dsn` | 접속 문자열 | — | noun | auto | Database Source Name |
| `enable` | 활성화 | — | verb | — | 기능을 켜는 설정 |
| `env` | 환경변수 | — | noun | auto | 환경변수 접두사 |
| `heartbeat` | 하트비트 | HB | noun | auto | 시스템 생존 신호. 주기적으로 Telegram system 봇에 전송. |
| `id` | 식별자 | — | noun | auto | 고유 식별자 |
| `key` | 키 | — | noun | auto | 인증 키 |
| `kis` | KIS API | KIS | noun | auto | 한국투자증권 REST API. 한국주식·미국주식 주문/시세 브로커. |
| `master` | 마스터 | — | noun | auto | 기준 데이터 테이블 |
| `mod` | 모듈 | — | noun | auto | 모듈/폴더 접두사 |
| `mt5` | MT5 | MT5 | noun | auto | 해외선물 접근 플랫폼. Windows 전용. 시장명이 아닌 툴명. |
| `name` | 이름 | — | noun | auto | 식별 이름 |
| `notification` | 알림 | — | noun | auto | 시스템 이벤트를 외부로 전달하는 알림 |
| `orchestrator` | 오케스트레이터 | ORCH | noun | auto | 전체 거래 루프를 조율하는 최상위 실행 컨트롤러 |
| `pg` | PostgreSQL | — | proper | — | PostgreSQL 데이터베이스 |
| `port` | 포트 | — | noun | auto | 네트워크 포트 번호 |
| `postgresql` | PostgreSQL | — | noun | auto | System of Record. 모든 거래·시세·계좌 데이터의 최종 진실 저장소. |
| `project` | 프로젝트 | — | noun | auto | 프로젝트 루트 |
| `proxy` | 프록시 | — | noun | auto | 통신을 중계하는 서버 |
| `redis` | Redis | REDIS | noun | auto | 실시간 캐시 + 이벤트 스트림. DB가 원본이며 Redis는 파생값. |
| `root` | 루트 | — | noun | auto | 최상위 경로 |
| `secret` | 시크릿 | — | noun | auto | 비밀 인증 키 |
| `storage` | 저장소 | — | noun | auto | 데이터 저장 추상화 레이어 |
| `table` | 테이블 | — | noun | auto | DB 테이블 또는 데이터 구조 |
| `telegram` | 텔레그램 | — | proper | — | 텔레그램 메시징 서비스 |
| `upbit` | 업비트 | UPBIT | noun | auto | 암호화폐 거래소. crypto 마켓의 브로커. |
| `url` | URL | — | noun | auto | Uniform Resource Locator |
| `watchdog` | 워치독 | WDG | noun | auto | 서비스 비정상 종료 감지 및 자동 재시작 |

### general

| 단어 | 한글 | 약어 | 품사 | 복수형 | 설명 |
|------|------|------|------|--------|------|
| `candidates` | 후보들 | — | noun | auto | 선정 대상 후보 목록 |
| `daily` | 일간 | — | adj | — | 하루 단위 |
| `force` | 강제 | — | verb | — | 조건과 무관하게 강제 실행 |
| `in` | 내에서 | — | adv | — | 시간 내, 범위 내 |
| `max` | 최대 | — | adj | — | 최대값 |
| `size` | 크기 | — | noun | auto | 수량 또는 비중 |
| `top` | 상위 | — | adj | — | 순위/값 기준 상위 |

---

## 복합어 사전 (Compounds)

| 복합어 | 구성 단어 | 한글 | camelCase | 약어 | 복수형 | 등록 사유 |
|--------|----------|------|-----------|------|--------|----------|
| `[N]m` | m | N분봉 | `[N]m` | `[N]M` | auto | 숫자+단위 조합 패턴. 개별 등록 시 무한 증식 |
| `account_snapshot` | account + snapshot | 계좌 스냅샷 | `accountSnapshot` | `ASNAP` | auto | 공인 약어 |
| `active_trade` | active + trade | 활성 거래 | `activeTrade` | `AT` | auto | 공인 약어 |
| `candle_personality` | candle + personality | 캔들 성격 | `candlePersonality` | `CP` | auto | 공인 약어 |
| `cfg_backtest` | config + backtest | 백테스트 설정 | `backtest` | `BT` | auto | 공인 약어 |
| `cfg_entry_deny` | config + entry + deny | 진입 차단 설정 | `entryDeny` | `ED` | auto | 공인 약어 |
| `cfg_kr_selector` | config + kr + selector | KR 셀렉터 설정 | `krSelector` | `KR_SEL` | auto | 의미 비합산 |
| `cfg_kr_strategy` | config + kr + strategy | KR 전략 설정 | `krStrategy` | `KR_STR` | auto | 의미 비합산 |
| `cfg_reporting` | config + reporting | 리포트 설정 | `reporting` | `RPT_CFG` | auto | 의미 비합산 |
| `cfg_scoring` | config + scoring | 스코어링 설정 | `scoring` | `SCR_CFG` | auto | 의미 비합산 |
| `cfg_sessions` | config + sessions | 세션 설정 | `sessions` | `SESS` | auto | 공인 약어 |
| `cfg_system` | config + system | 시스템 설정 | `system` | `SYS` | auto | 공인 약어 |
| `closed_trade` | closed + trade | 청산 거래 | `closedTrade` | `CT` | auto | 공인 약어 |
| `cls_account_snapshot` | cls + account + snapshot | 계좌 스냅샷 모델 | `AccountSnapshot` | `ASNAP_C` | auto | 공인 약어, 시스템 객체 |
| `cls_crypto_risk_manager` | cls + crypto + risk + manager | 코인 리스크 매니저 | `CryptoRiskManager` | `CRY_RM` | auto | 시스템 객체 |
| `cls_crypto_signal_engine` | cls + crypto + signal + engine | 크립토 시그널 엔진 | `CryptoSignalEngine` | `CRY_SIG` | auto | 시스템 객체 |
| `cls_db_engine` | cls + db + engine | DB 엔진 | `DBEngine` | `DBA` | auto | 공인 약어, 시스템 객체 |
| `cls_execution_engine` | cls + execution + engine | 실행 엔진 | `ExecutionEngine` | `EXEC_ENG` | auto | 시스템 객체 |
| `cls_fx_signal_engine` | cls + fx + signal + engine | FX 시그널 엔진 | `FxSignalEngine` | `FX_SIG` | auto | 시스템 객체 |
| `cls_kis_adapter` | cls + kis + adapter | KIS 어댑터 | `KisAdapter` | `KIS_ADP` | auto | 시스템 객체, 고유명사 |
| `cls_kis_auth` | cls + kis + auth | KIS 인증 클래스 | `KisAuth` | `KIS_AUTH` | auto | 시스템 객체, 고유명사 |
| `cls_kis_mock_auth` | cls + kis + mock + auth | KIS 모의 인증 클래스 | `KisMockAuth` | `KIS_MAUTH` | auto | 시스템 객체, 고유명사 |
| `cls_kis_us_adapter` | cls + kis + us + adapter | KIS 미국주식 어댑터 | `KisUsAdapter` | `KIS_US_ADP` | auto | 시스템 객체, 고유명사 |
| `cls_kr_orderbook_filter` | cls + kr + orderbook + filter | KR 호가 필터 | `KrOrderbookFilter` | `KR_OBF` | auto | 시스템 객체 |
| `cls_kr_signal_engine` | cls + kr + signal + engine | KR 시그널 엔진 | `KrSignalEngine` | `KR_SIG` | auto | 시스템 객체 |
| `cls_market` | cls + market | Market 열거형 | `Market` | `MKT` | auto | 공인 약어, 시스템 객체 |
| `cls_mt5_bridge` | cls + mt5 + bridge | MT5 브릿지 클래스 | `MT5Bridge` | `MT5B_C` | auto | 공인 약어, 시스템 객체, 고유명사 |
| `cls_mt5_local_adapter` | cls + mt5 + local + adapter | MT5 로컬 어댑터 | `MT5LocalAdapter` | `MT5_ADP` | auto | 시스템 객체, 고유명사 |
| `cls_mt5_proxy_server` | cls + mt5 + proxy + server | MT5 프록시 서버 | `MT5ProxyServer` | `MT5PS` | auto | 공인 약어, 시스템 객체, 고유명사 |
| `cls_order_intent` | cls + order + intent | 주문 의도 모델 | `OrderIntent` | `OI_C` | auto | 공인 약어, 시스템 객체 |
| `cls_order_side` | cls + order + side | 주문 방향 열거형 | `OrderSide` | `OSIDE` | auto | 공인 약어, 시스템 객체 |
| `cls_order_status` | cls + order + status | 주문 상태 열거형 | `OrderStatus` | `OS_C` | auto | 공인 약어, 시스템 객체 |
| `cls_order_type` | cls + order + type | 주문 유형 열거형 | `OrderType` | `OT` | auto | 공인 약어, 시스템 객체 |
| `cls_replay_runner` | cls + replay + runner | 리플레이 러너 | `ReplayRunner` | `RPL_RUN` | auto | 시스템 객체 |
| `cls_report_generator` | cls + report + generator | 리포트 생성기 | `ReportGenerator` | `RPT_GEN` | auto | 시스템 객체 |
| `cls_sector_ranker` | cls + sector + ranker | 섹터 랭커 | `SectorRanker` | `SEC_RNK_C` | auto | 시스템 객체 |
| `cls_service_info` | cls + service + info | 서비스 정보 모델 | `ServiceInfo` | `SVC_I` | auto | 시스템 객체 |
| `cls_service_status` | cls + service + status | 서비스 상태 열거형 | `ServiceStatus` | `SVC_S` | auto | 시스템 객체 |
| `cls_service_type` | cls + service + type | 서비스 유형 열거형 | `ServiceType` | `SVC_T` | auto | 시스템 객체 |
| `cls_settings` | cls + settings | 설정 클래스 | `Settings` | `CFG_C` | auto | 공인 약어, 시스템 객체 |
| `cls_signal_direction` | cls + signal + direction | 시그널 방향 열거형 | `SignalDirection` | `DIR_C` | auto | 공인 약어, 시스템 객체 |
| `cls_signal_event` | cls + signal + event | 시그널 이벤트 | `SignalEvent` | `SIG_EVT` | auto | 시스템 객체 |
| `cls_symbol_ranker` | cls + symbol + ranker | 종목 랭커 | `SymbolRanker` | `SYM_RNK_C` | auto | 시스템 객체 |
| `cls_telegram_bot` | cls + telegram + bot | 텔레그램 봇 클래스 | `TelegramBot` | `TG_BOT_C` | auto | 시스템 객체 |
| `cls_time_in_force` | cls + time + in + force | 주문 유효 기간 열거형 | `TimeInForce` | `TIF` | auto | 공인 약어, 시스템 객체 |
| `cls_trade_record` | cls + trade + record | 거래 기록 모델 | `TradeRecord` | `TR` | auto | 공인 약어, 시스템 객체 |
| `cls_trading_orchestrator` | cls + trading + orchestrator | 트레이딩 오케스트레이터 | `TradingOrchestrator` | `T_ORCH` | auto | 시스템 객체 |
| `cls_upbit_adapter` | cls + upbit + adapter | 업비트 어댑터 | `UpbitAdapter` | `UPB_ADP` | auto | 시스템 객체, 고유명사 |
| `cls_upbit_auth` | cls + upbit + auth | 업비트 인증 | `UpbitAuth` | `UPB_AUTH` | auto | 시스템 객체, 고유명사 |
| `cls_us_swing_signal_engine` | cls + us + swing + signal + engine | US 스윙 시그널 엔진 | `UsSwingSignalEngine` | `US_SIG` | auto | 시스템 객체 |
| `consecutive_stops` | consecutive + stop | 연속 손절 횟수 | `consecutiveStops` | `CS` | auto | 공인 약어 |
| `db_account_snapshots` | db + account + snapshot | 계좌 스냅샷 테이블 | `accountSnapshots` | `ASNAP_DB` | auto | 공인 약어 |
| `db_bars_1m` | db + bar | 1분봉 테이블 | `bars1m` | `BAR1M` | auto | 공인 약어 |
| `db_fills` | db + fill | 체결 테이블 | `dbFills` | `FILL_DB` | auto | 의미 비합산 |
| `db_kr_orderbook_snapshot` | db + kr + orderbook + snapshot | KR 호가 스냅샷 테이블 | `krOrderbookSnapshot` | `KR_OB_DB` | auto | 의미 비합산 |
| `db_orders` | db + order | 주문 테이블 | `dbOrders` | `ORD_DB` | auto | 의미 비합산 |
| `db_risk_events` | db + risk + event | 리스크 이벤트 테이블 | `riskEvents` | `REVT` | auto | 공인 약어 |
| `db_sector_master` | db + sector + master | 섹터 마스터 테이블 | `sectorMaster` | `SEC_MST` | auto | 의미 비합산 |
| `db_sector_rankings` | db + sector + ranking | 섹터 랭킹 테이블 | `sectorRankings` | `SEC_RNK_DB` | auto | 의미 비합산 |
| `db_signals` | db + signal | 시그널 테이블 | `dbSignals` | `SIG_DB` | auto | 의미 비합산 |
| `db_stock_master` | db + stock + master | 주식 마스터 테이블 | `stockMaster` | `STK_MST` | auto | 의미 비합산 |
| `db_symbols` | db + symbol | 종목 마스터 테이블 | `symbols` | `SYM` | auto | 공인 약어 |
| `db_ticks` | db + tick | 틱 테이블 | `ticks` | `TK_DB` | auto | 공인 약어 |
| `env_dashboard_port` | env + dashboard + port | 대시보드 포트 | `dashboardPort` | `DASH_P` | auto | 의미 비합산 |
| `env_enable_fx` | env + enable + fx | FX 마켓 활성화 | `enableFx` | `E_FX` | auto | 의미 비합산 |
| `env_enable_kr` | env + enable + kr | KR 마켓 활성화 | `enableKr` | `E_KR` | auto | 의미 비합산 |
| `env_enable_us` | env + enable + us | US 마켓 활성화 | `enableUs` | `E_US` | auto | 의미 비합산 |
| `env_kis_account_no` | env + kis + account + no | KIS 계좌번호 | `kisAccountNo` | `KIS_ACCT` | auto | 의미 비합산 |
| `env_kis_app_key` | env + kis + app + key | KIS 앱키 | `kisAppKey` | `KIS_AK` | auto | 의미 비합산 |
| `env_kis_app_secret` | env + kis + app + secret | KIS 앱시크릿 | `kisAppSecret` | `KIS_AS` | auto | 의미 비합산 |
| `env_kis_mock_app_key` | env + kis + mock + app + key | KIS 모의 앱키 | `kisMockAppKey` | `KIS_MAK` | auto | 의미 비합산 |
| `env_mt5_proxy_url` | env + mt5 + proxy + url | MT5 프록시 URL | `mt5ProxyUrl` | `MT5P_E` | auto | 공인 약어 |
| `env_node_name` | env + node + name | 노드명 환경변수 | `nodeNameEnv` | `NODE_E` | auto | 공인 약어 |
| `env_pg_dsn` | env + pg + dsn | PostgreSQL DSN | `pgDsn` | `PG_DSN` | auto | 의미 비합산 |
| `env_project_root` | env + project + root | 프로젝트 루트 | `projectRoot` | `PROJECT_ROOT` | auto | 의미 비합산 |
| `env_redis_url` | env + redis + url | Redis URL | `redisUrl` | `REDIS_URL` | auto | 의미 비합산 |
| `env_var` | env + var | 환경변수 | `envVar` | `ENV_E` | auto | 공인 약어 |
| `eod_flatten` | eod + flatten | 장 종료 전량 청산 | `eodFlatten` | `EODF` | auto | 공인 약어 |
| `exec_strength` | exec + strength | 체결 강도 | `execStrength` | `ES` | auto | 공인 약어 |
| `exec_strength_score` | exec + strength + score | 체결 강도 점수 | `execStrengthScore` | `ESS` | auto | 공인 약어 |
| `extended_market_end` | extended + market + end | 시간외 종료 | `extendedMarketEnd` | `EXT_END` | auto | 의미 비합산 |
| `extended_market_start` | extended + market + start | 시간외 시작 | `extendedMarketStart` | `EXT_ST` | auto | 의미 비합산 |
| `fx_futures` | fx + futures | 외환선물 | `fxFutures` | `FX_FUT` | auto | 혼동 방지 |
| `kill_switch` | kill + switch | 킬스위치 | `killSwitch` | `KSW` | auto | 공인 약어 |
| `kr_stock` | kr + stock | 한국주식 | `krStock` | `KR_STOCK` | auto | 혼동 방지 |
| `leader_candidates` | leader + candidates | 대장주 후보 | `leaderCandidates` | `LCAND` | auto | 공인 약어 |
| `leader_stock` | leader + stock | 대장주 | `leaderStock` | `LEAD` | auto | 공인 약어 |
| `limit_order` | limit + order | 지정가 주문 | `limitOrder` | `LMT` | auto | 공인 약어 |
| `live_trading` | live + trading | 실전 거래 | `liveTrading` | `` | auto | 공인 약어 |
| `lower_wick` | lower + wick | 아랫꼬리 | `lowerWick` | `LW` | auto | 공인 약어 |
| `margin_used` | margin + used | 사용 증거금 | `marginUsed` | `MRG` | auto | 공인 약어 |
| `market_close` | market + close | 장 종료 | `marketClose` | `MC` | auto | 공인 약어 |
| `market_open` | market + open | 장 시작 | `marketOpen` | `MO` | auto | 공인 약어 |
| `market_order` | market + order | 시장가 주문 | `marketOrder` | `MKT_ORD` | auto | 의미 비합산 |
| `market_scanner` | market + scanner | 마켓 스캐너 | `marketScanner` | `SCAN` | auto | 공인 약어 |
| `market_strength` | market + strength | 시장 강도 | `marketStrength` | `MS` | auto | 공인 약어 |
| `max_daily_loss` | max + daily + loss | 일일 최대 손실 | `maxDailyLoss` | `MDL` | auto | 공인 약어 |
| `max_open_positions` | max + open + position | 최대 동시 보유 수 | `maxOpenPositions` | `MOP` | auto | 공인 약어 |
| `mock_trading` | mock + trading | 모의 거래 | `mockTrading` | `` | auto | 공인 약어 |
| `mod_adapters` | mod + adapter | 어댑터 모듈 | `adapters` | `ADP` | auto | 공인 약어, 시스템 객체 |
| `mod_collectors` | mod + collector | 수집기 모듈 | `collectors` | `COL` | auto | 공인 약어, 시스템 객체 |
| `mod_common` | mod + common | 공통 모듈 | `common` | `CMN` | auto | 공인 약어, 시스템 객체 |
| `mod_config` | mod + config | 설정 모듈 | `config` | `CFG_M` | auto | 공인 약어, 시스템 객체 |
| `mod_env` | mod + env | 환경변수 모듈 | `env` | `ENV_M` | auto | 공인 약어, 시스템 객체 |
| `mod_execution` | mod + execution | 실행 모듈 | `execution` | `` | auto | 공인 약어, 시스템 객체 |
| `mod_logs` | mod + log | 로그 디렉토리 | `logs` | `` | auto | 공인 약어, 시스템 객체 |
| `mod_notifications` | mod + notification | 알림 모듈 | `notifications` | `NTF` | auto | 공인 약어, 시스템 객체 |
| `mod_replay` | mod + replay | 리플레이 모듈 | `replay` | `RPL` | auto | 공인 약어, 시스템 객체 |
| `mod_report` | mod + report | 리포트 모듈 | `report` | `RPT` | auto | 공인 약어, 시스템 객체 |
| `mod_risk` | mod + risk | 리스크 모듈 | `risk` | `RSK` | auto | 공인 약어, 시스템 객체 |
| `mod_selector` | mod + selector | 셀렉터 모듈 | `selector` | `SEL` | auto | 공인 약어, 시스템 객체 |
| `mod_signals` | mod + signal | 시그널 모듈 | `signals` | `SIG_M` | auto | 공인 약어, 시스템 객체 |
| `mod_storage` | mod + storage | 스토리지 모듈 | `storage` | `STG` | auto | 공인 약어, 시스템 객체 |
| `momentum_score` | momentum + score | 모멘텀 점수 | `momentumScore` | `MOM` | auto | 공인 약어 |
| `mt5_bridge` | mt5 + bridge | MT5 브릿지 | `mt5Bridge` | `MT5B` | auto | 공인 약어, 고유명사 |
| `mt5_proxy` | mt5 + proxy | MT5 프록시 | `mt5Proxy` | `MT5P` | auto | 공인 약어, 고유명사 |
| `no_bounce_exit` | no + bounce + exit | 반등 불발 청산 | `noBounceExit` | `NBE` | auto | 공인 약어 |
| `no_entry_after` | no + entry + after | 진입 차단 시각 | `noEntryAfter` | `NEA` | auto | 공인 약어 |
| `node_name` | node + name | 노드명 | `nodeName` | `` | auto | 공인 약어 |
| `order_intent` | order + intent | 주문 의도 | `orderIntent` | `OI` | auto | 공인 약어 |
| `order_status` | order + status | 주문 상태 | `orderStatus` | `OS` | auto | 공인 약어 |
| `partial_fill` | partial + fill | 부분 체결 | `partialFill` | `PART` | auto | 공인 약어 |
| `position_size` | position + size | 포지션 크기 | `positionSize` | `PSIZ` | auto | 공인 약어 |
| `process_guard` | process + guard | 프로세스 가드 | `processGuard` | `PGD` | auto | 공인 약어 |
| `realized_pnl` | realized + pnl | 실현 손익 | `realizedPnl` | `RPNL` | auto | 공인 약어 |
| `realtime_log` | realtime + log | 실시간 로그 | `realtimeLog` | `RLOG` | auto | 공인 약어 |
| `reboot_time` | reboot + time | 리부트 시각 | `rebootTime` | `RBT` | auto | 공인 약어 |
| `risk_manager` | risk + manager | 리스크 매니저 | `riskManager` | `RM` | auto | 공인 약어 |
| `sector_ranking` | sector + ranking | 섹터 랭킹 | `sectorRanking` | `SEC_RNK` | auto | 의미 비합산 |
| `sector_score` | sector + score | 섹터 점수 | `sectorScore` | `SS` | auto | 공인 약어 |
| `sector_strength_score` | sector + strength + score | 섹터 강도 점수 | `sectorStrengthScore` | `SSS` | auto | 공인 약어 |
| `service_manager` | service + manager | 서비스 매니저 | `serviceManager` | `SVC_MGR` | auto | 의미 비합산 |
| `signal_direction` | signal + direction | 시그널 방향 | `signalDirection` | `DIR` | auto | 공인 약어 |
| `signal_engine` | signal + engine | 시그널 엔진 | `signalEngine` | `SIG_ENG` | auto | 의미 비합산 |
| `split_buy` | split + buy | 분할 매수 | `splitBuy` | `SBUY` | auto | 공인 약어 |
| `split_sell` | split + sell | 분할 매도 | `splitSell` | `SSELL` | auto | 공인 약어 |
| `stock_score` | stock + score | 종목 점수 | `stockScore` | `STS` | auto | 공인 약어 |
| `stop_loss` | stop + loss | 손절 | `stopLoss` | `SL` | auto | 공인 약어 |
| `symbol_ranking` | symbol + ranking | 종목 랭킹 | `symbolRanking` | `SYM_RNK` | auto | 의미 비합산 |
| `system_notifier` | system + notifier | 시스템 알림 | `systemNotifier` | `SYS_NTF` | auto | 의미 비합산 |
| `take_profit` | take + profit | 익절 | `takeProfit` | `TP` | auto | 공인 약어 |
| `task_scheduler` | task + scheduler | 태스크 스케줄러 | `taskScheduler` | `SCHED` | auto | 공인 약어 |
| `telegram_bot` | telegram + bot | 텔레그램 봇 | `telegramBot` | `TG_BOT` | auto | 의미 비합산 |
| `top[N]` | top | 상위 N개 | `top[N]` | `TOP[N]` | auto | 숫자 파라미터 패턴. 개별 등록 시 무한 증식 |
| `tracking_start` | tracking + start | 트래킹 시작 | `trackingStart` | `TRK_ST` | auto | 의미 비합산 |
| `trade_notifier` | trade + notifier | 거래 알림 | `tradeNotifier` | `TRD_NTF` | auto | 의미 비합산 |
| `trading_value_score` | trading + value + score | 거래대금 점수 | `tradingValueScore` | `TVS` | auto | 공인 약어 |
| `trailing_stop` | trailing + stop | 트레일링 스탑 | `trailingStop` | `TSL` | auto | 공인 약어 |
| `transaction_id` | transaction + id | 트랜잭션 ID | `transactionId` | `TR_ID` | auto | 의미 비합산 |
| `unrealized_pnl` | unrealized + pnl | 미실현 손익 | `unrealizedPnl` | `UPNL` | auto | 공인 약어 |
| `upper_wick` | upper + wick | 윗꼬리 | `upperWick` | `UW` | auto | 공인 약어 |
| `us_stock` | us + stock | 미국주식 | `usStock` | `US_STOCK` | auto | 의미 비합산 |
| `volatility_score` | volatility + score | 변동성 점수 | `volatilityScore` | `VOLS` | auto | 공인 약어 |
| `work_start` | work + start | 업무 시작 | `workStart` | `WS` | auto | 공인 약어 |

---

## [N] 패턴 (Numeric Pattern Compounds)

| 패턴 | 예시 | 설명 |
|------|------|------|
| `[N]m` | 1m, 5m, 10m, 15m, 60m | [N]분 단위 캔들/봉 데이터. [N]은 임의의 자연수(>0). 실제 사용: 1m, 5m, 10m, 15m, 60m 등 |
| `top[N]` | top3, top5, top10, top100 | 상위 N개 항목 선택/필터링. [N]은 임의의 자연수(>0). 실제 사용: top3, top5, top10, top100 등 |

---

## 금지 표현 (Banned)

| 금지 표현 | 올바른 표현 | 사유 | 위반 강도 |
|----------|------------|------|----------|
| `MT5_FUT` | `FX_FUT` | MT5는 플랫폼(tool)이지 시장(market)이 아님 (마켓 식별자로 사용 시) | warn |
| `mt5Futures` | `fxFutures` | MT5는 접근 툴이며 마켓명이 아님 (외환선물 변수명으로 사용 시) | warn |
| `KIS` | `KR_STOCK` | KIS는 브로커명. 마켓 식별자와 혼용 금지 (한국주식 마켓 식별자 의미로 사용 시) | warn |
| `MT5` | `FX_FUT 또는 fxFutures` | MT5는 MetaTrader5 플랫폼명 (외환선물 마켓 의미로 사용 시) | warn |
| `VOL` | `VOLS (volatilityScore) 또는 context 명시` | VOL은 거래량(volume)과 혼동 가능 (변동성(volatility) 의미로 단독 사용 시) | warn |
| `TS` | `문맥에 따라 trailingStop / TRK_ST 구분` | TS가 두 개념에 모두 사용되어 혼동 발생 (trailingStop 또는 trackingStart 단독 사용 시) | warn |
| `WR` | `문맥에 따라 weeklyReport / W_RPT 또는 winRate 구분` | WR이 두 개념에 모두 사용되어 혼동 발생 (weeklyReport 또는 winRate 단독 사용 시) | warn |
| `ON` | `각 의미에 맞는 전체 이름 사용` | ON이 세 가지 개념에 사용되어 혼동 발생 (enabled/online/overnight 혼용 시) | warn |
