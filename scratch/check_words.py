import json

with open('glossary/dictionary/words.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

words = data.get('words', [])

id_map = {w['id']: w for w in words}

collisions = []
for w in words:
    w_id = w['id']
    for v in w.get('variants', []):
        v_val = v['value']
        if v_val in id_map and v_val != w_id:
            collisions.append((w_id, v_val))

with open('collisions.txt', 'w', encoding='utf-8') as f:
    for c in collisions:
        f.write(f'{c[0]} -> {c[1]}\n')

with open('from_fields.txt', 'w', encoding='utf-8') as f:
    for w in words:
        if 'from' in w:
            f.write(f"{w['id']} is from {w['from']}\n")
