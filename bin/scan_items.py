#!/usr/bin/env python3
"""
scan_items.py  —  BOM_TS 프로젝트 소스 스캔 → word/term 후보 추출
위치: glossary/bin/scan_items.py

모드: 
  --mode word (기본값) : 식별자를 Tokenize하여 단일 영단어 추출
  --mode term : 기존 식별자 원형 추출 (하위 호환)

규칙:
  1. 단어 토큰 최소 길이 3 이상.
  2. 너무 일반적인 동사 (get, set, run, do) 제외.
  3. api_, kis_, env_ 와 같은 기술적 접두어 포함된 경우 제외.
  4. 숫자/해시 제외.
"""

import ast
import os
import re
import sys
import json
import argparse
import io
from pathlib import Path

# Add project root to sys.path
bin_dir = Path(__file__).resolve().parent
proj_root = bin_dir.parent.parent
if str(proj_root) not in sys.path:
    sys.path.insert(0, str(proj_root))

from glossary.core.token_rules import (
    is_managed_identifier,
    is_unit_token,
    is_tech_abbreviation,
    check_dictionary_api,
    auto_draft_dictionary_word
)

# ── Windows 인코딩 ──────────────────────────────────────────────────────
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding.lower() not in ('utf-8','utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def load_env(env_path: Path) -> dict:
    env = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding='utf-8', errors='replace').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, _, v = line.partition('=')
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def resolve_proj_root(bin_dir: Path, env: dict) -> Path:
    if env.get('PROJ_ROOT'):
        p = Path(env['PROJ_ROOT'])
        if p.exists():
            return p.resolve()
    return bin_dir.parent.parent.resolve()

def parse_list(s: str) -> set:
    return {x.strip() for x in s.split(',') if x.strip()}

DOMAIN_DOC_DIR_PATTERNS = re.compile(
    r'^(kr|us|fx|crypto|coin|kospi|kosdaq'
    r'|kis|kiwoom|upbit|mt5|binance'
    r'|stock|market|order|signal|risk|selector'
    r'|account|position|trade|execution'
    r'|collector|scanner|strategy|backtest'
    r'|session|config|setting)$',
    re.IGNORECASE,
)

_NOISE_RE = re.compile(
    r'^[0-9]'                        # 숫자 시작
    r'|^[a-f0-9]{7,}$'              # git 해시
    r'|\d{4}[-_]\d{2}[-_]\d{2}'     # 날짜 포함
    r'|T\d{2}[:\-]\d{2}'            # 타임스탬프
    r'|\.\d+[Zz]$'                  # .Z
    r'|^v\d+[\.\-]\d+'              # 버전
    r'|^(?:y{2,4}|m{2}|d{2}|h{2}|s{2})+$' # 날짜/시간 포맷 문자열 (yyyymmdd, hhmmss 등)
)

MIN_LEN_TERM = 4

SKIP_NAMES: set = {
    # 향후 제외할 범용어 추가용 (유저 요청에 의해 초기화)
}

EXTERNAL_LIBS: set = {
    'flask','fastapi','uvicorn','starlette','werkzeug',
    'sqlalchemy','alembic','psycopg2','asyncpg','aiopg',
    'redis','aioredis','celery','kombu',
    'pandas','numpy','scipy','sklearn','torch','tensorflow','keras',
    'pydantic','pytest','unittest','hypothesis','yaml','toml','dotenv',
    'asyncio','threading','requests','httpx','aiohttp','websockets','grpc',
    'apscheduler','schedule','croniter','cryptography','jwt','bcrypt',
}

def _split_tokens(name: str) -> list:
    """camelCase / snake_case → 소문자 토큰 목록. 숫자는 분리하여 처리."""
    s = name.replace('_', ' ').replace('-', ' ')
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', s)
    tokens = []
    for t in s.split():
        for chunk in re.findall(r"[A-Za-z]+|\d+", t):
            if chunk:
                tokens.append(chunk.lower())
    return tokens

def auto_plural(word_id: str) -> str:
    if word_id.endswith(('s', 'sh', 'ch', 'x', 'z')):
        return word_id + 'es'
    if word_id.endswith('y') and len(word_id) > 1 and word_id[-2] not in 'aeiou':
        return word_id[:-1] + 'ies'
    return word_id + 's'

def _is_noise_word(word: str) -> bool:
    if word in SKIP_NAMES: return True
    if word in EXTERNAL_LIBS: return True
    if _NOISE_RE.search(word): return True
    if re.fullmatch(r'[0-9_\-\.]+', word): return True
    if len(set(word)) == 1: return True
    return False

