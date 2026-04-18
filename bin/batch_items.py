#!/usr/bin/env python3
"""
batch_items.py  —  BOM_TS 용어 후보 → 상태 결정(auto/safety/normal) → 저장/병합
위치: glossary/bin/batch_items.py

사용법:
  python batch_items.py --mode word --register-mode auto
  python batch_items.py --mode word --register-mode safety
  python batch_items.py --mode word --register-mode normal
"""

import sys
import io
import os
import json
import time
import math
import urllib.request
import urllib.error
import argparse
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding.lower() not in ('utf-8','utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BIN_DIR = Path(__file__).parent.resolve()
GLOSSARY_DIR = BIN_DIR.parent.resolve()
sys.path.insert(0, str(BIN_DIR))

from scan_items import load_env, resolve_proj_root, parse_list, ItemScanner, load_existing_words_and_tokens, load_existing_terms

def get_env(env_arg: str = None) -> tuple:
    if env_arg:
        env_path = Path(env_arg)
    else:
        env_path = GLOSSARY_DIR.parent / ".env"
        if not env_path.exists():
            env_path = GLOSSARY_DIR / ".env"
    return load_env(env_path), str(env_path)

def _http_post(url: str, body: bytes, headers: dict, timeout: int = 120) -> dict:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))

def _http_get(url: str, headers: dict = None, timeout: int = 10) -> list:
    headers = headers or {}
    if "User-Agent" not in headers:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 BOM_TS Glossary/2.0"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode('utf-8')
            return json.loads(text)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        raise e

def call_claude(prompt: str, api_key: str, max_tokens: int, model: str) -> str:
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": "당신은 BOM_TS 프로젝트의 용어 판단가입니다. 주어진 단어가 도메인 개념이나 일반 단어로 적합한지 판단하세요.",
        "messages": [{"role": "user", "content": prompt}],
    }
    data = _http_post("https://api.anthropic.com/v1/messages", json.dumps(body).encode('utf-8'), {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    })
    return data["content"][0]["text"]

