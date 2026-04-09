#!/usr/bin/env python3
"""
scan_terms.py  —  프로젝트 소스 스캔 → 용어 후보 추출
위치: glossary/bin/scan_terms.py

역할:
  - 프로젝트 폴더를 순회하며 클래스명, 함수명, 변수명, DB 테이블/컬럼명,
    settings.yaml 키, .env 환경변수명을 추출
  - Claude API 호출 없이 순수 Python으로 동작 (토큰 절약)
  - 결과를 후보 목록(list[str])으로 반환 → batch_terms.py 가 API에 넘김

사용법:
  python scan_terms.py                    # 후보 출력
  python scan_terms.py --json             # JSON 형식 출력
  python scan_terms.py --count            # 후보 수만 출력
"""

import ast
import os
import re
import sys
import json
import argparse
import io
from pathlib import Path

# ── Windows 인코딩 안전 처리 ────────────────────────────────────────────
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding.lower() not in ('utf-8','utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── .env 로드 ───────────────────────────────────────────────────────────
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
    """PROJ_ROOT 환경변수 → 없으면 glossary 상위 폴더(=프로젝트 루트)."""
    if env.get('PROJ_ROOT'):
        p = Path(env['PROJ_ROOT'])
        if p.exists():
            return p.resolve()
    # glossary/bin/ → glossary/ → project/
    return bin_dir.parent.parent.resolve()


# ── 제외 설정 파싱 ──────────────────────────────────────────────────────
def parse_list(s: str) -> set:
    return {x.strip() for x in s.split(',') if x.strip()}


# ── 불용어 (항상 제외) ────────────────────────────────────────────────
SKIP_NAMES = {
    # Python 내장
    'self','cls','args','kwargs','None','True','False',
    'print','len','str','int','float','bool','list','dict','set','tuple',
    'range','open','type','super','isinstance','hasattr','getattr','setattr',
    'Exception','ValueError','TypeError','KeyError','IndexError',
    'os','sys','re','io','json','time','datetime','pathlib','logging',
    'Path','Optional','Union','List','Dict','Any','Tuple',
    # 흔한 지역 임시변수
    'i','j','k','n','m','x','y','z','v','t','s','p','q','r',
    'tmp','res','ret','err','e','ex','ok','val','buf','idx','key','line',
    'row','col','data','result','output','response','text','msg','name',
    'value','item','obj','ref','cls_','func','fn','cb','ctx',
    # 테스트/더미
    'test','mock','dummy','fixture','setUp','tearDown',
    # SQL 예약어
    'SELECT','FROM','WHERE','INSERT','UPDATE','DELETE','CREATE','TABLE',
    'INDEX','JOIN','LEFT','RIGHT','INNER','ON','AND','OR','NOT','IN',
    'NULL','PRIMARY','KEY','FOREIGN','REFERENCES','DEFAULT','CASCADE',
}

# 외부 라이브러리 루트 패키지명 (import 첫 토큰 기준)
EXTERNAL_LIBS = {
    'flask','fastapi','uvicorn','starlette',
    'sqlalchemy','alembic','psycopg2','asyncpg',
    'redis','aioredis',
    'pandas','numpy','scipy','sklearn','torch','tensorflow',
    'anthropic','openai','google',
    'pydantic','marshmallow',
    'pytest','unittest','mock',
    'yaml','toml','dotenv','environs',
    'click','typer','argparse','logging','pathlib',
    'datetime','collections','itertools','functools',
    'abc','enum','dataclasses','typing',
    'asyncio','threading','multiprocessing','subprocess',
    'requests','httpx','aiohttp','websockets',
    'celery','apscheduler',
}


# ════════════════════════════════════════════════════════════════════
# 스캐너
# ════════════════════════════════════════════════════════════════════

class TermScanner:
    def __init__(
        self,
        proj_root: Path,
        exclude_dirs: set,
        content_skip_dirs: set,
        exclude_exts: set,
        existing_terms: set,
    ):
        self.root            = proj_root
        self.exclude_dirs    = exclude_dirs
        self.content_skip    = content_skip_dirs   # 파일명만 보는 폴더
        self.exclude_exts    = exclude_exts
        self.existing        = existing_terms
        self.candidates: set = set()
        self.sources: dict   = {}   # candidate → 출처

    def _add(self, name: str, source: str):
        if not name or len(name) < 2:
            return
        if name in SKIP_NAMES:
            return
        if name.lower() in {x.lower() for x in EXTERNAL_LIBS}:
            return
        # 이미 등록된 용어면 건너뜀
        if name in self.existing:
            return
        # 순수 숫자, 대문자+숫자만(상수 제외 위해 최소 2자 이상 문자 포함)
        if re.fullmatch(r'[0-9_]+', name):
            return
        self.candidates.add(name)
        if name not in self.sources:
            self.sources[name] = []
        self.sources[name].append(source)

    def _should_skip_dir(self, rel: str) -> bool:
        parts = Path(rel).parts
        return bool(parts and parts[0] in self.exclude_dirs)

    def _content_skip_dir(self, rel: str) -> bool:
        parts = Path(rel).parts
        return bool(parts and parts[0] in self.content_skip)

    def scan(self):
        for dirpath, dirnames, filenames in os.walk(self.root):
            rel_dir = os.path.relpath(dirpath, self.root)

            # 완전 제외 폴더
            if self._should_skip_dir(rel_dir):
                dirnames.clear()
                continue

            # 숨김 폴더(.git 등) 제외
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]

            content_skip = self._content_skip_dir(rel_dir)

            for fname in filenames:
                fpath = Path(dirpath) / fname
                rel   = os.path.relpath(fpath, self.root)
                ext   = fpath.suffix.lower()

                # 파일명 스템 자체를 후보로
                stem = fpath.stem
                if stem and not stem.startswith('_'):
                    self._add(stem, f"filename:{rel}")

                if ext in self.exclude_exts or content_skip:
                    continue

                # 내용 스캔
                if ext == '.py':
                    self._scan_python(fpath, rel)
                elif ext in ('.yaml', '.yml'):
                    self._scan_yaml(fpath, rel)
                elif ext == '.env' or fname.startswith('.env'):
                    self._scan_env_file(fpath, rel)
                elif ext == '.sql':
                    self._scan_sql(fpath, rel)

        # 폴더명도 후보로
        for dirpath, dirnames, _ in os.walk(self.root):
            rel = os.path.relpath(dirpath, self.root)
            if self._should_skip_dir(rel):
                continue
            for d in dirnames:
                if not d.startswith('.') and d not in self.exclude_dirs:
                    self._add(d, f"dirname:{rel}")

    # ── Python AST 스캔 ─────────────────────────────────────────────
    def _scan_python(self, fpath: Path, rel: str):
        try:
            src  = fpath.read_text(encoding='utf-8', errors='replace')
            tree = ast.parse(src, filename=str(fpath))
        except SyntaxError:
            return

        for node in ast.walk(tree):
            # 클래스명
            if isinstance(node, ast.ClassDef):
                self._add(node.name, f"class:{rel}")

            # 함수/메서드명 (언더스코어 시작 제외)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith('_'):
                    self._add(node.name, f"func:{rel}")
                # 파라미터명 (self/cls 제외)
                for arg in node.args.args:
                    if arg.arg not in ('self','cls'):
                        self._add(arg.arg, f"param:{rel}:{node.name}")

            # 모듈/클래스 레벨 변수 (Assign, AnnAssign)
            elif isinstance(node, ast.Assign):
                # 클래스 또는 모듈 레벨인지는 부모 확인이 복잡하므로
                # 대문자 시작 상수 + 인스턴스 변수(self.) 만 뽑음
                for target in node.targets:
                    self._extract_assign_target(target, rel)

            elif isinstance(node, ast.AnnAssign):
                self._extract_assign_target(node.target, rel)

    def _extract_assign_target(self, target, rel: str):
        if isinstance(target, ast.Name):
            nm = target.id
            # 대문자 상수 또는 camelCase/snake_case 모듈 레벨
            if re.match(r'^[A-Z][A-Z0-9_]{2,}$', nm):   # 상수
                self._add(nm, f"const:{rel}")
        elif isinstance(target, ast.Attribute):
            # self.xxx → 인스턴스 변수
            if isinstance(target.value, ast.Name) and target.value.id == 'self':
                self._add(target.attr, f"attr:{rel}")

    # ── YAML 스캔 ───────────────────────────────────────────────────
    def _scan_yaml(self, fpath: Path, rel: str):
        try:
            import yaml
            with open(fpath, encoding='utf-8', errors='replace') as f:
                data = yaml.safe_load(f)
            self._walk_yaml(data, rel, [])
        except Exception:
            # yaml 없으면 정규식으로 키만 추출
            try:
                src = fpath.read_text(encoding='utf-8', errors='replace')
                for m in re.finditer(r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*):', src, re.MULTILINE):
                    self._add(m.group(2), f"yaml:{rel}")
            except Exception:
                pass

    def _walk_yaml(self, node, rel: str, path: list):
        if isinstance(node, dict):
            for k, v in node.items():
                self._add(str(k), f"yaml:{rel}:{'.'.join(path)}")
                self._walk_yaml(v, rel, path + [str(k)])
        elif isinstance(node, list):
            for item in node:
                self._walk_yaml(item, rel, path)

    # ── .env 스캔 ───────────────────────────────────────────────────
    def _scan_env_file(self, fpath: Path, rel: str):
        try:
            for line in fpath.read_text(encoding='utf-8', errors='replace').splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k = line.split('=', 1)[0].strip()
                if k:
                    self._add(k, f"env:{rel}")
        except Exception:
            pass

    # ── SQL 스캔 ────────────────────────────────────────────────────
    def _scan_sql(self, fpath: Path, rel: str):
        try:
            src = fpath.read_text(encoding='utf-8', errors='replace')
            # CREATE TABLE / CREATE INDEX
            for m in re.finditer(
                r'\b(CREATE\s+TABLE|CREATE\s+INDEX)\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
                src, re.IGNORECASE
            ):
                self._add(m.group(2), f"sql_table:{rel}")
            # 컬럼명: 단어 다음 데이터타입 패턴
            for m in re.finditer(
                r'^\s+(\w+)\s+(?:INTEGER|BIGINT|TEXT|VARCHAR|BOOLEAN|TIMESTAMP|FLOAT|NUMERIC|SERIAL|UUID)',
                src, re.IGNORECASE | re.MULTILINE
            ):
                self._add(m.group(1), f"sql_col:{rel}")
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════════
# 기존 terms.json 로드
# ════════════════════════════════════════════════════════════════════