def _is_noise_term(name: str) -> bool:
    clean = name.strip('_').lower()
    if len(name) < MIN_LEN_TERM: return True
    if clean in SKIP_NAMES: return True
    if clean in EXTERNAL_LIBS: return True
    if _NOISE_RE.search(clean): return True
    if re.fullmatch(r'[0-9_\-\.]+', clean): return True
    if len(set(clean)) == 1: return True
    return False

def load_existing_words_and_tokens(glossary_dir: Path) -> set:
    """words.json, compounds.json, words__derived_terms.json surface를 읽어
    이미 등록된 토큰 집합을 반환한다. scan 시 이 집합에 속한 토큰은 후보에서 제외된다.

    변경 이력:
    - v1.0: words.id + auto_plural only
    - v1.1: variants가 list[dict]로 변경됨을 반영, derived_terms surface 추가
    """
    dict_dir = glossary_dir / "dictionary"
    tokens: set = set()

    words_path = dict_dir / "words.json"
    if words_path.exists():
        try:
            data = json.loads(words_path.read_text(encoding='utf-8'))
            for w in data.get("words", []):
                wid = w.get('id', '').lower()
                if wid:
                    tokens.add(wid)
                    for tok in _split_tokens(wid):
                        tokens.add(tok)

                # variants: list[{type, value|short}] 구조 처리
                for v in w.get('variants', []):
                    val = (v.get('value') or v.get('short') or '').strip().lower()
                    if val:
                        tokens.add(val)

                # auto_plural: noun이고 variants에 plural이 없으면 자동 추가
                has_plural = any(
                    v.get('type') == 'plural' for v in w.get('variants', [])
                )
                if not has_plural and w.get('canonical_pos') == 'noun' and wid:
                    tokens.add(auto_plural(wid))
                    
                # top-level abbreviation
                if 'abbreviation' in w and isinstance(w['abbreviation'], dict):
                    abbr_short = (w['abbreviation'].get('short') or '').strip().lower()
                    if abbr_short:
                        tokens.add(abbr_short)
        except Exception:
            pass

    comp_path = dict_dir / "compounds.json"
    if comp_path.exists():
        try:
            data = json.loads(comp_path.read_text(encoding='utf-8'))
            for c in data.get("compounds", []):
                cid = c.get('id', '').lower()
                if cid:
                    tokens.add(cid)
                    for tok in _split_tokens(cid):
                        tokens.add(tok)
                        
                # variants: list[{type, value|short}] 구조 처리
                for v in c.get('variants', []):
                    val = (v.get('value') or v.get('short') or '').strip().lower()
                    if val:
                        tokens.add(val)
                        
                # top-level abbreviation (legacy)
                if 'abbreviation' in c and isinstance(c['abbreviation'], dict):
                    abbr_short = (c['abbreviation'].get('short') or '').strip().lower()
                    if abbr_short:
                        tokens.add(abbr_short)
        except Exception:
            pass

    # words__derived_terms.json: surface를 모두 exclusion에 추가
    # (variants, synonym surface 포함 — 이미 관계가 파악된 단어들)
    derived_path = dict_dir / "words__derived_terms.json"
    if derived_path.exists():
        try:
            data = json.loads(derived_path.read_text(encoding='utf-8'))
            for item in data.get("items", []):
                s = item.get('surface', '').strip().lower()
                if s and ' ' not in s and '_' not in s:
                    tokens.add(s)
        except Exception:
            pass

    # terms.json 폴백 (tokens가 비어있을 때만)
    term_path = dict_dir / "terms.json"
    if not tokens and term_path.exists():
        try:
            data = json.loads(term_path.read_text(encoding='utf-8'))
            for t in data.get("terms", []):
                for tok in _split_tokens(t.get('id', '')):
                    tokens.add(tok)
        except Exception:
            pass

    return tokens

def load_existing_terms(glossary_dir: Path) -> set:
    syms = set()
    dict_dir = glossary_dir / "dictionary"

    for fname in ["words.json", "compounds.json", "terms.json"]:
        path = dict_dir / fname
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                key = fname.split('.')[0]
                for item in data.get(key, []):
                    syms.add(item.get('id', '').lower())
            except Exception:
                pass
    return syms


