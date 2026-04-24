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

# ── GlossaryWriter 로드 ────────────────────────────────────────────────
# words.json / compounds.json write는 GlossaryWriter를 통해서만 수행.
sys.path.insert(0, str(REPO_ROOT))
try:
    from core.writer import GlossaryWriter as _GlossaryWriter
except ImportError:
    _GlossaryWriter = None  # fallback: 직접 write (하위 호환)
LOG_DIR   = REPO_ROOT / "log"
LOG_FILE  = LOG_DIR / "glossary.log"
RUN_PY    = BIN_DIR / "run.py"
GENERATE_PY   = REPO_ROOT / "generate_glossary.py"
DICT_DIR      = REPO_ROOT / "dictionary"
TERMS_PATH    = DICT_DIR / "terms.json"
WORDS_PATH    = DICT_DIR / "words.json"
COMPOUNDS_PATH = DICT_DIR / "compounds.json"
BANNED_PATH   = DICT_DIR / "banned.json"
PENDING_PATH  = DICT_DIR / "pending_words.json"
GLOSSARY_PATH = REPO_ROOT / "GLOSSARY.md"
GITIGNORE     = REPO_ROOT / ".gitignore"

LOG_DIR.mkdir(exist_ok=True)

# ── 알림 / Trading Freeze 모듈 로드 ────────────────────────────
try:
    from web.notifier import notify_info, notify_warning, notify_critical
except ImportError:
    try:
        from notifier import notify_info, notify_warning, notify_critical
    except ImportError:
        def notify_info(msg):     return {"telegram": False, "slack": False}  # type: ignore
        def notify_warning(msg):  return {"telegram": False, "slack": False}  # type: ignore
        def notify_critical(msg): return {"telegram": False, "slack": False}  # type: ignore

try:
    from web.trading_freeze import check_freeze_or_raise, get_freeze_status
except ImportError:
    try:
        from trading_freeze import check_freeze_or_raise, get_freeze_status
    except ImportError:
        def check_freeze_or_raise(action=""):  return None         # type: ignore
        def get_freeze_status():               return {"enabled": False, "is_frozen": False, "reason": ""}  # type: ignore

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

# ── v2: words / compounds / banned / drafts ─────────────────────────
# mtime-based in-memory cache: avoids re-reading large JSON files on every GET
_cache: dict = {}

def _load_json(path: Path, key: str) -> dict:
    if not path.exists():
        return {key: []}
    mtime = path.stat().st_mtime
    entry = _cache.get(str(path))
    if entry and entry['mtime'] == mtime:
        return entry['data']
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    _cache[str(path)] = {'mtime': mtime, 'data': data}
    return data

def _invalidate_cache(path: Path):
    _cache.pop(str(path), None)

def load_drafts() -> dict:
    return _load_json(DICT_DIR / "drafts.json", "drafts")

