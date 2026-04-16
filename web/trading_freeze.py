#!/usr/bin/env python3
"""
trading_freeze.py — 장중 배포 방지 모듈
위치: glossary/web/trading_freeze.py

§1.3 Trading Freeze 구현:
- 장중 / active position 상태에서 glossary 배포(generate + commit) 차단
- web/server.py 의 /api/git/commit, /api/generate 엔드포인트에서 호출

배포 금지 시간대 (KST):
- 한국 주식 (KIS): 09:00 – 15:30
- 해외 FX (MT5):   21:00 – 02:00 (다음날)
- 코인 (Upbit):    TRADING_FREEZE_CRYPTO=1 설정 시 상시 차단

.env 설정:
- TRADING_FREEZE_ENABLED=1  # 1=활성화, 0=비활성화 (기본: 1)
- TRADING_FREEZE_CRYPTO=0   # 1=코인 상시 차단 (기본: 0)
"""

import os
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Optional

log = logging.getLogger("glossary")

# ── .env 파싱 (notifier.py와 동일한 방식) ────────────────────────────
_ENV_CACHE: dict = {}
_ENV_LOADED: bool = False

def _load_env() -> dict:
    global _ENV_LOADED, _ENV_CACHE
    if _ENV_LOADED:
        return _ENV_CACHE
    script_dir = Path(__file__).parent.parent  # glossary/
    candidates = [script_dir / ".env", script_dir.parent / ".env"]
    env: dict = {}
    for path in candidates:
        if path.exists():
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip().strip('"').strip("'")
            break
    for k in list(env.keys()):
        if k in os.environ:
            env[k] = os.environ[k]
    _ENV_LOADED = True
    _ENV_CACHE = env
    return env

def _get(key: str, default: str = "") -> str:
    return os.environ.get(key) or _load_env().get(key, default)


# ── KST 시간 취득 ─────────────────────────────────────────────────────
def _now_kst() -> datetime:
    """현재 KST 시간 반환. pytz 미설치 시 UTC+9 고정 offset 사용."""
    try:
        import pytz
        KST = pytz.timezone("Asia/Seoul")
        return datetime.now(KST)
    except ImportError:
        from datetime import timezone, timedelta
        KST_OFFSET = timezone(timedelta(hours=9))
        return datetime.now(KST_OFFSET)


# ══════════════════════════════════════════════════════════════════════
# 핵심 함수
# ══════════════════════════════════════════════════════════════════════

def is_trading_freeze() -> tuple[bool, str]:
    """
    현재 시각이 Trading Freeze 구간인지 확인한다.

    Returns:
        tuple[bool, str]: (is_frozen, reason)
            - is_frozen: True이면 배포 금지 구간
            - reason:    금지 이유 (빈 문자열이면 허용)

    Trading Freeze 구간:
    - 한국 주식 시장 운영 중 (월–금 09:00–15:30 KST)
    - 해외 FX 거래 시간 (월–금 21:00–02:00 KST)
    - 코인 상시 차단 (TRADING_FREEZE_CRYPTO=1 설정 시)
    """
    # 기능 비활성화 체크
    enabled = _get("TRADING_FREEZE_ENABLED", "1")
    if enabled.strip() in ("0", "false", "False", "off"):
        return False, ""

    now_kst = _now_kst()
    weekday = now_kst.weekday()  # 0=월요일 … 4=금요일, 5=토, 6=일
    t = now_kst.time()
    time_str = t.strftime("%H:%M")

    # 주말은 허용
    if weekday >= 5:
        return False, ""

    # ── 코인 상시 차단 ───────────────────────────────────────────────
    crypto_freeze = _get("TRADING_FREEZE_CRYPTO", "0")
    if crypto_freeze.strip() in ("1", "true", "True", "on"):
        return True, f"코인(Upbit) 상시 Trading Freeze 활성화 ({time_str} KST)"

    # ── 한국 주식 시장 (09:00–15:30 KST) ────────────────────────────
    if time(9, 0) <= t <= time(15, 30):
        return True, f"한국 주식 시장 운영 중 ({time_str} KST, 허용: 15:35–08:55)"

    # ── 해외 FX 거래 시간 (21:00–02:00 KST) ─────────────────────────
    # 자정을 넘어가므로 OR 조건 사용
    if t >= time(21, 0) or t <= time(2, 0):
        return True, f"해외 FX 거래 시간 ({time_str} KST, 허용: 02:05–20:55)"

    return False, ""


def check_freeze_or_raise(action: str = "배포") -> Optional[dict]:
    """
    Trading Freeze 상태를 확인하고 차단 시 flask jsonify 응답 dict를 반환한다.

    Args:
        action: 차단된 작업명 (로그/메시지용)

    Returns:
        dict | None:
            - 차단 시: {"ok": False, "error": str, "frozen": True}
            - 허용 시: None
    """
    is_frozen, reason = is_trading_freeze()
    if is_frozen:
        msg = f"[Trading Freeze] {action} 차단: {reason}"
        log.warning(msg)

        # 알림 발송 (notifier 연동, import 실패 시 무시)
        try:
            from web.notifier import notify_warning
            notify_warning(msg)
        except Exception:
            try:
                from notifier import notify_warning
                notify_warning(msg)
            except Exception:
                pass

        return {
            "ok":     False,
            "frozen": True,
            "error":  f"Trading Freeze: {reason}. 장외 시간에 배포하세요.",
        }
    return None


# ── 상태 조회 API용 헬퍼 ─────────────────────────────────────────────
def get_freeze_status() -> dict:
    """
    현재 Trading Freeze 상태를 dict로 반환한다.
    /api/trading-freeze/status 엔드포인트에서 사용.
    """
    is_frozen, reason = is_trading_freeze()
    enabled = _get("TRADING_FREEZE_ENABLED", "1")
    now_kst = _now_kst()
    return {
        "enabled":   enabled.strip() not in ("0", "false", "False", "off"),
        "is_frozen": is_frozen,
        "reason":    reason,
        "time_kst":  now_kst.strftime("%Y-%m-%d %H:%M:%S KST"),
        "weekday":   ["월", "화", "수", "목", "금", "토", "일"][now_kst.weekday()],
    }


# ── CLI 확인 ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import io
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    status = get_freeze_status()
    print(f"Trading Freeze 상태 확인")
    print(f"  활성화 : {status['enabled']}")
    print(f"  현재 KST: {status['time_kst']} ({status['weekday']}요일)")
    print(f"  Freeze  : {status['is_frozen']}")
    if status["reason"]:
        print(f"  이유    : {status['reason']}")
    else:
        print(f"  → 배포 허용 구간입니다.")
