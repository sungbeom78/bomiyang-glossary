#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalize_build.py  -  Glossary Normalization System v3.2

2차 정제 기준 (2026-04-18 확정):

  changes from v3.1:
  - comparative/superlative (more X, most X) excluded from variants
  - normalize() implements 5-step priority:
      1. words.id
      2. words.variants
      3. words.synonyms
      4. from (lexical only - not stage)
      5. words__derived_terms.json (exact fallback only)
  - is_lexical_from(): lexical base vs etymology-stage 판별
  - enrich_word_variants(): migration/신규등록 공통 API
    - wikt_sense.fetch_and_process()에 위임 (AI-Centric Hard Gate v1.2)
    - 신규 등록은 batch_items.process_auto()가 직접 fetch_and_process() 호출
    - 두 경로 모두 동일한 variants 추출 기준 적용
  - from: 저장은 유지, canonical 판단에는 lexical from만 사용
  - derived_terms: 저장은 넓게, 조회는 exact fallback으로만 사용

단어 검색 우선순위 (normalize()):
  1. words.id
  2. words.variants  (plural, verb_form, present_participle, past, noun_form, ...)
  3. words.synonyms
  4. words.from (lexical from만 - is_lexical_from() True인 경우)
  5. words__derived_terms.json  (exact match 마지막 fallback)

용어 검색 원칙:
  - 용어를 단어 단위 분해 -> 각 단어를 위 1-4 순서로 조회
  - 핵심 단어 모두 해석 가능 -> 정상 용어
  - 위 방식으로 불가 시에만 derived_terms에서 전체 용어 exact match

Step 1. words.json:
  - variants enriched via wikt_sense (AI + Wiktionary)
  - derived_terms extracted -> words__derived_terms.json

Step 2. words__derived_terms.json:
  - surface -> canonical_id reverse-lookup index

Step 3. normalize engine:
  - normalize(word) -> canonical_id

Step 4. build/index/normalize_index.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("pip install requests beautifulsoup4 lxml", file=sys.stderr)
    raise

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent.resolve()
DICT_DIR = ROOT / "dictionary"
WORDS_PATH = DICT_DIR / "words.json"
DERIVED_PATH = DICT_DIR / "words__derived_terms.json"
BUILD_DIR = ROOT / "build"
INDEX_DIR = BUILD_DIR / "index"
REPORT_DIR = BUILD_DIR / "report"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WIKT_BASE = "https://en.wiktionary.org/wiki/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BOMTS-Glossary/3.1)"}

# language-stage 값들 (from 필드에서 제거)
LANG_STAGE_VALUES: Set[str] = {
    "middle", "old", "latin", "french", "greek", "ancient_greek", "anglo",
    "proto", "germanic", "norse", "norman", "dutch", "german", "italian",
    "spanish", "portuguese", "arabic", "hebrew", "sanskrit", "persian",
    "low", "new", "modern", "early", "late", "classical", "medieval",
    "middle_english", "old_english", "old_french", "ancient",
    "ecclesiastical", "vulgar",
}

# Wiktionary headword-line inflection label -> variant type
# NOTE: comparative / superlative removed  -  these produce compound forms
# ("more active", "most active") that are NOT useful for a term normalization system.
HEADWORD_INFLECTION_MAP: Dict[str, str] = {
    "third-person singular simple present": "verb_form",
    "third person singular": "verb_form",
    "present participle": "present_participle",
    "simple past": "past",
    "past tense": "past",
    "past participle": "past_participle",
    "plural": "plural",
    "singular": "singular",
    # comparative / superlative intentionally excluded
}

# Rule-based plural for nouns (fallback when Wiktionary missing)
def _rule_plural(word_id: str) -> str:
    if word_id.endswith(("s", "sh", "ch", "x", "z")):
        return word_id + "es"
    if word_id.endswith("y") and len(word_id) > 1 and word_id[-2] not in "aeiou":
        return word_id[:-1] + "ies"
    if word_id.endswith("f"):
        return word_id[:-1] + "ves"
    if word_id.endswith("fe"):
        return word_id[:-2] + "ves"
    return word_id + "s"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm_id(v: str) -> str:
    v = (v or "").strip().lower()
    v = v.replace(" ", "_")
    v = re.sub(r"[^a-z0-9_]+", "", v)
    v = re.sub(r"_+", "_", v).strip("_")
    return v