def save_drafts(data: dict):
    with open(DICT_DIR / "drafts.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _invalidate_cache(DICT_DIR / "drafts.json")

def _save_json(path: Path, data: dict):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _invalidate_cache(path)

def load_words()     -> dict: return _load_json(WORDS_PATH,     "words")
def load_compounds() -> dict: return _load_json(COMPOUNDS_PATH, "compounds")
def load_banned()    -> dict: return _load_json(BANNED_PATH,    "banned")

def save_words(d):     _save_json(WORDS_PATH,     d)
def save_compounds(d): _save_json(COMPOUNDS_PATH, d)
def save_banned(d):    _save_json(BANNED_PATH,    d)

def load_pending_words() -> dict: return _load_json(PENDING_PATH, "words")
def save_pending_words(d): _save_json(PENDING_PATH, d)

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

def _inject_metadata(new_item, old_item=None):
    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    new_item['status'] = new_item.get('status', 'active')
    
    # id, lang, variants, abbreviation 등의 소문자 정규화는 이제
    # core/writer.py의 _normalize_entry() 에서 일괄 처리됩니다.
    
    if old_item:
        new_item['created_at'] = old_item.get('created_at', now_str)
        if new_item['status'] == 'deprecated':
            new_item['deprecated_at'] = old_item.get('deprecated_at', now_str)
        else:
            if 'deprecated_at' in old_item:
                new_item['deprecated_at'] = old_item['deprecated_at']
            if 'deprecated_at' in new_item and 'deprecated_at' not in old_item:
                del new_item['deprecated_at']
    else:
        new_item['created_at'] = new_item.get('created_at', now_str)
        if new_item['status'] == 'deprecated':
            new_item['deprecated_at'] = new_item.get('deprecated_at', now_str)
            
    new_item['updated_at'] = now_str


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
    import hashlib
    data = load_words()
    etag = hashlib.md5(
        json.dumps(data, ensure_ascii=False, sort_keys=True).encode('utf-8')
    ).hexdigest()
    if request.headers.get('If-None-Match') == etag:
        from flask import Response
        return Response(status=304)
    resp = jsonify(data)
    resp.headers['ETag'] = etag
    resp.headers['Cache-Control'] = 'no-cache'
    return resp

@app.route("/api/words", methods=["POST"])
def add_word():
    w = request.get_json()
    if not w: return jsonify({"error": "요청 본문 없음"}), 400
    if _GlossaryWriter:
        try:
            gw = _GlossaryWriter()
            if not gw.add_word(w, skip_duplicate=False):
                return jsonify({"error": f"이미 존재하는 id: {w.get('id')}"}), 409
            gw.save()
            _invalidate_cache(WORDS_PATH)
        except ValueError as e:
            return jsonify({"error": str(e)}), 409
    else:
        # fallback (GlossaryWriter 없을 때)
        data = load_words()
        if any(x["id"] == w.get("id") for x in data["words"]):
            return jsonify({"error": f"이미 존재하는 id: {w.get('id')}"}), 409
        _inject_metadata(w)
        data["words"].append(w)
        data["words"].sort(key=lambda x: x["id"])
        save_words(data)
    log.info(f"[word:add] id={w.get('id')}")
    return jsonify({"ok": True, "word": w}), 201

@app.route("/api/words/<word_id>", methods=["PUT"])
def update_word(word_id):
    updated = request.get_json()
    if not updated: return jsonify({"error": "요청 본문 없음"}), 400
    if _GlossaryWriter:
        gw = _GlossaryWriter()
        if not gw.update_word(word_id, updated):
            return jsonify({"error": f"미존재: {word_id}"}), 404
        gw.save()
        _invalidate_cache(WORDS_PATH)
    else:
        data = load_words()
        idx = next((i for i,x in enumerate(data["words"]) if x["id"] == word_id), None)
        if idx is None: return jsonify({"error": f"미존재: {word_id}"}), 404
        _inject_metadata(updated, data["words"][idx])
        data["words"][idx] = updated
        save_words(data)
    log.info(f"[word:update] id={word_id}")
    return jsonify({"ok": True, "word": updated})

@app.route("/api/words/<word_id>", methods=["DELETE"])
def delete_word(word_id):
    if _GlossaryWriter:
        gw = _GlossaryWriter()
        if not gw.remove_word(word_id):
            return jsonify({"error": f"미존재: {word_id}"}), 404
        gw.save()
        _invalidate_cache(WORDS_PATH)
    else:
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
    if _GlossaryWriter:
        try:
            gw = _GlossaryWriter()
            if not gw.add_compound(c, skip_duplicate=False):
                return jsonify({"error": f"이미 존재하는 id: {c.get('id')}"}), 409
            gw.save()
            _invalidate_cache(COMPOUNDS_PATH)
        except ValueError as e:
            return jsonify({"error": str(e)}), 409
    else:
        data = load_compounds()
        if any(x["id"] == c.get("id") for x in data["compounds"]):
            return jsonify({"error": f"이미 존재하는 id: {c.get('id')}"}), 409
        _inject_metadata(c)
        data["compounds"].append(c)
        data["compounds"].sort(key=lambda x: x["id"])
        save_compounds(data)
    log.info(f"[compound:add] id={c.get('id')}")
    return jsonify({"ok": True, "compound": c}), 201

@app.route("/api/compounds/<cid>", methods=["PUT"])
def update_compound(cid):
    updated = request.get_json()
    if not updated: return jsonify({"error": "요청 본문 없음"}), 400
    if _GlossaryWriter:
        gw = _GlossaryWriter()
        if not gw.update_compound(cid, updated):
            return jsonify({"error": f"미존재: {cid}"}), 404
        gw.save()
        _invalidate_cache(COMPOUNDS_PATH)
    else:
        data = load_compounds()
        idx = next((i for i,x in enumerate(data["compounds"]) if x["id"] == cid), None)
        if idx is None: return jsonify({"error": f"미존재: {cid}"}), 404
        _inject_metadata(updated, data["compounds"][idx])
        data["compounds"][idx] = updated
        save_compounds(data)
    log.info(f"[compound:update] id={cid}")
    return jsonify({"ok": True, "compound": updated})

@app.route("/api/compounds/<cid>", methods=["DELETE"])
def delete_compound(cid):
    if _GlossaryWriter:
        gw = _GlossaryWriter()
        if not gw.remove_compound(cid):
            return jsonify({"error": f"미존재: {cid}"}), 404
        gw.save()
        _invalidate_cache(COMPOUNDS_PATH)
    else:
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
    _inject_metadata(b)
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
    _inject_metadata(updated, data["banned"][idx])
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
    # ── Trading Freeze 게이트 ───────────────────────────────
    freeze_resp = check_freeze_or_raise("generate")
    if freeze_resp:
        from flask import jsonify as _jsonify
        return _jsonify(freeze_resp), 403

    log.info("[generate] 시작")
    result = _run_generate()
    combined = result["stdout"]
    if result["stderr"]: combined += "\n" + result["stderr"]
    log.info(f"[generate] 완료 ok={result['ok']}")

    # ── 알림 ─────────────────────────────────────────
    fatal_in_output = "FATAL" in combined or "[CRITICAL]" in combined
    if result["ok"] and not fatal_in_output:
        notify_info("generate 완료: terms.json 재생성 성공")
    else:
        notify_warning(f"generate 실패 또는 FATAL 발생\n{combined[:300]}")

    return jsonify({"ok": result["ok"], "output": combined or f"(returncode={result['code']})"})

@app.route("/api/validate", methods=["POST"])
def api_validate():
    """generate_glossary.py validate 실행."""
    result = run_subprocess(sys.executable, str(GENERATE_PY), "validate", timeout=30)
    combined = result["stdout"]
    if result["stderr"]: combined += "\n" + result["stderr"]

    # FATAL 발생 시만 알림
    fatal_in_output = "FATAL" in combined or "[CRITICAL]" in combined
    if fatal_in_output:
        notify_critical(f"validate FATAL 발생!\n{combined[:400]}")

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

    # ── Trading Freeze 게이트 ───────────────────────────────
    freeze_resp = check_freeze_or_raise("컴바 + 배포")
    if freeze_resp:
        return jsonify(freeze_resp), 403

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
    notify_info(f"glossary 커바 완료: {message}")
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


# ════════════════════════════════════════════════════════
# API — Trading Freeze 상태
# ════════════════════════════════════════════════════════

@app.route("/api/trading-freeze/status", methods=["GET"])
def trading_freeze_status():
    """Trading Freeze 현재 상태 조회."""
    return jsonify(get_freeze_status())


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
        sys.executable, str(BIN_DIR / "scan_items.py"), "--mode", "word", "--json",
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
    reg_mode = body.get("register_mode", "normal")
    api_type = body.get("api_type", "").strip()   # UI에서 선택한 API 종류
    model    = body.get("model",    "").strip()   # UI에서 선택한 모델

    cmd_args = [sys.executable, str(BIN_DIR / "batch_items.py"), "--mode", "word", "--register-mode", reg_mode]
    
    cmd_args.append("--ui-prog")

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

    log.info(f"[batch] run 시작 auto_mode={reg_mode} api={api_type or '(.env)'} model={model or '(.env)'}")

    from flask import Response
    import subprocess as _sp

    def generate_stream():
        try:
            proc = _sp.Popen(
                cmd_args,
                cwd=str(REPO_ROOT),
                stdout=_sp.PIPE,
                stderr=_sp.STDOUT,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=extra_env,
            )
            for line in proc.stdout:
                yield line
            
            proc.wait(timeout=900)
            if proc.returncode != 0:
                yield f"\n[오류] 프로세스가 에러 코드 {proc.returncode}로 종료되었습니다.\n"
            else:
                yield "\n[완료] API 분석 프로세스 정상 종료"
        except Exception as e:
            yield f"\n[서버 오류] {e}\n"

    # text/plain event stream returning raw logs
    return Response(generate_stream(), mimetype="text/plain")


@app.route("/api/batch/files", methods=["GET"])
def batch_files():
    """tmp/items/ 하위 결과 파일 목록 반환."""
    out_dir = _proj_root() / "tmp" / "items"
    if not out_dir.exists():
        return jsonify({"ok": True, "files": []})

    files = []
    for f in sorted(out_dir.glob("items_*.json"), reverse=True):
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

    out_dir = _proj_root() / "tmp" / "items"
    fpath   = (out_dir / fname).resolve()

    # 경로 이탈 방지
    if not str(fpath).startswith(str(out_dir.resolve())):
        return jsonify({"error": "잘못된 경로"}), 400
    if not fpath.exists():
        return jsonify({"error": "파일 없음"}), 404

    try:
        data = json.loads(fpath.read_text(encoding='utf-8'))
        return jsonify({"ok": True, "items": data.get("items", [])})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/drafts", methods=["GET"])
def api_get_drafts():
    """BOM_TS drafts 보류 용어 조회"""
    return jsonify(load_drafts())

@app.route("/api/drafts/clear", methods=["POST"])
def clear_drafts():
    save_drafts({"drafts": []})
    return jsonify({"ok": True})


@app.route("/api/batch/register_compound", methods=["POST"])
def batch_register_compound():
    """
    합성어 구문(예: 'automatic data exchange')을 단일 트랜잭션으로 처리:
      1. 단어별로 words.json에서 검색 (id 또는 variants.value 기준)
      2. 미등록 단어를 words.json에 먼저 등록 (id/형태소 중복 제외)
      3. 합성어(compound)를 compounds.json에 등록 (약어 = abbrev_id.upper())
      실패 시 words.json / compounds.json 원본으로 rollback.
    """
    import copy
    from datetime import datetime, timezone

    body      = request.get_json() or {}
    abbrev_id   = body.get("abbrev", "").strip().lower()   # 현재 단어 id (예: adx)
    phrase      = body.get("phrase", "").strip()            # 전체 구문 (예: automatic data exchange)
    ref_url     = body.get("ref_url", "").strip()
    lang_custom = body.get("lang_custom") or {}             # {en, ko, ja, zh_hans} — 사용자 입력 명칭
    desc_custom = body.get("desc_custom") or {}             # {ko, en} — 사용자 입력 설명
    domain_custom = body.get("domain") or ["general"]       # 사용자 입력 도메인 배열

    if not abbrev_id or not phrase:
        return jsonify({"ok": False, "error": "abbrev, phrase 필수"})

    now_str      = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    phrase_words = [w.lower() for w in phrase.split() if w.strip()]
    compound_id  = "_".join(phrase_words)

    try:
        wd = load_words()
        cd = load_compounds()

        # ── 스냅샷 (rollback용) ──────────────────────────────────────
        wd_snapshot = copy.deepcopy(wd)
        cd_snapshot = copy.deepcopy(cd)

        existing_comp_ids = {c["id"] for c in cd.get("compounds", [])}

        # ── 단어 존재 여부 판별 ──────────────────────────────────────
        # id로 직접 등록된 단어 집합
        existing_word_ids = {w["id"] for w in wd.get("words", [])}
        # variants.value 로 이미 포함된 단어 집합 (형태소로 등록된 경우)
        variant_values: set = set()
        for w in wd.get("words", []):
            for v in w.get("variants", []):
                val = (v.get("value") or v.get("short") or "").lower()
                if val:
                    variant_values.add(val)

        words_found   = []   # words.json id로 이미 있는 단어
        words_as_var  = []   # id는 없지만 variant value로 이미 포함된 단어
        words_new     = []   # 완전히 새로 등록 필요한 단어

        for pw in phrase_words:
            if pw in existing_word_ids:
                words_found.append(pw)
            elif pw in variant_values:
                words_as_var.append(pw)
            else:
                words_new.append(pw)

        # ── Step 1: 미등록 단어 → words.json 먼저 등록 ──────────────
        newly_added_words = []
        for w in words_new:
            # 약어 단어 자체(abbrev_id)는 lang_custom/desc_custom 적용, 나머지는 기본값
            is_abbrev = (w == abbrev_id)
            w_lang = dict(lang_custom) if is_abbrev and lang_custom else {"en": w, "ko": ""}
            if "en" not in w_lang:
                w_lang["en"] = w
            w_desc = dict(desc_custom) if is_abbrev and desc_custom else {"en": w, "ko": ""}
            entry = {
                "id": w,
                "domain": domain_custom,
                "status": "active",
                "lang": w_lang,
                "description_i18n": w_desc,
                "canonical_pos": "noun",
                "created_at": now_str,
                "updated_at": now_str,
                "variants": [],
                "note": f"Auto-registered from compound: {compound_id}"
            }
            wd.setdefault("words", []).append(entry)
            existing_word_ids.add(w)
            newly_added_words.append(w)

        if newly_added_words:
            wd["words"].sort(key=lambda x: x["id"])
            save_words(wd)

        # ── Step 2: compound → compounds.json 등록 ──────────────────
        compound_added = False
        if compound_id not in existing_comp_ids:
            # compound lang: lang_custom 있으면 우선, 없으면 phrase 기반 기본값
            comp_lang = {"en": " ".join(w.title() for w in phrase_words), "ko": phrase}
            if lang_custom:
                comp_lang = {**comp_lang, **lang_custom}
            # compound description: desc_custom 있으면 사용, 없으면 간단 설명
            comp_desc: dict = {}
            if desc_custom:
                comp_desc = dict(desc_custom)
            else:
                comp_desc = {"ko": f"{phrase}의 약어", "en": phrase}
            compound_entry = {
                "id": compound_id,
                "words": phrase_words,
                "domain": domain_custom,
                "status": "active",
                "lang": comp_lang,
                "description_i18n": comp_desc,
                "created_at": now_str,
                "updated_at": now_str,
                "variants": [
                    {"type": "abbreviation", "short": abbrev_id.upper(), "long": abbrev_id}
                ],
            }
            if ref_url:
                compound_entry["source_urls"] = [ref_url]
            cd.setdefault("compounds", []).append(compound_entry)
            cd["compounds"].sort(key=lambda x: x["id"])
            save_compounds(cd)
            compound_added = True

        log.info(
            f"[batch] register_compound: {compound_id} | abbrev={abbrev_id} | "
            f"found={words_found} | as_variant={words_as_var} | new={newly_added_words} | "
            f"compound_added={compound_added}"
        )
        return jsonify({
            "ok": True,
            "compound_id": compound_id,
            "compound_added": compound_added,
            "words_found": words_found,
            "words_as_variant": words_as_var,
            "words_new": newly_added_words,
            "total_words_registered": len(newly_added_words),
        })

    except Exception as e:
        # ── Rollback ──────────────────────────────────────────────────
        log.error(f"[batch] register_compound 실패, rollback 수행: {e}")
        try:
            save_words(wd_snapshot)
            save_compounds(cd_snapshot)
            log.info("[batch] rollback 완료")
        except Exception as rb_err:
            log.error(f"[batch] rollback 실패: {rb_err}")
        return jsonify({"ok": False, "error": str(e), "rolled_back": True})


@app.route("/api/batch/ai_draft", methods=["POST"])
def batch_ai_draft():
    """
    단어/구문 하나를 받아 AI를 통해 다국어 명칭 + 발음 + 한 줄 설명을 반환.
    기존 .env 의 API_KEY_TYPE / API_MODEL / *_API_KEY 를 그대로 사용.

    Request body:
        { "word": "fifo", "api_type": "claude" (optional), "model": "" (optional) }

    Response:
        {
            "ok": true,
            "en":  "First-In, First-Out",
            "ko":  "선입선출(先入先出)",
            "ja":  "先入れ先出し",
            "zh":  "先进先出",
            "pronunciation": { "en": "퍼스트 인 퍼스트 아웃", "ko": "선입선출", ... },
            "description_ko": "먼저 들어온 데이터가...",
            "description_en": "A method where the first..."
        }
    """
    import os

    body     = request.get_json() or {}
    word     = body.get("word", "").strip()
    api_type = body.get("api_type", "").strip() or os.environ.get("API_KEY_TYPE", "claude")
    model    = body.get("model",    "").strip() or os.environ.get("API_MODEL",    "")
    sources  = body.get("sources", [])

    if not word:
        return jsonify({"ok": False, "error": "word 파라미터 필요"}), 400

    context_str = ""
    if isinstance(sources, list) and sources:
        context_str = f"Found in codebase context: {', '.join(sources[:5])}\n"
    elif isinstance(sources, str):
        context_str = f"Found in codebase context: {sources}\n"

    proj_name   = os.environ.get("GLOSSARY_PROJ_NAME", "BOM_TS")
    proj_domain = os.environ.get("GLOSSARY_PROJ_DOMAIN", "trading system and software architecture")

    prompt = (
        f"[단어]\n{word}\n\n"
        f"[소스]\n{context_str}\n\n"
        f"아래 내용을 출력해 줘\n"
        f"* 도메인 (domain)\n"
        f"** 다음 중 가장 적합한 하나를 선택: trading, market, system, infra, ui, general, proper\n"
        f"* 간단 설명 (short_description)\n"
        f"* 기본 단어 형태 (base_form)\n"
        f"** 단어 원형 원칙: 복수형(-s/-es), 과거분사(-ed), 진행형(-ing) 등의 파생 형태를 제거하고, 해당 단어의 사전적 기본형(Singular/Present Tense)을 출력할 것\n"
        f"** 도메인 관례 유지: 단, 트레이딩이나 IT 도메인에서 고유명사처럼 굳어진 약어(예: GTC, GICS)는 예외로 하되, 일반 명사는 반드시 단수형 원형을 우선할 것\n"
        f"* 다국어 번역\n"
        f"** 한글명(ko), 영문명(en), 일본어(ja), 중국어 간체(zh)\n"
        f"* 설명\n"
        f"** 한글/영어 한 줄 설명 작성해 줘. 한글, 영어 언급은 명시하지 말 것. 마침표 찍지 말 것\n"
        f"* 형태소 및 관계어 (없으면 빈 값 또는 빈 배열)\n"
        f"** 약어 (abbr): 2-5자 대문자\n"
        f"** 어원 (from): 파생된 원래 형태 (예: robot -> bot 인 경우 robot)\n"
        f"** 변형/파생어 (variants): 배열 형태 (예: type: plural, value: kills)\n"
        f"** 유의어 (synonyms): 관련된 영문 유의어 배열\n"
        f"** 반의어 (antonyms): 관련된 영문 반의어 배열\n"
        f"** 출처 (source_urls): wiktionary 등 참고 URL 배열\n"
        f"** 금지 표현 (not): 사용을 지양해야 할 표현 배열\n\n"
        f"결과는 반드시 아래 JSON 형식으로만 응답할 것 (다른 텍스트 금지):\n"
        f"{{\n"
        f'  "domain": "...",\n'
        f'  "short_description": "...",\n'
        f'  "base_form": "...",\n'
        f'  "ko": "...",\n'
        f'  "en": "...",\n'
        f'  "ja": "...",\n'
        f'  "zh": "...",\n'
        f'  "description_ko": "...",\n'
        f'  "description_en": "...",\n'
        f'  "abbr": "...",\n'
        f'  "from": "...",\n'
        f'  "variants": [{{"type": "plural", "value": "..."}}],\n'
        f'  "synonyms": ["..."],\n'
        f'  "antonyms": ["..."],\n'
        f'  "source_urls": ["..."],\n'
        f'  "not": ["..."]\n'
        f"}}"
    )

    try:
        raw_json = _call_ai_api(api_type, model, prompt)
        data     = json.loads(raw_json)
        data["ok"] = True
        log.info(f"[ai_draft] word={word} api={api_type} ok=True")
        return jsonify(data)
    except json.JSONDecodeError as je:
        log.warning(f"[ai_draft] JSON 파싱 실패 word={word}: {je}")
        return jsonify({"ok": False, "error": f"AI 응답 JSON 파싱 실패: {je}"}), 502
    except Exception as e:
        log.warning(f"[ai_draft] 실패 word={word}: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


def _call_ai_api(api_type: str, model: str, prompt: str) -> str:
    """
    api_type(claude|openai|google)에 따라 AI API를 호출하고 응답 텍스트를 반환.
    키는 모두 .env / 환경변수에서 로드한다.
    """
    import os, re

    def _extract_json(text: str) -> str:
        """마크다운 코드블록에 싸인 경우 JSON 추출."""
        m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # 중괄호로 감싼 부분만 추출
        m2 = re.search(r'(\{[\s\S]*\})', text)
        if m2:
            return m2.group(1).strip()
        return text.strip()

    if api_type == "claude" or api_type == "anthropic":
        import anthropic
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY 환경변수 미설정")
        mdl = model or "claude-haiku-4-5-20251001"
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model=mdl,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text if msg.content else ""
        return _extract_json(raw)

    elif api_type == "openai":
        import openai as _openai
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise ValueError("OPENAI_API_KEY 환경변수 미설정")
        mdl = model or "gpt-4o-mini"
        client = _openai.OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model=mdl,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content if resp.choices else ""
        return _extract_json(raw)

    elif api_type == "google":
        import google.generativeai as genai
        key = os.environ.get("GOOGLE_API_KEY", "")
        if not key:
            raise ValueError("GOOGLE_API_KEY 환경변수 미설정")
        mdl = model or "gemini-2.0-flash"
        genai.configure(api_key=key)
        gmodel = genai.GenerativeModel(mdl)
        resp = gmodel.generate_content(prompt)
        raw  = resp.text if hasattr(resp, "text") else ""
        return _extract_json(raw)

    else:
        raise ValueError(f"지원하지 않는 api_type: {api_type!r}. claude|openai|google 중 선택")


@app.route("/api/batch/merge", methods=["POST"])
def batch_merge():
    """
    승인된 단어(words), 복합어(compounds)를 병합하고, 선택받지 못한 용어는 drafts.json에 저장 (최대 100건).
    """
    body = request.get_json() or {}
    
    approved_words = body.get("approved_words", [])
    approved_comps = body.get("approved_compounds", [])
    rejected       = body.get("rejected", [])

    try:
        wd = load_words()
        cd = load_compounds()
        dd = load_drafts()

        existing_word_ids = {w["id"] for w in wd["words"]}
        existing_comp_ids = {c["id"] for c in cd["compounds"]}
        
        words_added = 0
        comps_added = 0

        # prefix detection helper
        _KNOWN_PREFIXES = (
            "re", "un", "pre", "dis", "mis", "over", "under",
            "out", "non", "de", "anti", "counter", "sub", "super",
        )

        def _detect_variant_type(child_id: str, parent_id: str) -> str:
            """Determine variant type based on relationship between child and parent word."""
            cl = child_id.lower()
            pl = parent_id.lower()
            for pfx in _KNOWN_PREFIXES:
                if cl == pfx + pl:
                    return "prefix"
            # suffix check (e.g., sender from send)
            if cl.startswith(pl):
                return "verb_derived"
            return "verb_derived"

        # 새 단어 추가
        for w in approved_words:
            wid = w.get("id")
            if not wid: continue

            # from 필드가 기존 단어를 가리키면: 독립 등록 대신 부모 단어의 variant로 추가
            from_word = w.get("from", "")
            if from_word and from_word in existing_word_ids and wid != from_word:
                parent_w = next((x for x in wd["words"] if x["id"] == from_word), None)
                if parent_w:
                    evars = parent_w.setdefault("variants", [])
                    vtype = _detect_variant_type(wid, from_word)
                    # check duplicate
                    already = any(
                        (ev.get("value") or "").lower() == wid.lower()
                        for ev in evars
                    )
                    if not already:
                        evars.append({"type": vtype, "value": wid})
                        from datetime import datetime, timezone
                        parent_w["updated_at"] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                        words_added += 1
                        log.info(f"[batch] added '{wid}' as {vtype} variant of '{from_word}'")
                    continue

            if wid not in existing_word_ids:
                _inject_metadata(w)
                wd["words"].append(w)
                existing_word_ids.add(wid)
                words_added += 1
            else:
                # 이미 존재하는 ID인 경우: variants 정보만 병합 시도
                existing_w = next((x for x in wd["words"] if x["id"] == wid), None)
                if existing_w and w.get("variants"):
                    evars = existing_w.setdefault("variants", [])
                    changed = False
                    for nv in w.get("variants"):
                        vtype = nv.get("type")
                        if vtype == "abbreviation":
                            if not any(ev.get("type") == "abbreviation" and (ev.get("short") or "").lower() == (nv.get("short") or "").lower() for ev in evars):
                                evars.append(nv)
                                changed = True
                        else:
                            if not any((ev.get("value") or "").lower() == (nv.get("value") or "").lower() for ev in evars):
                                evars.append(nv)
                                changed = True
                    if changed:
                        existing_w["updated_at"] = w.get("updated_at") or existing_w.get("updated_at")
                        words_added += 1

        # 복합어 추가
        for c in approved_comps:
            cid = c.get("id")
            if cid and cid not in existing_comp_ids:
                _inject_metadata(c)
                cd["compounds"].append(c)
                existing_comp_ids.add(cid)
                comps_added += 1

        # 거부된/선택받지 못한 항목 Drafts 덮어쓰기 (가장 마지막 스캔 기준)
        dd["drafts"] = rejected
        save_drafts(dd)

        if words_added > 0:
            wd["words"].sort(key=lambda x: x["id"])
            save_words(wd)
            
        if comps_added > 0:
            cd["compounds"].sort(key=lambda x: x["id"])
            save_compounds(cd)

        log.info(f"[batch] merge words={words_added} comps={comps_added} drafts={len(rejected)}")
        return jsonify({
            "ok": True,
            "added": words_added + comps_added,
            "skipped": 0,
            "note": "병합 처리 완료 및 드래프트 저장."
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

    # Trading Freeze 상태 출력
    freeze_status = get_freeze_status()
    freeze_mark = "🔴 FREEZE" if freeze_status["is_frozen"] else "🟢 OK"

    log.info(f"[server] 시작  port={args.port}  repo={REPO_ROOT}")
    print(f"\n  glossary UI 서버 시작")
    print(f"  저장소 루트  : {REPO_ROOT}")
    print(f"  로그 파일    : {LOG_FILE}")
    print(f"  접속 주소    : http://{args.host}:{args.port}")
    print(f"  Trading Freeze: {freeze_mark}")
    if freeze_status["is_frozen"]:
        print(f"    이유: {freeze_status['reason']}")
    print(f"  종료         : Ctrl+C\n")

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
