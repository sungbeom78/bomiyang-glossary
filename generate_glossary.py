#!/usr/bin/env python3
"""
generate_glossary.py v2  —  BOM_TS 용어 사전 생성·검증·조회
위치: glossary/generate_glossary.py

명령어:
  python generate_glossary.py generate          # GLOSSARY.md + terms.json 생성
  python generate_glossary.py validate          # 검증만 (CI용, 오류 시 exit 1)
  python generate_glossary.py stats             # 통계 출력
  python generate_glossary.py check-id <id>    # 식별자 단어 분해 + 등록 여부
  python generate_glossary.py suggest <id>     # 미등록 단어 등록 제안
  python generate_glossary.py migrate-from-legacy <terms.json>  # 마이그레이션
"""

import sys
import io
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

# ── Windows 인코딩 ──────────────────────────────────────────────────
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding.lower() not in ('utf-8','utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── 경로 ────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent.resolve()
DICT_DIR     = ROOT / "dictionary"
WORDS_PATH   = DICT_DIR / "words.json"
COMPOUNDS_PATH = DICT_DIR / "compounds.json"
BANNED_PATH  = DICT_DIR / "banned.json"
TERMS_PATH   = DICT_DIR / "terms.json"       # 자동 생성 (하위호환)
GLOSSARY_PATH = ROOT / "GLOSSARY.md"         # 자동 생성 (루트에 유지)

DOMAINS = ["trading","market","system","infra","ui","general","proper"]
POS_LIST = ["noun","verb","adj","adv","prefix","suffix","proper"]


# ════════════════════════════════════════════════════════════════════
# 데이터 로드
# ════════════════════════════════════════════════════════════════════

def load_all() -> tuple:
    """(words, compounds, banned) 반환."""
    def _load(path, key):
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding='utf-8'))
        return data.get(key, [])

    words     = _load(WORDS_PATH,     "words")
    compounds = _load(COMPOUNDS_PATH, "compounds")
    banned    = _load(BANNED_PATH,    "banned")
    return words, compounds, banned


# ════════════════════════════════════════════════════════════════════
# 검증 (V-001 ~ V-105)
# ════════════════════════════════════════════════════════════════════

def _auto_plural_check(word_id: str) -> str:
    """단어 id로부터 규칙 기반 복수형 추론 (V-105 검증용)."""
    if word_id.endswith(('s', 'sh', 'ch', 'x', 'z')):
        return word_id + 'es'
    if word_id.endswith('y') and len(word_id) > 1 and word_id[-2] not in 'aeiou':
        return word_id[:-1] + 'ies'
    return word_id + 's'


