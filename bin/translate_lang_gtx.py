import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

WORDS_PATH = Path("dictionary/words.json")

def translate_text(text, target_lang):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req, timeout=5)
        data = json.loads(response.read().decode("utf8"))
        return data[0][0][0]
    except Exception as e:
        print(f"Error translating '{text}': {e}")
        return text

def main():
    with open(WORDS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    words = data.get("words", [])
    print(f"Translating {len(words)} words...", flush=True)
    
    for i, w in enumerate(words):
        en_text = w.get("lang", {}).get("en")
        if not en_text:
            continue
            
        ja_text = translate_text(en_text, "ja")
        zh_text = translate_text(en_text, "zh-CN")
        
        w["lang"]["ja"] = ja_text
        w["lang"]["zh_hans"] = zh_text
        
        if (i + 1) % 10 == 0:
            print(f"Translated {i + 1}/{len(words)}", flush=True)
        time.sleep(0.05)
        
    with open(WORDS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Words translation completed.", flush=True)

if __name__ == "__main__":
    main()