def has_variant(word: Dict, vtype: str, value: str) -> bool:
    for v in (word.get("variants") or []):
        if v.get("type") == vtype:
            val = (v.get("value") or v.get("short") or "").strip().lower()
            if val == value.strip().lower():
                return True
    return False


def add_variant_safe(word: Dict, vtype: str, value: str) -> bool:
    """Add variant if not already present and value != word.id."""
    value = value.strip()
    if not value:
        return False
    if value.lower() == word["id"].lower():
        return False  # self-conflict prevention
    en = (word.get("lang") or {}).get("en", "")
    if value.lower() == en.lower():
        return False
    if has_variant(word, vtype, value):
        return False
    if "variants" not in word or word["variants"] is None:
        word["variants"] = []
    word["variants"].append({"type": vtype, "value": value})
    return True


# ---------------------------------------------------------------------------
# Wiktionary headword-line inflection parser
# ---------------------------------------------------------------------------
def _mw_heading_level(div) -> Optional[int]:
    for cls in (div.get("class") or []):
        m = re.match(r"mw-heading(\d)", cls)
        if m:
            return int(m.group(1))
    return None


def _get_sections(soup) -> List[Dict]:
    sections = []
    for div in soup.find_all("div", class_=re.compile(r"mw-heading")):
        lvl = _mw_heading_level(div)
        if lvl is None:
            continue
        title_tag = div.find(re.compile(r"^h\d$"))
        title = title_tag.get_text(" ", strip=True) if title_tag else div.get_text(" ", strip=True)
        title = re.sub(r"\s*\[\s*edit\s*\]\s*$", "", title).strip()
        content = []
        node = div.find_next_sibling()
        while node:
            if getattr(node, "name", None) == "div":
                nlvl = _mw_heading_level(node)
                if nlvl and nlvl <= lvl:
                    break
            content.append(node)
            node = node.find_next_sibling()
        sections.append({"level": lvl, "title": title, "nodes": content})
    return sections


def _find_english_subsections(sections: List[Dict]) -> List[Dict]:
    in_english = False
    result = []
    for sec in sections:
        if sec["level"] == 2:
            in_english = sec["title"].lower() == "english"
            if not in_english and result:
                break
        elif in_english:
            result.append(sec)
    return result


def parse_headword_inflections(nodes) -> List[Dict[str, str]]:
    """
    Parse inflection forms from the headword-line paragraph.
    e.g.: activate (third-person singular simple present activates,
                     present participle activating,
                     simple past and past participle activated)
    """
    results: List[Dict[str, str]] = []
    for node in nodes:
        if not hasattr(node, "name") or node.name != "p":
            continue
        if not node.find(class_="headword-line"):
            continue
        # Get the full text
        text = node.get_text(" ", strip=True)
        # Remove the headword itself (first bold word)
        headword_el = node.find(class_="headword")
        headword_val = headword_el.get_text(" ", strip=True) if headword_el else ""

        # Extract (label value, label value, ...) pairs from italics+bold pattern
        # Pattern: <i>label</i> ... <b>value</b>
        i_tags = node.find_all("i")
        b_tags = node.find_all(["b", "strong"])

        # Strategy: find italic labels and the b/strong that follows them
        for i_tag in i_tags:
            label = i_tag.get_text(" ", strip=True).lower()
            vtype = None
            for infl_label, vt in HEADWORD_INFLECTION_MAP.items():
                if infl_label in label:
                    vtype = vt
                    break
            if not vtype:
                continue
            # Find the next <b> sibling (could be in same parent or next sibling)
            candidates = []
            next_node = i_tag.find_next_sibling()
            while next_node:
                if hasattr(next_node, "name"):
                    if next_node.name in ("b", "strong"):
                        candidates.append(next_node.get_text(" ", strip=True))
                        break
                    if next_node.name in ("i",):
                        break  # next label, stop
                next_node = next_node.find_next_sibling()

            # Also look for <b> tag that is a child or sibling following <i>
            if not candidates:
                # try find_next for b/strong with lang="en" class
                b = i_tag.find_next("b", class_=re.compile(r"form-of|lang-en"))
                if b:
                    candidates.append(b.get_text(" ", strip=True))

            for val in candidates:
                val = re.sub(r"\s+", " ", val).strip(" .,;")
                if val and val.lower() != headword_val.lower():
                    # Could be "X and Y"  -  split on " and "
                    for part in re.split(r"\s+and\s+", val):
                        part = part.strip(" .,;")
                        if part:
                            results.append({"type": vtype, "value": part})
        break  # Only first headword-line paragraph
    return results


