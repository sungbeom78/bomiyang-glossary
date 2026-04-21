#!/usr/bin/env python3
"""
generate_glossary.py v2.5.1  —  BOM_TS 용어 사전 생성·검증·조회
위치: glossary/generate_glossary.py

명령어:
  python generate_glossary.py generate          # GLOSSARY.md + terms.json 생성
  python generate_glossary.py validate          # 검증만 (CI용, 오류 시 exit 1)
  python generate_glossary.py stats             # 통계 출력
  python generate_glossary.py check-id <id>    # 식별자 단어 분해 + 등록 여부
  python generate_glossary.py suggest <id>     # 미등록 단어 등록 제안
  python generate_glossary.py migrate-from-legacy <terms.json>  # 마이그레이션

v2.5.1 변경:
  - terms.json checksum (sha256) 포함
  - V-010 (checksum CRITICAL), V-013 (banned 위반 ERROR) 검증 추가
  - deprecated → dictionary/terms_legacy.json 분리 생성
  - alias / misspelling projection 보강
  - 운영 산출물 4종 자동 생성 (build/report/)
"""

import sys
import io
import json
import re
import hashlib
import argparse
from datetime import datetime
from pathlib import Path

# ── Windows 인코딩 ──────────────────────────────────────────────────
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding.lower() not in ('utf-8','utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── 경로 ────────────────────────────────────────────────────────────
ROOT              = Path(__file__).parent.resolve()
DICT_DIR          = ROOT / "dictionary"
WORDS_PATH        = DICT_DIR / "words.json"
COMPOUNDS_PATH    = DICT_DIR / "compounds.json"
BANNED_PATH       = DICT_DIR / "banned.json"
TERMS_PATH        = DICT_DIR / "terms.json"           # 자동 생성 (projection)
TERMS_LEGACY_PATH = DICT_DIR / "terms_legacy.json"   # 자동 생성 (deprecated)
GLOSSARY_PATH     = ROOT / "GLOSSARY.md"              # 자동 생성 (루트에 유지)
REPORT_DIR        = ROOT / "build" / "report"         # 운영 산출물 디렉토리

DOMAINS = ["trading","market","system","infra","ui","general","proper"]
POS_LIST = ["noun","verb","adj","adv","prefix","suffix","proper"]

# Projection에 포함하는 variant type 목록 (§4.4)
# §4.4 확장: 형태론적 파생형(past/adj_form 등)도 variant_map에 포함하여
# check-id에서 reached→reach, reachable→reach 등이 올바르게 인식되도록 함.
PROJECTION_VARIANT_TYPES = {
    # 기존 (abbreviation/alias 계열)
    "abbreviation", "alias", "plural", "misspelling",
    # 굴절형 (inflection)
    "singular", "verb_form", "past", "past_participle",
    "present_participle", "comparative", "superlative",
    # 형태론적 파생형 (morphological derivation)
    "noun_form", "verb_derived", "adj_form", "adv_form",
    "agent", "gerund", "prefix", "suffix",
}
# Projection에서 제외하는 variant type 목록 (§4.5)
PROJECTION_EXCLUDE_TYPES = {"pos_forms", "deprecated", "adjective", "adverb"}



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


def validate(words, compounds, banned, silent=False, skip_checksum=False) -> tuple:
    """
    (fatals: list, warns: list) 반환.
    §7 Validation Gate:
      V-001: id unique (ERROR)
      V-004: dependency (ERROR)
      V-008: abbr unique (ERROR)
      V-010: checksum (CRITICAL) — skip_checksum=False 시 terms.json 존재하면 검증
               generate 전 validate 시에는 skip_checksum=True 사용
      V-011: schema (ERROR)
      V-013: banned (ERROR) — words/compounds id가 banned.expression과 대소문자 완전 일치
    """
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

    # abbreviation 검증 (variants array 형식 지원 — §2단계)
    abbr_to_root = {}

    def _get_abbrs_from_variants(variants_field) -> list:
        """variants array 또는 object에서 abbreviation 값 목록 추출."""
        if isinstance(variants_field, list):
            return [v["short"] for v in variants_field
                    if isinstance(v, dict) and v.get("type") == "abbreviation" and v.get("short")]
        elif isinstance(variants_field, dict):
            abbrs = variants_field.get("abbreviation") or []
            return [abbrs] if isinstance(abbrs, str) else (abbrs if isinstance(abbrs, list) else [])
        return []

    def _get_plurals_from_variants(variants_field) -> list:
        """variants array 또는 object에서 plural 값 목록 추출."""
        if isinstance(variants_field, list):
            return [v["value"] for v in variants_field
                    if isinstance(v, dict) and v.get("type") == "plural" and v.get("value")]
        elif isinstance(variants_field, dict):
            plurals = variants_field.get("plural") or []
            return [plurals] if isinstance(plurals, str) else (plurals if isinstance(plurals, list) else [])
        return []

    for w in words:
        abbrs = _get_abbrs_from_variants(w.get("variants"))
        for a in abbrs:
            al = a.lower()
            if al in abbr_to_root:
                W("V-201", f"약어 중복 정의: '{a}' ({abbr_to_root[al]} vs {w['id']})")
            abbr_to_root[al] = w["id"]

    for c in compounds:
        # array: abbreviation variant에서 short 추출 / 하위호환: abbr.short
        c_abbrs = _get_abbrs_from_variants(c.get("variants"))
        if not c_abbrs and c.get("abbr", {}).get("short"):
            c_abbrs = [c["abbr"]["short"]]
        for abbr in c_abbrs:
            al = abbr.lower()
            if al in abbr_to_root:
                W("V-201", f"약어 중복 정의: '{abbr}' ({abbr_to_root[al]} vs {c['id']})")
            abbr_to_root[al] = c["id"]

    for w in words:
        if w["id"] in abbr_to_root and abbr_to_root[w["id"]] != w["id"]:
            F("V-202", f"abbreviation이 word로 독립 존재: '{w['id']}' (root: {abbr_to_root[w['id']]})")


    # V-013: banned.expression이 words/compounds id와 대소문자 완전 일치 시 ERROR (§7)
    # 주의: KIS(banned) ↔ kis(id)는 약어와 식별자 분리이므로 오탐 제외.
    # exact match(case-sensitive)로만 충돌 판별.
    all_registered_ids = set(word_ids) | set(compound_ids)
    banned_expressions_exact = set(b.get("expression", "") for b in banned)
    for b_expr in banned_expressions_exact:
        if b_expr in all_registered_ids:
            F("V-013", f"banned.expression '{b_expr}'이 등록 id '{b_expr}'와 완전 일치 (대소문자 포함)")

    # V-011: words/compounds/banned 필수 필드 schema 검증 (§7)
    for w in words:
        if not w.get("id"):
            F("V-011", "words.json 항목에 'id' 필드 없음")
        if not w.get("domain"):
            F("V-011", f"words['{w.get('id', '?')}'] 'domain' 필드 없음")
        if not w.get("canonical_pos"):
            F("V-011", f"words['{w.get('id', '?')}'] 'canonical_pos' 필드 없음")
        if not w.get("lang", {}).get("en"):
            F("V-011", f"words['{w.get('id', '?')}'] lang.en 필드 없음")
        if not w.get("created_at"):
            F("V-011", f"words['{w.get('id', '?')}'] 'created_at' 필드 없음")
    for c in compounds:
        if not c.get("id"):
            F("V-011", "compounds.json 항목에 'id' 필드 없음")
        if not c.get("words"):
            F("V-011", f"compounds['{c.get('id', '?')}'] 'words' 필드 없음")
        if not c.get("domain"):
            F("V-011", f"compounds['{c.get('id', '?')}'] 'domain' 필드 없음")
        if not c.get("lang", {}).get("en"):
            F("V-011", f"compounds['{c.get('id', '?')}'] lang.en 필드 없음")
        if not c.get("created_at"):
            F("V-011", f"compounds['{c.get('id', '?')}'] 'created_at' 필드 없음")

    # V-010: terms.json checksum 검증 (존재할 때만, CRITICAL) (§4.9, §7)
    # generate 전 validate(skip_checksum=True) 시에는 건너뜀.
    # standalone validate 명령(skip_checksum=False)에서만 실행.
    if not skip_checksum and TERMS_PATH.exists():
        try:
            terms_data = json.loads(TERMS_PATH.read_text(encoding="utf-8"))
            ok, stored, computed = verify_checksum(terms_data)
            if not ok:
                # checksum 불일치는 CRITICAL → fatals에 추가
                F("V-010", f"terms.json checksum CRITICAL: stored={stored[:30]}... computed={computed[:30]}...")
        except Exception as e:
            W("V-010", f"terms.json checksum 검증 실패 (파일 읽기 오류): {e}")

    for dic, source in [(words, 'words.json'), (compounds, 'compounds.json'), (banned, 'banned.json')]:
        for item in dic:
            for f in ['created_at', 'updated_at', 'deprecated_at']:
                if f in item:
                    try:
                        datetime.fromisoformat(item[f].replace('Z', '+00:00'))
                    except Exception:
                        W('V-403', f"{source} {item.get('id', item.get('expression'))} - {f} 형식이 올바른 ISO8601이 아닙니다: {item[f]}")
            status = item.get('status', 'active')
            if status not in ['active', 'deprecated']:
                F('V-404', f"{source} {item.get('id', item.get('expression'))} - 잘못된 status 값: {status}")
            if status == 'deprecated' and 'deprecated_at' not in item:
                W('V-405', f"{source} {item.get('id', item.get('expression'))} - status가 deprecated인데 deprecated_at이 없습니다.")

    for w in words:
        if not w.get("description_i18n"):
            W("V-401", f"description_i18n 없음: '{w['id']}'")
        if not w.get("domain"):
            W("V-402", f"domain 없음: '{w['id']}'")
            
    for c in compounds:
        if not c.get("description_i18n"):
            W("V-401", f"description_i18n 없음: '{c['id']}'")
        if not c.get("domain"):
            W("V-402", f"domain 없음: '{c['id']}'")

    word_lookup = {w["id"]: w for w in words}

    # V-460: 도메인 내 약어(short) 유일성 검사 및 약어 식별자 금지
    abbr_registry = {}  # (domain, short.lower()) -> source_id
    
    def _check_abbr_uniqueness(item, item_type):
        abbr_field = item.get("abbreviation")
        if not abbr_field or not isinstance(abbr_field, dict):
            return
        short_val = abbr_field.get("short", "").strip()
        if not short_val:
            return
            
        # 약어가 id와 동일하면 안 됨
        if item["id"].lower() == short_val.lower():
            F("V-460", f"약어({short_val})가 {item_type} 식별자(id)로 사용됨: '{item['id']}'")
            
        domains = item.get("domain", ["general"])
        if isinstance(domains, str):
            domains = [domains]
            
        for d in domains:
            key = (d, short_val.lower())
            if key in abbr_registry:
                W("V-460", f"[{d}] 도메인 내 약어 충돌 발생: '{short_val}' ({abbr_registry[key]} vs {item['id']})")
            else:
                abbr_registry[key] = item["id"]

    for w in words: _check_abbr_uniqueness(w, "words")
    for c in compounds: _check_abbr_uniqueness(c, "compounds")

    # V-450: top-level abbreviation 필드 정합성 검증
    for w in words:
        abbr = w.get("abbreviation")
        if not abbr or not isinstance(abbr, dict):
            continue
        short = abbr.get("short", "").strip()
        long_ = abbr.get("long", "").strip()
        # V-450-A: abbreviation.long이 존재하지만 words에 미등록
        if long_ and long_ not in word_id_set:
            W("V-450", f"words['{w['id']}'].abbreviation.long='{long_}' 이 words에 미등록 (등록 권장)")
        # V-451: abbreviation.short가 독립 word로도 존재할 때 일관성 확인
        # → 해당 word의 canonical_pos가 'prefix'/'suffix'거나 'from' 필드 있어야 함
        if short and short.lower() in word_id_set:
            short_word = word_lookup.get(short.lower())
            if short_word:
                pos_s = short_word.get("canonical_pos", "")
                from_s = short_word.get("from", "")
                if pos_s not in ("prefix", "suffix") and not from_s:
                    W("V-451", (
                        f"abbreviation.short='{short}'이 독립 word로 존재하지만 "
                        f"canonical_pos='prefix'/'suffix' 또는 'from' 필드 없음 "
                        f"(root: '{w['id']}')"
                    ))

    for w in words:
        wid = w["id"]
        pos = w.get("canonical_pos") or w.get("pos", "noun")
        variants_field = w.get("variants")
        plurals = _get_plurals_from_variants(variants_field)
        # plural 정의 여부: array인 경우 plural type 항목이 있는지, object인 경우 'plural' 키 존재
        if isinstance(variants_field, list):
            plural_defined = any(v.get("type") == "plural" for v in variants_field if isinstance(v, dict))
        elif isinstance(variants_field, dict):
            plural_defined = "plural" in variants_field
        else:
            plural_defined = False

        # V-303
        for p in plurals:
            if p == wid:
                F("V-303", f"singular/plural self-conflict 금지: '{wid}'")
            if p in word_lookup and p != wid:
                F("V-301", f"plural root 금지: '{p}'가 독립 root로 존재함 (root: '{wid}')")  

        # V-351
        if pos == "noun" and plural_defined and not plurals:
            W("V-351", f"noun인데 variants.plural이 비어 있음: '{wid}'")

        # V-352
        ko_val = w.get("lang", {}).get("ko") or w.get("ko", "")
        if ko_val.endswith("들"):
            W("V-352", f"ko 표현이 집합 표현으로만 남아 있음: '{wid}' -> '{ko_val}'")

        # V-301 manual check
        if pos == "noun" and wid.endswith("s") and wid not in ["status", "kis", "redis", "cls", "us", "futures", "options", "goods", "series", "news", "basis"]:
            singular = None
            if wid.endswith("ies") and len(wid) > 3: singular = wid[:-3] + "y"
            elif wid.endswith("es") and len(wid) > 2: singular = wid[:-2]
            elif wid.endswith("s") and len(wid) > 1: singular = wid[:-1]
            if singular and singular in word_lookup:
                F("V-301", f"plural root 금지: '{wid}' (단수형 '{singular}'가 존재함)")

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
# checksum 계산 헬퍼 (§4.9)
# ════════════════════════════════════════════════════════════════════

def compute_checksum(data: dict) -> str:
    """terms 데이터의 sha256 checksum 계산 (checksum 필드 자체 제외)."""
    stable = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return "sha256:" + hashlib.sha256(stable.encode("utf-8")).hexdigest()


def verify_checksum(data: dict) -> tuple:
    """
    terms.json checksum 검증.
    반환: (ok: bool, stored: str, computed: str)
    """
    stored = data.get("checksum", "")
    payload = {k: v for k, v in data.items() if k != "checksum"}
    computed = compute_checksum(payload)
    return stored == computed, stored, computed


# ════════════════════════════════════════════════════════════════════
# terms.json 생성 (Projection — §4)
# ════════════════════════════════════════════════════════════════════

def _parse_variant_list(vlist):
    res = []
    for v in vlist:
        if not isinstance(v, dict): continue
        vtypes = v.get("types", [])
        if not vtypes and "type" in v: vtypes = [v["type"]]
        
        val = v.get("value", "")
        if "abbreviation" in vtypes:
            val = v.get("short") or val
        if not val or not isinstance(val, str): continue
        
        for vtype in vtypes:
            if vtype in PROJECTION_EXCLUDE_TYPES or vtype not in PROJECTION_VARIANT_TYPES: continue
            res.append((vtype, val.strip()))
    return res

def _extract_word_variants(w: dict) -> list:
    """
    word의 variants(array 또는 object)에서 projection 포함 대상 항목만 추출.
    반환: [(variant_type, value), ...]
    §4.4 포함: abbreviation, alias, plural, misspelling + 굴절형 + 파생형 전체 (확장)
    §4.5 제외: pos_forms, deprecated, adjective, adverb
    §4.6 top-level abbreviation 필드: word.abbreviation.short → 약어 resolve 지원
    2단계: variants array 형식 지원
    """
    variants_field = w.get("variants")
    result = []

    # — Array 형식 (§2단계 이후)
    if isinstance(variants_field, list):
        result.extend(_parse_variant_list(variants_field))

    # — Object 형식 (하위호환 — 이론상 마이그레이션 후 발생 안 함)
    elif isinstance(variants_field, dict):
        for vtype, vval in variants_field.items():
            if vtype in PROJECTION_EXCLUDE_TYPES:
                continue
            if vtype not in PROJECTION_VARIANT_TYPES:
                continue
            if isinstance(vval, list):
                for v in vval:
                    if v and isinstance(v, str):
                        result.append((vtype, v.strip()))
            elif isinstance(vval, str) and vval.strip():
                result.append((vtype, vval.strip()))

    # §4.6 — top-level abbreviation 필드 처리 (단어 단위 약어, 선택 필드)
    # 예: automatic.abbreviation.short = "auto" → variant_map["auto"] = {root:"automatic", type:"abbreviation"}
    abbr_field = w.get("abbreviation")
    if isinstance(abbr_field, dict):
        short = abbr_field.get("short", "").strip()
        if short:
            result.append(("abbreviation", short))

    return result


def build_terms_json(words, compounds) -> tuple:
    """
    (active_data: dict, legacy_data: dict) 반환.
    - active_data: terms.json (projection-only, checksum 포함)
    - legacy_data: terms_legacy.json (deprecated 항목)
    §1.1: terms.json은 100% projection 결과물. 역방향 수정 절대 금지.
    §4.6 우선순위: abbreviation > alias > plural > singular
    §4.7 충돌 처리: 동일 id ERROR / ambiguity high 제외
    §4.8 legacy: deprecated → terms_legacy.json
    §4.9 checksum 포함
    """
    active_terms = []
    legacy_terms = []
    skipped = []       # projection_skipped 산출물용
    seen_ids = {}      # id 충돌 감지 (§4.7)

    def _register_term(entry: dict, source_desc: str) -> bool:
        """id + domain 조합 검사 후 terms 리스트에 추가."""
        term_id = entry["id"]
        term_domain = entry["domain"]
        key = f"{term_id}@{term_domain}"
        if key in seen_ids:
            skipped.append({
                "id": term_id,
                "reason": "id_conflict",
                "detail": f"{source_desc} vs {seen_ids[key]}",
            })
            return False
        seen_ids[key] = source_desc
        return True

    def _unroll_domains(item: dict) -> list:
        ds = item.get("domain", ["general"])
        if isinstance(ds, str):
            return [ds]
        return list(set(ds)) if isinstance(ds, list) else ["general"]

    for w in words:
        wid = w["id"]
        lang = w.get("lang", {})
        desc_i18n = w.get("description_i18n", {})
        status = w.get("status", "active")
        
        for domain in _unroll_domains(w):
            base_entry = {
                "id": wid,
                "source": "word",
                "root": wid,
                "term_type": "base",
                "domain": domain,
                "lang": lang,
                "description_i18n": desc_i18n,
            }

            if status == "deprecated":
                base_entry["deprecated_at"] = w.get("deprecated_at", "")
                legacy_terms.append(base_entry)
                continue

            if _register_term(base_entry, f"word:{wid}:{domain}:base"):
                active_terms.append(base_entry)

            for vtype, vval in _extract_word_variants(w):
                entry = {
                    "id": vval,
                    "source": "word",
                    "root": wid,
                    "term_type": "variant",
                    "variant_type": vtype,
                    "domain": domain,
                    "lang": lang,
                }
                if _register_term(entry, f"word:{wid}:{domain}:{vtype}"):
                    active_terms.append(entry)

    for c in compounds:
        cid = c["id"]
        lang = c.get("lang", {})
        desc_i18n = c.get("description_i18n", {})
        status = c.get("status", "active")

        # compounds 도 top-level abbreviation을 가짐 (words와 동일)
        c_variants = []
        c_variants_field = c.get("variants")
        if isinstance(c_variants_field, list):
            c_variants.extend(_parse_variant_list(c_variants_field))
        elif isinstance(c_variants_field, dict):
            # 하위호환 (구)
            abbr_short_legacy = c_variants_field.get("abbr", {}).get("short")
            if abbr_short_legacy: c_variants.append(("abbreviation", abbr_short_legacy.strip()))
            for vtype, vval in c_variants_field.items():
                if vtype in PROJECTION_EXCLUDE_TYPES or vtype not in PROJECTION_VARIANT_TYPES: continue
                vals = [vval] if isinstance(vval, str) else (vval if isinstance(vval, list) else [])
                for v in vals:
                    if v: c_variants.append((vtype, v.strip()))
                    
        abbr_field = c.get("abbreviation")
        if isinstance(abbr_field, dict):
            short = abbr_field.get("short", "").strip()
            if short: c_variants.append(("abbreviation", short))

        for domain in _unroll_domains(c):
            base_entry = {
                "id": cid,
                "source": "compound",
                "root": cid,
                "term_type": "base",
                "domain": domain,
                "lang": lang,
                "description_i18n": desc_i18n,
            }

            if status == "deprecated":
                base_entry["deprecated_at"] = c.get("deprecated_at", "")
                legacy_terms.append(base_entry)
                continue

            if _register_term(base_entry, f"compound:{cid}:{domain}:base"):
                active_terms.append(base_entry)

            for vtype, vval in c_variants:
                if not vval: continue
                entry = {
                    "id": vval,
                    "source": "compound",
                    "root": cid,
                    "term_type": "variant",
                    "variant_type": vtype,
                    "domain": domain,
                    "lang": lang,
                }
                if _register_term(entry, f"compound:{cid}:{domain}:{vtype}"):
                    active_terms.append(entry)

    # §4.9 checksum 계산
    generated_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "_WARNING": "이 파일은 자동 생성됩니다. 수동 편집 금지. words.json과 compounds.json을 편집하세요.",
        "version": "3.0.0",
        "generated": True,
        "generated_at": generated_at,
        "terms": active_terms,
    }
    checksum = compute_checksum(payload)
    active_data = dict(payload)
    active_data["checksum"] = checksum

    legacy_data = {
        "_WARNING": "이 파일은 자동 생성됩니다. deprecated 항목만 포함. 수동 편집 금지.",
        "version": "3.0.0",
        "generated": True,
        "generated_at": generated_at,
        "terms": legacy_terms,
    }

    return active_data, legacy_data, skipped


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
            # variants array 형식 지원
            variants_f = w.get("variants")
            abbr_list = []
            if isinstance(variants_f, list):
                abbr_list = [v.get("short") or v.get("value", "") for v in variants_f
                             if isinstance(v, dict) and v.get("type") == "abbreviation"]
            elif isinstance(variants_f, dict):
                raw = variants_f.get("abbreviation") or []
                abbr_list = [raw] if isinstance(raw, str) else raw
            abbr = (abbr_list[0] if abbr_list else w.get("abbr")) or "—"
            pos = w.get("canonical_pos") or w.get("pos", "noun")
            if pos != "noun":
                plural = "—"
            else:
                pl_list = []
                if isinstance(variants_f, list):
                    pl_list = [v.get("value", "") for v in variants_f
                               if isinstance(v, dict) and v.get("type") == "plural"]
                elif isinstance(variants_f, dict):
                    raw_pl = variants_f.get("plural")
                    pl_list = [raw_pl] if isinstance(raw_pl, str) else (raw_pl or [])
                plural = ", ".join(pl_list) if pl_list else "auto"
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
        # variants array: abbreviation 항목에서 long/short 추출
        c_variants = c.get("variants")
        abbr_long, abbr_short = "", ""
        c_plural_vals = []
        if isinstance(c_variants, list):
            for v in c_variants:
                if not isinstance(v, dict):
                    continue
                if v.get("type") == "abbreviation":
                    abbr_short = abbr_short or v.get("short", "")
                    abbr_long  = abbr_long  or v.get("long",  "")
                elif v.get("type") == "plural":
                    c_plural_vals.append(v.get("value", ""))
        else:
            # 하위호환: abbr object
            abbr_long  = c.get("abbr", {}).get("long",  "") or c.get("abbr_long",  "")
            abbr_short = c.get("abbr", {}).get("short", "") or c.get("abbr_short", "")
            raw_pl = c.get("variants", {}).get("plural") if isinstance(c.get("variants"), dict) else None
            if isinstance(raw_pl, list): c_plural_vals = raw_pl
            elif isinstance(raw_pl, str): c_plural_vals = [raw_pl]
        c_plural_txt = ", ".join(c_plural_vals) if c_plural_vals else "auto"
        ko_val = c.get("lang", {}).get("ko") or c.get("ko", "")
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
        desc = b.get("reason_i18n", {}).get("ko", "")
        severity = b.get("severity", "warn")
        correct = b.get("correct", {}).get("value", "") if isinstance(b.get("correct"), dict) else str(b.get("correct", ""))
        lines.append(
            f"| `{b['expression']}` | `{correct}` | {desc} | {severity} |"
        )

    lines.append("")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════
