#!/usr/bin/env python3
"""task.md 재작성 스크립트 — 중복 제거 + §5.3/§1.3 완료 반영"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent  # glossary/
TASK = ROOT / "doc" / "plan" / "Glossary Consolidation & Refactoring Plan v2.5.1 task.md"

# 원본 읽기
lines = TASK.read_text(encoding="utf-8", errors="replace").splitlines()

# L1~201(0-index: 0~200)만 유지 + §5.3/§1.3 완료 내용 추가
keep = lines[:201]  # 0-index: L1~L201 (L201 = "- [x] **Step 10. rollback**")

append_lines = [
    "  - `Push-Location` / `Pop-Location` 기반 디렉토리 전환",
    "  - `Get-Date -Format 'yyyyMMdd'` 기반 버전 태깅",
    "  - `Rename-Item` 기반 롤백 절차 + mklink 주석 안내",
    "",
    "### Plan §5.3 Alerting",
    "- [x] **Telegram / Slack 알림 연동** — `web/notifier.py` 신설 (2026-04-16)",
    "  - `.env` 키: `TELEGRAM_SYSTEM_TOKEN`, `TELEGRAM_DEFAULT_CHAT_ID`",
    "  - Slack 방식 1 (권장): `SLACK_WEBHOOK_URL` (Incoming Webhook)",
    "  - Slack 방식 2: `SLACK_BOT_TOKEN` + `SLACK_DEFAULT_CHAT_ID` (Web API, `xoxb-` 필수)",
    "  - 알림 시점: generate FATAL / validate CRITICAL / commit 완료",
    "  - 검증: Telegram `telegram=True` 전송 확인 완료",
    "  - ⚠️ **Slack 주의**: 제공된 `SLACK_SYSTEM_TOKEN`이 Telegram 토큰 형식 → Slack 사용 불가",
    "    `SLACK_WEBHOOK_URL` 또는 `xoxb-` Bot Token 발급 후 `.env`에 설정 필요",
    "",
    "### Plan §1.3 Trading Freeze",
    "- [x] **장중 배포 방지 메커니즘 코드 반영** — `web/trading_freeze.py` 신설 (2026-04-16)",
    "  - `.env` 키: `TRADING_FREEZE_ENABLED` (기본:1), `TRADING_FREEZE_CRYPTO` (기본:0)",
    "  - 차단 시간대 (모두 KST, 월–금):",
    "    - 한국 주식 09:00–15:30",
    "    - 해외 FX 21:00–02:00 (다음날)",
    "    - 코인(Upbit): `TRADING_FREEZE_CRYPTO=1` 시 상시 차단",
    "  - 연동 지점: `/api/generate`, `/api/git/commit` 엔드포인트에 403 반환 게이트 추가",
    "  - 신규 API: `GET /api/trading-freeze/status` — 현재 Freeze 상태 조회",
    "  - 검증: KST 12:35 → \"한국 주식 시장 운영 중\" FREEZE 정상 감지 확인",
    "  - 참고 스니펫: `web/trading_freeze.py` → `is_trading_freeze()` 함수",
]

final_content = "\n".join(keep + append_lines) + "\n"
TASK.write_text(final_content, encoding="utf-8")
print(f"완료: {TASK.name}, {len(keep) + len(append_lines)}줄")
