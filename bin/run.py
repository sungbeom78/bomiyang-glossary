#!/usr/bin/env python3
"""
run.py  —  glossary 빌드 러너
위치: glossary/bin/run.py

사용법:
    python run.py              # validate → generate (기본)
    python run.py --check      # validate만 (오류 확인)
    python run.py --force      # validate 실패해도 generate 강행
    python run.py --watch      # terms.json 변경 감지 시 자동 재실행
    python run.py --watch --check   # watch 모드에서 validate만

경로 기본값:
    terms.json  →  ../terms.json   (glossary 루트)
    GLOSSARY.md →  ../GLOSSARY.md  (glossary 루트)
"""

import sys
import os
import time
import argparse
import io
from pathlib import Path

# ── Windows cp949 인코딩 오류 방지 — stdout을 UTF-8로 강제 ──────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── bin/ 기준으로 glossary 루트 경로 계산 ──────────────────────────────
BIN_DIR    = Path(__file__).parent.resolve()   # glossary/bin/
REPO_ROOT  = BIN_DIR.parent.resolve()          # glossary/

DEFAULT_TERMS    = REPO_ROOT / "terms.json"
DEFAULT_GLOSSARY = REPO_ROOT / "GLOSSARY.md"

# ── 같은 bin/ 안의 모듈을 import할 수 있도록 경로 추가 ───────────────────
sys.path.insert(0, str(BIN_DIR))

from validate          import validate
from generate_glossary import load_terms, generate_md


# ══════════════════════════════════════════════════════════════════════
# 출력 헬퍼
# ══════════════════════════════════════════════════════════════════════

def _sep(char="-", width=52):
    print(char * width)

def _header(text: str):
    _sep("=")
    print(f"  {text}")
    _sep("=")

def _step(icon: str, text: str):
    # icon 인자는 무시하고 ASCII로만 출력 (Windows 인코딩 안전)
    print(f"\n>>  {text}")

def _ok(text: str):
    print(f"  [OK]   {text}")

def _fail(text: str):
    print(f"  [FAIL] {text}")

def _info(text: str):
    print(f"  [..]   {text}")

def _warn(text: str):
    print(f"  [WARN] {text}")


# ══════════════════════════════════════════════════════════════════════
# 핵심 동작
# ══════════════════════════════════════════════════════════════════════

def do_validate(terms_path: Path) -> bool:
    """validate.py의 validate() 를 호출하고 결과를 반환."""
    _step("🔍", f"validate  →  {terms_path}")
    ok = validate(str(terms_path))
    return ok


def do_generate(terms_path: Path, glossary_path: Path) -> bool:
    """generate_glossary.py의 로직을 호출해 GLOSSARY.md를 생성."""
    _step("📝", f"generate  →  {glossary_path}")
    try:
        data = load_terms(str(terms_path))
        md   = generate_md(data)
        glossary_path.parent.mkdir(parents=True, exist_ok=True)
        glossary_path.write_text(md, encoding="utf-8")
        _ok(f"GLOSSARY.md 생성 완료  ({len(data['terms'])}개 용어)")
        return True
    except Exception as e:
        _fail(f"generate 실패: {e}")
        return False


def run_once(terms_path: Path, glossary_path: Path,
             check_only: bool, force: bool) -> bool:
    """
    1회 실행 사이클.
    반환값: 전체 성공 여부 (bool)
    """
    from datetime import datetime
    _header(f"glossary run  |  {datetime.now().strftime('%H:%M:%S')}")
    _info(f"terms    : {terms_path}")
    _info(f"glossary : {glossary_path}")

    # ── validate ──────────────────────────────────────────────────────
    valid = do_validate(terms_path)

    if check_only:
        # --check: validate만 하고 종료
        print()
        if valid:
            _ok("check 통과 — 오류 없음")
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

    generated = do_generate(terms_path, glossary_path)

    print()
    if valid and generated:
        _ok("모두 완료")
    elif generated:
        _warn("generate 완료 (validate 오류 있음 — 내용을 확인하세요)")
    else:
        _fail("generate 실패")

    _sep()
    return valid and generated


# ══════════════════════════════════════════════════════════════════════
# watch 모드
# ══════════════════════════════════════════════════════════════════════

def _mtime(path: Path) -> float:
    """파일의 최종 수정 시각 반환. 없으면 0."""
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def run_watch(terms_path: Path, glossary_path: Path,
              check_only: bool, force: bool,
              interval: float = 1.0):
    """
    terms.json 변경을 감지해 자동으로 run_once() 를 재실행.
    Ctrl+C 로 종료.
    """
    print()
    _header("watch 모드 시작")
    _info(f"감시 파일 : {terms_path}")
    _info(f"종료      : Ctrl+C")
    _sep()

    last_mtime = 0.0

    # 시작 시 1회 즉시 실행
    last_mtime = _mtime(terms_path)
    run_once(terms_path, glossary_path, check_only, force)

    try:
        while True:
            time.sleep(interval)
            current_mtime = _mtime(terms_path)

            if current_mtime != last_mtime:
                last_mtime = current_mtime
                print(f"\n[변경 감지]  terms.json")
                run_once(terms_path, glossary_path, check_only, force)

    except KeyboardInterrupt:
        print("\n")
        _info("watch 모드 종료 (Ctrl+C)")
        print()


# ══════════════════════════════════════════════════════════════════════
# CLI 진입점
# ══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="glossary 빌드 러너 — validate + generate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python run.py                          기본 실행 (validate → generate)
  python run.py --check                  validate만 (오류 확인용)
  python run.py --force                  validate 실패해도 generate 강행
  python run.py --watch                  파일 변경 자동 감지 + 재실행
  python run.py --watch --check          watch 모드에서 validate만
  python run.py --terms ../terms.json    terms.json 경로 직접 지정
        """,
    )
    parser.add_argument(
        "--terms",
        type=Path,
        default=DEFAULT_TERMS,
        metavar="PATH",
        help=f"terms.json 경로 (기본: {DEFAULT_TERMS})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_GLOSSARY,
        metavar="PATH",
        help=f"GLOSSARY.md 출력 경로 (기본: {DEFAULT_GLOSSARY})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate만 실행 (generate 하지 않음)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="validate 실패해도 generate 강행",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="terms.json 변경 감지 시 자동 재실행",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SEC",
        help="watch 감지 주기(초), 기본 1.0",
    )

    args = parser.parse_args()

    # terms.json 존재 확인
    if not args.terms.exists():
        _fail(f"terms.json 을 찾을 수 없습니다: {args.terms}")
        _info("--terms 옵션으로 경로를 직접 지정하세요")
        sys.exit(1)

    if args.watch:
        run_watch(
            terms_path    = args.terms,
            glossary_path = args.output,
            check_only    = args.check,
            force         = args.force,
            interval      = args.interval,
        )
    else:
        ok = run_once(
            terms_path    = args.terms,
            glossary_path = args.output,
            check_only    = args.check,
            force         = args.force,
        )
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
