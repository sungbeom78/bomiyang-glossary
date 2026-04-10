#!/usr/bin/env python3
"""
scan_terms.py v2  —  BOM_TS 프로젝트 소스 스캔 → 용어 후보 추출
위치: glossary/bin/scan_terms.py

사전 기준:
  glossary/dictionary/words.json     (단어 원자 단위)
  glossary/dictionary/compounds.json (복합어)
  glossary/dictionary/terms.json     (fallback, 자동 생성)

== 스캔 대상 / 제외 규칙 ==

[완전 제외 폴더]  — 내용도 파일명도 안 봄
  backup/, data/, test/, tmp/, glossary/
  .* (숨김 폴더: .git, .omx 등 모두)
  EXCLUDE_DIRS 환경변수로 추가 가능
  ※ AGENTS.md Rule 8-A: 폴더명은 단수형 강제

[파일명만 보는 폴더]  — 내용 스캔 없음, 폴더명만 도메인 여부 판단
  cache/, log/
  EXCLUDE_FILE_CONTENT 환경변수로 지정

[doc/ 폴더 특별 규칙]
  - *.md 파일명 → 완전 무시 (자연어 제목이므로)
  - 폴더명 → 도메인 관련성 있는 것만 후보 (DOMAIN_DOC_DIR_PATTERNS 참고)
  - 내용(본문 텍스트) → 스캔 안 함

[스캔 대상]
  .py   : 클래스명, public 함수명(def), self.속성명
          ※ 파라미터명 제외 — 구현 상세이므로
          ※ 함수 바디 내 지역변수 제외
  .yaml : 상위 2단계 키만 (깊은 중첩은 구현 상세)
  .env  : 환경변수명(키)만
  .sql  : CREATE TABLE 테이블명, 컬럼명

[파일명 스캔]
  .py 파일 스템 → 후보 (예: kis_adapter.py → kis_adapter)
  기타 확장자 파일명 → 제외
  *.md 파일명 → 제외 (자연어 문서 제목)

[후보 등록 기준]
  1. 최소 4자 이상
  2. 숫자/타임스탬프/해시로 시작하는 것 제외
  3. 불용어 제외 (Python 내장, 범용 동사, 외부 라이브러리)
  4. dictionary/words.json + compounds.json 에 등록된 심볼 제외
  5. 복합어 분해 시 모든 토큰이 이미 등록된 경우 제외
     예) kisApiToken = kis + api + token → 모두 등록됨 → 제외

[규칙 준수]
  AGENTS.md Rule 8-B: 신규 식별자 생성 전 glossary 검증 필수
    python glossary/generate_glossary.py check-id <식별자>
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

# ════════════════════════════════════════════════════════════════════
# .env / 경로 헬퍼
# ════════════════════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════════════════════
# doc/ 폴더 중 도메인 관련성 있는 하위 폴더명 패턴
# — 이 패턴에 매치되는 폴더명만 후보로 등록
# ════════════════════════════════════════════════════════════════════

DOMAIN_DOC_DIR_PATTERNS = re.compile(
    r'^(kr|us|fx|crypto|coin|kospi|kosdaq'
    r'|kis|kiwoom|upbit|mt5|binance'
    r'|stock|market|order|signal|risk|selector'
    r'|account|position|trade|execution'
    r'|collector|scanner|strategy|backtest'
    r'|session|config|setting)$',
    re.IGNORECASE,
)


# ════════════════════════════════════════════════════════════════════
# 노이즈 필터
# ════════════════════════════════════════════════════════════════════

_NOISE_RE = re.compile(
    r'^[0-9]'                        # 숫자 시작
    r'|^[a-f0-9]{7,}$'              # git 해시
    r'|\d{4}[-_]\d{2}[-_]\d{2}'     # 날짜 포함 (2026-04-06 등)
    r'|T\d{2}[:\-]\d{2}'            # ISO 타임스탬프
    r'|\.\d+[Zz]$'                  # .387Z 말미
    r'|^v\d+[\.\-]\d+'              # 버전 v1.2
)

MIN_LEN = 4   # 최소 4자

SKIP_NAMES: set = {
    # Python 내장 타입·함수
    'self','cls','args','kwargs','None','True','False',
    'print','len','str','int','float','bool','list','dict','set','tuple',
    'range','open','type','super','isinstance','hasattr','getattr','setattr',
    'Exception','ValueError','TypeError','KeyError','IndexError','AttributeError',
    'RuntimeError','StopIteration','NotImplementedError',
    'os','sys','re','io','json','time','datetime','pathlib','logging','math',
    'Path','Optional','Union','List','Dict','Any','Tuple','Set','Callable',
    'ClassVar','Final','Literal','TypeVar','Generic','Protocol',
    'property','staticmethod','classmethod','abstractmethod',
    # 구현 상세 — 범용 변수
    'result','output','response','message','content','body','payload',
    'config','params','options','headers','timeout','retry','callback',
    'handler','wrapper','context','event','listener','observer',
    'logger','client','server','session','connection','cursor',
    'loop','queue','channel','topic','stream','buffer','chunk',
    'start','end','begin','finish','done','ready','active','enabled',
    'count','total','size','length','width','height','limit','offset',
    'index','pos','prev','next','curr','last','first',
    'flag','mode','state','phase','stage','step','level',
    'base','root','parent','child','node','leaf','tree',
    'path','url','host','port','addr','ip','uri',
    'name','label','title','desc','note','tag',
    'created','updated','deleted','modified','timestamp',
    'version','build','release','revision',
    # 범용 동사 — 단독으로 용어 아님
    'get','set','add','remove','delete','clear','reset','init','load',
    'save','read','write','send','receive','fetch','push','pull','sync',
    'run','stop','pause','resume','cancel','abort','close','lock','unlock',
    'check','validate','verify','parse','format','encode','decode',
    'encrypt','decrypt','hash','sign','connect','disconnect',
    'subscribe','publish','notify','trigger','execute','invoke','call',
    'handle','process','compute','calculate','convert','transform',
    'filter','sort','search','find','match','compare','merge','split',
    'copy','move','rename','create','build','compile','generate',
    'update','insert','append','extend','replace','wrap','unwrap',
    'action','activate','deactivate','enable','disable','toggle',
    'accept','reject','approve','deny','allow','block','grant','revoke',
    'login','logout','register','auth','open',
    # 테스트
    'test','mock','stub','fake','fixture','setup','teardown',
    # SQL 예약어
    'select','from','where','insert','update','delete','create','table',
    'index','join','left','right','inner','outer','cross','full',
    'group','order','having','union','except','intersect',
    'null','primary','foreign','references','default','cascade','unique',
    'constraint','trigger','view','procedure','schema','database',
}

EXTERNAL_LIBS: set = {
    'flask','fastapi','uvicorn','starlette','werkzeug',
    'sqlalchemy','alembic','psycopg2','asyncpg','aiopg',
    'redis','aioredis','celery','kombu',
    'pandas','numpy','scipy','sklearn','torch','tensorflow','keras',
    'anthropic','openai','google','cohere','mistral',
    'pydantic','marshmallow',
    'pytest','unittest','hypothesis',
    'yaml','toml','dotenv','environs',
    'click','typer','rich','colorama',
    'asyncio','threading','multiprocessing','subprocess','concurrent',
    'requests','httpx','aiohttp','websockets','grpc',
    'boto3','azure',
    'apscheduler','schedule','croniter',
    'cryptography','jwt','bcrypt',
    'MetaTrader5','pyupbit','ccxt',
}


def _is_noise(name: str) -> bool:
    if not name or len(name) < MIN_LEN:
        return True
    clean = name.strip('_')
    if not clean:
        return True
    if clean.lower() in {x.lower() for x in SKIP_NAMES}:
        return True
    if clean.lower() in {x.lower() for x in EXTERNAL_LIBS}:
        return True
    if _NOISE_RE.search(clean):
        return True
    if re.fullmatch(r'[0-9_\-\.]+', clean):
        return True
    # 단일 문자 반복 (aaaa, 0000)
    if len(set(clean.lower())) == 1:
        return True
    return False


# ════════════════════════════════════════════════════════════════════
# 복수형 헬퍼
# ════════════════════════════════════════════════════════════════════

def auto_plural(word_id: str) -> str:
    """
    단어 id로부터 규칙 기반 복수형 추론.
    words.json의 plural=null인 noun에 적용.
    """
    if word_id.endswith(('s', 'sh', 'ch', 'x', 'z')):
        return word_id + 'es'
    if word_id.endswith('y') and len(word_id) > 1 and word_id[-2] not in 'aeiou':
        return word_id[:-1] + 'ies'
    return word_id + 's'


# suffix 인식 — 본체만 추출 (역할/의미 suffix만, 타입 suffix 제외)
# 허용: 역할/의미 suffix (queue, pool, log, snapshot, state, cache, etc.)
# 비권장: list, array, dict, tuple (타입 중심)
COLLECTION_SUFFIXES = {
    # 역할/의미 suffix — 허용
    'queue', 'pool', 'stream', 'pipeline',
    'log', 'history', 'record', 'trace',
    'snapshot', 'state', 'status', 'cache',
    'registry', 'store',
    'map', 'set',
}

def _strip_collection_suffix(name: str) -> str:
    """
    order_queue → order (본체만 추출해서 사전 검증에 사용).
    타입 중심 suffix (list, array, dict)는 인식하지 않음.
    """
    parts = name.rsplit('_', 1)
    if len(parts) == 2 and parts[1].lower() in COLLECTION_SUFFIXES:
        return parts[0]
    return name


# ════════════════════════════════════════════════════════════════════
# 복합어 분해 — 기존 토큰 집합과 비교
# ════════════════════════════════════════════════════════════════════

def _split_tokens(name: str) -> list:
    """camelCase / snake_case → 소문자 토큰 목록."""
    s = name.replace('_', ' ').replace('-', ' ')
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', s)
    return [t.lower() for t in s.split() if len(t) >= 2]


def _all_tokens_known(name: str, known_tokens: set) -> bool:
    """
    복합어를 분해했을 때 모든 토큰이 이미 알려진 토큰이면 True.
    복수형 역변환 포함 (orders → order, indices → index 등).
    단순어(토큰 1개)는 항상 False 반환 → 개별 판단.
    """
    tokens = _split_tokens(name)
    if len(tokens) <= 1:
        return False

    for t in tokens:
        if t in known_tokens:
            continue
        # 복수형 역변환 시도
        if t.endswith('ies') and t[:-3] + 'y' in known_tokens:
            continue
        if t.endswith('es') and t[:-2] in known_tokens:
            continue
        if t.endswith('s') and t[:-1] in known_tokens:
            continue
        return False
    return True


# ════════════════════════════════════════════════════════════════════
# 기존 사전 로드 — dictionary/words.json + dictionary/compounds.json
# ════════════════════════════════════════════════════════════════════

def load_existing_terms(glossary_dir: Path) -> tuple:
    """
    (등록 심볼 집합, 분해 토큰 집합) 반환.

    v2 우선: dictionary/words.json + dictionary/compounds.json
    fallback: dictionary/terms.json (하위호환)

    복수형도 syms/tokens에 등록:
    - plural 명시 → 해당 값 사용
    - plural=null + pos=noun → auto_plural() 로 추론
    - plural="-" → 복수형 없음, 추가 안 함
    """
    dict_dir = glossary_dir / "dictionary"
    syms:   set = set()
    tokens: set = set()

    def _absorb_compound(entries: list, fields: tuple):
        for item in entries:
            for f in fields:
                v = item.get(f, '')
                if v:
                    syms.add(str(v))
                    syms.add(str(v).lower())
                    for tok in _split_tokens(str(v)):
                        tokens.add(tok)
            # compound plural 처리
            pl = item.get('plural')
            cid = item.get('id', '')
            if pl and pl != '-':
                syms.add(pl); tokens.add(pl.lower())
            elif pl is None and cid:
                auto = auto_plural(cid)
                syms.add(auto); tokens.add(auto.lower())

    # ── words.json ──────────────────────────────────────────────────
    words_path = dict_dir / "words.json"
    if words_path.exists():
        try:
            data = json.loads(words_path.read_text(encoding='utf-8'))
            for w in data.get("words", []):
                wid   = w.get('id', '')
                pos   = w.get('pos', '')
                abbr  = w.get('abbr', '')
                pl    = w.get('plural')  # 명시 값

                # 기본 심볼 등록
                for v in (wid, w.get('en',''), w.get('ko',''), abbr):
                    if v:
                        syms.add(str(v)); syms.add(str(v).lower())
                        for tok in _split_tokens(str(v)):
                            tokens.add(tok)

                # 복수형 등록
                if pl == '-':
                    pass  # 불가산 → 추가 안 함
                elif pl:
                    syms.add(pl); tokens.add(pl.lower())
                elif pl is None and pos == 'noun':
                    auto = auto_plural(wid)
                    syms.add(auto); tokens.add(auto.lower())
        except Exception:
            pass

    # ── compounds.json ───────────────────────────────────────────────
    compounds_path = dict_dir / "compounds.json"
    if compounds_path.exists():
        try:
            data = json.loads(compounds_path.read_text(encoding='utf-8'))
            _absorb_compound(
                data.get("compounds", []),
                ('id', 'abbr_long', 'abbr_short', 'ko', 'en'),
            )
        except Exception:
            pass

    # ── fallback: terms.json (하위호환, words/compounds 없을 때) ─────
    if not syms:
        terms_path = dict_dir / "terms.json"
        if terms_path.exists():
            try:
                data = json.loads(terms_path.read_text(encoding='utf-8'))
                for t in data.get("terms", []):
                    for f in ('id', 'abbr_long', 'abbr_short', 'en', 'ko'):
                        v = t.get(f, '')
                        if v:
                            syms.add(str(v)); syms.add(str(v).lower())
                            for tok in _split_tokens(str(v)):
                                tokens.add(tok)
            except Exception:
                pass

    return syms, tokens


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
        existing_syms: set,
        existing_tokens: set,
        yaml_max_depth: int = 2,
    ):
        self.root           = proj_root
        self.exclude_dirs   = exclude_dirs
        self.content_skip   = content_skip_dirs
        self.exclude_exts   = exclude_exts
        self.existing_syms  = existing_syms
        self.ex_tokens      = existing_tokens
        self.yaml_depth     = yaml_max_depth
        self.candidates: dict = {}   # name → [source, ...]

    # ── 후보 등록 ────────────────────────────────────────────────────
    def _add(self, name: str, source: str):
        name = name.strip().strip('_')
        if _is_noise(name):
            return
        if name in self.existing_syms or name.lower() in self.existing_syms:
            return

        # suffix 스트립 후 본체가 이미 알려진 경우 제외
        # 예) execution_log → execution + log → 둘 다 등록됨 → 후보 제외
        stripped = _strip_collection_suffix(name)
        if stripped != name and _all_tokens_known(stripped, self.ex_tokens):
            return

        if _all_tokens_known(name, self.ex_tokens):
            return
        if name not in self.candidates:
            self.candidates[name] = []
        if len(self.candidates[name]) < 3:   # 출처 최대 3개만 저장
            self.candidates[name].append(source)

    # ── 폴더 경로 판단 ───────────────────────────────────────────────
    def _top(self, rel: str) -> str:
        parts = Path(rel).parts
        return parts[0] if parts and rel != '.' else ''

    def _skip_dir(self, rel: str) -> bool:
        top = self._top(rel)
        return top in self.exclude_dirs or top.startswith('.')

    def _skip_content(self, rel: str) -> bool:
        return self._top(rel) in self.content_skip

    def _is_doc_dir(self, rel: str) -> bool:
        return self._top(rel) == 'doc'

    # ── 메인 스캔 ────────────────────────────────────────────────────
    def scan(self):
        for dirpath, dirnames, filenames in os.walk(self.root):
            rel_dir = os.path.relpath(dirpath, self.root)

            # 숨김 폴더 전부 제외
            dirnames[:] = [
                d for d in dirnames
                if not d.startswith('.')
                and d not in self.exclude_dirs
            ]

            if self._skip_dir(rel_dir):
                dirnames.clear()
                continue

            skip_content = self._skip_content(rel_dir)
            is_doc       = self._is_doc_dir(rel_dir)

            # doc/ 하위 폴더명: 도메인 관련성 있는 것만 후보
            if is_doc:
                for d in dirnames:
                    if DOMAIN_DOC_DIR_PATTERNS.match(d):
                        self._add(d, f"doc_dir:{rel_dir}/{d}")
                # doc/ 하위는 파일 내용 스캔 안 함
                continue

            for fname in filenames:
                fpath = Path(dirpath) / fname
                rel   = os.path.relpath(fpath, self.root)
                ext   = fpath.suffix.lower()

                # .md 파일명은 무시 (자연어 문서 제목)
                if ext == '.md':
                    continue

                # .py 파일명 스템만 후보로 (다른 확장자 파일명은 제외)
                if ext == '.py':
                    stem = fpath.stem
                    if stem and not stem.startswith('_') and not stem.startswith('test'):
                        self._add(stem, f"py_file:{rel}")

                # 내용 스캔 제외 조건
                if skip_content:
                    continue
                if ext in self.exclude_exts:
                    continue

                # 내용 스캔
                if ext == '.py':
                    self._scan_python(fpath, rel)
                elif ext in ('.yaml', '.yml'):
                    self._scan_yaml(fpath, rel)
                elif fname in ('.env', '.env.example', '.env.sample') or (
                    fname.startswith('.env') and '.' not in fname[4:]
                ):
                    self._scan_env_file(fpath, rel)
                elif ext == '.sql':
                    self._scan_sql(fpath, rel)

    # ── Python AST 스캔 ─────────────────────────────────────────────
    def _scan_python(self, fpath: Path, rel: str):
        try:
            src  = fpath.read_text(encoding='utf-8', errors='replace')
            tree = ast.parse(src, filename=str(fpath))
        except SyntaxError:
            return

        # 클래스 바디 파악 (모듈 레벨 vs 클래스 레벨 구분)
        class_bodies: set = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for child in ast.walk(node):
                    class_bodies.add(id(child))

        for node in ast.walk(tree):

            # ── 클래스명 ──────────────────────────────────────────
            if isinstance(node, ast.ClassDef):
                self._add(node.name, f"class:{rel}")

            # ── public 함수/메서드명 ──────────────────────────────
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nm = node.name
                # 언더스코어 시작 제외 (private/dunder)
                if not nm.startswith('_'):
                    self._add(nm, f"func:{rel}")

                # ※ 파라미터명은 수집하지 않음 (구현 상세)

            # ── self.속성명 ───────────────────────────────────────
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = [node.target] if isinstance(node, ast.AnnAssign) else node.targets
                for target in targets:
                    if isinstance(target, ast.Attribute):
                        # self.xxx 만
                        if (isinstance(target.value, ast.Name)
                                and target.value.id == 'self'):
                            attr = target.attr.lstrip('_')
                            if attr:
                                self._add(attr, f"attr:{rel}")

    # ── YAML 스캔 (상위 2단계 키만) ────────────────────────────────
    def _scan_yaml(self, fpath: Path, rel: str):
        try:
            import yaml
            with open(fpath, encoding='utf-8', errors='replace') as f:
                data = yaml.safe_load(f)
            self._walk_yaml(data, rel, depth=0)
        except Exception:
            # yaml 모듈 없으면 정규식 fallback — 들여쓰기 0~2칸 키만
            try:
                src = fpath.read_text(encoding='utf-8', errors='replace')
                for m in re.finditer(
                    r'^( {0,4})([a-zA-Z_][a-zA-Z0-9_]*)\s*:',
                    src, re.MULTILINE
                ):
                    indent = len(m.group(1))
                    # 들여쓰기 0 또는 2칸(1단계, 2단계)만
                    if indent <= 4:
                        self._add(m.group(2), f"yaml:{rel}")
            except Exception:
                pass

    def _walk_yaml(self, node, rel: str, depth: int):
        if depth > self.yaml_depth:
            return
        if isinstance(node, dict):
            for k, v in node.items():
                key = str(k)
                # 숫자 키, 특수문자 포함 키 제외
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                    self._add(key, f"yaml:{rel}:depth{depth}")
                self._walk_yaml(v, rel, depth + 1)
        elif isinstance(node, list):
            for item in node:
                self._walk_yaml(item, rel, depth)

    # ── .env 스캔 ───────────────────────────────────────────────────
    def _scan_env_file(self, fpath: Path, rel: str):
        try:
            for line in fpath.read_text(encoding='utf-8', errors='replace').splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k = line.split('=', 1)[0].strip()
                # 환경변수명: 알파벳+숫자+언더스코어만
                if k and re.match(r'^[A-Z][A-Z0-9_]+$', k):
                    self._add(k, f"env:{rel}")
        except Exception:
            pass

    # ── SQL 스캔 ────────────────────────────────────────────────────
    def _scan_sql(self, fpath: Path, rel: str):
        try:
            src = fpath.read_text(encoding='utf-8', errors='replace')
            # 주석 제거
            src = re.sub(r'--[^\n]*', '', src)
            src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)

            # CREATE TABLE 테이블명
            for m in re.finditer(
                r'\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
                src, re.IGNORECASE
            ):
                self._add(m.group(1), f"sql_table:{rel}")

            # 컬럼명: 타입 키워드 앞에 오는 단어
            for m in re.finditer(
                r'^\s{2,}(\w+)\s+'
                r'(?:INTEGER|BIGINT|SMALLINT|TEXT|VARCHAR|CHAR|BOOLEAN|BOOL'
                r'|TIMESTAMP|DATE|TIME|FLOAT|DOUBLE|NUMERIC|DECIMAL'
                r'|SERIAL|BIGSERIAL|UUID|JSONB|JSON|BYTEA)',
                src, re.IGNORECASE | re.MULTILINE
            ):
                col = m.group(1)
                # SQL 예약어 제외
                if col.upper() not in {
                    'PRIMARY','UNIQUE','NOT','NULL','DEFAULT',
                    'REFERENCES','CHECK','FOREIGN','CONSTRAINT',
                }:
                    self._add(col, f"sql_col:{rel}")
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════════
# 메인
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="프로젝트 소스 → 용어 후보 추출 (v2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
출력 형식:
  기본      : 후보명 + 첫 번째 출처 텍스트
  --json    : batch_terms.py 에 넘길 JSON 형식
  --count   : 후보 수만 출력
        """,
    )
    parser.add_argument("--json",  action="store_true", help="JSON 형식 출력")
    parser.add_argument("--count", action="store_true", help="후보 수만 출력")
    parser.add_argument("--env",   default=None,        help=".env 파일 경로 직접 지정")
    parser.add_argument("--yaml-depth", type=int, default=2,
                        help="YAML 키 스캔 최대 깊이 (기본 2)")
    args = parser.parse_args()

    bin_dir      = Path(__file__).parent.resolve()
    glossary_dir = bin_dir.parent.resolve()

    # .env 로드
    if args.env:
        env_path = Path(args.env)
    else:
        env_path = glossary_dir.parent / ".env"
        if not env_path.exists():
            env_path = glossary_dir / ".env"

    env       = load_env(env_path)
    proj_root = resolve_proj_root(bin_dir, env)

    exclude_dirs = parse_list(env.get('EXCLUDE_DIRS',
        'backup,data,test,lib_test,tmp,glossary,.git,__pycache__,node_modules,.venv,venv'))
    content_skip = parse_list(env.get('EXCLUDE_FILE_CONTENT', 'cache,log'))
    raw_exts     = parse_list(env.get('EXCLUDE_EXTENSIONS',
        '.md,.txt,.log,.csv,.tsv,.png,.jpg,.jpeg,.gif,.pdf,.ico,.svg,.zip,.tar'))
    exclude_exts = {e if e.startswith('.') else f'.{e}' for e in raw_exts}

    existing_syms, existing_tokens = load_existing_terms(glossary_dir)

    scanner = TermScanner(
        proj_root       = proj_root,
        exclude_dirs    = exclude_dirs,
        content_skip_dirs = content_skip,
        exclude_exts    = exclude_exts,
        existing_syms   = existing_syms,
        existing_tokens = existing_tokens,
        yaml_max_depth  = args.yaml_depth,
    )
    scanner.scan()

    candidates = sorted(scanner.candidates.keys())

    if args.count:
        print(len(candidates))
        return

    if args.json:
        out = {
            "proj_root":  str(proj_root),
            "count":      len(candidates),
            "candidates": [
                {
                    "name":    c,
                    "sources": scanner.candidates[c],
                }
                for c in candidates
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"[scan v2]  루트: {proj_root}")
        print(f"[scan v2]  후보: {len(candidates)}개\n")
        # 출처 유형별로 그루핑해서 보여줌
        by_type: dict = {}
        for c in candidates:
            src = scanner.candidates[c][0] if scanner.candidates[c] else 'unknown'
            stype = src.split(':')[0]
            by_type.setdefault(stype, []).append((c, src))

        for stype in sorted(by_type):
            items = by_type[stype]
            print(f"  [{stype}]  {len(items)}개")
            for name, src in items[:5]:
                print(f"    {name:<40} {src}")
            if len(items) > 5:
                print(f"    ... 외 {len(items)-5}개")
            print()


if __name__ == "__main__":
    main()