def load_scan_config(glossary_dir: Path) -> dict:
    """
    .scan_list 와 .scan_ignore 파일을 읽어 스캔 설정을 반환한다.

    반환 구조:
      {
        'scan_dirs':  ['config', 'script', 'src'],   # dir: 항목
        'root_patterns': ['.env*', 'run*.py'],        # root: 항목
        'ignore_dirs':   {'__pycache__'},             # dir: 항목
        'ignore_exts':   {'.md'},                    # ext: 항목
        'ignore_patterns': ['.git*'],                 # pattern: 항목
      }
    제외 규칙이 없으면 scan_list가 통째로 신뢰된다.
    두 파일이 없으면 None을 반환 (기존 EXCLUDE_DIRS 방식 폴백).
    """
    scan_list_path   = glossary_dir / ".scan_list"
    scan_ignore_path = glossary_dir / ".scan_ignore"

    if not scan_list_path.exists() and not scan_ignore_path.exists():
        return {}

    cfg: dict = {
        'scan_dirs': [],
        'root_patterns': [],
        'ignore_dirs': set(),
        'ignore_exts': set(),
        'ignore_patterns': [],
    }

    if scan_list_path.exists():
        for raw in scan_list_path.read_text(encoding='utf-8').splitlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('dir:'):
                cfg['scan_dirs'].append(line[4:].strip())
            elif line.startswith('root:'):
                cfg['root_patterns'].append(line[5:].strip())

    if scan_ignore_path.exists():
        for raw in scan_ignore_path.read_text(encoding='utf-8').splitlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('dir:'):
                cfg['ignore_dirs'].add(line[4:].strip())
            elif line.startswith('ext:'):
                ext = line[4:].strip()
                if not ext.startswith('.'):
                    ext = '.' + ext
                cfg['ignore_exts'].add(ext)
            elif line.startswith('pattern:'):
                cfg['ignore_patterns'].append(line[8:].strip())

    return cfg


import fnmatch

def _matches_ignore_pattern(name: str, patterns: list) -> bool:
    """파일명이 .scan_ignore의 pattern: 목록과 하나라도 일치하면 True."""
    for pat in patterns:
        if fnmatch.fnmatch(name, pat):
            return True
    return False


