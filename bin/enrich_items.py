#!/usr/bin/env python3
"""
enrich_items.py - 단어 사전(words.json) 빈 항목 자동 채우기 유틸리티
Google Translate GTX 통신을 통한 다국어(lang.ja, lang.zh_hans, lang.ko) 보완 및
dictionaryapi.dev 와 AI(LLM) Fallback을 통한 영문/한글 정의(description_i18n) 자동 채우기를 수행합니다.
"""
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import sys
from pathlib import Path

BIN_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BIN_DIR))
from batch_items import get_env

WORDS_PATH = Path("dictionary/words.json")

def _http_get(url: str, timeout: int = 5):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode('utf-8')
            return json.loads(text)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        return None
    except Exception:
        return None

def _http_post(url: str, body: bytes, headers: dict, timeout: int = 5) -> dict:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))

def call_ai_timeout(prompt: str, env: dict, max_tokens: int = 150) -> str:
    """ 5초 타임아웃을 적용한 AI 호출기 (절대 Blocking 금지) """
    api_type = env.get("API_KEY_TYPE", "claude").lower()
    model = env.get("API_MODEL", "claude-sonnet-4-20250514")
    
    if api_type == "claude":
        key = env.get("ANTHROPIC_API_KEY", "")
        if not key: raise ValueError("ANTHROPIC_API_KEY missing")
        body = {
            "model": model, "max_tokens": max_tokens,
            "system": "You are a terminology expert. Follow instructions precisely.",
            "messages": [{"role": "user", "content": prompt}]
        }
        data = _http_post("https://api.anthropic.com/v1/messages", json.dumps(body).encode('utf-8'), {
            "Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"
        }, timeout=5)
        return data["content"][0]["text"]
    elif api_type == "openai":
        key = env.get("OPENAI_API_KEY", "")
        if not key: raise ValueError("OPENAI_API_KEY missing")
        body = {
            "model": model, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        data = _http_post("https://api.openai.com/v1/chat/completions", json.dumps(body).encode('utf-8'), {
            "Content-Type": "application/json", "Authorization": f"Bearer {key}"
        }, timeout=5)
        return data["choices"][0]["message"]["content"]
    elif api_type == "google":
        key = env.get("GOOGLE_API_KEY", "")
        if not key: raise ValueError("GOOGLE_API_KEY missing")
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens}
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        data = _http_post(url, json.dumps(body).encode('utf-8'), {"Content-Type": "application/json"}, timeout=5)
        return data["candidates"][0]["content"]["parts"][0]["text"]
    return ""

def translate_text(text, target_lang):
    if not text: return ""
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
    try:
        data = _http_get(url)
        if data and isinstance(data, list) and len(data) > 0 and len(data[0]) > 0:
            return data[0][0][0]
    except Exception as e:
        print(f"WARN: Error translating '{text}': {e}")
    return text

def fetch_dictionary_definition(word):
    url = f"https://api.dictionaryapi.dev/v2/entries/en/{urllib.parse.quote(word)}"
    data = _http_get(url)
    if data and isinstance(data, list) and len(data) > 0:
        meanings = data[0].get("meanings", [])
        if meanings:
            first_meaning = meanings[0]
            pos = first_meaning.get("partOfSpeech", "")
            definitions = first_meaning.get("definitions", [])
            if definitions:
                return definitions[0].get("definition", ""), pos
    return "", ""

def ask_ai_validation(word, env) -> bool:
    prompt = f"다음 단어가 일반적인 영어 단어 또는 기술 용어로 유효한가?\n\nword: {word}\n\nYES 또는 NO로 답하라."
    try:
        resp = call_ai_timeout(prompt, env, max_tokens=10)
        resp = resp.strip().upper()
        if resp.startswith("YES"):
            return True
        elif resp.startswith("NO"):
            return False
        else:
            print(f"WARN: Invalid AI format for validation '{word}': {resp}")
            return False
    except Exception as e:
        print(f"WARN: AI validation failed for '{word}' - {e}")
        return False

