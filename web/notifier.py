#!/usr/bin/env python3
"""
notifier.py — Glossary 시스템 알림 모듈
위치: glossary/web/notifier.py

§5.3 Alerting 구현:
- Telegram 알림: TELEGRAM_SYSTEM_TOKEN + TELEGRAM_DEFAULT_CHAT_ID (.env)
- Slack 알림:    SLACK_WEBHOOK_URL (.env)  ← Incoming Webhook 방식
                 SLACK_BOT_TOKEN + SLACK_DEFAULT_CHAT_ID (.env) ← Bot 방식 fallback

실행 환경:
- .env 파일은 glossary/ 루트 또는 프로젝트 루트(..)에서 탐색
- 값이 없으면 알림 비활성화 (예외 발생 없음)
"""

import os
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

log = logging.getLogger("glossary")

# ── .env 로더 (dotenv 의존성 없이 직접 파싱) ──────────────────────────
_ENV_LOADED: bool = False
_ENV_CACHE: dict = {}

def _load_env() -> dict:
    """glossary/.env 또는 ../.env 를 파싱하여 dict 반환 (1회 캐싱)."""
    global _ENV_LOADED, _ENV_CACHE
    if _ENV_LOADED:
        return _ENV_CACHE

    script_dir = Path(__file__).parent.parent  # glossary/
    candidates = [
        script_dir / ".env",
        script_dir.parent / ".env",
    ]
    env: dict = {}
    for path in candidates:
        if path.exists():
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                env[key] = val
            break  # 첫 번째 발견된 파일만 사용

    # 시스템 환경변수가 .env보다 우선
    for k in list(env.keys()):
        if k in os.environ:
            env[k] = os.environ[k]

    _ENV_LOADED = True
    _ENV_CACHE = env
    return env


def _get(key: str, default: str = "") -> str:
    """환경변수 값 조회 (시스템 환경변수 → .env 순서)."""
    return os.environ.get(key) or _load_env().get(key, default)


# ── HTTP POST 공통 헬퍼 ────────────────────────────────────────────────
def _http_post(url: str, payload: dict, timeout: int = 10) -> bool:
    """JSON POST 요청을 보내고 성공 여부를 반환한다. 예외는 로그로만 처리."""
    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        log.warning(f"[notifier] HTTP {e.code}: {body}")
    except Exception as e:
        log.warning(f"[notifier] 요청 실패: {e}")
    return False


# ══════════════════════════════════════════════════════════════════════
# Telegram
# ══════════════════════════════════════════════════════════════════════

def send_telegram(message: str, chat_id: Optional[str] = None) -> bool:
    """
    Telegram 봇으로 메시지를 전송한다.

    Args:
        message: 전송할 텍스트 (Markdown 지원)
        chat_id: 대상 chat_id (None이면 .env의 TELEGRAM_DEFAULT_CHAT_ID 사용)

    Returns:
        bool: 전송 성공 여부
    """
    token = _get("TELEGRAM_SYSTEM_TOKEN")
    target_chat_id = chat_id or _get("TELEGRAM_DEFAULT_CHAT_ID")

    if not token or not target_chat_id:
        log.debug("[notifier:telegram] 설정 없음 — 알림 스킵")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    ok = _http_post(url, payload)
    if ok:
        log.info("[notifier:telegram] 전송 완료")
    else:
        log.warning("[notifier:telegram] 전송 실패")
    return ok


# ══════════════════════════════════════════════════════════════════════
# Slack
# ══════════════════════════════════════════════════════════════════════

def send_slack(message: str, channel: Optional[str] = None) -> bool:
    """
    Slack으로 메시지를 전송한다.

    우선순위:
    1. SLACK_WEBHOOK_URL 이 설정된 경우 → Incoming Webhook 방식 (권장)
    2. SLACK_BOT_TOKEN + SLACK_DEFAULT_CHAT_ID → Web API 방식

    Args:
        message: 전송할 텍스트
        channel: 대상 채널 ID (None이면 .env 기본값 사용)

    Returns:
        bool: 전송 성공 여부
    """
    # ── 방식 1: Incoming Webhook ──────────────────────────────────────
    webhook_url = _get("SLACK_WEBHOOK_URL")
    if webhook_url:
        payload = {"text": message}
        ok = _http_post(webhook_url, payload)
        if ok:
            log.info("[notifier:slack] 웹훅 전송 완료")
        else:
            log.warning("[notifier:slack] 웹훅 전송 실패")
        return ok

    # ── 방식 2: Bot Token (chat.postMessage) ───────────────────────────
    bot_token = _get("SLACK_BOT_TOKEN") or _get("SLACK_SYSTEM_TOKEN")
    target_channel = channel or _get("SLACK_DEFAULT_CHAT_ID")

    if not bot_token or not target_channel:
        log.debug("[notifier:slack] 설정 없음 — 알림 스킵")
        return False

    # Slack Bot token은 xoxb- 로 시작해야 함
    if not bot_token.startswith("xoxb-") and not bot_token.startswith("xoxp-"):
        log.warning(
            "[notifier:slack] SLACK_BOT_TOKEN 형식 불일치 "
            "(Slack token은 xoxb- 또는 xoxp- 로 시작해야 합니다). "
            "SLACK_WEBHOOK_URL 설정을 권장합니다."
        )
        return False

    url = "https://slack.com/api/chat.postMessage"
    payload = {
        "channel": target_channel,
        "text": message,
    }
    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {bot_token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("ok"):
                log.info("[notifier:slack] Bot API 전송 완료")
                return True
            else:
                log.warning(f"[notifier:slack] API 오류: {result.get('error')}")
    except Exception as e:
        log.warning(f"[notifier:slack] 요청 실패: {e}")
    return False


# ══════════════════════════════════════════════════════════════════════
# 통합 알림 (Telegram + Slack 동시 발송)
# ══════════════════════════════════════════════════════════════════════

class AlertLevel:
    """알림 레벨 상수."""
    INFO     = "INFO"
    WARNING  = "WARNING"
    CRITICAL = "CRITICAL"


def notify(message: str, level: str = AlertLevel.INFO) -> dict:
    """
    Telegram + Slack 동시 알림 전송.

    Args:
        message: 전송할 메시지
        level:   AlertLevel.INFO / WARNING / CRITICAL

    Returns:
        dict: {"telegram": bool, "slack": bool}
    """
    # 레벨별 이모지 접두사
    prefix_map = {
        AlertLevel.INFO:     "ℹ️",
        AlertLevel.WARNING:  "⚠️",
        AlertLevel.CRITICAL: "🚨",
    }
    prefix = prefix_map.get(level, "📢")
    formatted = f"{prefix} *[Glossary]* {message}"

    tg_ok  = send_telegram(formatted)
    slk_ok = send_slack(formatted)

    return {"telegram": tg_ok, "slack": slk_ok}


# ── 편의 함수 ─────────────────────────────────────────────────────────
def notify_info(message: str) -> dict:
    """INFO 레벨 알림."""
    return notify(message, AlertLevel.INFO)

def notify_warning(message: str) -> dict:
    """WARNING 레벨 알림."""
    return notify(message, AlertLevel.WARNING)

def notify_critical(message: str) -> dict:
    """CRITICAL 레벨 알림."""
    return notify(message, AlertLevel.CRITICAL)


# ── CLI 테스트 ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import io
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    msg = sys.argv[1] if len(sys.argv) > 1 else "Glossary 알림 테스트 메시지"
    print(f"전송 메시지: {msg}")
    result = notify_info(msg)
    print(f"결과: telegram={result['telegram']}, slack={result['slack']}")