class ItemScanner:
    def __init__(
        self,
        proj_root: Path,
        exclude_dirs: set,
        content_skip: set,
        exclude_exts: set,
        mode: str,
        existing_items: set,
        yaml_depth: int = 2,
        scan_config: dict | None = None,
    ):
        self.root = proj_root
        self.exclude_dirs = exclude_dirs
        self.content_skip = content_skip
        self.exclude_exts = exclude_exts
        self.mode = mode
        self.existing = existing_items
        self.yaml_depth = yaml_depth
        self.scan_config = scan_config or {}

        self.candidates_count: dict = {}
        self.candidates_sources: dict = {}

    def _add(self, name: str, source: str):
        if not is_managed_identifier(name): return

        if self.mode == "word":
            nl = name.lower()
            if nl.startswith(('api_', 'kis_', 'env_')): return

            tokens = _split_tokens(name)
            for t in tokens:
                # single-char tokens are code prefixes (v_align, n_count), not domain terms
                if len(t) <= 1: continue
                if _is_noise_word(t): continue
                if is_unit_token(t): continue
                if is_tech_abbreviation(t): continue

                if t in self.existing: continue

                # Look up dictionary
                is_valid, meaning = check_dictionary_api(t)
                if is_valid:
                    auto_draft_dictionary_word(t, meaning)
                    continue

                # Not in glossary, not in dict, not a unit token -> if it's 2 chars, it's noise/excluded
                if len(t) <= 2:
                    continue

                self.candidates_count[t] = self.candidates_count.get(t, 0) + 1
                if t not in self.candidates_sources: self.candidates_sources[t] = []
                if len(self.candidates_sources[t]) < 5:
                    self.candidates_sources[t].append(source)
        else:
            name = name.strip('_')
            if _is_noise_term(name): return
            if name.lower() in self.existing: return
            
            self.candidates_count[name] = self.candidates_count.get(name, 0) + 1
            if name not in self.candidates_sources: self.candidates_sources[name] = []
            if len(self.candidates_sources[name]) < 5:
                self.candidates_sources[name].append(source)

    def _top(self, rel: str) -> str:
        parts = Path(rel).parts
        return parts[0] if parts and rel != '.' else ''

    def scan(self):
        """
        .scan_list가 정의되어 있으면 해당 설정을 기준으로 스캔한다.
        - scan_dirs 에 있는 폴더만 재귀 스캔
        - root_patterns 에 맞는 루트 파일만 스캔
        - ignore_dirs / ignore_exts / ignore_patterns 규칙이 항상 우선
        .scan_list가 없으면 기존 exclude_dirs 기반 전체 스캔으로 폴백.
        """
        cfg = self.scan_config
        has_scan_list = bool(cfg.get('scan_dirs') or cfg.get('root_patterns'))

        if has_scan_list:
            self._scan_with_config(cfg)
        else:
            self._scan_legacy()

    def _should_ignore_file(self, fpath: Path, cfg: dict) -> bool:
        """개별 파일이 ignore 규칙에 해당하면 True."""
        fname = fpath.name
        ext   = fpath.suffix.lower()
        if ext in cfg.get('ignore_exts', set()):        return True
        if _matches_ignore_pattern(fname, cfg.get('ignore_patterns', [])): return True
        return False

    def _should_ignore_dir(self, dname: str, cfg: dict) -> bool:
        """폴더 이름이 ignore 규칙에 해당하면 True."""
        if dname in cfg.get('ignore_dirs', set()):      return True
        if _matches_ignore_pattern(dname, cfg.get('ignore_patterns', [])): return True
        return False

    def _scan_with_config(self, cfg: dict):
        """scan_dirs + root_patterns 기반 스캔."""
        # 1. root_patterns: 루트 디렉토리의 파일만 glob
        for pat in cfg.get('root_patterns', []):
            for fpath in sorted(self.root.glob(pat)):
                if not fpath.is_file(): continue
                if self._should_ignore_file(fpath, cfg): continue
                rel = str(fpath.relative_to(self.root))
                self._scan_file(fpath, rel, cfg)

        # 2. scan_dirs: 지정된 폴더만 재귀 스캔
        for target_dir in cfg.get('scan_dirs', []):
            target_path = self.root / target_dir
            if not target_path.exists() or not target_path.is_dir():
                continue
            for dirpath, dirnames, filenames in os.walk(target_path):
                # ignore_dirs 적용 (in-place 수정)
                dirnames[:] = [
                    d for d in dirnames
                    if not self._should_ignore_dir(d, cfg)
                ]
                for fname in filenames:
                    fpath = Path(dirpath) / fname
                    if self._should_ignore_file(fpath, cfg): continue
                    rel = str(fpath.relative_to(self.root))
                    self._scan_file(fpath, rel, cfg)

    def _scan_file(self, fpath: Path, rel: str, cfg: dict):
        """단일 파일 스캔 — 확장자별 분기."""
        ext = fpath.suffix.lower()
        ignore_exts = cfg.get('ignore_exts', set()) | self.exclude_exts

        if ext == '.md': return  # .md 는 항상 제외
        if ext == '.py':
            stem = fpath.stem
            if stem and not stem.startswith('_') and not stem.startswith('test'):
                self._add(stem, f"py_file:{rel}")

        if ext in ignore_exts: return

        if ext == '.py':
            self._scan_python(fpath, rel)
        elif ext in ('.yaml', '.yml'):
            self._scan_yaml(fpath, rel)
        elif fpath.name.startswith('.env'):
            self._scan_env_file(fpath, rel)
        elif ext == '.sql':
            self._scan_sql(fpath, rel)

    def _scan_legacy(self):
        """기존 exclude_dirs 기반 전체 스캔 (scan_list 없을 때 폴백)."""
        for dirpath, dirnames, filenames in os.walk(self.root):
            rel_dir = os.path.relpath(dirpath, self.root)
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in self.exclude_dirs]

            top = self._top(rel_dir)
            if top in self.exclude_dirs or top.startswith('.'):
                dirnames.clear()
                continue

            skip_content = top in self.content_skip
            if top == 'doc':
                for d in dirnames:
                    if DOMAIN_DOC_DIR_PATTERNS.match(d):
                        self._add(d, f"doc_dir:{rel_dir}/{d}")
                continue

            for fname in filenames:
                fpath = Path(dirpath) / fname
                rel = os.path.relpath(fpath, self.root)
                ext = fpath.suffix.lower()

                if ext == '.md': continue
                if ext == '.py':
                    stem = fpath.stem
                    if stem and not stem.startswith('_') and not stem.startswith('test'):
                        self._add(stem, f"py_file:{rel}")

                if skip_content or ext in self.exclude_exts: continue

                if ext == '.py':
                    self._scan_python(fpath, rel)
                elif ext in ('.yaml', '.yml'):
                    self._scan_yaml(fpath, rel)
                elif fname.startswith('.env'):
                    self._scan_env_file(fpath, rel)
                elif ext == '.sql':
                    self._scan_sql(fpath, rel)


    def _scan_python(self, fpath: Path, rel: str):
        try:
            src = fpath.read_text(encoding='utf-8', errors='replace')
            tree = ast.parse(src, filename=str(fpath))
        except SyntaxError: return

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._add(node.name, f"class:{rel}")
                # 클래스 레벨의 속성 추출 (Dataclass, Pydantic fields 등)
                for child in node.body:
                    if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                        attr = child.target.id.lstrip('_')
                        if attr: self._add(attr, f"attr:{rel}")
                    elif isinstance(child, ast.Assign):
                        for tgt in child.targets:
                            if isinstance(tgt, ast.Name):
                                attr = tgt.id.lstrip('_')
                                if attr: self._add(attr, f"attr:{rel}")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith('_'): self._add(node.name, f"func:{rel}")
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = [node.target] if isinstance(node, ast.AnnAssign) else node.targets
                for target in targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                        attr = target.attr.lstrip('_')
                        if attr: self._add(attr, f"attr:{rel}")

    def _scan_yaml(self, fpath: Path, rel: str):
        try:
            import yaml
            with open(fpath, encoding='utf-8', errors='replace') as f:
                data = yaml.safe_load(f)
            self._walk_yaml(data, rel, depth=0)
        except Exception: pass

    def _walk_yaml(self, node, rel: str, depth: int):
        if depth > self.yaml_depth: return
        if isinstance(node, dict):
            for k, v in node.items():
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', str(k)):
                    self._add(str(k), f"yaml:{rel}")
                self._walk_yaml(v, rel, depth + 1)
        elif isinstance(node, list):
            for item in node: self._walk_yaml(item, rel, depth)

    def _scan_env_file(self, fpath: Path, rel: str):
        try:
            for line in fpath.read_text(encoding='utf-8', errors='replace').splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k = line.split('=', 1)[0].strip()
                    if re.match(r'^[A-Z][A-Z0-9_]+$', k): self._add(k, f"env:{rel}")
        except Exception: pass

    def _scan_sql(self, fpath: Path, rel: str):
        try:
            src = fpath.read_text(encoding='utf-8', errors='replace')
            for m in re.finditer(r'\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', src, re.IGNORECASE):
                self._add(m.group(1), f"sql_table:{rel}")
        except Exception: pass