# Prepositions and articles that carry no naming semantics — always removed from tokens.
_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the",
    "at", "by", "for", "from", "in", "of", "on", "to", "with",
})


def _strip_numeric_suffix(tokens: list) -> list:
    """
    같은 알파 접두사에 숫자만 다른 토큰이 2개 이상 존재하면
    숫자 부분을 제거하고 알파 부분만 남긴다.

    예) ['stage', '1'], ['stage', '2'], ['stage', '3']  →  ['stage']
        ['scenario', '1'], ['scenario', '2']              →  ['scenario']
        ['phase', '1']  (단 1개)                           →  ['phase', '1']  (제거 안 함)

    처리 대상: 순수 숫자 토큰이 바로 앞 알파 토큰과 짝을 이루는 경우만.
    이는 tokenize() 내부에서 이미 분리된 토큰 목록에 적용한다.
    """
    from collections import defaultdict
    # [alpha_prefix → list[numeric_token]] 집계
    prefix_nums: dict[str, list[str]] = defaultdict(list)
    i = 0
    # (alpha, digit) 인접 쌍을 수집
    while i < len(tokens) - 1:
        alpha = tokens[i]
        digit = tokens[i + 1]
        if alpha.isalpha() and digit.isdigit():
            prefix_nums[alpha].append(digit)
        i += 1

    # 2개 이상의 숫자 변형이 있는 접두사만 대상으로 삼음
    remove_pairs: set[tuple[str, str]] = set()
    for alpha, nums in prefix_nums.items():
        if len(nums) >= 2:
            for n in nums:
                remove_pairs.add((alpha, n))

    if not remove_pairs:
        return tokens

    # remove_pairs에 해당하는 (alpha, digit) 인접 쌍에서 digit 제거
    result: list[str] = []
    i = 0
    while i < len(tokens):
        if i < len(tokens) - 1:
            pair = (tokens[i], tokens[i + 1])
            if pair in remove_pairs:
                result.append(tokens[i])
                i += 2  # digit 건너뜀
                continue
        result.append(tokens[i])
        i += 1
    return result


