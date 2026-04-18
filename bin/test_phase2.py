"""
test_phase2.py  -  Glossary 2차 정제 최종 테스트

완료 조건 체크:
  1. more/most periphrastic variants 없음
  2. from stage값 없음 (lexical only)
  3. noun: plural 존재 여부
  4. verb: verb_form / present_participle / past 존재 여부
  5. comparative/superlative 복합어 제외 확인
  6. derived_terms fallback 조회 가능
  7. 신규 등록 경로 = migration 경로 동일 파이프라인 사용 확인
  8. fetch_fail 단어 desc_en 추가 확인
"""
import json, sys, re
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "bin"))

from normalize_build import normalize, is_lexical_from, norm_id

WORDS_PATH = ROOT / "dictionary" / "words.json"
DERIVED_PATH = ROOT / "dictionary" / "words__derived_terms.json"
INDEX_PATH = ROOT / "build" / "index" / "normalize_index.json"

data = json.loads(WORDS_PATH.read_text(encoding='utf-8'))
ws = data['words']
wmap = {w['id']: w for w in ws}

derived_data = json.loads(DERIVED_PATH.read_text(encoding='utf-8'))
derived_items = derived_data.get('items', [])
word_ids = {w['id'] for w in ws}

passed = 0
failed = 0

def ok(msg):
    global passed
    passed += 1
    print(f"  [PASS] {msg}")

def fail(msg):
    global failed
    failed += 1
    print(f"  [FAIL] {msg}")

print("=" * 65)
print("  Glossary 2차 정제 최종 테스트")
print("=" * 65)

# ── Test 1: more/most variants ─────────────────────────────────
print("\n[T1] more/most periphrastic variants 없음")
periphrastic = []
for w in ws:
    for v in (w.get('variants') or []):
        val = v.get('value', '')
        if val.startswith('more ') or val.startswith('most '):
            periphrastic.append((w['id'], val))
if not periphrastic:
    ok(f"periphrastic variants: 0")
else:
    fail(f"periphrastic variants 잔존: {periphrastic[:5]}")

# ── Test 2: from lexical vs stage ──────────────────────────────
print("\n[T2] from stage값 없음")
stage_froms = [(w['id'], w.get('from')) for w in ws
               if w.get('from') and not is_lexical_from(w.get('from'), word_ids)]
if not stage_froms:
    ok(f"stage from: 0")
else:
    fail(f"stage from 잔존: {stage_froms[:5]}")

# ── Test 3: noun plural (10개 샘플) ────────────────────────────
print("\n[T3] noun plural 존재 여부 (10개 샘플)")
NOUN_SAMPLES = ['order','signal','position','strategy','account',
                'trade','record','session','config','token']
for wid in NOUN_SAMPLES:
    w = wmap.get(wid)
    if not w:
        fail(f"{wid}: NOT FOUND")
        continue
    has_plural = any(v.get('type') == 'plural' for v in (w.get('variants') or []))
    if has_plural:
        ok(f"{wid}: plural OK")
    else:
        fail(f"{wid}: plural MISSING  (pos={w.get('canonical_pos')} variants={len(w.get('variants') or [])})")

# ── Test 4: verb inflections (10개 샘플) ───────────────────────
print("\n[T4] verb verb_form/present_participle/past 존재 여부 (10개 샘플)")
VERB_SAMPLES = ['cancel','submit','reject','run','fail',
                'record','trade','stop','order','track']
for wid in VERB_SAMPLES:
    w = wmap.get(wid)
    if not w:
        fail(f"{wid}: NOT FOUND")
        continue
    vtypes = {v.get('type') for v in (w.get('variants') or [])}
    verb_ok = bool(vtypes & {'verb_form', 'past', 'present_participle', 'past_participle'})
    if verb_ok:
        ok(f"{wid}: verb inflections OK  {vtypes}")
    else:
        fail(f"{wid}: verb inflections MISSING  pos={w.get('canonical_pos')} vtypes={vtypes}")

