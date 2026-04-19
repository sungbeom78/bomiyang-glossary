from __future__ import annotations
import re
import json
from pathlib import Path
from dataclasses import dataclass

import sys
GLOSSARY_ROOT = Path(__file__).resolve().parent.parent

# Inject glossary root to import specific glossary modules if not already
if str(GLOSSARY_ROOT) not in sys.path:
    sys.path.insert(0, str(GLOSSARY_ROOT))

try:
    from generate_glossary import tokenize, match_n_pattern, find_singular_token, build_n_pattern_regexes
except ImportError:
    pass

LOCAL_VAR_EXCLUDE = {"i", "j", "k", "tmp", "res", "ret", "e", "ex"}

EXTERNAL_LIB_TOKENS = {
    "flask",
    "redis",
    "pandas",
    "numpy",
    "sqlalchemy",
    "fastapi",
    "pydantic",
    "uvicorn",
    "requests",
    "pytest",
}

_STOP_WORDS_AUDIT: frozenset[str] = frozenset({
    "a", "an", "the",
    "at", "by", "for", "from", "in", "of", "on", "to", "with",
})

class GlossaryAuditor:
    def __init__(self):
        self.words, self.compounds, self.variant_map, self.banned, self.n_patterns, self.pending_ids = self.load_glossary()

    def load_glossary(self) -> tuple[dict, dict, dict, list[dict], list[re.Pattern], set]:
        words, compounds, variant_map, banned, pending_ids = {}, {}, {}, [], set()
        n_patterns = []
        
        WORDS_PATH = GLOSSARY_ROOT / "dictionary" / "words.json"
        COMPOUNDS_PATH = GLOSSARY_ROOT / "dictionary" / "compounds.json"
        BANNED_PATH = GLOSSARY_ROOT / "dictionary" / "banned.json"
        PENDING_PATH = GLOSSARY_ROOT / "dictionary" / "pending_words.json"
        INDEX_WORD_MIN = GLOSSARY_ROOT / "build" / "index" / "word_min.json"
        INDEX_COMPOUND_MIN = GLOSSARY_ROOT / "build" / "index" / "compound_min.json"
        INDEX_VARIANT_MAP = GLOSSARY_ROOT / "build" / "index" / "variant_map.json"

        if INDEX_WORD_MIN.exists():
            data = json.loads(INDEX_WORD_MIN.read_text(encoding="utf-8"))
            words = {normalize_term(w.get("id", "")): w for w in data if w.get("id")}
        
        if INDEX_COMPOUND_MIN.exists():
            data = json.loads(INDEX_COMPOUND_MIN.read_text(encoding="utf-8"))
            compounds = {normalize_term(c.get("id", "")): c for c in data if c.get("id")}
            n_patterns_tuples = build_n_pattern_regexes(data) if "build_n_pattern_regexes" in globals() else []
            n_patterns = [c_re for cid, c_re in n_patterns_tuples]
            
        if INDEX_VARIANT_MAP.exists():
            data = json.loads(INDEX_VARIANT_MAP.read_text(encoding="utf-8"))
            variant_map = {normalize_term(k): v for k, v in data.items()}

        if BANNED_PATH.exists():
            banned = json.loads(BANNED_PATH.read_text(encoding="utf-8")).get("banned", [])
            
        if PENDING_PATH.exists():
            try:
                pending_data = json.loads(PENDING_PATH.read_text(encoding="utf-8")).get("pending", [])
                pending_ids = {normalize_term(p) if isinstance(p, str) else normalize_term(p.get("id", "")) for p in pending_data}
            except Exception:
                pass

        return words, compounds, variant_map, banned, n_patterns, pending_ids
        
    def audit_identifier(self, identifier: str, kind: str, source: str) -> list[AuditIssue]:
        issues = []
        issues.extend(check_formatting(identifier, kind, source))
        banned_issue = check_banned(identifier, kind, source, self.banned)
        if banned_issue:
            issues.append(banned_issue)
            
        if kind != "file":
            issues.extend(check_glossary(identifier, kind, source, self.words, self.compounds, self.variant_map, self.n_patterns, self.pending_ids))
            
        issues.extend(check_singular(identifier, kind, source))
        issues.extend(check_collection_semantic(identifier, kind, source))
        issues.extend(check_numeric_pattern(identifier, kind, source, self.n_patterns))
        return issues


SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*$")

PASCAL_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")

UPPER_SNAKE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

PY_FILE_RE = re.compile(r"^[a-z0-9_]+\.py$")

ALLOWED_CHAR_RE = re.compile(r"^[A-Za-z0-9_]+$")

STRICT_GLOSSARY_KINDS = {"env_key", "config_key"}

BANNED_STRICT_KINDS = {"folder", "db_table", "module", "env_key", "config_key"}

VARIABLE_KINDS = {"module_var", "class_attr", "self_attr", "param", "model_field"}

NUMERIC_PATTERN_KINDS = {
    "module",
    "class",
    "function",
    "module_var",
    "class_attr",
    "self_attr",
    "param",
    "model_field",
    "db_table",
    "db_column",
    "config_key",
    "env_key",
}

COLLECTION_HINT_TOKENS = {
    "list",
    "set",
    "dict",
    "map",
    "queue",
    "pool",
    "items",
    "rows",
    "records",
    "history",
    "logs",
    "snapshots",
    "cache",
    "stream",
    "pipeline",
    "values",
    "keys",
}

SCALAR_HINT_TOKENS = {
    "id",
    "name",
    "code",
    "count",
    "price",
    "qty",
    "rate",
    "ratio",
    "flag",
    "status",
    "state",
    "time",
    "date",
    "index",
    "score",
    "value",
    "amount",
    "size",
    "mode",
    "type",
    "level",
}

@dataclass
class AuditIssue:
    severity: str
    code: str
    identifier: str
    kind: str
    source: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "identifier": self.identifier,
            "kind": self.kind,
            "source": self.source,
            "detail": self.detail,
        }

def normalize_identifier(identifier: str) -> list[str]:
    # Step 1: 공백 및 특수문자(하이픈, 슬래시, 괄호, 점 등)를 밑줄 구분자로 치환
    s = re.sub(r"[\s\-/\\.()\[\]{}<>:,;!?@#$%^&*+=|~`'\"]", "_", identifier)
    # Step 2: camelCase / PascalCase 분해
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    parts: list[str] = []
    for token in s.split("_"):
        if not token:
            continue
        # Step 3: 알파/숫자 경계 분리 (sma5 → sma, 5 / stage1 → stage, 1)
        chunks = re.findall(r"[A-Za-z]+|\d+", token)
        if not chunks:
            chunks = [token]
        parts.extend(c.lower() for c in chunks if c)
    # Step 4: 전치사/관사(stop words) 제거
    parts = [p for p in parts if p not in _STOP_WORDS_AUDIT]
    return parts

def normalize_term(term: str) -> str:
    return term.strip().lower().replace("-", "_")

def check_plural(word: str) -> bool:
    if re.match(r".*(es|s)$", word) and not re.match(r".*(ss|us|is|ics|news)$", word):
        return True
    return False

def check_banned(identifier: str, kind: str, source: str, banned_rows: list[dict[str, str]]) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    if kind not in BANNED_STRICT_KINDS:
        return issues

    ident_norm = normalize_term(identifier)
    for row in banned_rows:
        expr = normalize_term(row.get("expression", ""))
        if not expr:
            continue
        # BANNED rows are intended for ambiguous standalone identifiers.
        # Do not hard-fail compound identifiers like breakout_vol_mult.
        if ident_norm == expr:
            issues.append(
                AuditIssue(
                    severity="FATAL",
                    code="BANNED_TERM",
                    identifier=identifier,
                    kind=kind,
                    source=source,
                    detail=f"banned '{row.get('expression', expr)}' -> use '{row.get('correct', '')}'",
                )
            )
    return issues