def ask_ai_description(word, env) -> str:
    prompt = f"다음 단어의 의미를 설명하라.\n\n조건:\n- 구현 설명 금지\n- 개념 중심 설명\n- 1문장\n- 20~60자\n- 한국어로 작성\n\nword: {word}"
    try:
        resp = call_ai_timeout(prompt, env, max_tokens=80)
        desc = resp.strip().replace('\n', ' ')
        return desc[:80]
    except Exception as e:
        print(f"WARN: AI description failed for '{word}' - {e}")
        return ""

def ask_ai_pos(word, env) -> str:
    prompt = f"이 단어의 품사를 하나 선택하라: noun / verb / adj / adv / proper / mixed\n\nword: {word}\n\n위 보기 중 정확히 하나의 단어로만 답하라."
    try:
        resp = call_ai_timeout(prompt, env, max_tokens=10)
        resp = resp.strip().lower()
        for p in ["noun", "verb", "adj", "adv", "proper", "mixed"]:
            if p in resp:
                return p
        return ""
    except Exception as e:
        print(f"WARN: AI POS failed for '{word}' - {e}")
        return ""

def main():
    if not WORDS_PATH.exists():
        print(f"{WORDS_PATH} not found.")
        return
        
    env, _ = get_env()
    
    with open(WORDS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    words = data.get("words", [])
    print(f"Enriching {len(words)} words...")
    
    modified_count = 0
    total = len(words)
    
    for i, w in enumerate(words):
        en_text = w.get("lang", {}).get("en")
        if not en_text:
            continue
            
        changed = False
        lang_dict = w.get("lang", {})
        
        # 1. 빈번한 다국어 부족분 (ja, zh_hans, ko) 채우기 (AI 안 씀, 오직 GTX)
        if not lang_dict.get("ja"):
            val = translate_text(en_text, "ja")
            if val and val != en_text:
                lang_dict["ja"] = val
                changed = True
        
        if not lang_dict.get("zh_hans"):
            val = translate_text(en_text, "zh-CN")
            if val and val != en_text:
                lang_dict["zh_hans"] = val
                changed = True
                
        if not lang_dict.get("ko") or lang_dict.get("ko") == en_text:
            val = translate_text(en_text, "ko")
            if val and val != en_text:
                lang_dict["ko"] = val
                changed = True
                
        w["lang"] = lang_dict

        # 2. Dictionary & AI Fallback 으로 설명, 품사 채우기
        desc_dict = w.get("description_i18n", {})
        ko_desc = desc_dict.get("ko", "")
        curr_pos = w.get("canonical_pos")
        needs_desc = not ko_desc
        needs_pos = not curr_pos or curr_pos == "unknown"
        
        if needs_desc or needs_pos:
            en_def, api_pos = fetch_dictionary_definition(en_text)
            time.sleep(0.5)
            
            # Dictionary 로 조회가 실패했을 경우
            is_valid_word = True
            if not en_def and not api_pos:
                is_valid_word = ask_ai_validation(en_text, env)
                if not is_valid_word:
                    print(f"WARN: Skipping '{en_text}' due to validation decline.")
                    continue
            
            # 설명 채우기
            if needs_desc:
                if en_def:
                    translated_def = translate_text(en_def, "ko")
                    if translated_def:
                        desc_dict["ko"] = translated_def
                        w["description_i18n"] = desc_dict
                        changed = True
                else:
                    ai_desc = ask_ai_description(en_text, env)
                    if ai_desc:
                        desc_dict["ko"] = ai_desc
                        w["description_i18n"] = desc_dict
                        changed = True

            # 품사 채우기
            if needs_pos:
                if api_pos:
                    if api_pos in ("noun", "verb", "adjective", "adverb"):
                        mapped_pos = "adj" if api_pos == "adjective" else "adv" if api_pos == "adverb" else api_pos
                        w["canonical_pos"] = mapped_pos
                        changed = True
                else:
                    ai_pos = ask_ai_pos(en_text, env)
                    if ai_pos:
                        w["canonical_pos"] = ai_pos
                        changed = True
        
        if changed:
            modified_count += 1
            print(f"[{i+1}/{total}] Updated '{en_text}'")
            
        time.sleep(0.05)
        
    if modified_count > 0:
        with open(WORDS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nDone! {modified_count} words enriched and saved.")
    else:
        print("\nAll words are fully enriched. No changes saved.")

if __name__ == "__main__":
    main()