def fetch_wiktionary_inflections(term: str) -> Tuple[str, List[Dict[str, str]]]:
    """Fetch Wiktionary and extract inflections from headword line. Returns (url, [variants])."""
    url = f"{WIKT_BASE}{requests.utils.quote(term)}"
    try:
        resp = requests.get(url, timeout=20, headers=HEADERS)
        resp.raise_for_status()
    except Exception as exc:
        return url, []
    soup = BeautifulSoup(resp.text, "lxml")
    sections = _get_sections(soup)
    eng_subs = _find_english_subsections(sections)
    inflections = []
    for sec in eng_subs:
        pos_lower = sec["title"].lower()
        if pos_lower in ("verb", "noun", "adjective", "adverb"):
            inflections.extend(parse_headword_inflections(sec["nodes"]))
    return url, inflections


# ---------------------------------------------------------------------------
# from field: lexical vs etymology-stage classification
# ---------------------------------------------------------------------------
def is_lexical_from(from_val: Optional[str], word_ids: Optional[Set[str]] = None) -> bool:
    """
    Return True if from_val is a lexical base (actual word), not an etymology stage.

    Lexical from: adapter -> adapt, auth -> authenticate, flatten -> flat
    Stage from:   middle, latin, french, old_english, etc.

    Rule (per spec):
    - If from_val is in LANG_STAGE_VALUES -> False (stage)
    - If from_val matches a known words.id -> True (lexical)
    - If from_val looks like a real English lemma (single word, alpha) -> True
    - Otherwise -> False
    """
    if not from_val:
        return False
    nid = norm_id(from_val)
    if not nid:
        return False
    # Language stage set
    if nid in LANG_STAGE_VALUES:
        return False
    # If we have a word index, check direct match
    if word_ids and nid in word_ids:
        return True
    # Single lowercase english word that is not a language name -> assume lexical
    if re.match(r"^[a-z]{2,}$", nid) and nid not in LANG_STAGE_VALUES:
        return True
    return False


def clean_from_value(from_val: Optional[str]) -> Optional[str]:
    """Return None if from_val is a language stage (latin, middle, etc)."""
    if not from_val:
        return None
    nid = norm_id(from_val)
    if nid in LANG_STAGE_VALUES:
        return None
    return nid if nid else None


