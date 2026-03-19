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
import json
import argparse
import subprocess
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────────────────────────────
WEB_DIR   = Path(__file__).parent.resolve()   # glossary/web/
REPO_ROOT = WEB_DIR.parent.resolve()          # glossary/
BIN_DIR   = REPO_ROOT / "bin"

TERMS_PATH    = REPO_ROOT / "terms.json"
GLOSSARY_PATH = REPO_ROOT / "GLOSSARY.md"
RUN_PY        = BIN_DIR / "run.py"

sys.path.insert(0, str(BIN_DIR))

try:
    from flask import Flask, jsonify, request, send_from_directory
except ImportError:
    print("Flask가 설치되어 있지 않습니다.")
    print("설치: pip install flask")
    sys.exit(1)

app = Flask(__name__, static_folder=str(WEB_DIR))


# ══════════════════════════════════════════════════════════════════════
# 헬퍼
# ══════════════════════════════════════════════════════════════════════

def load_terms() -> dict:
    with open(TERMS_PATH, encoding="utf-8") as f:
        return json.load(f)

def save_terms(data: dict):
    with open(TERMS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run_git(*args, timeout=15) -> dict:
    """git 명령 실행. cwd는 항상 REPO_ROOT."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "ok":     result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "code":   result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": f"타임아웃 ({timeout}초 초과)", "code": -1}
    except FileNotFoundError:
        return {"ok": False, "stdout": "", "stderr": "git이 설치되어 있지 않습니다.", "code": -1}


# ══════════════════════════════════════════════════════════════════════
# API — UI 서빙
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
        return jsonify({"error": f"이미 존재하는 id입니다: {new_term.get('id')}"}), 409
    data["terms"].append(new_term)
    save_terms(data)
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
    return jsonify({"ok": True, "term": updated})


@app.route("/api/terms/<term_id>", methods=["DELETE"])
def delete_term(term_id):
    data = load_terms()
    before = len(data["terms"])
    data["terms"] = [t for t in data["terms"] if t["id"] != term_id]
    if len(data["terms"]) == before:
        return jsonify({"error": f"용어를 찾을 수 없습니다: {term_id}"}), 404
    save_terms(data)
    return jsonify({"ok": True, "deleted": term_id})


@app.route("/api/categories", methods=["GET"])
def get_categories():
    data = load_terms()
    return jsonify(data["meta"]["categories"])


# ══════════════════════════════════════════════════════════════════════
# API — run.py
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/run", methods=["POST"])
def run_command():
    body = request.get_json() or {}
    mode = body.get("mode", "default")

    cmd = [sys.executable, str(RUN_PY)]
    if mode == "check":
        cmd.append("--check")
    elif mode == "force":
        cmd.append("--force")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return jsonify({
            "ok":         result.returncode == 0,
            "stdout":     result.stdout,
            "stderr":     result.stderr,
            "returncode": result.returncode,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "stdout": "", "stderr": "타임아웃 (30초 초과)"}), 500
    except Exception as e:
        return jsonify({"ok": False, "stdout": "", "stderr": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════
# API — Git
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/git/status", methods=["GET"])
def git_status():
    """변경된 파일 목록 + 현재 브랜치 반환."""
    branch = run_git("rev-parse", "--abbrev-ref", "HEAD")
    status = run_git("status", "--porcelain")
    log    = run_git("log", "--oneline", "-5")

    changed_files = []
    if status["ok"] and status["stdout"]:
        for line in status["stdout"].splitlines():
            flag = line[:2].strip()
            path = line[3:].strip()
            changed_files.append({"flag": flag, "path": path})

    return jsonify({
        "ok":           True,
        "branch":       branch["stdout"] if branch["ok"] else "unknown",
        "changed":      changed_files,
        "has_changes":  len(changed_files) > 0,
        "recent_log":   log["stdout"] if log["ok"] else "",
    })


@app.route("/api/git/commit", methods=["POST"])
def git_commit_push():
    """
    1. run.py (validate + generate) 실행
    2. git add terms.json GLOSSARY.md
    3. git commit -m <message>
    4. git push
    """
    body    = request.get_json() or {}
    message = body.get("message", "").strip()

    if not message:
        return jsonify({"error": "커밋 메시지를 입력하세요"}), 400

    steps = []

    # ── Step 1: validate + generate ──────────────────────────────────
    try:
        run_result = subprocess.run(
            [sys.executable, str(RUN_PY)],
            capture_output=True, text=True, timeout=30,
        )
        step1 = {
            "step":   "validate + generate",
            "ok":     run_result.returncode == 0,
            "output": run_result.stdout + run_result.stderr,
        }
    except Exception as e:
        step1 = {"step": "validate + generate", "ok": False, "output": str(e)}
    steps.append(step1)

    if not step1["ok"]:
        return jsonify({"ok": False, "steps": steps,
                        "error": "validate 실패 — 커밋을 중단했습니다."})

    # ── Step 2: git add ───────────────────────────────────────────────
    add = run_git("add", "terms.json", "GLOSSARY.md")
    steps.append({"step": "git add", "ok": add["ok"], "output": add["stdout"] or add["stderr"]})
    if not add["ok"]:
        return jsonify({"ok": False, "steps": steps, "error": "git add 실패"})

    # ── Step 3: git commit ────────────────────────────────────────────
    commit = run_git("commit", "-m", message)
    steps.append({"step": "git commit", "ok": commit["ok"], "output": commit["stdout"] or commit["stderr"]})

    # "nothing to commit"은 오류가 아님
    nothing_to_commit = "nothing to commit" in commit["stdout"] + commit["stderr"]
    if not commit["ok"] and not nothing_to_commit:
        return jsonify({"ok": False, "steps": steps, "error": "git commit 실패"})

    # ── Step 4: git push ──────────────────────────────────────────────
    push = run_git("push", timeout=30)
    steps.append({"step": "git push", "ok": push["ok"], "output": push["stdout"] or push["stderr"]})
    if not push["ok"]:
        return jsonify({"ok": False, "steps": steps, "error": "git push 실패 — 인증 또는 네트워크 확인"})

    return jsonify({"ok": True, "steps": steps, "message": message})


@app.route("/api/git/log", methods=["GET"])
def git_log():
    """최근 커밋 이력 반환."""
    limit = request.args.get("limit", 10, type=int)
    log = run_git("log", f"--pretty=format:%h|%s|%an|%ar", f"-{limit}")
    entries = []
    if log["ok"] and log["stdout"]:
        for line in log["stdout"].splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                entries.append({
                    "hash":    parts[0],
                    "subject": parts[1],
                    "author":  parts[2],
                    "when":    parts[3],
                })
    return jsonify({"ok": True, "entries": entries})


# ══════════════════════════════════════════════════════════════════════
# 진입점
# ══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="glossary 웹 UI 서버")
    parser.add_argument("--port", type=int, default=9001)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    print(f"\n  glossary UI 서버 시작")
    print(f"  저장소 루트  : {REPO_ROOT}")
    print(f"  terms.json   : {TERMS_PATH}")
    print(f"  접속 주소    : http://{args.host}:{args.port}")
    print(f"  종료         : Ctrl+C\n")

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