def load_existing_terms(glossary_dir: Path) -> set:
    tj = glossary_dir / "terms.json"
    if not tj.exists():
        return set()
    try:
        data = json.loads(tj.read_text(encoding='utf-8'))
        existing = set()
        for t in data.get("terms", []):
            existing.add(t.get("id",""))
            existing.add(t.get("abbr_long",""))
            existing.add(t.get("abbr_short",""))
            existing.add(t.get("en",""))
            existing.add(t.get("ko",""))
        return existing
    except Exception:
        return set()


# ════════════════════════════════════════════════════════════════════
# 메인
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="프로젝트 소스 → 용어 후보 추출")
    parser.add_argument("--json",   action="store_true", help="JSON 형식 출력")
    parser.add_argument("--count",  action="store_true", help="후보 수만 출력")
    parser.add_argument("--env",    default=None,        help=".env 파일 경로 직접 지정")
    args = parser.parse_args()

    bin_dir = Path(__file__).parent.resolve()
    glossary_dir = bin_dir.parent.resolve()

    # .env 로드
    env_path = Path(args.env) if args.env else None
    if env_path is None:
        # glossary 상위(프로젝트 루트)에서 .env 찾기
        env_path = glossary_dir.parent / ".env"
        if not env_path.exists():
            env_path = glossary_dir / ".env"

    env = load_env(env_path)
    proj_root = resolve_proj_root(bin_dir, env)

    exclude_dirs     = parse_list(env.get('EXCLUDE_DIRS',
        'backup,data,tests,tmp,glossary,.git,__pycache__,node_modules,.venv,venv'))
    content_skip     = parse_list(env.get('EXCLUDE_FILE_CONTENT', 'cache,doc,logs'))
    exclude_exts_raw = parse_list(env.get('EXCLUDE_EXTENSIONS', '.md,.txt,.log,.csv,.png,.jpg,.pdf'))
    exclude_exts     = {e if e.startswith('.') else f'.{e}' for e in exclude_exts_raw}

    existing = load_existing_terms(glossary_dir)

    scanner = TermScanner(proj_root, exclude_dirs, content_skip, exclude_exts, existing)
    scanner.scan()

    candidates = sorted(scanner.candidates)

    if args.count:
        print(len(candidates))
        return

    if args.json:
        result = {
            "proj_root":   str(proj_root),
            "count":       len(candidates),
            "candidates":  [
                {"name": c, "sources": scanner.sources.get(c, [])}
                for c in candidates
            ]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[scan] 프로젝트 루트: {proj_root}")
        print(f"[scan] 후보 {len(candidates)}개\n")
        for c in candidates:
            src = scanner.sources.get(c, [])
            print(f"  {c:<40} {src[0] if src else ''}")


if __name__ == "__main__":
    main()
