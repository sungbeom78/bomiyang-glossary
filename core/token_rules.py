from __future__ import annotations
import json
from pathlib import Path
from functools import lru_cache
import httpx
import logging

log = logging.getLogger(__name__)

GLOSSARY_ROOT = Path(__file__).resolve().parent.parent
UNIT_TOKENS_PATH = GLOSSARY_ROOT / "dictionary" / "unit_tokens.json"
TECH_ABBREV_PATH = GLOSSARY_ROOT / "dictionary" / "tech_abbreviations.json"
DRAFTS_PATH = GLOSSARY_ROOT / "dictionary" / "drafts.json"

STOP_WORDS_2CHAR = {
    "is", "in", "if", "to", "as", "at", "on", "by", "do", "it", 
    "of", "or", "up", "be", "he", "we", "me", "us", "am", "an"
}

@lru_cache(maxsize=1)
def load_unit_tokens() -> set[str]:
    if not UNIT_TOKENS_PATH.exists():
        return set()
    try:
        data = json.loads(UNIT_TOKENS_PATH.read_text(encoding="utf-8"))
        return {item["id"] for item in data.get("units", []) if "id" in item}
    except Exception as e:
        log.error(f"Failed to load unit_tokens.json: {e}")
        return set()

@lru_cache(maxsize=1)
def load_tech_abbreviations() -> set[str]:
    if not TECH_ABBREV_PATH.exists():
        return set()
    try:
        data = json.loads(TECH_ABBREV_PATH.read_text(encoding="utf-8"))
        return {item["id"] for item in data.get("abbreviations", []) if "id" in item}
    except Exception as e:
        log.error(f"Failed to load tech_abbreviations.json: {e}")
        return set()

def is_managed_identifier(name: str) -> bool:
    """_ 로 시작하는 식별자는 내부 로직용이므로 관리 대상에서 일괄 제외한다."""
    return not name.startswith("_")

def is_unit_token(token: str) -> bool:
    return token in load_unit_tokens()

def is_tech_abbreviation(token: str) -> bool:
    return token in load_tech_abbreviations()

@lru_cache(maxsize=5000)
def check_dictionary_api(token: str) -> tuple[bool, str]:
    """
    web dictionary API를 조회하여 단어가 유효한 명사 혹은 동사인지 판별 (2글자 무의미 단어, 관사 등 제외)
    Return: (is_valid, meaning_en)
    """
    if len(token) <= 2 and token in STOP_WORDS_2CHAR:
        return False, ""

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{token}"
    try:
        resp = httpx.get(url, timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            for entry in data:
                for meaning in entry.get("meanings", []):
                    pos = meaning.get("partOfSpeech", "").lower()
                    if pos in ("noun", "verb"):
                        defs = meaning.get("definitions", [])
                        m_en = defs[0].get("definition", "") if defs else ""
                        return True, m_en
    except Exception:
        pass
    return False, ""

def auto_draft_dictionary_word(token: str, meaning_en: str) -> None:
    """
    dictionary API 에서 발견된 단어는 drafts.json 에 AI 초기 입력 초안으로 자동 등재.
    이 함수가 실행된 단어는 시스템에서 패스(PASS) 상태를 부여받음 (향후 승인 대기).
    """
    data = {"drafts": []}
    if DRAFTS_PATH.exists():
        try:
            data = json.loads(DRAFTS_PATH.read_text(encoding="utf-8"))
            if not isinstance(data.get("drafts"), list):
                data["drafts"] = []
        except Exception:
            pass
            
    if any(item.get("id") == token for item in data.get("drafts", [])):
        return

    data["drafts"].append({
        "id": token,
        "source": "dictionaryapi.dev",
        "classification": "word",
        "meaning_en": meaning_en,
        "status": "ai_draft"
    })
    DRAFTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