# ---------------------------------------------------------------------------
# Public API: enrich_word_variants()
# v1.1: Delegates to wikt_sense.py (AI-Centric Hard Gate Spec v1.1)
# Shared by both migration and new-word registration paths.
# ---------------------------------------------------------------------------
def enrich_word_variants(
    word: Dict,
    sleep_sec: float = 0.0,
    derived_index: Optional[List[Dict]] = None,
    seen_derived: Optional[Set[str]] = None,
    ai_env: Optional[Dict] = None,
) -> int:
    # v1.1: Uses unified AI-centric pipeline.
    # Returns number of variants added.
    try:
        from wikt_sense import fetch_and_process
        wid = word["id"]
        term = (word.get("lang") or {}).get("en") or wid
        _, result = fetch_and_process(term, word, ai_env=ai_env)

        if sleep_sec > 0:
            time.sleep(sleep_sec)

        if result is None:
            return 0

        # Apply description_en if pipeline produced one
        if result.description_en:
            if "description_i18n" not in word:
                word["description_i18n"] = {}
            if not word["description_i18n"].get("en"):
                word["description_i18n"]["en"] = result.description_en

        # Apply from_word if pipeline produced one and word has no from yet
        if result.from_word and not word.get("from"):
            word["from"] = norm_id(result.from_word)

        # Apply selected_pos if pipeline changed it
        if result.selected_pos and result.selected_pos != word.get("canonical_pos"):
            word["canonical_pos"] = result.selected_pos

        # Apply variants
        added = 0
        for infl in result.variants:
            if add_variant_safe(word, infl["type"], infl["value"]):
                added += 1
                if derived_index is not None and seen_derived is not None:
                    surface = norm_id(infl["value"])
                    if surface and surface not in seen_derived:
                        seen_derived.add(surface)
                        derived_index.append({
                            "surface": surface,
                            "canonical_id": wid,
                            "type": "variant",
                            "variant_type": infl["type"],
                            "source": "wiktionary",
                            "confidence": "high",
                        })

        return added

    except Exception:
        if sleep_sec > 0:
            time.sleep(sleep_sec)
        return 0


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def run(apply: bool, enrich_variants: bool, sleep_sec: float = 0.4) -> int:
    data = read_json(WORDS_PATH)
    words: List[Dict] = data["words"]

    stats = {
        "total": len(words),
        "from_cleaned": 0,
        "from_removed": 0,
        "variants_added": 0,
        "derived_items": 0,
        "skipped_rule_plural": 0,
    }

    # Build derived index
    derived_items: List[Dict] = []
    seen_derived: Set[str] = set()

    total = len(words)
    for i, word in enumerate(words):
        wid = word["id"]
        print(f"[{i+1}/{total}] {wid} ...", flush=True)

        # ── Step A: keep `from` as-is (spec: stored either way) ──────────
        # from is preserved regardless of stage/lexical classification.
        # Canonical judgment uses is_lexical_from() at lookup time.
        # Only normalise id format: spaces -> underscores, lowercase.
        raw_from = word.get("from")
        if raw_from:
            nid_from = norm_id(raw_from)
            if nid_from and nid_from != raw_from:
                word["from"] = nid_from
                stats["from_cleaned"] += 1

        # ── Step B: collect derived_terms -> index ────────
        for dt in (word.get("derived_terms") or []):
            surface = norm_id(dt)
            if not surface or surface in seen_derived:
                continue
            seen_derived.add(surface)
            derived_items.append({
                "surface": surface,
                "canonical_id": wid,
                "type": "derived_term",
                "source": "dictionary",
                "confidence": "high",
            })
            stats["derived_items"] += 1

        # Also add variants to derived index
        for v in (word.get("variants") or []):
            surface = norm_id(v.get("value") or v.get("short") or "")
            if not surface or surface == wid or surface in seen_derived:
                continue
            seen_derived.add(surface)
            derived_items.append({
                "surface": surface,
                "canonical_id": wid,
                "type": "variant",
                "variant_type": v.get("type", ""),
                "source": "glossary",
                "confidence": "high",
            })

        # ── Step C: remove derived_terms from word ───────
        word.pop("derived_terms", None)

        # ── Step D: enrich variants via shared enrich_word_variants() ──────
        if enrich_variants:
            added = enrich_word_variants(
                word,
                sleep_sec=sleep_sec,
                derived_index=derived_items,
                seen_derived=seen_derived,
            )
            stats["variants_added"] += added

    # ── Step E: add synonyms to derived index ─────────────
    for word in words:
        wid = word["id"]
        for syn in (word.get("synonyms") or []):
            surface = norm_id(syn)
            if not surface or surface in seen_derived:
                continue
            seen_derived.add(surface)
            derived_items.append({
                "surface": surface,
                "canonical_id": wid,
                "type": "synonym",
                "source": "dictionary",
                "confidence": "medium",
            })

    # ── Output ────────────────────────────────────────────
    print(f"\n=== Stats ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  derived_index total: {len(derived_items)}")

    if apply:
        write_json(WORDS_PATH, data)
        print("[APPLY] words.json updated")

        derived_data = {
            "_note": "Auto-generated. Do not edit manually. Source: words.json derived_terms + variants + synonyms.",
            "items": derived_items,
        }
        write_json(DERIVED_PATH, derived_data)
        print(f"[APPLY] {DERIVED_PATH} written ({len(derived_items)} items)")

        # ── normalize index ───────────────────────────────
        _build_normalize_index(words, derived_items, apply=True)
    else:
        print("[DRY-RUN] No files modified.")

    return 0


