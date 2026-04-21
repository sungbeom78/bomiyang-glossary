import json
import urllib.request
import urllib.error
import time
import os

p = 'dictionary/words.json'
with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)

words_list = data.get('words', [])

updated = 0
for w in words_list:
    if not w.get('lang', {}).get('ko'):
        word_id = w['id']
        print(f"Fetching AI draft for: {word_id}")
        payload = json.dumps({"word": word_id}).encode('utf-8')
        req = urllib.request.Request(
            'http://127.0.0.1:5000/api/batch/ai_draft',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        try:
            res = urllib.request.urlopen(req)
            resp_data = json.loads(res.read().decode('utf-8'))
            if resp_data.get('ok'):
                if 'lang' not in w: w['lang'] = {}
                w['lang']['en'] = resp_data.get('en', word_id)
                w['lang']['ko'] = resp_data.get('ko', '')
                w['lang']['ja'] = resp_data.get('ja', '')
                w['lang']['zh'] = resp_data.get('zh', '')
                
                if 'description_i18n' not in w: w['description_i18n'] = {}
                w['description_i18n']['ko'] = resp_data.get('description_ko', '')
                w['description_i18n']['en'] = resp_data.get('description_en', '')
                
                print(f"  -> Added KO: {w['lang']['ko']}")
                updated += 1
            else:
                print(f"  -> Error API payload: {resp_data}")
        except urllib.error.URLError as e:
            print(f"  -> Connection Error: {e}")
            break
        # Throttle heavily so we don't bombard the API
        time.sleep(0.5)

if updated > 0:
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n[DONE] Updated {updated} words.")
else:
    print("\n[DONE] No updates made.")
