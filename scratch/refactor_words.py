import json
import os

WORDS_PATH = 'glossary/dictionary/words.json'

with open(WORDS_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

words = data.get('words', [])
id_map = {w['id']: w for w in words}

MERGE_PAIRS = [
    ('activity', 'active'),
    ('aggregator', 'aggregate'),
    ('application', 'apply'),
    ('auditor', 'audit'),
    ('calculator', 'calculate'),
    ('classification', 'classify'),
    ('collection', 'collect'),
    ('collector', 'collect'),
    ('escalated', 'escalate'),
    ('execution', 'execute'),
    ('generator', 'generate'),
    ('manager', 'manage'),
    ('normalization', 'normalize'),
    ('normalizer', 'normalize'),
    ('notifier', 'notify'),
    ('notification', 'notify'),
    ('recovery', 'recover'),
    ('resolution', 'resolve'),
    ('resolver', 'resolve'),
    ('scanner', 'scan'),
    ('selector', 'select'),
    ('similarity', 'similar'),
    ('started', 'start'),
    ('storage', 'store'),
    ('validation', 'validate'),
    ('volatility', 'volatile'),
    ('realized', 'realize'),
    ('extended', 'extend'),
    ('used', 'use')
]

if 'detection' in id_map and 'detect' not in id_map:
    # Rename detection to detect to create the base
    d = id_map['detection']
    d['id'] = 'detect'
    d['lang']['en'] = 'detect'
    d['canonical_pos'] = 'verb'
    if 'ko' in d['lang'] and d['lang']['ko'] == 'detection':
        d['lang']['ko'] = '탐지'
    id_map['detect'] = d
    del id_map['detection']
    
    # We still want to treat 'detection' as merged into 'detect'
    id_map['detection'] = d.copy() # temporarily for the merge loop to see it? Actually better:

if 'detect' in id_map:
    # Now detect is guaranteed to exist
    MERGE_PAIRS.extend([
        ('detection', 'detect'),
        ('detector', 'detect')
    ])

DETACH_PAIRS = [
    ('model', 'module'),
    ('module', 'model'),
    ('model', 'modularity'),
    ('model', 'modulization'),
    ('model', 'modulator'),
    ('model', 'modulation'),
    ('new', 'news'),
    ('news', 'new'),
    ('cleanup', 'clean'),
    ('clean', 'cleanup'),
    ('public', 'publish'),
    ('publish', 'public'),
    ('reentry', 'entry'),
    ('entry', 'reentry'),
    ('slip', 'slippage'),
    ('slippage', 'slip'),
    ('snap', 'snapshot'),
    ('snapshot', 'snap'),
    ('current', 'currency'),
    ('currency', 'current')
]

# Detaching
for detach_from, detach_what in DETACH_PAIRS:
    if detach_from in id_map:
        v_list = id_map[detach_from].get('variants', [])
        new_v_list = []
        for v in v_list:
            if v['value'] != detach_what:
                new_v_list.append(v)
        id_map[detach_from]['variants'] = new_v_list

# Merging
to_delete = set()

for derived_id, base_id in MERGE_PAIRS:
    # Try find them in words list
    base = None
    derived = None
    for w in words:
        if w['id'] == base_id: base = w
        if w['id'] == derived_id: derived = w
        
    if derived_id == 'detection' and base_id == 'detect' and derived is None:
        pass # Already handled by rename
        
    if base and derived and derived_id not in to_delete:
        print(f"Merging {derived_id} -> {base_id}")
        
        # Merge domains
        b_dom = base.get('domain', [])
        if isinstance(b_dom, str): b_dom = [b_dom]
        d_dom = derived.get('domain', [])
        if isinstance(d_dom, str): d_dom = [d_dom]
        
        new_doms = list(set(b_dom + d_dom))
        base['domain'] = new_doms
        
        # Merge variants (avoid duplicates string value)
        b_vars = base.get('variants', [])
        d_vars = derived.get('variants', [])
        
        existing_v = {v['value'] for v in b_vars}
        
        for dv in d_vars:
            if dv['value'] not in existing_v and dv['value'] != base_id:
                b_vars.append(dv)
                existing_v.add(dv['value'])
                
        # Also ensure derived_id itself is in base variants
        if derived_id not in existing_v and derived_id != base_id:
            # try to guess type or use generic derived
            t = "noun_form" if derived.get('canonical_pos') == "noun" else "derived"
            if derived.get('canonical_pos') == "adj": t = "adj_form"
            if derived.get('canonical_pos') == "verb": t = "verb_derived"
            b_vars.append({"types": [t], "value": derived_id})
            
        base['variants'] = b_vars
        to_delete.add(derived_id)

new_words = []
for w in words:
    if w['id'] not in to_delete:
        new_words.append(w)

data['words'] = new_words

# Save output
with open(WORDS_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Removed {len(to_delete)} duplicate entries by merging.")
