#!/usr/bin/env python3
"""
server.py  —  glossary 웹 UI 서버
위치: glossary/web/server.py

사용법:
    python web/server.py
    python web/server.py --port 8080

접속: http://localhost:5000
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
LOG_DIR   = REPO_ROOT / "log"
LOG_FILE  = LOG_DIR / "glossary.log"
RUN_PY    = BIN_DIR / "run.py"
GENERATE_PY   = REPO_ROOT / "generate_glossary.py"
DICT_DIR      = REPO_ROOT / "dictionary"
TERMS_PATH    = DICT_DIR / "terms.json"
WORDS_PATH    = DICT_DIR / "words.json"
COMPOUNDS_PATH = DICT_DIR / "compounds.json"
BANNED_PATH   = DICT_DIR / "banned.json"
GLOSSARY_PATH = REPO_ROOT / "GLOSSARY.md"
GITIGNORE     = REPO_ROOT / ".gitignore"

LOG_DIR.mkdir(exist_ok=True)

# ── .gitignore 에 logs/ 자동 추가 ─────────────────────────────────────
def ensure_gitignore():
    lines = GITIGNORE.read_text(encoding='utf-8').splitlines() if GITIGNORE.exists() else []
    changed = False
    for entry in ['log/', '*.log']:
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

# ── v2: words / compounds / banned ────────────────────────────────────
def _load_json(path: Path, key: str) -> dict:
    if not path.exists():
        return {key: []}
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def _save_json(path: Path, data: dict):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_words()     -> dict: return _load_json(WORDS_PATH,     "words")
def load_compounds() -> dict: return _load_json(COMPOUNDS_PATH, "compounds")
def load_banned()    -> dict: return _load_json(BANNED_PATH,    "banned")

def save_words(d):     _save_json(WORDS_PATH,     d)
def save_compounds(d): _save_json(COMPOUNDS_PATH, d)
def save_banned(d):    _save_json(BANNED_PATH,    d)

def _run_generate():
    """generate_glossary.py generate 실행 → terms.json + GLOSSARY.md 재생성."""
    if GENERATE_PY.exists():
        return run_subprocess(sys.executable, str(GENERATE_PY), "generate", timeout=30)
    # fallback: bin/run.py
    return run_subprocess(sys.executable, str(RUN_PY), timeout=30)


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
    return jsonify(data.get("meta", {}).get("categories", {}))


# ══════════════════════════════════════════════════════════════════════
# API v2 — words
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/words", methods=["GET"])
def get_words():
    return jsonify(load_words())

@app.route("/api/words", methods=["POST"])
def add_word():
    w = request.get_json()
    if not w: return jsonify({"error": "요청 본문 없음"}), 400
    data = load_words()
    if any(x["id"] == w.get("id") for x in data["words"]):
        return jsonify({"error": f"이미 존재하는 id: {w.get('id')}"}), 409
    data["words"].append(w)
    data["words"].sort(key=lambda x: x["id"])
    save_words(data)
    log.info(f"[word:add] id={w.get('id')}")
    return jsonify({"ok": True, "word": w}), 201

@app.route("/api/words/<word_id>", methods=["PUT"])
def update_word(word_id):
    updated = request.get_json()
    if not updated: return jsonify({"error": "요청 본문 없음"}), 400
    data = load_words()
    idx = next((i for i,x in enumerate(data["words"]) if x["id"] == word_id), None)
    if idx is None: return jsonify({"error": f"미존재: {word_id}"}), 404
    data["words"][idx] = updated
    save_words(data)
    log.info(f"[word:update] id={word_id}")
    return jsonify({"ok": True, "word": updated})

@app.route("/api/words/<word_id>", methods=["DELETE"])
def delete_word(word_id):
    data = load_words()
    before = len(data["words"])
    data["words"] = [x for x in data["words"] if x["id"] != word_id]
    if len(data["words"]) == before:
        return jsonify({"error": f"미존재: {word_id}"}), 404
    save_words(data)
    log.info(f"[word:delete] id={word_id}")
    return jsonify({"ok": True})


# ══════════════════════════════════════════════════════════════════════
# API v2 — compounds
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/compounds", methods=["GET"])
def get_compounds():
    return jsonify(load_compounds())

@app.route("/api/compounds", methods=["POST"])
def add_compound():
    c = request.get_json()
    if not c: return jsonify({"error": "요청 본문 없음"}), 400
    data = load_compounds()
    if any(x["id"] == c.get("id") for x in data["compounds"]):
        return jsonify({"error": f"이미 존재하는 id: {c.get('id')}"}), 409
    data["compounds"].append(c)
    data["compounds"].sort(key=lambda x: x["id"])
    save_compounds(data)
    log.info(f"[compound:add] id={c.get('id')}")
    return jsonify({"ok": True, "compound": c}), 201

@app.route("/api/compounds/<cid>", methods=["PUT"])
def update_compound(cid):
    updated = request.get_json()
    if not updated: return jsonify({"error": "요청 본문 없음"}), 400
    data = load_compounds()
    idx = next((i for i,x in enumerate(data["compounds"]) if x["id"] == cid), None)
    if idx is None: return jsonify({"error": f"미존재: {cid}"}), 404
    data["compounds"][idx] = updated
    save_compounds(data)
    log.info(f"[compound:update] id={cid}")
    return jsonify({"ok": True, "compound": updated})

@app.route("/api/compounds/<cid>", methods=["DELETE"])
def delete_compound(cid):
    data = load_compounds()
    before = len(data["compounds"])
    data["compounds"] = [x for x in data["compounds"] if x["id"] != cid]
    if len(data["compounds"]) == before:
        return jsonify({"error": f"미존재: {cid}"}), 404
    save_compounds(data)
    log.info(f"[compound:delete] id={cid}")
    return jsonify({"ok": True})


# ══════════════════════════════════════════════════════════════════════
# API v2 — banned
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/banned", methods=["GET"])
def get_banned():
    return jsonify(load_banned())

@app.route("/api/banned", methods=["POST"])
def add_banned():
    b = request.get_json()
    if not b: return jsonify({"error": "요청 본문 없음"}), 400
    data = load_banned()
    if any(x["expression"] == b.get("expression") for x in data["banned"]):
        return jsonify({"error": f"이미 존재: {b.get('expression')}"}), 409
    data["banned"].append(b)
    save_banned(data)
    log.info(f"[banned:add] expr={b.get('expression')}")
    return jsonify({"ok": True, "banned": b}), 201

@app.route("/api/banned/<expr>", methods=["PUT"])
def update_banned(expr):
    updated = request.get_json()
    if not updated: return jsonify({"error": "요청 본문 없음"}), 400
    data = load_banned()
    idx = next((i for i,x in enumerate(data["banned"]) if x["expression"] == expr), None)
    if idx is None: return jsonify({"error": f"미존재: {expr}"}), 404
    data["banned"][idx] = updated
    save_banned(data)
    return jsonify({"ok": True})

@app.route("/api/banned/<expr>", methods=["DELETE"])
def delete_banned(expr):
    data = load_banned()
    before = len(data["banned"])
    data["banned"] = [x for x in data["banned"] if x["expression"] != expr]
    if len(data["banned"]) == before:
        return jsonify({"error": f"미존재: {expr}"}), 404
    save_banned(data)
    log.info(f"[banned:delete] expr={expr}")
    return jsonify({"ok": True})


# ══════════════════════════════════════════════════════════════════════
# API v2 — generate (words+compounds → terms.json + GLOSSARY.md)
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/generate", methods=["POST"])
def api_generate():
    """generate_glossary.py generate 실행."""
    log.info("[generate] 시작")
    result = _run_generate()
    combined = result["stdout"]
    if result["stderr"]: combined += "\n" + result["stderr"]
    log.info(f"[generate] 완료 ok={result['ok']}")
    return jsonify({"ok": result["ok"], "output": combined or f"(returncode={result['code']})"})

@app.route("/api/validate", methods=["POST"])
def api_validate():
    """generate_glossary.py validate 실행."""
    result = run_subprocess(sys.executable, str(GENERATE_PY), "validate", timeout=30)
    combined = result["stdout"]
    if result["stderr"]: combined += "\n" + result["stderr"]
    return jsonify({"ok": result["ok"], "output": combined})

@app.route("/api/check-id", methods=["POST"])
def api_check_id():
    """식별자 단어 분해 확인."""
    body = request.get_json() or {}
    identifier = body.get("id", "").strip()
    if not identifier: return jsonify({"error": "id 파라미터 필요"}), 400
    result = run_subprocess(sys.executable, str(GENERATE_PY), "check-id", identifier, timeout=15)
    combined = result["stdout"] + (result["stderr"] or "")
    return jsonify({"ok": result["ok"], "output": combined})

@app.route("/api/suggest", methods=["POST"])
def api_suggest():
    """미등록 단어 제안."""
    body = request.get_json() or {}
    identifier = body.get("id", "").strip()
    if not identifier: return jsonify({"error": "id 파라미터 필요"}), 400
    result = run_subprocess(sys.executable, str(GENERATE_PY), "suggest", identifier, timeout=15)
    combined = result["stdout"] + (result["stderr"] or "")
    return jsonify({"ok": result["ok"], "output": combined})


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
    add = run_git("add", "dictionary/words.json", "dictionary/compounds.json",
                  "dictionary/banned.json", "dictionary/terms.json", "GLOSSARY.md")
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
# API — 배치 (scan / batch / merge / list)
# ══════════════════════════════════════════════════════════════════════

def _proj_root() -> Path:
    """프로젝트 루트 반환 (PROJ_ROOT 환경변수 우선, 없으면 REPO_ROOT 상위)."""
    import os
    pr = os.environ.get("PROJ_ROOT","").strip()
    if pr and Path(pr).exists():
        return Path(pr).resolve()
    # .env 파일에서 읽기
    env_path = REPO_ROOT.parent / ".env"
    if not env_path.exists():
        env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8', errors='replace').splitlines():
            if line.strip().startswith('PROJ_ROOT='):
                val = line.split('=',1)[1].strip().strip('"').strip("'")
                if val and Path(val).exists():
                    return Path(val).resolve()
    return REPO_ROOT.parent.resolve()


@app.route("/api/batch/scan", methods=["POST"])
def batch_scan():
    """소스 스캔 → 후보 수 + 미리보기 반환 (API 미호출)."""
    log.info("[batch] scan 시작")
    result = run_subprocess(
        sys.executable, str(BIN_DIR / "scan_terms.py"), "--json",
        timeout=60,
    )
    if not result["ok"] and not result["stdout"]:
        log.warning(f"[batch] scan 실패: {result['stderr']}")
        return jsonify({"ok": False, "error": result["stderr"] or "scan 실패"})

    try:
        data = json.loads(result["stdout"])
        log.info(f"[batch] scan 완료: {data.get('count',0)}개 후보")
        return jsonify({"ok": True, **data})
    except Exception as e:
        return jsonify({"ok": False, "error": f"scan 출력 파싱 실패: {e}\n{result['stdout'][:300]}"})


@app.route("/api/batch/run", methods=["POST"])
def batch_run():
    """scan + API 분석 → terms_날짜.json 생성 (dry_run 옵션 지원)."""
    body     = request.get_json() or {}
    dry_run  = body.get("dry_run", False)
    chunk    = body.get("chunk", None)
    api_type = body.get("api_type", "").strip()   # UI에서 선택한 API 종류
    model    = body.get("model",    "").strip()   # UI에서 선택한 모델

    cmd_args = [sys.executable, str(BIN_DIR / "batch_terms.py")]
    if dry_run:
        cmd_args.append("--dry-run")
    if chunk:
        cmd_args += ["--chunk", str(chunk)]

    # UI 선택값을 환경변수로 주입 (비어있으면 .env 값 그대로 사용)
    import os
    extra_env = os.environ.copy()
    extra_env['PYTHONIOENCODING'] = 'utf-8'
    extra_env['PYTHONUTF8']       = '1'
    if api_type:
        extra_env['API_KEY_TYPE'] = api_type
        log.info(f"[batch] API_KEY_TYPE 오버라이드: {api_type}")
    if model:
        extra_env['API_MODEL'] = model
        log.info(f"[batch] API_MODEL 오버라이드: {model}")

    log.info(f"[batch] run 시작 dry_run={dry_run} api={api_type or '(.env)'} model={model or '(.env)'}")

    import subprocess as _sp
    try:
        proc = _sp.run(
            cmd_args,
            cwd=str(REPO_ROOT),
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=300,
            env=extra_env,
        )
        combined = proc.stdout or ""
        if proc.stderr:
            combined += "\n" + proc.stderr
        ok = proc.returncode == 0
    except _sp.TimeoutExpired:
        combined = "타임아웃 (300초 초과)"
        ok = False
    except Exception as e:
        combined = str(e)
        ok = False

    log.info(f"[batch] run 완료 ok={ok}")
    return jsonify({
        "ok":     ok,
        "output": combined.strip() or f"(출력 없음)",
    })


@app.route("/api/batch/files", methods=["GET"])
def batch_files():
    """tmp/terms/ 하위 결과 파일 목록 반환."""
    out_dir = _proj_root() / "tmp" / "terms"
    if not out_dir.exists():
        return jsonify({"ok": True, "files": []})

    files = []
    for f in sorted(out_dir.glob("terms_*.json"), reverse=True):
        try:
            data  = json.loads(f.read_text(encoding='utf-8'))
            count = data.get("meta", {}).get("count", len(data.get("terms", [])))
            files.append({
                "name":    f.name,
                "path":    str(f),
                "count":   count,
                "generated_at": data.get("meta", {}).get("generated_at", ""),
            })
        except Exception:
            files.append({"name": f.name, "path": str(f), "count": 0, "generated_at": ""})

    return jsonify({"ok": True, "files": files})


@app.route("/api/batch/preview", methods=["GET"])
def batch_preview():
    """결과 파일 내용 미리보기."""
    fname = request.args.get("file", "")
    if not fname:
        return jsonify({"error": "file 파라미터 필요"}), 400

    out_dir = _proj_root() / "tmp" / "terms"
    fpath   = (out_dir / fname).resolve()

    # 경로 이탈 방지
    if not str(fpath).startswith(str(out_dir.resolve())):
        return jsonify({"error": "잘못된 경로"}), 400
    if not fpath.exists():
        return jsonify({"error": "파일 없음"}), 404

    try:
        data = json.loads(fpath.read_text(encoding='utf-8'))
        return jsonify({"ok": True, **data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/batch/merge", methods=["POST"])
def batch_merge():
    """
    결과 파일의 용어를 dictionary/words.json 에 병합 (중복 id 제외).

    batch_terms.py 결과는 terms.json 포맷이므로,
    단순어(토큰 1개)는 words.json으로, 복합어는 compounds.json으로 분류 후 병합.
    분류 불가 항목은 words.json에 병합 (사용자가 이후 수동 검토).
    """
    import re

    body  = request.get_json() or {}
    fname = body.get("file", "")
    ids   = body.get("ids", None)   # None = 전체, list = 선택

    if not fname:
        return jsonify({"error": "file 파라미터 필요"}), 400

    out_dir = _proj_root() / "tmp" / "terms"
    fpath   = (out_dir / fname).resolve()
    if not str(fpath).startswith(str(out_dir.resolve())):
        return jsonify({"error": "잘못된 경로"}), 400
    if not fpath.exists():
        return jsonify({"error": "파일 없음"}), 404

    def _tokenize(name: str) -> list:
        s = str(name).replace('-', '_')
        s = re.sub(r'([a-z])([A-Z])', r'\1_\2', s)
        return [t.lower() for t in s.split('_') if len(t) >= 2]

    try:
        src_data = json.loads(fpath.read_text(encoding='utf-8'))
        candidates = src_data.get("terms", [])

        # ids 필터
        if ids is not None:
            candidates = [t for t in candidates if t.get("id") in ids]

        # words.json / compounds.json 기존 id 수집
        wd = load_words()
        cd = load_compounds()
        existing_word_ids = {w["id"] for w in wd["words"]}
        existing_comp_ids = {c["id"] for c in cd["compounds"]}
        existing_all      = existing_word_ids | existing_comp_ids

        words_to_add = []
        skipped      = 0

        for t in candidates:
            tid = t.get("id", "").strip()
            if not tid or tid in existing_all:
                skipped += 1
                continue

            tokens = _tokenize(tid)
            cats   = t.get("categories", ["system"])

            # domain 변환
            CAT_MAP = {
                'order':'trading','risk':'trading','trading':'trading',
                'domain':'trading','account':'trading',
                'market':'market','data':'market','selector':'market',
                'system':'system','status':'system','session':'system',
                'module':'system','config':'system','class':'system',
                'infra':'infra','tool':'infra','report':'ui',
            }
            domain = next((CAT_MAP.get(c) for c in cats if c in CAT_MAP), "general")
            abbr   = t.get("abbr_short", "")
            abbr_v = abbr if (abbr and 2 <= len(abbr) <= 5 and abbr.isupper()
                              and '_' not in abbr) else None

            # 단순어 → words.json
            words_to_add.append({
                "id":          tid,
                "en":          (t.get("en") or tid).lower(),
                "ko":          t.get("ko") or tid,
                "abbr":        abbr_v,
                "pos":         "noun",
                "domain":      domain,
                "description": t.get("description") or "",
                "not":         [],
            })
            existing_all.add(tid)

        if words_to_add:
            wd["words"].extend(words_to_add)
            wd["words"].sort(key=lambda w: w["id"])
            save_words(wd)

        log.info(f"[batch] merge words={len(words_to_add)} skipped={skipped} from {fname}")
        return jsonify({
            "ok":      True,
            "added":   len(words_to_add),
            "skipped": skipped,
            "note":    "words.json에 병합됨. 복합어는 UI에서 수동 이동 필요.",
        })
    except Exception as e:
        log.warning(f"[batch] merge 실패: {e}")
        return jsonify({"ok": False, "error": str(e)})


# ══════════════════════════════════════════════════════════════════════
# 진입점
# ══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="glossary 웹 UI 서버")
    parser.add_argument("--port", type=int, default=5000)
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
