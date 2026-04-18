#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys
sys.path.insert(0, 'bin')

data  = json.load(open('dictionary/words.json', encoding='utf-8'))
words = data['words']

no_v     = [w for w in words if not w.get('variants')]
has_from = [w for w in words if w.get('from')]
no_desc  = [w for w in words if not (w.get('description_i18n') or {}).get('en')]
has_src  = [w for w in words if w.get('source_urls')]

print(f"Total words  : {len(words)}")
print(f"No variants  : {len(no_v)}")
print(f"  ids: {[w['id'] for w in no_v[:20]]}")
print(f"Has from     : {len(has_from)}")
print(f"  samples: {[(w['id'], w['from']) for w in has_from[:15]]}")
print(f"No desc_en   : {len(no_desc)}")
print(f"Has src_urls : {len(has_src)}")

print("\n--- Sample 10 words ---")
for w in words[:10]:
    vs = [v['value'] for v in (w.get('variants') or [])]
    print(f"  {w['id']:20} pos={w.get('canonical_pos',''):6} variants={vs}  from={w.get('from')!r}")
