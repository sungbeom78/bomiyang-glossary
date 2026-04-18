import json
from pathlib import Path

WORDS_PATH = Path('dictionary/words.json')
d = json.loads(WORDS_PATH.read_text(encoding='utf-8'))
ws = d['words']

for w in ws:
    if w['id'] == 'cancel':
        # Ensure both cancelled (UK) and cancelling (UK) are present
        existing_vals = {v['value'].lower() for v in w.get('variants', [])}
        additions = []
        if 'cancelled' not in existing_vals:
            additions.append({"type": "past", "value": "cancelled"})
        if 'cancelling' not in existing_vals:
            additions.append({"type": "present_participle", "value": "cancelling"})
        w['variants'].extend(additions)
        print(f"cancel variants after fix: {[(v['type'],v['value']) for v in w['variants']]}")
        break

WORDS_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print("Saved.")
