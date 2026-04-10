#!/usr/bin/env python3
"""
validate.py v2  —  BOM_TS glossary 검증 래퍼 (CI용)
위치: glossary/bin/validate.py

역할:
  generate_glossary.py validate 명령에 위임한다.
  CI 파이프라인 또는 run.py 에서 직접 호출 가능.

사용법:
    python validate.py              # 검증 실행 (FATAL 있으면 exit 1)
    python validate.py --silent     # 출력 없이 종료 코드만 반환

검증 규칙 (generate_glossary.py 참조):
  [FATAL]
  V-001: words.json id 고유
  V-002: compounds.json id 고유
  V-003: words ↔ compounds id 충돌 없음
  V-004: compounds.words[] 참조가 words.json에 존재
  V-005: compounds.reason 비어있지 않음
  V-006: abbr 중복 없음

  [WARN]
  V-101: 고아 단어 (compound 미참조)
  V-102: banned.correct 가 words/compounds에 존재
  V-103: not[] 값이 다른 id와 충돌
"""

import sys
import io
import os
import subprocess
import argparse
from pathlib import Path

# ── Windows cp949 인코딩 오류 방지 ────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BIN_DIR     = Path(__file__).parent.resolve()
REPO_ROOT   = BIN_DIR.parent.resolve()
GENERATE_PY = REPO_ROOT / "generate_glossary.py"


def validate(silent: bool = False) -> bool:
    """
    generate_glossary.py validate 실행.
    반환: True(FATAL 없음) / False(FATAL 있음)
    """
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8']       = '1'

    try:
        result = subprocess.run(
            [sys.executable, str(GENERATE_PY), "validate"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=30,
            env=env,
        )
        if not silent:
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(result.stderr, end='', file=sys.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        if not silent:
            print("[FAIL] validate 타임아웃 (30초 초과)")
        return False
    except Exception as e:
        if not silent:
            print(f"[FAIL] validate 실행 오류: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="BOM_TS glossary 검증 (generate_glossary.py validate 래퍼)"
    )
    parser.add_argument("--silent", action="store_true",
                        help="출력 없이 종료 코드만 반환")
    args = parser.parse_args()

    ok = validate(silent=args.silent)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
