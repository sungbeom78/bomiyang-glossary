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
# 검증 (V-001 ~ V-103)
# ════════════════════════════════════════════════════════════════════

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

    # V-004: compounds.words[] 참조 검증
    word_id_set = set(word_ids)
    for c in compounds:
        for ref in c.get("words", []):
            if ref not in word_id_set:
                F("V-004", f"compounds['{c['id']}'].words 참조 미등록: '{ref}'")

    # V-005: compounds.reason 비어있지 않은지
    for c in compounds:
        if not c.get("reason","").strip():
            F("V-005", f"compounds['{c['id']}'].reason 비어있음")

    # V-006: abbr 중복
    word_abbrs     = [(w["abbr"], w["id"]) for w in words if w.get("abbr")]
    compound_abbrs = [(c["abbr_short"], c["id"]) for c in compounds if c.get("abbr_short")]
    all_abbrs = word_abbrs + compound_abbrs
    abbr_vals = [a[0] for a in all_abbrs]
    for abbr, aid in all_abbrs:
        if abbr_vals.count(abbr) > 1:
            others = [a[1] for a in all_abbrs if a[0] == abbr and a[1] != aid]
            F("V-006", f"abbr 중복: '{abbr}' → {aid}, {others}")

    # V-101: 고아 단어 (어떤 compound에서도 미참조)
    all_refs = set()
    for c in compounds:
        all_refs.update(c.get("words", []))
    for w in words:
        if w["id"] not in all_refs:
            W("V-101", f"고아 단어 (compound 미참조): '{w['id']}'")

    # V-102: banned.correct 가 words/compounds에 존재하는지
    all_ids = word_id_set | set(compound_ids)
    for b in banned:
        correct = b.get("correct","")
        # correct에 여러 표현이 있을 수 있으므로 단순 체크
        if correct and not any(x in correct for x in all_ids):
            W("V-102", f"banned.correct '{correct}' → 미등록 표현")

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
        abbr_short = w.get("abbr") or w["en"].upper()[:5]
        terms.append({
            "id":          w["id"],
            "ko":          w["ko"],
            "en":          w["en"].title(),
            "abbr_long":   w["en"],
            "abbr_short":  abbr_short,
            "categories":  [w["domain"]],
            "type":        "word",
            "description": w["description"],
        })
    for c in compounds:
        terms.append({
            "id":          c["id"],
            "ko":          c["ko"],
            "en":          c["en"],
            "abbr_long":   c["abbr_long"],
            "abbr_short":  c["abbr_short"],
            "categories":  [c["domain"]],
            "type":        "compound",
            "description": c["description"],
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
        lines.append("| 단어 | 한글 | 약어 | 품사 | 설명 |")
        lines.append("|------|------|------|------|------|")
        for w in wlist:
            abbr = w.get("abbr") or "—"
            lines.append(f"| `{w['id']}` | {w['ko']} | {abbr} | {w['pos']} | {w['description']} |")
        lines.append("")

    lines += [
        "---",
        "",
        "## 복합어 사전 (Compounds)",
        "",
        "| 복합어 | 구성 단어 | 한글 | camelCase | 약어 | 등록 사유 |",
        "|--------|----------|------|-----------|------|----------|",
    ]
    for c in sorted(compounds, key=lambda x: x["id"]):
        wds = " + ".join(c.get("words", []))
        lines.append(
            f"| `{c['id']}` | {wds} | {c['ko']} | `{c['abbr_long']}` | `{c['abbr_short']}` | {c['reason']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 금지 표현 (Banned)",
        "",
        "| 금지 표현 | 문맥 | 올바른 표현 | 사유 |",
        "|----------|------|------------|------|",
    ]
    for b in banned:
        lines.append(
            f"| `{b['expression']}` | {b['context']} | `{b['correct']}` | {b['reason']} |"
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
    words, compounds, _ = load_all()
    word_ids = {w["id"]: w for w in words}
    compound_ids = {c["id"]: c for c in compounds}

    tokens = tokenize(identifier)
    print(f"\n식별자: {identifier}")
    print(f"분해:   {tokens}\n")

    missing = []
    for tok in tokens:
        if tok in word_ids:
            w = word_ids[tok]
            print(f"  {tok:<20} → [OK]  words.json ({w['domain']}, {w['pos']}, \"{w['ko']}\")")
        elif tok in compound_ids:
            c = compound_ids[tok]
            print(f"  {tok:<20} → [OK]  compounds.json (\"{c['ko']}\")")
        else:
            print(f"  {tok:<20} → [미등록]")
            missing.append(tok)

    print()
    if missing:
        print(f"미등록 단어 {len(missing)}개: {missing}")
        print(f"→ words.json에 등록 후 사용 가능합니다.")
        print(f"→ python generate_glossary.py suggest {identifier}")
    else:
        # 복합어 등록 필요 여부
        if identifier in compound_ids:
            print(f"→ 복합어로 이미 등록됨.")
        elif len(tokens) > 1:
            print(f"→ 모든 단어 등록됨. 복합어 등록은 조건 충족 시만 필요.")
        else:
            print(f"→ 단어로 등록됨.")
    print()


def cmd_suggest(identifier: str):
    words, _, _ = load_all()
    word_ids = {w["id"] for w in words}
    tokens = tokenize(identifier)
    missing = [t for t in tokens if t not in word_ids]

    if not missing:
        print(f"\n'{identifier}' — 모든 단어가 이미 등록되어 있습니다.\n")
        return

    print(f"\n미등록 단어 제안 ({len(missing)}개):\n")
    for tok in missing:
        template = {
            "id":          tok,
            "en":          tok,
            "ko":          "",
            "abbr":        None,
            "pos":         "noun",
            "domain":      "general",
            "description": "",
            "not":         [],
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