def validate(words, compounds, banned, silent=False) -> tuple:
    """(fatals: list, warns: list) 반환."""
    fatals, warns = [], []

    def F(code, msg): fatals.append(f"[{code}] {msg}")
    def W(code, msg): warns.append(f"[{code}] {msg}")

    word_ids     = [w["id"] for w in words]
    compound_ids = [c["id"] for c in compounds]

    # V-001: words id 고유
    dup_w = [x for x in word_ids if word_ids.count(x) > 1]
    for d in set(dup_w):
        F("V-001", f"words.json id 중복: '{d}'")

    # V-002: compounds id 고유
    dup_c = [x for x in compound_ids if compound_ids.count(x) > 1]
    for d in set(dup_c):
        F("V-002", f"compounds.json id 중복: '{d}'")

    # V-003: words ↔ compounds id 충돌
    cross = set(word_ids) & set(compound_ids)
    for d in cross:
        F("V-003", f"words ↔ compounds id 충돌: '{d}'")

    # V-104: compounds.words[] 참조 검증 및 순환 참조 방지
    word_id_set = set(word_ids)
    compound_id_set = set(compound_ids)
    compound_dict = {c["id"]: c.get("words", []) for c in compounds}
    
    def has_cycle(cid, visited, stack):
        visited.add(cid)
        stack.add(cid)
        for ref in compound_dict.get(cid, []):
            if ref in stack:
                return True, ref
            if ref in compound_dict and ref not in visited:
                cycle_found, conflict = has_cycle(ref, visited, stack)
                if cycle_found:
                    return True, conflict
        stack.remove(cid)
        return False, None

    visited = set()
    for c in compounds:
        cid = c["id"]
        for ref in c.get("words", []):
            if ref not in word_id_set and ref not in compound_id_set:
                F("V-104", f"compounds['{cid}'].words 참조 미등록: '{ref}'")
        
        if cid not in visited:
            stack = set()
            cycle_found, conflict = has_cycle(cid, visited, stack)
            if cycle_found:
                F("V-104", f"순환 참조 발생: '{cid}' -> '{conflict}'")

    # abbreviation 검증
    abbr_to_root = {}
    
    for w in words:
        abbrs = w.get("variants", {}).get("abbreviation")
        if abbrs:
            if isinstance(abbrs, str): abbrs = [abbrs]
            for a in abbrs:
                al = a.lower()
                if al in abbr_to_root:
                    W("V-201", f"약어 중복 정의: '{a}' ({abbr_to_root[al]} vs {w['id']})")
                abbr_to_root[al] = w["id"]

    for c in compounds:
        abbr = c.get("abbr", {}).get("short")
        if abbr:
            al = abbr.lower()
            if al in abbr_to_root:
                W("V-201", f"약어 중복 정의: '{abbr}' ({abbr_to_root[al]} vs {c['id']})")
            abbr_to_root[al] = c["id"]

    for w in words:
        if w["id"] in abbr_to_root and abbr_to_root[w["id"]] != w["id"]:
            F("V-202", f"abbreviation이 word로 독립 존재: '{w['id']}' (root: {abbr_to_root[w['id']]})")

    if not silent:
        print(f"\n{'='*52}")
        print(f"  validate  —  {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*52}")
        print(f"  words    : {len(words)}개")
        print(f"  compounds: {len(compounds)}개")
        print(f"  banned   : {len(banned)}개")

        if fatals:
            print(f"\n[FATAL] {len(fatals)}건:")
            for f in fatals:
                print(f"  {f}")
        else:
            print("\n[OK] FATAL 없음")

        if warns:
            print(f"\n[WARN] {len(warns)}건:")
            for w in warns[:20]:
                print(f"  {w}")
            if len(warns) > 20:
                print(f"  ... 외 {len(warns)-20}건")
        print(f"\n{'='*52}\n")

    return fatals, warns


# ════════════════════════════════════════════════════════════════════
# terms.json 생성 (하위호환)
# ════════════════════════════════════════════════════════════════════

def build_terms_json(words, compounds) -> dict:
    terms = []
    for w in words:
        en_val = w.get("lang", {}).get("en") or w.get("en", "")
        ko_val = w.get("lang", {}).get("ko") or w.get("ko", "")
        abbrs = w.get("variants", {}).get("abbreviation") or []
        if isinstance(abbrs, str): abbrs = [abbrs]
        abbr = abbrs[0] if abbrs else w.get("abbr")
        abbr_short = abbr or en_val.upper()[:5]
        desc = w.get("description_i18n", {}).get("ko") or w.get("description", "")
        terms.append({
            "id":          w["id"],
            "ko":          ko_val,
            "en":          en_val.title() if en_val else "",
            "abbr_long":   en_val,
            "abbr_short":  abbr_short,
            "categories":  [w.get("domain", "general")],
            "type":        "word",
            "description": desc,
        })
    for c in compounds:
        en_val = c.get("lang", {}).get("en") or c.get("en", "")
        ko_val = c.get("lang", {}).get("ko") or c.get("ko", "")
        abbr_long = c.get("abbr", {}).get("long") or c.get("abbr_long", "")
        abbr_short = c.get("abbr", {}).get("short") or c.get("abbr_short", "")
        desc = c.get("description_i18n", {}).get("ko") or c.get("description", "")
        terms.append({
            "id":          c["id"],
            "ko":          ko_val,
            "en":          en_val,
            "abbr_long":   abbr_long,
            "abbr_short":  abbr_short,
            "categories":  [c.get("domain", "general")],
            "type":        "compound",
            "description": desc,
        })
    return {
        "_WARNING": "이 파일은 자동 생성됩니다. 수동 편집 금지. words.json과 compounds.json을 편집하세요.",
        "version":   "2.0.0",
        "generated": True,
        "generated_at": datetime.now().isoformat(),
        "terms": terms,
    }