def tokenize(identifier: str) -> list:
    """
    식별자를 소문자 단어 토큰 목록으로 분해한다.

    처리 순서:
    1. 특수문자(하이픈, 슬래시, 괄호, 점 등)를 밑줄 구분자로 치환
    2. camelCase / PascalCase → snake_case 분해
    3. 알파/숫자 경계에서 추가 분리 (sma5 → sma, 5)
    4. 순수 숫자만인 토큰은 유지 (뒤에서 숫자 패턴 처리)
    5. 전치사/관사(stop words) 제거
    6. 복수 숫자 변형(stage1/stage2/...) 패턴에서 숫자 부분 제거
    """
    # Step 1: 공백 및 특수문자(하이픈, 슬래시, 괄호 등)를 밑줄로 치환
    s = re.sub(r"[\s\-/\\.()\[\]{}<>:,;!?@#$%^&*+=|~`'\"]", "_", identifier)

    # Step 2: camelCase 분해
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)

    # Step 3: 알파/숫자 경계 분리 (예: stage1 → stage, 1)
    s = re.sub(r"([A-Za-z])(\d)", r"\1_\2", s)
    s = re.sub(r"(\d)([A-Za-z])", r"\1_\2", s)

    # 기본 분해
    raw_tokens = [t.lower() for t in s.split("_") if t]

    # Step 4: 빈 문자열 제거
    raw_tokens = [t for t in raw_tokens if t]

    # Step 5: 전치사/관사(stop words) 제거
    filtered = [t for t in raw_tokens if t not in _STOP_WORDS]

    # Step 6: 복수 숫자 변형 패턴에서 숫자 제거 (stage1/stage2 → stage)
    filtered = _strip_numeric_suffix(filtered)

    return filtered