def main():
    parser = argparse.ArgumentParser(description="프로젝트 소스 → 용어 후보 추출")
    parser.add_argument("--mode", choices=["word", "term"], default="word", help="스캔 기준 (word: 단어, term: 식별자 원형)")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    parser.add_argument("--count", action="store_true", help="후보 수만 출력")
    args = parser.parse_args()

    bin_dir = Path(__file__).parent.resolve()
    glossary_dir = bin_dir.parent.resolve()

    env_path = glossary_dir.parent / ".env"
    if not env_path.exists(): env_path = glossary_dir / ".env"
    env = load_env(env_path)
    proj_root = resolve_proj_root(bin_dir, env)

    scan_config = load_scan_config(glossary_dir)
    exclude_dirs = parse_list(env.get('EXCLUDE_DIRS', 'backup,data,test,lib_test,tmp,glossary,.git,__pycache__,node_modules,.venv,venv'))
    content_skip = parse_list(env.get('EXCLUDE_FILE_CONTENT', 'cache,log'))
    exclude_exts = {e if e.startswith('.') else f'.{e}' for e in parse_list(env.get('EXCLUDE_EXTENSIONS', '.md,.txt,.log,.csv,.tsv,.png,.jpg,.jpeg,.gif,.pdf,.ico,.svg,.zip,.tar'))}

    if args.mode == "word":
        existing = load_existing_words_and_tokens(glossary_dir)
    else:
        existing = load_existing_terms(glossary_dir)

    scanner = ItemScanner(proj_root, exclude_dirs, content_skip, exclude_exts, args.mode, existing,
                          scan_config=scan_config)
    scanner.scan()

    results = []
    for k in sorted(scanner.candidates_count.keys()):
        results.append({
            "name": k if args.mode == "term" else k,
            "word": k if args.mode == "word" else k,
            "count": scanner.candidates_count[k],
            "sources": scanner.candidates_sources[k]
        })

    if args.count:
        print(len(results))
        return

    if args.json:
        out = {
            "proj_root": str(proj_root),
            "count": len(results),
            "mode": args.mode,
            "candidates": results,
            "words": results if args.mode == "word" else []
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"[scan_items] 모드: {args.mode}")
        print(f"[scan_items] 후보: {len(results)}개\n")
        for item in results[:20]:
            print(f"  {item['name']:<30} (count: {item['count']}) - {item['sources'][0]}")
        if len(results) > 20:
            print(f"  ... 외 {len(results)-20}개")

if __name__ == "__main__":
    main()
