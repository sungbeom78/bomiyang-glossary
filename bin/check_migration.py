import json, sys
d = json.load(open('dictionary/words.json', 'r', encoding='utf-8'))
ws = d['words']
print(f'Total words: {len(ws)}')

no_desc = [w for w in ws if not (w.get('description_i18n') or {}).get('en')]
print(f'No desc_en: {len(no_desc)}')
print('  ids:', [w['id'] for w in no_desc])

STATUS_KEEP = {'closed','pending','trading','reporting','scoring','setting','trailing'}
no_var = [w for w in ws if not w.get('variants') and w['id'] not in STATUS_KEEP]
print(f'No variants (excl status): {len(no_var)}')
print('  ids:', [w['id'] for w in no_var[:20]])

only_plural = [w for w in ws if w.get('variants') and all(v.get('type')=='plural' for v in w.get('variants',[]))]
print(f'Only-plural variants: {len(only_plural)}')
print('  sample:', [(w['id'], w.get('canonical_pos')) for w in only_plural[:10]])

cancel = next((w for w in ws if w['id']=='cancel'), None)
if cancel:
    print(f"cancel: pos={cancel.get('canonical_pos')} nvar={len(cancel.get('variants',[]))} desc={bool((cancel.get('description_i18n') or {}).get('en'))}")
else:
    print('cancel: NOT FOUND')

active = next((w for w in ws if w['id']=='active'), None)
if active:
    print(f"active: pos={active.get('canonical_pos')} variants={[(v['type'],v['value']) for v in active.get('variants',[])]}")
