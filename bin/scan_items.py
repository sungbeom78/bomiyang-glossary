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
)

MIN_LEN_TERM = 4
MIN_LEN_WORD = 3

SKIP_NAMES: set = {
    'self','cls','args','kwargs','none','true','false',
    'print','len','str','int','float','bool','list','dict','set','tuple',
    'exception','valueerror','typeerror','keyerror','indexerror',
    'path','optional','union','list','dict','any','tuple','set','callable',
    'result','output','response','message','content','body','payload',
    'config','params','options','headers','timeout','retry','callback',
    'flag','mode','state','phase','stage','step','level',
    'get','set','add','remove','delete','clear','reset','init','load',
    'run','do','make',
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
    """camelCase / snake_case → 소문자 토큰 목록."""
    s = name.replace('_', ' ').replace('-', ' ')
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', s)
    return [t.lower() for t in s.split() if len(t) >= MIN_LEN_WORD]

def auto_plural(word_id: str) -> str:
    if word_id.endswith(('s', 'sh', 'ch', 'x', 'z')):
        return word_id + 'es'
    if word_id.endswith('y') and len(word_id) > 1 and word_id[-2] not in 'aeiou':
        return word_id[:-1] + 'ies'
    return word_id + 's'

def _is_noise_word(word: str) -> bool:
    if len(word) < MIN_LEN_WORD: return True
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
    """words.json, compounds.json 을 읽어서 토큰 단위 집합만 반환"""
    dict_dir = glossary_dir / "dictionary"
    tokens: set = set()
    
    words_path = dict_dir / "words.json"
    if words_path.exists():
        try:
            data = json.loads(words_path.read_text(encoding='utf-8'))
            for w in data.get("words", []):
                for tok in _split_tokens(w.get('id', '')): tokens.add(tok)
                if w.get('variants', {}).get('plural') not in (None, '-'):
                    tokens.add(w['variants']['plural'])
                elif w.get('variants', {}).get('plural') is None and w.get('canonical_pos') == 'noun':
                    tokens.add(auto_plural(w.get('id', '')))
        except Exception: pass

    comp_path = dict_dir / "compounds.json"
    if comp_path.exists():
        try:
            data = json.loads(comp_path.read_text(encoding='utf-8'))
            for c in data.get("compounds", []):
                for tok in _split_tokens(c.get('id', '')): tokens.add(tok)
        except Exception: pass
        
    term_path = dict_dir / "terms.json"
    if not tokens and term_path.exists():
        try:
            data = json.loads(term_path.read_text(encoding='utf-8'))
            for t in data.get("terms", []):
                for tok in _split_tokens(t.get('id', '')): tokens.add(tok)
        except Exception: pass

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
            except Exception: pass
    return syms

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
    ):
        self.root = proj_root
        self.exclude_dirs = exclude_dirs
        self.content_skip = content_skip
        self.exclude_exts = exclude_exts
        self.mode = mode
        self.existing = existing_items
        self.yaml_depth = yaml_depth
        
        self.candidates_count: dict = {}
        self.candidates_sources: dict = {}

    def _add(self, name: str, source: str):
        if self.mode == "word":
            # tech 접두어 제외 로직
            nl = name.lower()
            if nl.startswith(('api_', 'kis_', 'env_')): return
            
            tokens = _split_tokens(name)
            for t in tokens:
                if _is_noise_word(t): continue
                if t in self.existing or t.endswith('s') and t[:-1] in self.existing: continue
                
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

    exclude_dirs = parse_list(env.get('EXCLUDE_DIRS', 'backup,data,test,lib_test,tmp,glossary,.git,__pycache__,node_modules,.venv,venv'))
    content_skip = parse_list(env.get('EXCLUDE_FILE_CONTENT', 'cache,log'))
    exclude_exts = {e if e.startswith('.') else f'.{e}' for e in parse_list(env.get('EXCLUDE_EXTENSIONS', '.md,.txt,.log,.csv,.tsv,.png,.jpg,.jpeg,.gif,.pdf,.ico,.svg,.zip,.tar'))}

    if args.mode == "word":
        existing = load_existing_words_and_tokens(glossary_dir)
    else:
        existing = load_existing_terms(glossary_dir)

    scanner = ItemScanner(proj_root, exclude_dirs, content_skip, exclude_exts, args.mode, existing)
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
