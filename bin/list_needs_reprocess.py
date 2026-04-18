import json
d = json.load(open('dictionary/words.json', 'r', encoding='utf-8'))
ws = d['words']

STATUS_KEEP = {'closed','pending','trading','reporting','scoring','setting','trailing'}

only_plural = [w for w in ws
               if w.get('variants')
               and all(v.get('type') == 'plural' for v in w.get('variants', []))
               and w['id'] not in STATUS_KEEP]

no_variant = [w for w in ws
              if not w.get('variants')
              and w['id'] not in STATUS_KEEP]

needs_retry = only_plural + no_variant
# deduplicate
seen = set()
deduped = []
for w in needs_retry:
    if w['id'] not in seen:
        seen.add(w['id'])
        deduped.append(w['id'])

print(f"Only-plural: {len(only_plural)}")
print(f"No variants: {len(no_variant)}")
print(f"Total needs v1.2 re-enrichment: {len(deduped)}")
print(f"At 1.5s/word: ~{len(deduped)*1.5/60:.1f} min")
print()
print("IDs to reprocess:")
for wid in sorted(deduped):
    print(f"  {wid}")