def build_n_pattern_regexes(compounds: list) -> list:
    """
    compounds id 중 [N] 패턴을 정규식으로 변환.
    예) [N]m -> ^\\d+m$, top[N] -> ^top\\d+$
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

def _build_report_dependency_missing(words: list, compounds: list) -> list:
    """dependency_missing.json 내용 생성 (§11, §6.2)."""
    word_id_set = set(w["id"] for w in words)
    compound_id_set = set(c["id"] for c in compounds)
    missing = []
    for c in compounds:
        for ref in c.get("words", []):
            if ref not in word_id_set and ref not in compound_id_set:
                missing.append({"compound": c["id"], "missing_ref": ref})
    return missing


def _build_report_banned_autofix(words: list, compounds: list, banned: list) -> list:
    """banned_autofix_report.json 내용 생성 (§9, §11)."""
    report = []
    all_ids = {w["id"] for w in words} | {c["id"] for c in compounds}
    for b in banned:
        expr = b.get("expression", "")
        correct_val = ""
        if isinstance(b.get("correct"), dict):
            correct_val = b["correct"].get("value", "")
        elif isinstance(b.get("correct"), str):
            correct_val = b["correct"]
        severity = b.get("severity", "warn")
        # §9 원칙: 코드 자동 수정 금지, glossary 내부 mapping만 허용
        report.append({
            "expression": expr,
            "correct": correct_val,
            "severity": severity,
            "autofix_allowed": False,  # §9: 코드 자동 수정 절대 금지
            "correct_registered": correct_val.split()[0] in all_ids if correct_val else False,
        })
    return report


def _build_report_merge_candidates(words: list) -> list:
    """merge_candidates.json — 의미/ko가 동일한 word 후보 (§11)."""
    from collections import defaultdict
    ko_groups = defaultdict(list)
    for w in words:
        ko = w.get("lang", {}).get("ko") or ""
        if ko:
            ko_groups[ko].append(w["id"])
    candidates = [
        {"ko": ko, "ids": ids, "action": "review_merge_or_keep"}
        for ko, ids in ko_groups.items() if len(ids) > 1
    ]
    return candidates


def cmd_generate():
    words, compounds, banned = load_all()
    # generate 전 validate: 기존 terms.json의 checksum은 검증하지 않음 (skip_checksum=True)
    # 이유: generate 자체가 새 terms.json을 생성하는 과정이므로
    fatals, _ = validate(words, compounds, banned, silent=False, skip_checksum=True)
    if fatals:
        print("[FAIL] FATAL 오류가 있어 생성을 중단합니다.")
        sys.exit(1)

    DICT_DIR.mkdir(exist_ok=True)

    # terms.json + terms_legacy.json (§4.8, §4.9)
    active_data, legacy_data, skipped = build_terms_json(words, compounds)
    TERMS_PATH.write_text(json.dumps(active_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[OK] terms.json 생성 ({len(active_data['terms'])}개, checksum 포함)")

    TERMS_LEGACY_PATH.write_text(json.dumps(legacy_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[OK] terms_legacy.json 생성 ({len(legacy_data['terms'])}개 deprecated 항목)")

    # 운영 산출물 (§11)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    dep_missing = _build_report_dependency_missing(words, compounds)
    (REPORT_DIR / "dependency_missing.json").write_text(
        json.dumps({"generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "count": len(dep_missing), "items": dep_missing},
                   ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[OK] dependency_missing.json ({len(dep_missing)}건)")

    proj_skipped = skipped
    (REPORT_DIR / "projection_skipped.json").write_text(
        json.dumps({"generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "count": len(proj_skipped), "items": proj_skipped},
                   ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[OK] projection_skipped.json ({len(proj_skipped)}건)")

    merge_cands = _build_report_merge_candidates(words)
    (REPORT_DIR / "merge_candidates.json").write_text(
        json.dumps({"generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "count": len(merge_cands), "items": merge_cands},
                   ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[OK] merge_candidates.json ({len(merge_cands)}건)")

    banned_report = _build_report_banned_autofix(words, compounds, banned)
    (REPORT_DIR / "banned_autofix_report.json").write_text(
        json.dumps({"generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "count": len(banned_report), "items": banned_report},
                   ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[OK] banned_autofix_report.json ({len(banned_report)}건)")

    # Index 생성
    INDEX_DIR = ROOT / "build" / "index"
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Keep the runtime index sparse, but preserve naming-gate metadata for AI agents.
    word_min = [
        {
            "id": w["id"],
            "lang": w.get("lang", {}),
            "domain": w.get("domain"),
            "status": w.get("status"),
            "canonical_pos": w.get("canonical_pos"),
        }
        for w in words
    ]
    compound_min = [
        {
            "id": c["id"],
            "words": c.get("words", []),
            "lang": c.get("lang", {}),
            "domain": c.get("domain"),
            "status": c.get("status"),
        }
        for c in compounds
    ]

    # variant_map: PROJECTION_VARIANT_TYPES 전체 포함 (§4.4) — array + object 하위호환
    variant_map = {}
    for w in words:
        for vtype, vval in _extract_word_variants(w):
            variant_map[vval] = {"root": w["id"], "type": vtype}

    for c in compounds:
        c_vf = c.get("variants")
        if isinstance(c_vf, list):
            # §2단계 array 형식
            for v in c_vf:
                if not isinstance(v, dict):
                    continue
                vtype = v.get("type", "")
                if vtype in PROJECTION_EXCLUDE_TYPES or vtype not in PROJECTION_VARIANT_TYPES:
                    continue
                val = v.get("short") if vtype == "abbreviation" else v.get("value", "")
                if val:
                    variant_map[val] = {"root": c["id"], "type": vtype}
        elif isinstance(c_vf, dict):
            # §1단계 object 형식 하위호환
            abbr = c.get("abbr", {}).get("short")
            if abbr:
                variant_map[abbr] = {"root": c["id"], "type": "abbreviation"}
            for vtype, vval in c_vf.items():
                if vtype in PROJECTION_EXCLUDE_TYPES or vtype not in PROJECTION_VARIANT_TYPES:
                    continue
                vals = [vval] if isinstance(vval, str) else (vval if isinstance(vval, list) else [])
                for v in vals:
                    if v:
                        variant_map[v] = {"root": c["id"], "type": vtype}

    (INDEX_DIR / "word_min.json").write_text(
        json.dumps(word_min, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (INDEX_DIR / "compound_min.json").write_text(
        json.dumps(compound_min, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (INDEX_DIR / "variant_map.json").write_text(
        json.dumps(variant_map, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f"[OK] Index 생성 (build/index/)")

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
    pc = Counter(w.get("canonical_pos") or w.get("pos", "unknown") for w in words)
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
        # 순수 숫자 토큰: [N] 패턴 매칭 후 통과 처리
        if tok.isdigit():
            normalized_list.append(tok)
            print(f"  {tok:<20} → [OK]  numeric literal (skip glossary check)")
            continue
        # Check variant specifically
        if tok in variant_map_lower:
            v_info = variant_map_lower[tok]
            root_id = v_info["root"]
            normalized_list.append(root_id)
            variant_list.append(v_info["type"])
            if v_info["type"] == "abbreviation":
                print(f"  {tok:<20} → [WARN] abbreviation 사용 (root: {root_id})")
            elif v_info["type"] == "plural":
                print(f"  {tok:<20} → [INFO] plural variant 정규화 (root: {root_id})")
            else:
                print(f"  {tok:<20} → [INFO] variant 사용: {v_info['type']} (root: {root_id})")
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
        normalized_identifier = "_".join(normalized_list)
        if normalized_identifier in compound_ids or identifier in compound_ids:
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

    for w in words:
        if not w.get("description_i18n"):
            W("V-401", f"description_i18n 없음: '{w['id']}'")
        if not w.get("domain"):
            W("V-402", f"domain 없음: '{w['id']}'")
            
    for c in compounds:
        if not c.get("description_i18n"):
            W("V-401", f"description_i18n 없음: '{c['id']}'")
        if not c.get("domain"):
            W("V-402", f"domain 없음: '{c['id']}'")

    word_lookup = {w["id"]: w for w in words}
    n_patterns = build_n_pattern_regexes(compounds)
    tokens = tokenize(identifier)
    missing = [
        t for t in tokens
        if not t.isdigit()
        and t not in word_ids
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
        
        # AI 초안 서버 연동 (선택적)
        try:
            import urllib.request
            payload = json.dumps({"word": tok}).encode('utf-8')
            req = urllib.request.Request(
                'http://127.0.0.1:5000/api/batch/ai_draft',
                data=payload,
                headers={'Content-Type': 'application/json'}
            )
            res = urllib.request.urlopen(req, timeout=3.0)
            ai_data = json.loads(res.read().decode('utf-8'))
            if ai_data.get('ok'):
                template["lang"]["ko"] = ai_data.get('ko', "")
                template["lang"]["en"] = ai_data.get('en', tok)
                template["lang"]["ja"] = ai_data.get('ja', "")
                template["lang"]["zh"] = ai_data.get('zh', "")
                template["description_i18n"]["ko"] = ai_data.get('description_ko', "")
                template["description_i18n"]["en"] = ai_data.get('description_en', "")
                print(f"(* AI 자동 채움: {template['lang']['ko']})")
        except Exception as e:
            pass

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