def check_glossary(
    identifier: str, 
    kind: str, 
    source: str, 
    words: dict, 
    compounds: dict, 
    variant_map: dict, 
    n_patterns: list[re.Pattern],
    pending_ids: set[str]
) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    ident_norm = normalize_term(identifier)
    
    # 1. Full matches
    if ident_norm in compounds or (ident_norm in variant_map and variant_map[ident_norm]["type"] == "abbreviation"):
        return issues
        
    n_patterns_tuples = []
    if "match_n_pattern" in globals():
        # recreate tuples for match_n_pattern
        for pat in n_patterns:
            # We don't have the original cid, but match_n_pattern doesn't strictly need it if we change how we call it
            pass
        # Actually it's easier to just match the compiled patterns directly:
        if any(pat.fullmatch(ident_norm) for pat in n_patterns):
            return issues
            
    # 2. Tokenization & component checks
    if "tokenize" in globals():
        tokens = tokenize(identifier)
    else:
        tokens = normalize_identifier(identifier)
        
    if not tokens:
        return issues
        
    missing = []
    pending_usages = []
    
    for tok in tokens:
        if tok in EXTERNAL_LIB_TOKENS or tok in LOCAL_VAR_EXCLUDE or tok.isdigit():
            continue
            
        if tok in pending_ids:
            pending_usages.append(tok)
            continue
            
        if tok in variant_map:
            v_type = variant_map[tok]["type"]
            root_id = variant_map[tok]["root"]
            if v_type == "abbreviation":
                issues.append(
                    AuditIssue(
                        severity="WARN" if kind not in STRICT_GLOSSARY_KINDS else "ERROR",
                        code="VARIANT_ABBREVIATION",
                        identifier=identifier,
                        kind=kind,
                        source=source,
                        detail=f"variant '{tok}' used directly instead of root '{root_id}'",
                    )
                )
            elif v_type == "plural":
                # SEMANTIC: exempt warnings for code-layer plurals. Checked by semantic consistency instead.
                is_semantic = kind in {"module_var", "class_attr", "self_attr", "param", "model_field", "function", "json_key"}
                if not is_semantic:
                    issues.append(
                        AuditIssue(
                            severity="WARN",
                            code="VARIANT_PLURAL",
                            identifier=identifier,
                            kind=kind,
                            source=source,
                            detail=f"plural variant '{tok}' should be auto-normalized to root '{root_id}'",
                        )
                    )
            continue
            
        if tok in words:
            continue
            
        if tok in compounds:
            continue
            
        matched = False
        if "match_n_pattern" in globals():
            # recreate tuples locally for match backwards compat
            tmp_pats = [("pattern", p) for p in n_patterns]
            if match_n_pattern(tok, tmp_pats):
                matched = True
        else:
            if any(pat.fullmatch(tok) for pat in n_patterns):
                matched = True
                
        if matched:
            continue
            
        if "find_singular_token" in globals():
            singular = find_singular_token(tok, words)
            if singular:
                is_semantic = kind in {"module_var", "class_attr", "self_attr", "param", "model_field", "function", "json_key"}
                if not is_semantic:
                    issues.append(
                        AuditIssue(
                            severity="WARN",
                            code="VARIANT_PLURAL",
                            identifier=identifier,
                            kind=kind,
                            source=source,
                            detail=f"plural-like variant '{tok}' should be normalized to root '{singular}'",
                        )
                    )
                continue
                
        missing.append(tok)
        
    if missing:
        severity = "ERROR" if kind in STRICT_GLOSSARY_KINDS else "FATAL" # making it strict
        issues.append(
            AuditIssue(
                severity=severity,
                code="UNREGISTERED_WORD",
                identifier=identifier,
                kind=kind,
                source=source,
                detail=f"missing words: {', '.join(sorted(set(missing)))}",
            )
        )
        
    if pending_usages:
        issues.append(
            AuditIssue(
                severity="WARN",
                code="PENDING_WORD",
                identifier=identifier,
                kind=kind,
                source=source,
                detail=f"pending words used: {', '.join(sorted(set(pending_usages)))}. wait for approval.",
            )
        )

    return issues