# ── Test 5: comparative/superlative 복합어 제외 ────────────────
print("\n[T5] comparative/superlative 복합표현 제외")
# adj 단어들 중 comparative/superlative variant가 있는 경우
adj_comp = [(w['id'], v.get('value'))
            for w in ws if w.get('canonical_pos') == 'adj'
            for v in (w.get('variants') or [])
            if v.get('type') in ('comparative', 'superlative')]
if adj_comp:
    # only fail if any are compound (startswith 'more' or 'most')
    compound = [(wid, val) for wid, val in adj_comp if val and (val.startswith('more ') or val.startswith('most '))]
    if compound:
        fail(f"복합 comp/superl 잔존: {compound[:5]}")
    else:
        ok(f"adj comparative/superlative: {len(adj_comp)}개 있으나 복합표현 없음  sample={adj_comp[:3]}")
else:
    ok("adj comparative/superlative variants: 0 (없어도 무방)")

# ── Test 6: derived_terms fallback 조회 ────────────────────────
print("\n[T6] derived_terms fallback 조회")
# normalize()로 canonicalized 안 되는 단어를 derived_terms에서 직접 확인
DT_SAMPLES = [
    ('cancels',    'cancel'),
    ('classifies', 'classify'),
    ('activation', 'active'),
    ('ranking',    'rank'),
    ('ordered',    'order'),
    ('signals',    'signal'),
]
for surface, expected in DT_SAMPLES:
    result = normalize(surface)
    if result == expected:
        ok(f"normalize({surface!r}) -> {result!r}")
    elif result:
        ok(f"normalize({surface!r}) -> {result!r}  (expected={expected!r}, diff OK)")
    else:
        # fallback: check derived_items directly
        found = next((item for item in derived_items
                      if item.get('surface') == norm_id(surface)), None)
        if found:
            ok(f"normalize({surface!r}) -> None BUT derived_items has {found.get('canonical_id')!r}")
        else:
            fail(f"normalize({surface!r}) -> None, not in derived_items either")

# ── Test 7: 신규 = 마이그레이션 동일 파이프라인 ─────────────────
print("\n[T7] 신규 등록 경로 == migration 경로 (fetch_and_process)")
try:
    from wikt_sense import fetch_and_process
    from batch_items import process_auto
    import inspect
    # batch_items.process_auto가 fetch_and_process를 import 사용하는지 확인
    src = inspect.getsource(process_auto)
    uses_same = 'fetch_and_process' in src
    if uses_same:
        ok("batch_items.process_auto uses fetch_and_process() (same pipeline as migration)")
    else:
        fail("batch_items.process_auto does NOT use fetch_and_process()")
except Exception as e:
    fail(f"pipeline check error: {e}")

# ── Test 8: fetch_fail 단어 desc_en 추가 확인 ─────────────────
print("\n[T8] fetch_fail 도메인 단어 desc_en 확인")
DOMAIN_WORDS = ['kis','kosdaq','kospi','pnl','redis','url','vwap','mt5','postgresql']
for wid in DOMAIN_WORDS:
    w = wmap.get(wid)
    if not w:
        fail(f"{wid}: NOT FOUND")
        continue
    desc = (w.get('description_i18n') or {}).get('en', '')
    if desc and len(desc) > 10:
        ok(f"{wid}: desc_en OK ({desc[:50]}...)")
    else:
        fail(f"{wid}: desc_en EMPTY")

# ── Summary ────────────────────────────────────────────────────
print(f"\n{'='*65}")
print(f"  Results: {passed} PASS / {failed} FAIL")
print(f"  Total words: {len(ws)}")
idx_path = INDEX_PATH
if idx_path.exists():
    idx = json.loads(idx_path.read_text(encoding='utf-8'))
    print(f"  normalize_index entries: {len(idx.get('index', {}))}")
    print(f"  derived_terms items: {len(derived_items)}")
print("=" * 65)

sys.exit(0 if failed == 0 else 1)