# ════════════════════════════════════════════════════════════════════
# GLOSSARY.md 생성
# ════════════════════════════════════════════════════════════════════

def build_glossary_md(words, compounds, banned) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines += [
        "# BOM_TS 용어 사전",
        "",
        "> 자동 생성 파일. 수동 편집 금지.",
        "> 원본: `words.json` + `compounds.json` + `banned.json`",
        f"> 생성: {now}",
        "",
        "## 통계",
        f"- 단어: {len(words)}개",
        f"- 복합어: {len(compounds)}개",
        f"- 금지 표현: {len(banned)}개",
        "",
        "---",
        "",
        "## 단어 사전 (Words)",
        "",
    ]

    # 도메인별 그루핑
    for domain in DOMAINS:
        wlist = [w for w in sorted(words, key=lambda x: x["id"]) if w["domain"] == domain]
        if not wlist:
            continue
        lines.append(f"### {domain}")
        lines.append("")
        lines.append("| 단어 | 한글 | 약어 | 품사 | 복수형 | 설명 |")
        lines.append("|------|------|------|------|--------|------|")
        for w in wlist:
            abbrs = w.get("variants", {}).get("abbreviation") or []
            if isinstance(abbrs, str): abbrs = [abbrs]
            abbr = (abbrs[0] if abbrs else w.get("abbr")) or "—"
            pos = w.get("canonical_pos") or w.get("pos", "noun")
            if pos != "noun":
                plural = "—"
            else:
                pl = w.get("variants", {}).get("plural") or w.get("plural")
                if pl is None:
                    plural = "auto"
                else:
                    plural = str(pl)
            ko_val = w.get("lang", {}).get("ko") or w.get("ko", "")
            desc = w.get("description_i18n", {}).get("ko") or w.get("description", "")
            lines.append(f"| `{w['id']}` | {ko_val} | {abbr} | {pos} | {plural} | {desc} |")
        lines.append("")

    lines += [
        "---",
        "",
        "## 복합어 사전 (Compounds)",
        "",
        "| 복합어 | 구성 단어 | 한글 | camelCase | 약어 | 복수형 | 등록 사유 |",
        "|--------|----------|------|-----------|------|--------|----------|",
    ]
    for c in sorted(compounds, key=lambda x: x["id"]):
        wds = " + ".join(c.get("words", []))
        c_plural = c.get("variants", {}).get("plural") or c.get("plural")
        c_plural_txt = "auto" if c_plural is None else str(c_plural)
        ko_val = c.get("lang", {}).get("ko") or c.get("ko", "")
        abbr_long = c.get("abbr", {}).get("long") or c.get("abbr_long", "")
        abbr_short = c.get("abbr", {}).get("short") or c.get("abbr_short", "")
        reason = c.get("reason", "")
        lines.append(
            f"| `{c['id']}` | {wds} | {ko_val} | `{abbr_long}` | `{abbr_short}` | {c_plural_txt} | {reason} |"
        )

    n_compounds = [c for c in sorted(compounds, key=lambda x: x["id"]) if "[N]" in c.get("id", "")]
    lines += [
        "",
        "---",
        "",
        "## [N] 패턴 (Numeric Pattern Compounds)",
        "",
    ]
    if n_compounds:
        lines += [
            "| 패턴 | 예시 | 설명 |",
            "|------|------|------|",
        ]
        for c in n_compounds:
            if c["id"] == "[N]m":
                sample = "1m, 5m, 10m, 15m, 60m"
            elif c["id"] == "top[N]":
                sample = "top3, top5, top10, top100"
            else:
                sample = "—"
            desc = c.get("description_i18n", {}).get("ko") or c.get("description", "")
            lines.append(f"| `{c['id']}` | {sample} | {desc} |")
    else:
        lines.append("- 등록된 [N] 패턴 복합어가 없습니다.")

    lines += [
        "",
        "---",
        "",
        "## 금지 표현 (Banned)",
        "",
        "| 금지 표현 | 올바른 표현 | 사유 | 위반 강도 |",
        "|----------|------------|------|----------|",
    ]
    for b in banned:
        desc = b.get("reason_i18n", {}).get("ko") or b.get("reason", "")
        severity = b.get("severity", "warn")
        lines.append(
            f"| `{b['expression']}` | `{b['correct']}` | {desc} | {severity} |"
        )

    lines.append("")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════
