#!/usr/bin/env python3
"""
server.py  —  glossary 웹 UI 서버
위치: glossary/web/server.py

사용법:
    python web/server.py
    python web/server.py --port 8080

접속: http://localhost:9001
"""

import sys
import io
import json
import logging
import argparse
import subprocess
import traceback
from datetime import datetime, timezone
from pathlib import Path

# ── Windows cp949 인코딩 오류 방지 ────────────────────────────────────
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding.lower() not in ('utf-8','utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer') and sys.stderr.encoding.lower() not in ('utf-8','utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── 경로 설정 ──────────────────────────────────────────────────────────
WEB_DIR   = Path(__file__).parent.resolve()   # glossary/web/
REPO_ROOT = WEB_DIR.parent.resolve()          # glossary/
BIN_DIR   = REPO_ROOT / "bin"
LOG_DIR   = REPO_ROOT / "logs"
LOG_FILE  = LOG_DIR / "glossary.log"
RUN_PY    = BIN_DIR / "run.py"
TERMS_PATH    = REPO_ROOT / "terms.json"
GLOSSARY_PATH = REPO_ROOT / "GLOSSARY.md"
GITIGNORE     = REPO_ROOT / ".gitignore"

LOG_DIR.mkdir(exist_ok=True)

# ── .gitignore 에 logs/ 자동 추가 ─────────────────────────────────────
def ensure_gitignore():
    lines = GITIGNORE.read_text(encoding='utf-8').splitlines() if GITIGNORE.exists() else []
    changed = False
    for entry in ['logs/', '*.log']:
        if entry not in lines:
            lines.append(entry)
            changed = True
    if changed:
        GITIGNORE.write_text('\n'.join(lines) + '\n', encoding='utf-8')

ensure_gitignore()

# ── 로거 설정 ──────────────────────────────────────────────────────────
LOG_MAX_LINES = 500   # 초과 시 오래된 절반 삭제
LOG_MAX_DAYS  = 7

def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("glossary")
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-5s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    # 파일 핸들러 — UTF-8 강제
    fh = logging.FileHandler(str(LOG_FILE), encoding='utf-8')
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger

log = _setup_logger()


def _rotate_log():
    """로그 파일이 MAX_LINES 초과 시 오래된 절반 삭제."""
    if not LOG_FILE.exists():
        return
    try:
        lines = LOG_FILE.read_text(encoding='utf-8', errors='replace').splitlines()
        if len(lines) > LOG_MAX_LINES:
            keep = lines[len(lines) // 2:]          # 최신 절반만 유지
            LOG_FILE.write_text('\n'.join(keep) + '\n', encoding='utf-8')
            log.info(f"[rotate] 로그 정리: {len(lines)} → {len(keep)}줄")
    except Exception as e:
        pass  # 로그 정리 실패는 무시


def _purge_old_logs():
    """LOG_MAX_DAYS 보다 오래된 로그 항목 제거 (날짜 파싱 기반)."""
    if not LOG_FILE.exists():
        return
    try:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=LOG_MAX_DAYS)
        lines  = LOG_FILE.read_text(encoding='utf-8', errors='replace').splitlines()
        kept   = []
        for line in lines:
            try:
                ts = datetime.strptime(line[:19], '%Y-%m-%d %H:%M:%S')
                if ts >= cutoff:
                    kept.append(line)
            except Exception:
                kept.append(line)   # 날짜 파싱 불가 줄은 유지
        if len(kept) < len(lines):
            LOG_FILE.write_text('\n'.join(kept) + '\n', encoding='utf-8')
    except Exception:
        pass


# 서버 시작 시 1회 정리
_purge_old_logs()
_rotate_log()

try:
    from flask import Flask, jsonify, request, send_from_directory
except ImportError:
    print("Flask가 설치되어 있지 않습니다.  pip install flask")
    sys.exit(1)

app = Flask(__name__, static_folder=str(WEB_DIR))


# ══════════════════════════════════════════════════════════════════════
# 헬퍼
# ══════════════════════════════════════════════════════════════════════

def load_terms() -> dict:
    with open(TERMS_PATH, encoding='utf-8') as f:
        return json.load(f)

def save_terms(data: dict):
    with open(TERMS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_subprocess(*cmd, timeout=30, env_utf8=True) -> dict:
    """
    subprocess 실행 공통 함수.
    - env_utf8=True: PYTHONIOENCODING=utf-8 환경변수 주입 (Windows cp949 문제 해결)
    - cwd는 항상 REPO_ROOT
    """
    import os
    env = os.environ.copy()
    if env_utf8:
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8']       = '1'       # Python 3.7+ UTF-8 모드

    try:
        result = subprocess.run(
            list(cmd),
            cwd=str(REPO_ROOT),
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            env=env,
        )
        return {
            "ok":     result.returncode == 0,
            "stdout": result.stdout.strip() if result.stdout else "",
            "stderr": result.stderr.strip() if result.stderr else "",
            "code":   result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": f"타임아웃 ({timeout}초 초과)", "code": -1}
    except FileNotFoundError as e:
        return {"ok": False, "stdout": "", "stderr": f"명령어를 찾을 수 없습니다: {e}", "code": -1}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "code": -1}


def run_git(*args, timeout=20) -> dict:
    return run_subprocess("git", *args, timeout=timeout, env_utf8=False)


def run_runpy(*extra_args) -> dict:
    return run_subprocess(sys.executable, str(RUN_PY), *extra_args, timeout=30)


# ══════════════════════════════════════════════════════════════════════
# API — UI
# ══════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory(str(WEB_DIR), "index.html")


# ══════════════════════════════════════════════════════════════════════
# API — 용어 CRUD
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/terms", methods=["GET"])
def get_terms():
    return jsonify(load_terms())


@app.route("/api/terms/<term_id>", methods=["GET"])
def get_term(term_id):
    data = load_terms()
    term = next((t for t in data["terms"] if t["id"] == term_id), None)
    if not term:
        return jsonify({"error": f"용어를 찾을 수 없습니다: {term_id}"}), 404
    return jsonify(term)


@app.route("/api/terms", methods=["POST"])
def add_term():
    new_term = request.get_json()
    if not new_term:
        return jsonify({"error": "요청 본문이 없습니다"}), 400
    data = load_terms()
    if any(t["id"] == new_term.get("id") for t in data["terms"]):
        return jsonify({"error": f"이미 존재하는 id: {new_term.get('id')}"}), 409
    data["terms"].append(new_term)
    save_terms(data)
    log.info(f"[term:add] id={new_term.get('id')} ko={new_term.get('ko')}")
    return jsonify({"ok": True, "term": new_term}), 201


@app.route("/api/terms/<term_id>", methods=["PUT"])
def update_term(term_id):
    updated = request.get_json()
    if not updated:
        return jsonify({"error": "요청 본문이 없습니다"}), 400
    data = load_terms()
    idx = next((i for i, t in enumerate(data["terms"]) if t["id"] == term_id), None)
    if idx is None:
        return jsonify({"error": f"용어를 찾을 수 없습니다: {term_id}"}), 404
    data["terms"][idx] = updated
    save_terms(data)
    log.info(f"[term:update] id={term_id}")
    return jsonify({"ok": True, "term": updated})


@app.route("/api/terms/<term_id>", methods=["DELETE"])
def delete_term(term_id):
    data = load_terms()
    before = len(data["terms"])
    data["terms"] = [t for t in data["terms"] if t["id"] != term_id]
    if len(data["terms"]) == before:
        return jsonify({"error": f"용어를 찾을 수 없습니다: {term_id}"}), 404
    save_terms(data)
    log.info(f"[term:delete] id={term_id}")
    return jsonify({"ok": True, "deleted": term_id})


@app.route("/api/categories", methods=["GET"])
def get_categories():
    data = load_terms()
    return jsonify(data["meta"]["categories"])


# ══════════════════════════════════════════════════════════════════════
# API — run.py
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/run", methods=["POST"])
def api_run():
    body = request.get_json() or {}
    mode = body.get("mode", "default")

    extra = []
    if mode == "check": extra = ["--check"]
    elif mode == "force": extra = ["--force"]

    log.info(f"[run] mode={mode}")
    result = run_runpy(*extra)

    combined = result["stdout"]
    if result["stderr"]:
        combined += ("\n" if combined else "") + result["stderr"]
    if not combined:
        combined = f"(returncode={result['code']}, 출력 없음)"

    log.info(f"[run] mode={mode} ok={result['ok']} returncode={result['code']}")
    if not result["ok"]:
        log.warning(f"[run] stderr: {result['stderr'][:300]}")

    return jsonify({
        "ok":         result["ok"],
        "stdout":     combined,
        "stderr":     result["stderr"],
        "returncode": result["code"],
    })


# ══════════════════════════════════════════════════════════════════════
# API — Git
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/git/status", methods=["GET"])
def git_status():
    branch  = run_git("rev-parse", "--abbrev-ref", "HEAD")
    status  = run_git("status", "--porcelain")
    git_log = run_git("log", "--oneline", "-5")

    changed = []
    if status["ok"] and status["stdout"]:
        for line in status["stdout"].splitlines():
            flag = line[:2].strip()
            path = line[3:].strip()
            changed.append({"flag": flag, "path": path})

    return jsonify({
        "ok":          True,
        "branch":      branch["stdout"] if branch["ok"] else "unknown",
        "changed":     changed,
        "has_changes": len(changed) > 0,
    })


@app.route("/api/git/commit", methods=["POST"])
def git_commit_push():
    body    = request.get_json() or {}
    message = body.get("message", "").strip()

    if not message:
        return jsonify({"error": "커밋 메시지를 입력하세요"}), 400

    log.info(f"[commit] start  msg={message!r}")
    steps = []

    # ── Step 1: validate + generate ──────────────────────────────────
    r1 = run_runpy()
    combined1 = r1["stdout"]
    if r1["stderr"]:
        combined1 += "\n" + r1["stderr"]
    if not combined1:
        combined1 = f"(returncode={r1['code']}, 출력 없음)"

    step1 = {"step": "validate + generate", "ok": r1["ok"], "output": combined1}
    steps.append(step1)
    log.info(f"[commit] step1 ok={r1['ok']} code={r1['code']}")
    if not r1["ok"]:
        log.warning(f"[commit] step1 output: {combined1[:400]}")
        return jsonify({"ok": False, "steps": steps, "error": "validate 실패 — 커밋을 중단했습니다."})

    # ── Step 2: git add ───────────────────────────────────────────────
    add = run_git("add", "terms.json", "GLOSSARY.md")
    steps.append({"step": "git add", "ok": add["ok"], "output": add["stdout"] or add["stderr"]})
    log.info(f"[commit] step2 git add ok={add['ok']}")
    if not add["ok"]:
        log.warning(f"[commit] git add error: {add['stderr']}")
        return jsonify({"ok": False, "steps": steps, "error": "git add 실패"})

    # ── Step 3: git commit ────────────────────────────────────────────
    commit = run_git("commit", "-m", message)
    nothing = "nothing to commit" in (commit["stdout"] + commit["stderr"])
    steps.append({"step": "git commit", "ok": commit["ok"] or nothing,
                  "output": commit["stdout"] or commit["stderr"]})
    log.info(f"[commit] step3 git commit ok={commit['ok']} nothing={nothing}")
    if not commit["ok"] and not nothing:
        log.warning(f"[commit] git commit error: {commit['stderr']}")
        return jsonify({"ok": False, "steps": steps, "error": "git commit 실패"})

    # ── Step 4: git push (실패 시 pull --rebase 후 재시도) ───────────────
    REJECT_SIGNALS = ("rejected", "fetch first", "non-fast-forward", "tip of your current branch is behind")

    push = run_git("push", timeout=30)
    push_out = (push["stdout"] + push["stderr"]).lower()

    if not push["ok"] and any(sig in push_out for sig in REJECT_SIGNALS):
        # remote에 앞선 커밋이 있는 상황 → pull --rebase 후 재push
        log.info("[commit] push rejected — trying git pull --rebase")

        pull = run_git("pull", "--rebase", timeout=30)
        pull_output = pull["stdout"] or pull["stderr"]
        log.info(f"[commit] git pull --rebase ok={pull['ok']}")

        steps.append({
            "step":   "git pull --rebase",
            "ok":     pull["ok"],
            "output": pull_output,
        })

        if not pull["ok"]:
            log.warning(f"[commit] git pull --rebase error: {pull['stderr']}")
            return jsonify({
                "ok": False, "steps": steps,
                "error": "git pull --rebase 실패 — 충돌이 있을 수 있습니다. 수동으로 해결하세요.",
            })

        # rebase 성공 → 재push
        push = run_git("push", timeout=30)
        log.info(f"[commit] retry push ok={push['ok']}")
        steps.append({
            "step":   "git push (재시도)",
            "ok":     push["ok"],
            "output": push["stdout"] or push["stderr"],
        })
    else:
        steps.append({
            "step":   "git push",
            "ok":     push["ok"],
            "output": push["stdout"] or push["stderr"],
        })

    log.info(f"[commit] step4 git push ok={push['ok']}")
    if not push["ok"]:
        log.warning(f"[commit] git push error: {push['stderr']}")
        return jsonify({"ok": False, "steps": steps, "error": "git push 실패 — 인증 또는 네트워크 확인"})

    log.info(f"[commit] done  msg={message!r}")
    return jsonify({"ok": True, "steps": steps, "message": message})


@app.route("/api/git/log", methods=["GET"])
def git_log_api():
    limit = request.args.get("limit", 10, type=int)
    r = run_git("log", "--pretty=format:%h|%s|%an|%ar", f"-{limit}")
    entries = []
    if r["ok"] and r["stdout"]:
        for line in r["stdout"].splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                entries.append({"hash": parts[0], "subject": parts[1],
                                 "author": parts[2], "when": parts[3]})
    return jsonify({"ok": True, "entries": entries})


# ══════════════════════════════════════════════════════════════════════
# API — 로그 뷰어
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/logs", methods=["GET"])
def get_logs():
    """최근 N줄 반환. ?lines=200"""
    n = request.args.get("lines", 200, type=int)
    if not LOG_FILE.exists():
        return jsonify({"ok": True, "lines": [], "total": 0})
    try:
        all_lines = LOG_FILE.read_text(encoding='utf-8', errors='replace').splitlines()
        recent    = all_lines[-n:] if len(all_lines) > n else all_lines
        return jsonify({"ok": True, "lines": recent, "total": len(all_lines)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "lines": [], "total": 0})


@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    try:
        LOG_FILE.write_text("", encoding='utf-8')
        log.info("[logs] 수동 초기화")
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ══════════════════════════════════════════════════════════════════════
# 진입점
# ══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="glossary 웹 UI 서버")
    parser.add_argument("--port", type=int, default=9001)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    log.info(f"[server] 시작  port={args.port}  repo={REPO_ROOT}")
    print(f"\n  glossary UI 서버 시작")
    print(f"  저장소 루트  : {REPO_ROOT}")
    print(f"  로그 파일    : {LOG_FILE}")
    print(f"  접속 주소    : http://{args.host}:{args.port}")
    print(f"  종료         : Ctrl+C\n")

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
