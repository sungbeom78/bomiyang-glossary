"""
2차 정제 진단 스크립트
- more/most 형태 variants 잔존 여부
- from 값 분류 (lexical vs stage)
- variants 중복 존재 여부
- 신규 등록 경로 vs migration 경로 품질 비교
"""
import json, sys, re
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from normalize_build import is_lexical_from, norm_id

WORDS_PATH = ROOT / "dictionary" / "words.json"
data = json.loads(WORDS_PATH.read_text(encoding='utf-8'))
ws = data['words']

print("=" * 65)
print("  Glossary 2차 정제 진단")
print("=" * 65)

# 1. more/most 형태 variants 잔존
periphrastic = []
for w in ws:
    for v in (w.get('variants') or []):
        val = v.get('value', '')
        if val.startswith('more ') or val.startswith('most '):
            periphrastic.append((w['id'], v['type'], val))

print(f"\n[1] more/most (periphrastic) variants: {len(periphrastic)}")
for wid, vt, val in periphrastic[:20]:
    print(f"  {wid:20} {vt:25} -> {val}")

# 2. from 분류: lexical vs stage
word_ids = {w['id'] for w in ws}
from_lexical, from_stage, from_none = [], [], []
for w in ws:
    fv = w.get('from')
    if not fv:
        from_none.append(w['id'])
    elif is_lexical_from(fv, word_ids):
        from_lexical.append((w['id'], fv))
    else:
        from_stage.append((w['id'], fv))

print(f"\n[2] from 분류:")
print(f"  Lexical: {len(from_lexical)} | Stage/Unknown: {len(from_stage)} | None: {len(from_none)}")
print(f"  Stage/Unknown from values:")
for wid, fv in from_stage[:15]:
    print(f"    {wid:20} -> from={fv!r}")

# 3. variants 타입 중복 (동일 type+value 중복)
dup_words = []
for w in ws:
    pairs = [(v.get('type'), v.get('value','').lower()) for v in (w.get('variants') or [])]
    if len(pairs) != len(set(pairs)):
        from collections import Counter
        c = Counter(pairs)
        dups = [(p, cnt) for p, cnt in c.items() if cnt > 1]
        dup_words.append((w['id'], dups))

print(f"\n[3] variants 타입+값 중복 단어: {len(dup_words)}")
for wid, dups in dup_words[:10]:
    print(f"  {wid}: {dups}")

# 4. 73개 only-plural 단어 POS 확인 (진짜 명사인지)
only_plural = [w for w in ws
               if w.get('variants') and all(v.get('type') == 'plural' for v in w.get('variants', []))]
print(f"\n[4] Only-plural: {len(only_plural)}")
pos_dist = {}
for w in only_plural:
    pos = w.get('canonical_pos', 'unknown')
    pos_dist[pos] = pos_dist.get(pos, 0) + 1
print(f"  POS distribution: {pos_dist}")

# 5. fetch_fail/error 단어 variants 상태
fetch_fail_ids = ['cls','db','dsn','eod','goldenkey','kis','kosdaq','kospi',
                  'kr','main','meta','mt5','orderbook','pnl','postgresql',
                  'redis','upbit','url','vwap']
print(f"\n[5] fetch_fail 단어 variants:")
wmap = {w['id']:w for w in ws}
for wid in fetch_fail_ids:
    w = wmap.get(wid)
    if w:
        nv = len(w.get('variants') or [])
        has_desc = bool((w.get('description_i18n') or {}).get('en'))
        print(f"  {wid:15} nvar={nv} desc_en={has_desc} pos={w.get('canonical_pos','?')}")

# 6. 샘플 10개 (기존 단어) 품질 체크
print(f"\n[6] 기존 단어 10개 샘플 품질:")
sample_ids = ['trade','signal','order','position','stop','run','score','record','report','config']
for wid in sample_ids:
    w = wmap.get(wid)
    if w:
        vs = [(v['type'], v['value']) for v in (w.get('variants') or [])]
        has_plural = any(t == 'plural' for t, _ in vs)
        has_verb = any(t in ('verb_form','past','present_participle','past_participle') for t, _ in vs)
        has_deriv = any(t in ('noun_form','verb_derived','adj_form','adv_form','agent') for t, _ in vs)
        print(f"  {wid:15} pos={w.get('canonical_pos','?'):5} nvar={len(vs):2} plural={has_plural} verb={has_verb} deriv={has_deriv}")

print("\n" + "=" * 65)