# 식별자 단어 분해 헬퍼
# ════════════════════════════════════════════════════════════════════

def tokenize(identifier: str) -> list:
    s = identifier.replace('-', '_')
    # camelCase 분해
    s = re.sub(r'([a-z])([A-Z])', r'\1_\2', s)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    return [t.lower() for t in s.split('_') if t]


def build_n_pattern_regexes(compounds: list) -> list:
    """
    compounds id 중 [N] 패턴을 정규식으로 변환.
    예) [N]m -> ^\d+m$, top[N] -> ^top\d+$
    """
    patterns = []
    for c in compounds:
        cid = c.get("id", "")
        if "[N]" not in cid:
            continue
        pat = re.escape(cid).replace(r"\[N\]", r"\d+")
        patterns.append((cid, re.compile(rf"^{pat}$", re.IGNORECASE)))
    return patterns


def match_n_pattern(token: str, n_patterns: list) -> str | None:
    for cid, cre in n_patterns:
        if cre.fullmatch(token):
            return cid
    return None


def find_singular_token(token: str, word_ids: dict) -> str | None:
    """
    복수형 토큰을 단수형으로 역변환해 words.json 존재 여부 확인.
    """
    if token.endswith("ies") and len(token) > 3:
        cand = token[:-3] + "y"
        if cand in word_ids:
            return cand
    if token.endswith("es") and len(token) > 2:
        cand = token[:-2]
        if cand in word_ids:
            return cand
    if token.endswith("s") and len(token) > 1:
        cand = token[:-1]
        if cand in word_ids:
            return cand
    return None


# ════════════════════════════════════════════════════════════════════
# 명령 구현
# ════════════════════════════════════════════════════════════════════

