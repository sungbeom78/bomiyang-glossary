"""
patch_upper.py
'upper'는 이미 comparative 형태이므로 잘못 생성된 uppermore/uppermost 제거.
유사하게 잘못된 comparative/superlative variant 전체 정제.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
WORDS_PATH = ROOT / "dictionary" / "words.json"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

data = json.loads(WORDS_PATH.read_text(encoding='utf-8'))
ws = data['words']

# 패턴: word_id + "more" 또는 word_id + "most" 형태의 잘못된 comparative/superlative
fixed = 0
for w in ws:
    wid = w['id']
    variants = w.get('variants') or []
    before_count = len(variants)
    cleaned = []
    for v in variants:
        val = v.get('value', '').lower()
        vtype = v.get('type', '')
        # 잘못된 패턴: wordid + "more" / wordid + "most"
        if vtype in ('comparative', 'superlative'):
            if val == wid + 'more' or val == wid + 'most':
                print(f"  [REMOVE] {wid}: {vtype}={val!r}  (잘못된 appendix 형태)")
                continue
            # "more X" / "most X" 방어 (이미 없지만)
            if val.startswith('more ') or val.startswith('most '):
                print(f"  [REMOVE] {wid}: {vtype}={val!r}  (periphrastic)")
                continue
        cleaned.append(v)
    if len(cleaned) != before_count:
        w['variants'] = cleaned
        w['updated_at'] = NOW
        fixed += 1

WORDS_PATH.write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + '\n',
    encoding='utf-8'
)
print(f"[DONE] Fixed {fixed} words.")
