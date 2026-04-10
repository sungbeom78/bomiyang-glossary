#!/usr/bin/env python3
"""
run.py v2  —  BOM_TS glossary 빌드 러너
위치: glossary/bin/run.py

역할:
  generate_glossary.py 의 validate / generate 명령을 실행하는 래퍼.
  v2 체계(words.json + compounds.json + banned.json)에서
  직접 모듈을 import 하지 않고 subprocess 로 위임한다.

사용법:
    python run.py              # validate → generate (기본)
    python run.py --check      # validate만 (오류 확인)
    python run.py --force      # validate 실패해도 generate 강행
    python run.py --watch      # dictionary/ 변경 감지 시 자동 재실행

감시 파일 (watch 모드):
    glossary/dictionary/words.json
    glossary/dictionary/compounds.json
    glossary/dictionary/banned.json

규칙 준수:
    AGENTS.md Rule 8-A: 폴더명 단수형 (log/, test/ 등)
    08_naming.md: 시스템 공식 명칭 BOM_TS 사용
"""

import sys
import os
import time
import argparse
import io
import subprocess
from pathlib import Path
from datetime import datetime

# ── Windows cp949 인코딩 오류 방지 ────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── 경로 ─────────────────────────────────────────────────────────────
BIN_DIR      = Path(__file__).parent.resolve()   # glossary/bin/
REPO_ROOT    = BIN_DIR.parent.resolve()          # glossary/
GENERATE_PY  = REPO_ROOT / "generate_glossary.py"
DICT_DIR     = REPO_ROOT / "dictionary"
GLOSSARY_MD  = REPO_ROOT / "GLOSSARY.md"

# watch 대상 파일 목록
WATCH_FILES = [
    DICT_DIR / "words.json",
    DICT_DIR / "compounds.json",
    DICT_DIR / "banned.json",
]


# ════════════════════════════════════════════════════════════════════
# 출력 헬퍼 (ASCII only — Windows cp949 안전)
# ════════════════════════════════════════════════════════════════════

def _sep(char="-", width=52): print(char * width)

def _header(text: str):
    _sep("="); print(f"  {text}"); _sep("=")

def _ok(text: str):   print(f"  [OK]   {text}")
def _fail(text: str): print(f"  [FAIL] {text}")
def _info(text: str): print(f"  [..]   {text}")
def _warn(text: str): print(f"  [WARN] {text}")
def _step(text: str): print(f"\n>>  {text}")


# ════════════════════════════════════════════════════════════════════
# subprocess 헬퍼
# ════════════════════════════════════════════════════════════════════

def _run_generate_py(*args) -> tuple:
    """
    generate_glossary.py <args> 를 subprocess 로 실행.
    반환: (returncode: int, output: str)
    """
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8']       = '1'

    cmd = [sys.executable, str(GENERATE_PY)] + list(args)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=60,
            env=env,
        )
        output = result.stdout or ""
        if result.stderr:
            output += "\n" + result.stderr
        return result.returncode, output.strip()
    except subprocess.TimeoutExpired:
        return -1, "[FAIL] 타임아웃 (60초 초과)"
    except Exception as e:
        return -1, f"[FAIL] 실행 오류: {e}"


# ════════════════════════════════════════════════════════════════════
# 핵심 동작
# ════════════════════════════════════════════════════════════════════

def do_validate() -> bool:
    """generate_glossary.py validate 실행."""
    _step(f"validate  →  {DICT_DIR}")
    code, out = _run_generate_py("validate")
    if out:
        print(out)
    return code == 0


def do_generate() -> bool:
    """generate_glossary.py generate 실행 → terms.json + GLOSSARY.md."""
    _step(f"generate  →  {GLOSSARY_MD}")
    code, out = _run_generate_py("generate")
    if out:
        print(out)
    if code == 0:
        _ok("generate 완료")
    else:
        _fail("generate 실패")
    return code == 0


