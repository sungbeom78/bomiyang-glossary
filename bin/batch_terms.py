#!/usr/bin/env python3
"""
batch_terms.py  —  용어 후보 → Claude/OpenAI/Google API → terms_날짜.json
위치: glossary/bin/batch_terms.py

사용법:
  python batch_terms.py              # 스캔 + API 분석 + 결과 저장
  python batch_terms.py --dry-run    # API 미호출, 토큰 예상치만 출력
  python batch_terms.py --chunk 200  # 청크 크기 지정
"""

import sys
import io
import os
import json
import time
import math
import argparse
from datetime import datetime
from pathlib import Path

# ── Windows 인코딩 ──────────────────────────────────────────────────
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding.lower() not in ('utf-8','utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BIN_DIR      = Path(__file__).parent.resolve()
GLOSSARY_DIR = BIN_DIR.parent.resolve()
sys.path.insert(0, str(BIN_DIR))

from scan_terms import load_env, resolve_proj_root, parse_list, load_existing_terms, TermScanner


# ════════════════════════════════════════════════════════════════════
# .env 로드
# ════════════════════════════════════════════════════════════════════

def get_env() -> dict:
    env_path = GLOSSARY_DIR.parent / ".env"
    if not env_path.exists():
        env_path = GLOSSARY_DIR / ".env"
    return load_env(env_path)


# ════════════════════════════════════════════════════════════════════
# 프롬프트 생성
# ════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """당신은 자동매매 시스템 개발 프로젝트의 용어 사전 관리자입니다.
주어진 용어 후보 목록을 분석해서, 진정한 도메인 용어만 골라 terms.json 포맷으로 정리하세요.

규칙:
1. 기술 구현 상세(지역변수, 임시변수, 외부 라이브러리명)는 제외
2. 비즈니스 도메인 용어, 시스템 아키텍처 용어, 설정 키, DB 스키마만 포함
3. 이미 등록된 용어의 단순 조합이면 제외 (예: kisApiToken = kisApi + Token)
4. 반드시 JSON 배열만 출력. 설명 텍스트 없이.
5. abbr_long은 camelCase, abbr_short는 UPPER_SNAKE_CASE
6. categories는 아래 중 복수 선택:
   market, tool, infra, domain, order, risk, data, account,
   system, config, report, module, class, session, selector, status"""

USER_PROMPT_TMPL = """아래는 프로젝트 소스에서 추출한 용어 후보 목록입니다.
각 항목 형식: 용어명 | 출처

{candidates}

위 목록 중 terms.json에 추가해야 할 용어만 골라 아래 JSON 포맷으로 출력하세요.
설명 텍스트 없이 JSON 배열만 출력.

[
  {{
    "id": "snake_case_id",
    "ko": "한글명",
    "en": "English Name",
    "abbr_long": "camelCase",
    "abbr_short": "UPPER_SNAKE",
    "categories": ["category1"],
    "description": "설명"
  }}
]"""


def build_prompt(candidates: list[dict]) -> str:
    lines = []
    for c in candidates:
        src = c["sources"][0] if c["sources"] else "unknown"
        lines.append(f"{c['name']} | {src}")
    return USER_PROMPT_TMPL.format(candidates="\n".join(lines))


def estimate_tokens(text: str) -> int:
    """대략적인 토큰 수 추정 (문자수 / 3.5)."""
    return int(len(text) / 3.5)


# ════════════════════════════════════════════════════════════════════
# API 호출
# ════════════════════════════════════════════════════════════════════

def call_claude(prompt: str, api_key: str, max_tokens: int) -> str:
    import urllib.request
    body = json.dumps({
        "model":      "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "system":     SYSTEM_PROMPT,
        "messages":   [{"role": "user", "content": prompt}],
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data["content"][0]["text"]


def call_openai(prompt: str, api_key: str, max_tokens: int) -> str:
    import urllib.request
    body = json.dumps({
        "model":      "gpt-4o",
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": prompt},
        ],
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data["choices"][0]["message"]["content"]


def call_google(prompt: str, api_key: str, max_tokens: int) -> str:
    import urllib.request
    model = "gemini-1.5-pro"
    body  = json.dumps({
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }).encode('utf-8')

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data["candidates"][0]["content"]["parts"][0]["text"]


def call_api(prompt: str, env: dict, max_tokens: int) -> str:
    api_type = env.get("API_KEY_TYPE", "claude").lower()

    if api_type == "claude":
        key = env.get("ANTHROPIC_API_KEY","")
        if not key: raise ValueError("ANTHROPIC_API_KEY 가 .env에 없습니다")
        return call_claude(prompt, key, max_tokens)

    elif api_type == "openai":
        key = env.get("OPENAI_API_KEY","")
        if not key: raise ValueError("OPENAI_API_KEY 가 .env에 없습니다")
        return call_openai(prompt, key, max_tokens)

    elif api_type == "google":
        key = env.get("GOOGLE_API_KEY","")
        if not key: raise ValueError("GOOGLE_API_KEY 가 .env에 없습니다")
        return call_google(prompt, key, max_tokens)

    else:
        raise ValueError(f"지원하지 않는 API_KEY_TYPE: {api_type}")


# ════════════════════════════════════════════════════════════════════
# 결과 파싱
# ════════════════════════════════════════════════════════════════════

def parse_response(text: str) -> list[dict]:
    """API 응답에서 JSON 배열 추출."""
    # ```json ... ``` 블록 제거
    text = text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    # [ ... ] 범위만 추출
    start = text.find('[')
    end   = text.rfind(']') + 1
    if start == -1 or end == 0:
        return []

    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return []


# ════════════════════════════════════════════════════════════════════
# 결과 파일 저장
# ════════════════════════════════════════════════════════════════════

def save_result(terms: list[dict], proj_root: Path) -> Path:
    out_dir = proj_root / "tmp" / "terms"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts   = datetime.now().strftime("%Y%m%d_%H%M")
    path = out_dir / f"terms_{ts}.json"

    # terms.json 메타 포맷 동일하게
    result = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "description":  "batch_terms.py 자동 추출 결과 — glossary/terms.json 에 병합 전 검토 필요",
            "count":        len(terms),
        },
        "terms": terms,
    }
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


# ════════════════════════════════════════════════════════════════════
# 메인
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="용어 후보 → API 분석 → terms_날짜.json")
    parser.add_argument("--dry-run", action="store_true", help="API 미호출, 토큰 예상치만 출력")
    parser.add_argument("--chunk",   type=int, default=None, help="청크 크기 (기본: .env BATCH_CHUNK_SIZE)")
    parser.add_argument("--env",     default=None,           help=".env 경로 직접 지정")
    args = parser.parse_args()

    env = get_env()
    proj_root  = resolve_proj_root(BIN_DIR, env)
    chunk_size = args.chunk or int(env.get("BATCH_CHUNK_SIZE", 300))
    max_tokens = int(env.get("MAX_OUTPUT_TOKENS", 4000))

    # ── 스캔 ──────────────────────────────────────────────────────
    exclude_dirs = parse_list(env.get('EXCLUDE_DIRS',
        'backup,data,tests,lib_test,tmp,glossary,.git,__pycache__,node_modules,.venv,venv'))
    content_skip = parse_list(env.get('EXCLUDE_FILE_CONTENT', 'cache,doc,logs'))
    exclude_exts = {e if e.startswith('.') else f'.{e}'
                    for e in parse_list(env.get('EXCLUDE_EXTENSIONS', '.md,.txt,.log,.csv,.png,.jpg,.pdf'))}
    existing     = load_existing_terms(GLOSSARY_DIR)

    print(f"[1/3] 소스 스캔 중... ({proj_root})")
    scanner = TermScanner(proj_root, exclude_dirs, content_skip, exclude_exts, existing)
    scanner.scan()
    candidates = sorted(
        [{"name": c, "sources": scanner.sources.get(c,[])} for c in scanner.candidates],
        key=lambda x: x["name"]
    )
    print(f"      후보 {len(candidates)}개 추출됨")

    if not candidates:
        print("[완료] 추가할 신규 용어 후보가 없습니다.")
        return

    # ── 청크 분할 & 토큰 예상 ────────────────────────────────────
    n_chunks = math.ceil(len(candidates) / chunk_size)
    chunks   = [candidates[i*chunk_size:(i+1)*chunk_size] for i in range(n_chunks)]
    prompts  = [build_prompt(c) for c in chunks]
    est_in   = sum(estimate_tokens(SYSTEM_PROMPT + p) for p in prompts)
    est_out  = max_tokens * n_chunks

    print(f"\n[2/3] API 호출 계획")
    print(f"      API 종류     : {env.get('API_KEY_TYPE','claude').upper()}")
    print(f"      청크 수      : {n_chunks}개 ({chunk_size}개/청크)")
    print(f"      예상 입력    : ~{est_in:,} 토큰")
    print(f"      예상 출력(최대): ~{est_out:,} 토큰")
    print(f"      예상 합계    : ~{est_in+est_out:,} 토큰")

    if args.dry_run:
        print("\n[dry-run] API 호출 없이 종료합니다.")
        return

    confirm = input("\n계속 진행하시겠습니까? (y/N): ").strip().lower()
    if confirm != 'y':
        print("취소했습니다.")
        return

    # ── API 호출 ─────────────────────────────────────────────────
    print(f"\n[3/3] API 분석 중...")
    all_terms: list[dict] = []

    for i, (chunk, prompt) in enumerate(zip(chunks, prompts), 1):
        print(f"      청크 {i}/{n_chunks} 처리 중 ({len(chunk)}개)...", end=" ", flush=True)
        try:
            response = call_api(prompt, env, max_tokens)
            parsed   = parse_response(response)
            all_terms.extend(parsed)
            print(f"→ {len(parsed)}개 용어 추출")
        except Exception as e:
            print(f"→ 오류: {e}")

        if i < n_chunks:
            time.sleep(1)   # rate limit 여유

    # 중복 id 제거
    seen: set = set()
    deduped   = []
    for t in all_terms:
        tid = t.get("id","")
        if tid and tid not in seen:
            seen.add(tid)
            deduped.append(t)

    # ── 저장 ─────────────────────────────────────────────────────
    if deduped:
        out_path = save_result(deduped, proj_root)
        print(f"\n[완료] {len(deduped)}개 용어 → {out_path}")
        print(f"       웹 UI에서 검토 후 terms.json 에 병합하세요.")
    else:
        print("\n[완료] API 응답에서 추출된 용어가 없습니다.")


if __name__ == "__main__":
    main()