def _build_normalize_index(words: List[Dict], derived_items: List[Dict], apply: bool) -> Dict[str, str]:
    # Build surface -> canonical_id index.
    # Priority (per v3.2 spec):
    #   1. words.id (and lang.en alias)
    #   2. words.variants (plural, verb_form, present_participle, past, etc.)
    #   3. words.synonyms
    #   4. words.from (lexical only - is_lexical_from() == True)
    #   5. words__derived_terms (exact fallback)
    index: Dict[str, str] = {}
    word_ids: Set[str] = {w["id"] for w in words}

    # 1. Direct word id + lang.en aliases
    for w in words:
        index[w["id"]] = w["id"]
        en = (w.get("lang") or {}).get("en", "")
        if en:
            nid = norm_id(en)
            if nid and nid not in index:
                index[nid] = w["id"]

    # 2. Variants (all types)
    for w in words:
        for v in (w.get("variants") or []):
            surface = norm_id(v.get("value") or v.get("short") or "")
            if surface and surface not in index:
                index[surface] = w["id"]

    # 3. Synonyms
    for w in words:
        for syn in (w.get("synonyms") or []):
            surface = norm_id(syn)
            if surface and surface not in index:
                index[surface] = w["id"]

    # 4. from (lexical only)
    for w in words:
        from_val = w.get("from")
        if from_val and is_lexical_from(from_val, word_ids):
            surface = norm_id(from_val)
            if surface and surface not in index:
                index[surface] = w["id"]

    # 5. Derived items (exact fallback  -  lowest priority, do not overwrite)
    for item in derived_items:
        surface = item["surface"]
        if surface and surface not in index:
            index[surface] = item["canonical_id"]

    if apply:
        out = {
            "_note": (
                "surface -> canonical_id normalize index. "
                "Priority: words.id > variants > synonyms > from(lexical) > derived_terms"
            ),
            "priority_order": [
                "1: words.id",
                "2: words.variants",
                "3: words.synonyms",
                "4: words.from (lexical only)",
                "5: words__derived_terms (exact fallback)",
            ],
            "index": index,
        }
        out_path = INDEX_DIR / "normalize_index.json"
        write_json(out_path, out)
        print(f"[APPLY] normalize_index.json written ({len(index)} entries)")

    return index


# ---------------------------------------------------------------------------
# normalize() API   -  5-step runtime lookup (no file rebuild needed)
# ---------------------------------------------------------------------------
_WORDS_CACHE: Optional[List[Dict]] = None
_DERIVED_CACHE: Optional[List[Dict]] = None
_INDEX_CACHE: Optional[Dict[str, str]] = None


def _load_caches() -> None:
    global _WORDS_CACHE, _DERIVED_CACHE, _INDEX_CACHE
    if _WORDS_CACHE is None:
        _WORDS_CACHE = read_json(WORDS_PATH).get("words", []) if WORDS_PATH.exists() else []
    if _INDEX_CACHE is None:
        idx_path = INDEX_DIR / "normalize_index.json"
        _INDEX_CACHE = read_json(idx_path).get("index", {}) if idx_path.exists() else {}


def normalize(word: str) -> Optional[str]:
    """
    Map any surface form to canonical word id.

    Priority (v3.2):
      1. words.id exact match
      2. words.variants
      3. words.synonyms
      4. words.from (lexical only)
      5. words__derived_terms (exact fallback via pre-built index)
    """
    _load_caches()
    key = norm_id(word)
    if not key:
        return None
    return _INDEX_CACHE.get(key)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(description="Glossary Normalization System v3.1")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    p.add_argument("--enrich-variants", action="store_true",
                   help="Fetch Wiktionary inflections for each word (slow)")
    p.add_argument("--sleep", type=float, default=0.4)
    p.add_argument("--test", metavar="WORD",
                   help="Test normalize() on a word and exit")
    args = p.parse_args()

    if args.test:
        result = normalize(args.test)
        print(f"normalize({args.test!r}) -> {result!r}")
        return 0

    return run(
        apply=args.apply,
        enrich_variants=args.enrich_variants,
        sleep_sec=args.sleep,
    )


if __name__ == "__main__":
    raise SystemExit(main())