def call_openai(prompt: str, api_key: str, max_tokens: int, model: str) -> str:
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": "당신은 BOM_TS 프로젝트의 용어 판단가입니다. 주어진 단어가 도메인 개념이나 일반 단어로 적합한지 판단하세요."},
            {"role": "user", "content": prompt},
        ],
    }
    data = _http_post("https://api.openai.com/v1/chat/completions", json.dumps(body).encode('utf-8'), {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    return data["choices"][0]["message"]["content"]

def call_google(prompt: str, api_key: str, max_tokens: int, model: str) -> str:
    body = {
        "contents": [{"parts": [{"text": "당신은 BOM_TS 프로젝트의 용어 판단가입니다.\n" + prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    data = _http_post(url, json.dumps(body).encode('utf-8'), {"Content-Type": "application/json"})
    return data["candidates"][0]["content"]["parts"][0]["text"]

def call_api(prompt: str, env: dict, max_tokens: int) -> str:
    api_type = env.get("API_KEY_TYPE", "claude").lower()
    model = env.get("API_MODEL", "claude-sonnet-4-20250514")
    
    if api_type == "claude":
        key = env.get("ANTHROPIC_API_KEY", "")
        if not key: raise ValueError("ANTHROPIC_API_KEY missing")
        return call_claude(prompt, key, max_tokens, model)
    elif api_type == "openai":
        key = env.get("OPENAI_API_KEY", "")
        if not key: raise ValueError("OPENAI_API_KEY missing")
        return call_openai(prompt, key, max_tokens, model)
    elif api_type == "google":
        key = env.get("GOOGLE_API_KEY", "")
        if not key: raise ValueError("GOOGLE_API_KEY missing")
        return call_google(prompt, key, max_tokens, model)
    else:
        raise ValueError(f"Unknown API_KEY_TYPE: {api_type}")

def _parse_llm_json(text: str) -> list:
    start = text.find('[')
    end = text.rfind(']') + 1
    if start == -1 or end <= 0: return []
    try:
        return json.loads(text[start:end])
    except Exception:
        return []

def process_safety(candidates: list, env: dict, max_tokens: int, prog_cb) -> list:
    results = []
    chunk_size = 50
    n_chunks = math.ceil(len(candidates) / chunk_size)
    for i in range(n_chunks):
        chunk = candidates[i*chunk_size:(i+1)*chunk_size]
        prog_cb(i, f"LLM 청크 {i+1}/{n_chunks}", len(chunk), len(chunk), "진행중")
        
        prompt = "다음 단어 목록을 평가하세요. JSON 배열 형식으로만 응답. [{ \"word\": \"단어\", \"recommended\": true/false, \"reason\": \"이유\" }]\n\n"
        prompt += ", ".join([c["word"] for c in chunk])
        
        try:
            resp = call_api(prompt, env, max_tokens)
            parsed = _parse_llm_json(resp)
            lookup = {p.get("word"): p for p in parsed}
            for c in chunk:
                w = c["word"]
                if w in lookup:
                    c["recommended"] = lookup[w].get("recommended", False)
                    c["reason"] = lookup[w].get("reason", "API 응답")
                    results.append(c)
                else:
                    c["recommended"] = False
                    c["reason"] = "LLM 응답 누락"
                    results.append(c)
            prog_cb(i, f"LLM 청크 {i+1}/{n_chunks}", len(chunk), len(chunk), "완료")
        except Exception as e:
            prog_cb(i, f"LLM 청크 {i+1}/{n_chunks}", len(chunk), len(chunk), "오류")
            for c in chunk:
                c["recommended"] = False
                c["reason"] = str(e)
                results.append(c)
        time.sleep(1)
    return results

def process_auto(candidates: list, env: dict, max_tokens: int, prog_cb) -> list:
    # v1.2: Wiktionary single source + AI pipeline + Hard Gate  (통일된 경로)
    # Migration(migrate_v1_1.py)과 동일한 fetch_and_process() 사용.
    # variants 추출 기준, from 규칙, Hard Gate 모두 동일.
    # dictionaryapi.dev 완전 제거됨.
    results = []
    batch_size = 10
    total = len(candidates)

    from wikt_sense import fetch_and_process as _fetch_and_process

    for i in range(0, total, batch_size):
        chunk = candidates[i:i+batch_size]
        prog_cb(i//batch_size, f"Auto Wikt {i}/{total}", len(chunk), len(chunk), "진행중")
        for c in chunk:
            w = c["word"]
            if len(w) < 2:
                c["recommended"] = False
                c["reason"] = "길이 부족 (<2)"
                results.append(c)
                continue

            try:
                # Build temporary word entry for pipeline
                _tmp_word = {
                    "id": w,
                    "canonical_pos": "noun",  # default; AI will correct
                    "domain": "general",
                    "lang": {"en": w},
                    "variants": [],
                }

                url, pipe_result = _fetch_and_process(w, _tmp_word, ai_env=env)

                if pipe_result is None:
                    c["recommended"] = False
                    c["reason"] = "Wiktionary fetch 실패"
                    results.append(c)
                    continue

                if pipe_result.status == "rejected":
                    c["recommended"] = False
                    reason = pipe_result.rejection_reason or "Hard Gate 실패"
                    c["reason"] = f"Gate 차단: {reason}"
                    results.append(c)
                    continue

                if pipe_result.status == "error":
                    c["recommended"] = False
                    c["reason"] = f"파이프라인 오류: {pipe_result.rejection_reason or 'unknown'}"
                    results.append(c)
                    continue

                # Pipeline passed -> recommended
                c["recommended"] = True
                c["reason"] = "AI+Wikt 검증 완료"
                c["enriched"] = {
                    "canonical_pos":    pipe_result.selected_pos or "noun",
                    "description_i18n": {"en": pipe_result.description_en} if pipe_result.description_en else {},
                    "source_urls":      [url] if url else [],
                    "variants":         pipe_result.variants,
                    "from":             pipe_result.from_word,
                }
            except Exception as e:
                c["recommended"] = False
                c["reason"] = f"처리 오류: {str(e)}"

            results.append(c)
            time.sleep(1.0)  # API rate limit

        # Batch Translate EN -> KO (for Korean labels)
        words_to_translate = [c["word"] for c in chunk if "enriched" in c]
        if words_to_translate:
            prompt = "Return a brief Korean translation (1-2 words) for the following English words in JSON array format: [{\"word\": \"...\", \"ko\": \"...\"}]. Words: " + ", ".join(words_to_translate)
            try:
                resp = call_api(prompt, env, max_tokens)
                parsed = _parse_llm_json(resp)
                ko_lookup = {p.get("word"): p.get("ko") for p in parsed if isinstance(p, dict)}
                for c in results:
                    if "enriched" in c and c["word"] in ko_lookup:
                        if "description_i18n" not in c["enriched"]:
                            c["enriched"]["description_i18n"] = {}
                        ko_txt = ko_lookup[c["word"]]
                        c["enriched"]["description_i18n"]["ko"] = ko_txt
                        c["lang"] = {"en": c["word"], "ko": ko_txt}
            except Exception:
                pass

        prog_cb(i//batch_size, f"Auto Wikt {i}/{total}", len(chunk), len(chunk), "완료")

        if total > 50 and i + batch_size < total:
            time.sleep(3)

    return results

def process_normal(candidates: list, prog_cb) -> list:
    for c in candidates:
        c["recommended"] = False
        c["reason"] = ""
    return candidates

def _save_tmp(data: list, proj_root: Path):
    out_dir = proj_root / "tmp" / "items"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    path = out_dir / f"items_{ts}.json"
    path.write_text(json.dumps({
        "meta": {"generated_at": datetime.now().isoformat(), "count": len(data)},
        "items": data
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    return path

def _apply_to_words_json(approved_items: list):
    words_path = GLOSSARY_DIR / "dictionary" / "words.json"
    if not words_path.exists():
        data = {"words": []}
    else:
        data = json.loads(words_path.read_text(encoding='utf-8'))
        
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    existing_ids = {w["id"] for w in data["words"]}
    
    for item in approved_items:
        w = item["word"]
        if w in existing_ids:
            continue
        enriched = item.get("enriched") or {}
        # Ko label: prefer from LLM translation, else the word itself
        ko_label = enriched.get("description_i18n", {}).get("ko") or w
        en_label  = (item.get("lang") or {}).get("en") or w
        new_w = {
            "id": w,
            "lang": {"en": en_label, "ko": ko_label},
            "domain": "general",
            "canonical_pos": enriched.get("canonical_pos") or "noun",
            "description_i18n": enriched.get("description_i18n") or {},
            "source_urls": enriched.get("source_urls") or [],
            "status": "auto_registered" if item.get("reason") == "사전 확인" else "active",
            "created_at": now,
            "updated_at": now,
        }
        # Apply enriched variants (already pos-filtered and deduped)
        if enriched.get("variants"):
            new_w["variants"] = enriched["variants"]
        # Apply enriched from (already quality-filtered)
        if enriched.get("from"):
            new_w["from"] = enriched["from"]
        data["words"].append(new_w)

    words_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["word", "term"], default="word")
    parser.add_argument("--register-mode", choices=["auto", "safety", "normal"], default="normal")
    parser.add_argument("--ui-prog", action="store_true")
    args = parser.parse_args()

    def prog(idx, name, current, total, status):
        # UI_PROG is strictly handled here to notify Web API.
        if args.ui_prog:
            print(f"PROG|{idx}|{name}|{current}|{total}|{status}", flush=True)

    env, _ = get_env()
    proj_root = resolve_proj_root(BIN_DIR, env)
    max_tokens = int(env.get("MAX_OUTPUT_TOKENS", 8192))
    
    exclude_dirs = parse_list(env.get('EXCLUDE_DIRS', 'backup,data,test,lib_test,tmp,glossary,.git,__pycache__,node_modules,.venv,venv'))
    content_skip = parse_list(env.get('EXCLUDE_FILE_CONTENT', 'cache,log'))
    exclude_exts = {e if e.startswith('.') else f'.{e}' for e in parse_list(env.get('EXCLUDE_EXTENSIONS', '.md,.txt,.log,.csv,.tsv,.png,.jpg,.jpeg,.gif,.pdf,.ico,.svg,.zip,.tar'))}

    if args.mode == "word":
        existing = load_existing_words_and_tokens(GLOSSARY_DIR)
    else:
        existing = load_existing_terms(GLOSSARY_DIR)

    prog(0, "소스 스캔", 0, 100, "진행중")
    print(f"[1/3] 소스 스캔... ({proj_root})")
    scanner = ItemScanner(proj_root, exclude_dirs, content_skip, exclude_exts, args.mode, existing)
    scanner.scan()
    
    candidates = []
    for k in sorted(scanner.candidates_count.keys()):
        candidates.append({"word": k, "count": scanner.candidates_count[k], "sources": scanner.candidates_sources[k][:3]})
        
    prog(0, "소스 스캔", len(candidates), len(candidates), "완료")
    print(f"      후보 {len(candidates)}개 추출")
    
    if not candidates:
        print("[완료] 처리할 후보가 없습니다.")
        return

    print(f"\n[2/3] 모드({args.register_mode}) 처리 시작")
    if args.register_mode == "auto":
        processed = process_auto(candidates, env, max_tokens, prog)
    elif args.register_mode == "safety":
        processed = process_safety(candidates, env, max_tokens, prog)
    else:
        processed = process_normal(candidates, prog)

    # Output formatting
    if args.ui_prog:
        out_path = _save_tmp(processed, proj_root)
        print(f"\n[완료] 결과 저장: {out_path}")
    else:
        # CLI Mode (Auto Merge and save files directly as mandated by Rule 1.1)
        print("\n[3/3] CLI 모드 자동 병합")
        approved = [p for p in processed if p.get("recommended")]
        pending = [p for p in processed if not p.get("recommended")]
        
        _apply_to_words_json(approved)
        print(f"      {len(approved)}건 자동 승인(words.json 반영)")
        
        if pending:
            out_path = _save_tmp(pending, proj_root)
            print(f"      {len(pending)}건 보류({out_path} 에 저장)")

if __name__ == "__main__":
    main()
