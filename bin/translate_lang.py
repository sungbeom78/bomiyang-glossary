#!/usr/bin/env python3
import json
import time
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("pip install deep-translator is required")
    import sys; sys.exit(1)

WORDS_PATH = Path("dictionary/words.json")
COMPOUNDS_PATH = Path("dictionary/compounds.json")

def translate_text(text, target_lang):
    try:
        translated = GoogleTranslator(source='en', target=target_lang).translate(text)
        return translated
    except Exception as e:
        print(f"Translate failed for {text} -> {target_lang}: {e}")
        return text

def main():
    with open(WORDS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    words = data.get("words", [])
    
    print(f"Translating {len(words)} words...")
    for i, w in enumerate(words):
        en_text = w.get("lang", {}).get("en")
        if not en_text:
            continue
            
        print(f"[{i+1}/{len(words)}] Translating '{en_text}'...")
        ja_text = translate_text(en_text, "ja")
        zh_text = translate_text(en_text, "zh-CN") # zh-CN acts as zh_hans
        
        w["lang"]["ja"] = ja_text
        w["lang"]["zh_hans"] = zh_text
        
        # Sleep slightly to prevent rate limit
        time.sleep(0.1)
        
    with open(WORDS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Words translation completed.")

if __name__ == "__main__":
    main()