def cmd_generate():
    words, compounds, banned = load_all()
    fatals, _ = validate(words, compounds, banned, silent=False)
    if fatals:
        print("[FAIL] FATAL 오류가 있어 생성을 중단합니다.")
        sys.exit(1)

    DICT_DIR.mkdir(exist_ok=True)

    # terms.json
    terms_data = build_terms_json(words, compounds)
    TERMS_PATH.write_text(json.dumps(terms_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[OK] terms.json 생성 ({len(terms_data['terms'])}개)")

    # Index Shift
    INDEX_DIR = ROOT / "build" / "index"
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    
    # Strip unnecessary fields for minimum size
    word_min = [{"id": w["id"], "lang": w.get("lang", {}), "domain": w.get("domain")} for w in words]
    compound_min = [{"id": c["id"], "words": c.get("words", []), "lang": c.get("lang", {}), "domain": c.get("domain")} for c in compounds]
    
    variant_map = {}
    for w in words:
        abbrs = w.get("variants", {}).get("abbreviation") or []
        if isinstance(abbrs, str): abbrs = [abbrs]
        for a in abbrs:
            variant_map[a] = {"root": w["id"], "type": "abbreviation"}
            
    for c in compounds:
        abbr = c.get("abbr", {}).get("short")
        if abbr:
            variant_map[abbr] = {"root": c["id"], "type": "abbreviation"}

    (INDEX_DIR / "word_min.json").write_text(json.dumps(word_min, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (INDEX_DIR / "compound_min.json").write_text(json.dumps(compound_min, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (INDEX_DIR / "variant_map.json").write_text(json.dumps(variant_map, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f"[OK] Index 생성 (build/index/word_min.json, compound_min.json, variant_map.json)")

    # GLOSSARY.md
    md = build_glossary_md(words, compounds, banned)
    GLOSSARY_PATH.write_text(md, encoding='utf-8')
    print(f"[OK] GLOSSARY.md 생성")


def cmd_validate():
    words, compounds, banned = load_all()
    fatals, warns = validate(words, compounds, banned)
    sys.exit(1 if fatals else 0)


def cmd_stats():
    words, compounds, banned = load_all()
    from collections import Counter

    print(f"\n{'='*40}")
    print(f"  BOM_TS Glossary 통계")
    print(f"{'='*40}")
    print(f"  단어     : {len(words)}개")
    print(f"  복합어   : {len(compounds)}개")
    print(f"  금지표현 : {len(banned)}개")

    print(f"\n  [단어 domain 분포]")
    dc = Counter(w["domain"] for w in words)
    for d, n in dc.most_common():
        print(f"    {d:<12}: {n}개")

    print(f"\n  [단어 pos 분포]")
    pc = Counter(w["pos"] for w in words)
    for p, n in pc.most_common():
        print(f"    {p:<10}: {n}개")

    print(f"\n  [복합어 등록 사유]")
    rc = Counter()
    for c in compounds:
        for r in c.get("reason","").split(","):
            rc[r.strip()] += 1
    for r, n in rc.most_common():
        print(f"    {r:<20}: {n}개")
    print()


def cmd_check_id(identifier: str):
    INDEX_DIR = ROOT / "build" / "index"
    w_idx = INDEX_DIR / "word_min.json"
    c_idx = INDEX_DIR / "compound_min.json"
    v_idx = INDEX_DIR / "variant_map.json"
    if not w_idx.exists() or not c_idx.exists() or not v_idx.exists():
        print("인덱스가 없습니다. 'python generate_glossary.py generate'를 먼저 실행하세요.")
        sys.exit(1)
        
    words = json.loads(w_idx.read_text(encoding='utf-8'))
    compounds = json.loads(c_idx.read_text(encoding='utf-8'))
    variant_map = json.loads(v_idx.read_text(encoding='utf-8'))
    # Make a lowercase map for case-insensitive lookup
    variant_map_lower = {k.lower(): v for k, v in variant_map.items()}
    
    word_ids = {w["id"]: w for w in words}
    compound_ids = {c["id"]: c for c in compounds}
    n_patterns = build_n_pattern_regexes(compounds)

    tokens = tokenize(identifier)
    print(f"\n식별자: {identifier}")
    print(f"분해:   {tokens}\n")

    missing = []
    pattern_hits = []
    
    normalized_list = []
    variant_list = []

    for tok in tokens:
        # Check variant specifically
        if tok in variant_map_lower:
            v_info = variant_map_lower[tok]
            root_id = v_info["root"]
            normalized_list.append(root_id)
            variant_list.append(v_info["type"])
            print(f"  {tok:<20} → [WARN] abbreviation 사용 (root: {root_id})")
        elif tok in word_ids:
            w = word_ids[tok]
            ko_val = w.get("lang", {}).get("ko", "")
            normalized_list.append(tok)
            print(f"  {tok:<20} → [OK]  word_min.json ({w.get('domain', '')}, \"{ko_val}\")")
        elif tok in compound_ids:
            c = compound_ids[tok]
            ko_val = c.get("lang", {}).get("ko", "")
            normalized_list.append(tok)
            print(f"  {tok:<20} → [OK]  compound_min.json (\"{ko_val}\")")
        else:
            matched = match_n_pattern(tok, n_patterns)
            if matched:
                pattern_hits.append((tok, matched))
                normalized_list.append(tok)
                print(f"  {tok:<20} → [OK]  compound_min.json (pattern: '{matched}')")
            else:
                singular = find_singular_token(tok, word_ids)
                if singular:
                    w = word_ids[singular]
                    ko_val = w.get("lang", {}).get("ko", "")
                    normalized_list.append(singular)
                    variant_list.append("plural_to_singular")
                    print(f"  {tok:<20} → [OK]  word_min.json ({w.get('domain', '')}, \"{ko_val}\", singular='{singular}')")
                else:
                    print(f"  {tok:<20} → [ERROR] 미등록")
                    missing.append(tok)

    print()
    if missing:
        print(f"미등록 단어 {len(missing)}개: {missing}")
        print(f"→ words.json에 등록 후 사용 가능합니다.")
        print(f"→ python generate_glossary.py suggest {identifier}")
    else:
        # JSON 결과 출력 (정책 참조)
        result_payload = {
            "normalized": normalized_list,
        }
        if variant_list:
            result_payload["variant"] = variant_list
            
        print("결과:")
        print(json.dumps(result_payload, indent=2, ensure_ascii=False))

        # 복합어 등록 필요 여부
        if identifier in compound_ids:
            print(f"→ 복합어로 이미 등록됨.")
        elif match_n_pattern(identifier, n_patterns):
            print(f"→ [N] 패턴 복합어로 매칭됨.")
        elif len(tokens) > 1:
            print(f"→ 모든 단어 등록됨. 복합어 등록은 조건 충족 시만 필요.")
        else:
            print(f"→ 단어로 등록됨.")
    print()


def cmd_suggest(identifier: str):
    words, compounds, _ = load_all()
    word_ids = {w["id"] for w in words}
    word_lookup = {w["id"]: w for w in words}
    n_patterns = build_n_pattern_regexes(compounds)
    tokens = tokenize(identifier)
    missing = [
        t for t in tokens
        if t not in word_ids
        and not match_n_pattern(t, n_patterns)
        and not find_singular_token(t, word_lookup)
    ]

    if not missing:
        print(f"\n'{identifier}' — 모든 단어가 이미 등록되어 있습니다.\n")
        return

    print(f"\n미등록 단어 제안 ({len(missing)}개):\n")
    for tok in missing:
        template = {
            "id":          tok,
            "domain":      "general",
            "status":      "active",
            "canonical_pos": "noun",
            "lang": {
                "en": tok,
                "ko": ""
            },
            "description_i18n": {
                "ko": ""
            }
        }
        print(json.dumps(template, ensure_ascii=False, indent=2))
        print()

    if len(tokens) > 1:
        print("복합어 등록 필요 여부: 조건 충족 여부 확인 필요")
        print("  1. 의미 비합산  2. 공인 약어  3. 혼동 방지  4. 시스템 객체  5. 고유명사")
    print()


def cmd_migrate(legacy_path: str):
    """기존 terms.json → words_draft.json + compounds_draft.json + migrate_review.md"""
    src = Path(legacy_path)
    if not src.exists():
        print(f"파일 없음: {legacy_path}")
        sys.exit(1)

    data   = json.loads(src.read_text(encoding='utf-8'))
    terms  = data.get("terms", [])
    print(f"[migrate] 기존 terms.json: {len(terms)}개 항목")

    CAT_TO_DOMAIN = {
        'order':'trading','risk':'trading','trading':'trading','domain':'trading','account':'trading',
        'market':'market','data':'market','selector':'market',
        'system':'system','status':'system','session':'system','module':'system','config':'system','class':'system',
        'infra':'infra','tool':'infra','report':'ui',
    }

    words_draft, compounds_draft, review = [], [], []

    for t in terms:
        tid    = t.get("id","")
        tokens = tokenize(tid)
        cats   = t.get("categories",[])
        domain = next((CAT_TO_DOMAIN.get(c) for c in cats if c in CAT_TO_DOMAIN), "general")
        as_    = t.get("abbr_short","")
        abbr   = as_ if (as_ and 2<=len(as_)<=5 and as_.isupper() and '_' not in as_) else None
        not_   = t.get("NOT",[])

        if len(tokens) <= 1:
            words_draft.append({
                "id": tid, "en": t.get("en","").lower() or tid,
                "ko": t.get("ko",tid), "abbr": abbr,
                "pos": "noun", "domain": domain,
                "description": t.get("description",""), "not": not_,
            })
        else:
            reasons = []
            if not_: reasons.append("혼동 방지")
            if abbr:  reasons.append("공인 약어")
            if any(c in ("class","module") for c in cats): reasons.append("시스템 객체")
            if not reasons: reasons.append("의미 비합산")

            auto = len(reasons) > 0 and reasons[0] != "의미 비합산"

            compounds_draft.append({
                "id": tid, "words": tokens,
                "ko": t.get("ko",""), "en": t.get("en",""),
                "abbr_long": t.get("abbr_long",""), "abbr_short": as_,
                "domain": domain, "description": t.get("description",""),
                "reason": ", ".join(reasons), "not": not_,
            })

            if not auto:
                review.append({
                    "id": tid, "tokens": tokens,
                    "reason_auto": ", ".join(reasons),
                    "action": "compound / word분리 / 삭제",
                })

    # 저장
    out = DICT_DIR
    out.mkdir(exist_ok=True)
    (out / "words_draft.json").write_text(
        json.dumps({"version":"1.0.0","words":words_draft}, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / "compounds_draft.json").write_text(
        json.dumps({"version":"1.0.0","compounds":compounds_draft}, ensure_ascii=False, indent=2), encoding='utf-8')

    # 리뷰 파일
    review_lines = [
        "# migrate_review.md — 사용자 판단 필요 항목\n",
        f"총 {len(review)}개 항목을 확인하세요.\n",
        "각 항목에서 action 을 결정해 주세요: **compound** / **word분리** / **삭제**\n\n",
    ]
    for r in review:
        review_lines.append(f"## {r['id']}")
        review_lines.append(f"- 분해: {r['tokens']}")
        review_lines.append(f"- 자동 사유: {r['reason_auto']}")
        review_lines.append(f"- **action**: {r['action']}\n")

    (out / "migrate_review.md").write_text("\n".join(review_lines), encoding='utf-8')

    print(f"[OK] words_draft.json    : {len(words_draft)}개")
    print(f"[OK] compounds_draft.json: {len(compounds_draft)}개")
    print(f"[OK] migrate_review.md   : 판단 필요 {len(review)}개")
    print(f"\n리뷰 완료 후:")
    print(f"  mv words_draft.json words.json")
    print(f"  mv compounds_draft.json compounds.json")
    print(f"  python generate_glossary.py generate")


# ════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="BOM_TS 용어 사전 생성·검증",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("generate",  help="GLOSSARY.md + terms.json 생성")
    sub.add_parser("validate",  help="검증만 (CI용)")
    sub.add_parser("stats",     help="통계 출력")

    p_check = sub.add_parser("check-id", help="식별자 단어 분해 확인")
    p_check.add_argument("identifier")

    p_suggest = sub.add_parser("suggest", help="미등록 단어 등록 제안")
    p_suggest.add_argument("identifier")

    p_migrate = sub.add_parser("migrate-from-legacy", help="기존 terms.json 마이그레이션")
    p_migrate.add_argument("legacy_path")

    args = parser.parse_args()

    if args.cmd == "generate":
        cmd_generate()
    elif args.cmd == "validate":
        cmd_validate()
    elif args.cmd == "stats":
        cmd_stats()
    elif args.cmd == "check-id":
        cmd_check_id(args.identifier)
    elif args.cmd == "suggest":
        cmd_suggest(args.identifier)
    elif args.cmd == "migrate-from-legacy":
        cmd_migrate(args.legacy_path)


if __name__ == "__main__":
    main()