def run_once(check_only: bool, force: bool) -> bool:
    """1회 실행 사이클. 반환값: 전체 성공 여부."""
    _header(f"BOM_TS glossary run  |  {datetime.now().strftime('%H:%M:%S')}")
    _info(f"dictionary : {DICT_DIR}")
    _info(f"GLOSSARY   : {GLOSSARY_MD}")

    # ── validate ──────────────────────────────────────────────────────
    valid = do_validate()

    if check_only:
        print()
        if valid:
            _ok("check 통과 — FATAL 없음")
        else:
            _fail("check 실패 — 위 오류를 수정하세요")
        _sep()
        return valid

    # ── generate ──────────────────────────────────────────────────────
    if not valid and not force:
        print()
        _fail("validate 실패 → generate 중단")
        _info("강행하려면:  python run.py --force")
        _sep()
        return False

    if not valid and force:
        print()
        _warn("validate 실패이지만 --force 옵션으로 generate를 진행합니다")

    generated = do_generate()

    print()
    if valid and generated:
        _ok("모두 완료")
    elif generated:
        _warn("generate 완료 (validate 오류 있음 — 내용을 확인하세요)")
    else:
        _fail("generate 실패")

    _sep()
    return valid and generated


# ════════════════════════════════════════════════════════════════════
# watch 모드 — dictionary/ 내 파일 변경 감지
# ════════════════════════════════════════════════════════════════════

def _mtimes() -> dict:
    """감시 파일들의 최종 수정 시각 dict 반환."""
    result = {}
    for p in WATCH_FILES:
        try:
            result[str(p)] = p.stat().st_mtime
        except FileNotFoundError:
            result[str(p)] = 0.0
    return result


def run_watch(check_only: bool, force: bool, interval: float = 1.0):
    """dictionary/ 파일 변경을 감지해 자동으로 run_once() 재실행."""
    print()
    _header("watch 모드 시작")
    for p in WATCH_FILES:
        _info(f"감시: {p.name}")
    _info("종료: Ctrl+C")
    _sep()

    last = _mtimes()
    run_once(check_only, force)

    try:
        while True:
            time.sleep(interval)
            current = _mtimes()
            changed = [k for k in current if current[k] != last[k]]
            if changed:
                last = current
                names = ", ".join(Path(k).name for k in changed)
                print(f"\n[변경 감지]  {names}")
                run_once(check_only, force)
    except KeyboardInterrupt:
        print("\n")
        _info("watch 모드 종료 (Ctrl+C)")
        print()


# ════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="BOM_TS glossary 빌드 러너 — validate + generate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python run.py              기본 실행 (validate → generate)
  python run.py --check      validate만 (오류 확인용)
  python run.py --force      validate 실패해도 generate 강행
  python run.py --watch      dictionary/ 변경 자동 감지 + 재실행
        """,
    )
    parser.add_argument("--check",    action="store_true", help="validate만 실행")
    parser.add_argument("--force",    action="store_true", help="validate 실패해도 generate 강행")
    parser.add_argument("--watch",    action="store_true", help="파일 변경 자동 감지")
    parser.add_argument("--interval", type=float, default=1.0, metavar="SEC",
                        help="watch 감지 주기(초), 기본 1.0")
    args = parser.parse_args()

    # generate_glossary.py 존재 확인
    if not GENERATE_PY.exists():
        _fail(f"generate_glossary.py 를 찾을 수 없습니다: {GENERATE_PY}")
        sys.exit(1)

    # dictionary/ 폴더 존재 확인
    if not DICT_DIR.exists():
        _fail(f"dictionary/ 폴더가 없습니다: {DICT_DIR}")
        _info("words.json, compounds.json, banned.json 을 dictionary/ 에 배치하세요.")
        sys.exit(1)

    if args.watch:
        run_watch(check_only=args.check, force=args.force, interval=args.interval)
    else:
        ok = run_once(check_only=args.check, force=args.force)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