def check_formatting(identifier: str, kind: str, source: str) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    # JSON keys frequently come from external protocols/headers and may include
    # hyphen/dot or vendor formats. Skip strict formatting for these keys.
    if kind == "json_key":
        return issues

    id_for_chars = Path(identifier).stem if kind == "file" else identifier
    if not ALLOWED_CHAR_RE.match(id_for_chars):
        issues.append(
            AuditIssue(
                severity="ERROR",
                code="FORMAT_ALLOWED_CHAR",
                identifier=identifier,
                kind=kind,
                source=source,
                detail="allowed chars are letters, digits, underscore",
            )
        )

    snake_target = identifier
    if kind == "function":
        # Allow private/dunder methods (e.g., _run, __init__) in snake-case validation.
        snake_target = identifier.strip("_")
    elif kind == "module":
        snake_target = identifier.strip("_")

    if kind in {"module", "variable", "db_table", "db_column", "config_key"} and (
        not snake_target or not SNAKE_RE.match(snake_target)
    ):
        issues.append(
            AuditIssue(
                severity="ERROR",
                code="FORMAT_SNAKE_CASE",
                identifier=identifier,
                kind=kind,
                source=source,
                detail="must match snake_case",
            )
        )
    elif kind == "class" and not PASCAL_RE.match(identifier.strip("_")):
        issues.append(
            AuditIssue(
                severity="ERROR",
                code="FORMAT_PASCAL_CASE",
                identifier=identifier,
                kind=kind,
                source=source,
                detail="must match PascalCase",
            )
        )
    elif kind == "env_key" and not UPPER_SNAKE_RE.match(identifier):
        issues.append(
            AuditIssue(
                severity="ERROR",
                code="FORMAT_UPPER_SNAKE",
                identifier=identifier,
                kind=kind,
                source=source,
                detail="must match UPPER_SNAKE_CASE",
            )
        )
    elif kind == "file" and identifier.endswith(".py") and not PY_FILE_RE.match(identifier):
        issues.append(
            AuditIssue(
                severity="ERROR",
                code="FORMAT_FILE_NAME",
                identifier=identifier,
                kind=kind,
                source=source,
                detail="python filename must match ^[a-z0-9_]+\\.py$",
            )
        )
    return issues

def check_singular(identifier: str, kind: str, source: str) -> list[AuditIssue]:
    if kind not in {"folder", "db_table"}:
        return []
    plural = any(check_plural(w) for w in identifier.split("_"))
    if not plural:
        return []
    return [
        AuditIssue(
            severity="WARN",
            code="SINGULAR_CHECK",
            identifier=identifier,
            kind=kind,
            source=source,
            detail="name appears plural; singular preferred",
        )
    ]

def check_collection_semantic(identifier: str, kind: str, source: str) -> list[AuditIssue]:
    if kind not in VARIABLE_KINDS:
        return []
    tokens = [t for t in normalize_identifier(identifier) if t and not t.isdigit()]
    if not tokens:
        return []

    has_collection_hint = any(t in COLLECTION_HINT_TOKENS for t in tokens)
    has_scalar_hint = any(t in SCALAR_HINT_TOKENS for t in tokens)
    plural_name = any(check_plural(t) for t in tokens)

    issues: list[AuditIssue] = []
    if plural_name and has_scalar_hint and not has_collection_hint:
        issues.append(
            AuditIssue(
                severity="WARN",
                code="SEMANTIC_PLURAL_SINGLE",
                identifier=identifier,
                kind=kind,
                source=source,
                detail="plural-looking variable may represent a single/scalar value",
            )
        )
    if (not plural_name) and has_collection_hint:
        issues.append(
            AuditIssue(
                severity="WARN",
                code="SEMANTIC_SINGLE_COLLECTION",
                identifier=identifier,
                kind=kind,
                source=source,
                detail="singular-looking variable may represent a collection",
            )
        )
    return issues

def check_numeric_pattern(identifier: str, kind: str, source: str, n_patterns: list[re.Pattern[str]]) -> list[AuditIssue]:
    if kind not in NUMERIC_PATTERN_KINDS:
        return []
    lowered = identifier.replace("-", "_").lower()
    parts = [p for p in lowered.split("_") if p]
    # 숫자+문자 조합만 [N] 대상(순수 숫자는 제외)
    candidate_parts = [p for p in parts if re.search(r"\d", p) and re.search(r"[a-z]", p)]
    if not candidate_parts:
        return []

    unmatched = [p for p in candidate_parts if not any(pat.fullmatch(p) for pat in n_patterns)]
    if not unmatched:
        return []
    return [
        AuditIssue(
            severity="WARN",
            code="NUMERIC_PATTERN",
            identifier=identifier,
            kind=kind,
            source=source,
            detail=f"numeric segments not matched to [N] pattern: {', '.join(sorted(set(unmatched)))}",
        )
    ]