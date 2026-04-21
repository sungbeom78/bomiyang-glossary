#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# wikt_sense.py -- Glossary Sense Selection Hard Gate Spec v1.1 (AI-Centric)
#
# Architecture:
#   Wiktionary HTML -> Parser -> Dictionary Score -> AI Judgment -> Hard Gate -> Save
#
# Entry point:
#   process_word_pipeline(word_id, word_entry, ai_env) -> PipelineResult
#   fetch_and_process(term, word_entry, ai_env)        -> PipelineResult

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    raise ImportError("pip install beautifulsoup4 lxml")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# POS normalisation map
POS_NORM: Dict[str, str] = {
    "noun":         "noun",
    "proper noun":  "noun",
    "verb":         "verb",
    "adjective":    "adj",
    "adverb":       "adv",
    "preposition":  "prep",
    "conjunction":  "conj",
    "interjection": "intj",
    "pronoun":      "pron",
    "numeral":      "num",
}

# Status/participle words that remain as standalone IDs (not merged into base).
# These are domain terms used as nouns/adjectives in their own right.
# They do NOT need inflection variants.
STATUS_WORDS: Set[str] = {
    "closed", "pending", "unrealized",
    "trading", "reporting", "scoring", "setting", "trailing",
}

# All allowed variant types (expanded: inflection + morphological derivation)
# AI is instructed to maximize these; Hard Gate checks against this set only.
ALL_VARIANT_TYPES: Set[str] = {
    # -- Inflection (from Wiktionary headword) --
    "plural",              # noun: bots
    "singular",            # noun (irregular)
    "verb_form",           # verb: 3rd person singular (classifies)
    "past",                # verb: simple past (classified)
    "past_participle",     # verb: past participle (classified)
    "present_participle",  # verb: -ing form (classifying)
    "comparative",         # adj/adv: higher
    "superlative",         # adj/adv: highest
    # -- Morphological derivation (same lemma family, cross-POS) --
    "noun_form",           # noun derived from this: activate -> activation
    "verb_derived",        # verb derived from this: active -> activate
    "adj_form",            # adj derived from this: activate -> active
    "adv_form",            # adv derived from this: active -> actively
    "agent",               # -er/-or form: classify -> classifier
    "gerund",              # -ing as noun: running (the act of)
}

# Backward compat: strict per-POS filter (used only by filter_variants_by_pos)
VARIANTS_KEEP_BY_POS: Dict[str, List[str]] = {
    "noun":  ["plural", "singular", "gerund", "noun_form"],
    "verb":  ["verb_form", "past", "present_participle", "past_participle",
              "agent", "noun_form", "adj_form", "adv_form"],
    "adj":   ["comparative", "superlative", "adv_form", "verb_derived", "noun_form"],
    "adv":   ["comparative", "superlative", "adj_form"],
    "prep":  [],
    "conj":  [],
    "intj":  [],
    "pron":  [],
    "num":   [],
}

# Rare/historical markers
RARE_MARKERS = [
    "obsolete", "archaic", "historical", "rare", "dated",
    "poetic", "literary", "dialectal", "regional",
]

# Domain keyword maps for dictionary scoring
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "infra":    ["server", "service", "daemon", "process", "system", "network",
                 "deploy", "container", "cloud", "infrastructure", "program",
                 "automated", "software", "application", "computer"],
    "trading":  ["trade", "market", "price", "stock", "order", "position",
                 "buy", "sell", "broker", "exchange", "equity", "futures"],
    "finance":  ["financial", "money", "capital", "fund", "asset", "liability",
                 "balance", "account", "credit", "debit"],
    "data":     ["data", "database", "record", "table", "query", "schema",
                 "index", "field", "row", "column"],
    "general":  [],
}

# From: banned words (language stages, too generic)
FROM_BANNED: Set[str] = {
    "latin", "greek", "french", "english", "german", "dutch",
    "norse", "arabic", "hebrew", "sanskrit", "persian", "italian",
    "spanish", "portuguese", "gothic", "celtic", "proto", "old",
    "middle", "classical", "medieval", "vulgar", "ancient",
    "late", "early", "modern", "post", "new",
    "deverbal", "lemma", "suffix", "prefix", "compound",
    "ultimately", "borrowed",
}


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class Etymology:
    text: str
    tokens: List[str] = field(default_factory=list)

@dataclass
class PosBlock:
    pos: str
    pos_raw: str
    definitions: List[str] = field(default_factory=list)
    inflections: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class WiktData:
    etymologies: List[Etymology] = field(default_factory=list)
    pos_blocks: List[PosBlock] = field(default_factory=list)

@dataclass
class DictScore:
    score: int = 0
    quality: str = "low"  # high / medium / low
    detail: Dict[str, int] = field(default_factory=dict)

@dataclass
class HardGateResult:
    passed: bool = False
    failures: List[str] = field(default_factory=list)

@dataclass
class PipelineResult:
    # Final output
    selected_pos: Optional[str] = None
    from_word: Optional[str] = None
    variants: List[Dict[str, str]] = field(default_factory=list)
    description_en: Optional[str] = None
    confidence: str = "low"
    # Status
    status: str = "pending"  # ok / rejected / error
    ai_used: bool = False
    rejection_reason: Optional[str] = None
    dict_score: Optional[DictScore] = None
    gate_result: Optional[HardGateResult] = None


# ===========================================================================
# SECTION 1: Wiktionary HTML parser (preserved from v1.0, with adj fix)
# ===========================================================================

def _mw_heading_level(div: Tag) -> Optional[int]:
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


def _parse_etymology_section(nodes) -> Optional[Etymology]:
    for node in nodes:
        if not hasattr(node, "name"):
            continue
        if node.name == "p":
            text = node.get_text(" ", strip=True)
            if not text:
                continue
            tokens = []
            for a in node.find_all("a"):
                t = a.get_text(strip=True).lower()
                if t and re.match(r"^[a-z][a-z\-']+$", t):
                    tokens.append(t)
            return Etymology(text=text.strip(), tokens=tokens)
    return None


def _parse_definitions(nodes) -> List[str]:
    defs = []
    for node in nodes:
        if not hasattr(node, "name"):
            continue
        if node.name == "ol":
            for li in node.find_all("li", recursive=False):
                parts = []
                for child in li.children:
                    if hasattr(child, "name"):
                        if child.name in ("dl", "ul", "ol"):
                            break
                    parts.append(child.get_text(" ", strip=True) if hasattr(child, "get_text") else str(child))
                text = " ".join(parts).strip()
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    defs.append(text)
            break
    return defs


def _parse_headword_inflections(nodes) -> List[Dict[str, str]]:
    # v1.1: Now includes comparative/superlative for adj
    INFL_MAP = {
        "third-person singular simple present": "verb_form",
        "third person singular": "verb_form",
        "present participle": "present_participle",
        "simple past": "past",
        "past tense": "past",
        "past participle": "past_participle",
        "plural": "plural",
        "singular": "singular",
        "comparative": "comparative",
        "superlative": "superlative",
    }
    results = []
    for node in nodes:
        if not hasattr(node, "name") or node.name != "p":
            continue
        if not node.find(class_="headword-line"):
            continue
        headword_el = node.find(class_="headword")
        headword_val = headword_el.get_text(" ", strip=True) if headword_el else ""
        for i_tag in node.find_all("i"):
            label = i_tag.get_text(" ", strip=True).lower()
            vtype = None
            for infl_label, vt in INFL_MAP.items():
                if infl_label in label:
                    vtype = vt
                    break
            if not vtype:
                continue
            next_node = i_tag.find_next_sibling()
            while next_node:
                if hasattr(next_node, "name"):
                    if next_node.name in ("b", "strong"):
                        val = next_node.get_text(" ", strip=True).strip(" .,;")
                        if val and val.lower() != headword_val.lower():
                            for part in re.split(r"\s+and\s+", val):
                                part = part.strip(" .,;")
                                if part and not part.startswith("more ") and not part.startswith("most "):
                                    results.append({"type": vtype, "value": part})
                        break
                    if next_node.name == "i":
                        break
                next_node = next_node.find_next_sibling()
        break
    return results


def parse_wiktionary_full(soup) -> WiktData:
    sections = _get_sections(soup)
    eng_subs = _find_english_subsections(sections)

    etymologies: List[Etymology] = []
    pos_blocks: List[PosBlock] = []

    for sec in eng_subs:
        title_lower = sec["title"].lower()

        if title_lower.startswith("etymology"):
            etym = _parse_etymology_section(sec["nodes"])
            if etym:
                etymologies.append(etym)

        elif title_lower in POS_NORM:
            pos_norm = POS_NORM[title_lower]
            defs = _parse_definitions(sec["nodes"])
            inflections = _parse_headword_inflections(sec["nodes"])
            pos_blocks.append(PosBlock(
                pos=pos_norm,
                pos_raw=sec["title"],
                definitions=defs,
                inflections=inflections,
            ))

    return WiktData(etymologies=etymologies, pos_blocks=pos_blocks)


# ===========================================================================
# SECTION 2: Dictionary Score Calculator (spec §5)
# ===========================================================================

def calculate_dict_score(word_entry: Dict, wikt_data: WiktData) -> DictScore:
    score = 0
    detail: Dict[str, int] = {}
    canonical_pos = word_entry.get("canonical_pos", "")
    domain = word_entry.get("domain", "general")

    # POS match check
    pos_set = {pb.pos for pb in wikt_data.pos_blocks}
    if canonical_pos in pos_set:
        score += 5
        detail["pos_match"] = 5

    # Single POS bonus
    if len(pos_set) == 1:
        score += 2
        detail["single_pos"] = 2
    elif len(pos_set) >= 2:
        score -= 3
        detail["multi_pos"] = -3

    # Single etymology bonus
    if len(wikt_data.etymologies) == 1:
        score += 2
        detail["single_etym"] = 2
    elif len(wikt_data.etymologies) >= 2:
        score -= 2
        detail["multi_etym"] = -2

    # Domain keyword in definitions
    domain_kws = DOMAIN_KEYWORDS.get(domain, [])
    all_defs_text = " ".join(
        d.lower() for pb in wikt_data.pos_blocks for d in pb.definitions
    )
    kw_hits = sum(1 for kw in domain_kws if kw in all_defs_text) if domain_kws else 0
    if kw_hits > 0:
        kw_score = min(kw_hits * 2, 5)
        score += kw_score
        detail["domain_kw"] = kw_score

    # Rare marker penalty
    rare_count = sum(1 for marker in RARE_MARKERS if marker in all_defs_text)
    if rare_count > 0:
        penalty = min(rare_count * 2, 4)
        score -= penalty
        detail["rare_penalty"] = -penalty

    # Quality label
    if score >= 8:
        quality = "high"
    elif score >= 5:
        quality = "medium"
    else:
        quality = "low"

    return DictScore(score=score, quality=quality, detail=detail)


# ===========================================================================
# SECTION 3: AI Judgment (spec §6 -- THE CORE)
# ===========================================================================

# -- 3.1 Prompt Construction --

_AI_SYSTEM_PROMPT = """\
You are a glossary entry curator for BOM_TS, an automated stock/FX trading system built in Python.
The glossary defines canonical words used across the codebase for naming variables, functions, classes, files, and database columns.

YOUR TASK: Given a word, its glossary context, and Wiktionary parse data, produce ONE clean glossary entry.

─── CORE PHILOSOPHY ───

❗ MAXIMIZE variants. DROP only if completely wrong meaning.
   A word family shares one root. Collect ALL morphological relatives.

─── FIELD RULES ───

1. selected_pos
   The PRIMARY part of speech this word represents in software code.
   - Names a thing / concept / entity: "noun"
   - Names an action or process: "verb"
   - Describes a property or state: "adj"
   - Modifies a verb/adj: "adv"
   - Status labels (cancelled, closed, filled, stopped, failed, rejected, completed, disabled, enabled): "adj"
   - Default to the existing canonical_pos if it makes sense.

2. from (lexical base)
   ONLY set if this word is a clear modern shortening/clipping.
   CORRECT: bot→robot, app→application, exec→execute, config→configuration
   NEVER:   bot→bottom, backtest→back, bridge→earlier, fill→thill
   RULE: When in doubt, set null. Never use language names or words ≤ 3 characters.

3. variants_keep — ❗ COLLECT ALL MORPHOLOGICAL RELATIVES

   Include ALL of the following that apply — across POS:

   INFLECTION (direct conjugations/forms):
   use EXACT type names:
   - "plural"             noun:    bots, trades
   - "verb_form"          verb:    3rd-person singular — classifies, runs
   - "past"               verb:    simple past — classified, ran
   - "past_participle"    verb:    completed, classified
   - "present_participle" verb:    classifying, running
   - "comparative"        adj/adv: higher, faster
   - "superlative"        adj/adv: highest, fastest

   DERIVATION (morphological relatives, even if different POS):
   use EXACT type names:
   - "noun_form"          noun derived from this: activate→activation, classify→classification
   - "verb_derived"       verb derived from this: active→activate, signal→signaling
   - "adj_form"           adj derived from this: activate→active, classify→classified
   - "adv_form"           adverb derived: active→actively, direct→directly
   - "agent"              -er/-or form: classify→classifier, run→runner
   - "gerund"             -ing as noun: running (the act of running)

   RULES:
   - NEVER include "more X" or "most X" (periphrastic forms)
   - NEVER include words from completely different meanings
   - INCLUDE even if it's a different POS than selected_pos
   - If Wiktionary missed a form you are confident about, ADD it
   - Status adjectives (cancelled, closed, etc.) → NO variants needed ([] is ok)

   EXAMPLES:
   "active" (adj) → [{"type":"verb_derived","value":"activate"},{"type":"present_participle","value":"activating"},{"type":"past_participle","value":"activated"},{"type":"noun_form","value":"activation"},{"type":"adv_form","value":"actively"}]
   "classify" (verb) → [{"type":"verb_form","value":"classifies"},{"type":"past","value":"classified"},{"type":"present_participle","value":"classifying"},{"type":"noun_form","value":"classification"},{"type":"agent","value":"classifier"}]
   "run" (verb) → [{"type":"verb_form","value":"runs"},{"type":"past","value":"ran"},{"type":"present_participle","value":"running"},{"type":"agent","value":"runner"},{"type":"gerund","value":"running"}]
   "bot" (noun) → [{"type":"plural","value":"bots"}]

4. description_en
   One concise sentence, domain-specific (software/trading/finance).
   Example: "bot" → "An automated program that performs tasks without human intervention."
   NOT the archaic or unrelated meaning.

5. confidence: "high" / "medium" / "low"

─── OUTPUT FORMAT ───

Return ONLY valid JSON, no explanation, no markdown fences:
{
  "selected_pos": "adj",
  "from": null,
  "variants_keep": [
    {"type": "verb_derived", "value": "activate"},
    {"type": "noun_form", "value": "activation"},
    {"type": "adv_form", "value": "actively"}
  ],
  "description_en": "...",
  "confidence": "high"
}"""


def _build_ai_user_prompt(
    word_entry: Dict,
    wikt_data: WiktData,
    dict_score: DictScore,
) -> str:
    # Build a compact but complete context for AI
    wikt_summary = {
        "etymologies": [
            {"text": e.text[:300], "tokens": e.tokens[:10]}
            for e in wikt_data.etymologies
        ],
        "pos_blocks": [],
    }
    for pb in wikt_data.pos_blocks:
        block = {
            "pos": pb.pos,
            "definitions": pb.definitions[:5],
            "inflections": pb.inflections[:10],
        }
        wikt_summary["pos_blocks"].append(block)

    word_context = {
        "id": word_entry.get("id", ""),
        "canonical_pos": word_entry.get("canonical_pos", ""),
        "domain": word_entry.get("domain", "general"),
    }
    desc_ko = (word_entry.get("description_i18n") or {}).get("ko")
    if desc_ko:
        word_context["description_ko"] = desc_ko
    lang_ko = (word_entry.get("lang") or {}).get("ko")
    if lang_ko and lang_ko != word_entry.get("id"):
        word_context["ko_label"] = lang_ko

    prompt = (
        f"Word entry:\n{json.dumps(word_context, ensure_ascii=False, indent=2)}\n\n"
        f"Wiktionary data:\n{json.dumps(wikt_summary, ensure_ascii=False, indent=2)}\n\n"
        f"Dictionary score: {dict_score.score} ({dict_score.quality})\n"
    )
    return prompt


# -- 3.2 AI Call --

def _load_ai_env() -> Optional[Dict]:
    # Load API keys from .env file.  Walk up to find project root.
    search = Path(__file__).resolve().parent.parent
    for _ in range(5):
        env_path = search / ".env"
        if env_path.exists():
            env = {}
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
            return env
        search = search.parent
    return None


def _call_ai(
    word_entry: Dict,
    wikt_data: WiktData,
    dict_score: DictScore,
    ai_env: Dict,
) -> Optional[Dict]:
    try:
        import sys
        bin_dir = os.path.dirname(os.path.abspath(__file__))
        if bin_dir not in sys.path:
            sys.path.insert(0, bin_dir)
        from batch_items import call_api as _raw_call_api

        user_prompt = _build_ai_user_prompt(word_entry, wikt_data, dict_score)

        # Build the full prompt with system instructions
        ai_system = _AI_SYSTEM_PROMPT
        if ai_env:
            proj = ai_env.get("GLOSSARY_PROJ_NAME", "BOM_TS")
            domain = ai_env.get("GLOSSARY_PROJ_DOMAIN", "an automated stock/FX trading system")
            ai_system = _AI_SYSTEM_PROMPT.replace("BOM_TS", proj).replace("an automated stock/FX trading system", domain)

        api_type = ai_env.get("API_KEY_TYPE", "google").lower()

        if api_type == "google":
            # Google API: system prompt goes as prefix to the content
            full_prompt = ai_system + "\n\n---\n\n" + user_prompt
        else:
            # Simplest approach: combine system + user as one prompt for all backends.
            full_prompt = ai_system + "\n\n---\n\n" + user_prompt

        resp = _raw_call_api(full_prompt, ai_env, max_tokens=600)

        # Parse JSON from response
        # Try to find a JSON object in the response
        resp_clean = resp.strip()
        # Remove markdown fences if present
        resp_clean = re.sub(r"^```(?:json)?\s*", "", resp_clean)
        resp_clean = re.sub(r"\s*```$", "", resp_clean)
        resp_clean = resp_clean.strip()

        # Find the JSON object
        start = resp_clean.find("{")
        end = resp_clean.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(resp_clean[start:end])
    except Exception as exc:
        # Log but don't fail the pipeline
        print(f"    [AI-WARN] {word_entry.get('id','?')}: {exc}")
    return None


# ===========================================================================
# SECTION 4: Hard Gate (spec §7)
# ===========================================================================

def validate_hard_gate(
    word_id: str,
    result: Dict,
    word_entry: Dict,
) -> HardGateResult:
    failures = []

    # Gate 1: description_en must exist
    desc_en = result.get("description_en")
    if not desc_en or not isinstance(desc_en, str) or len(desc_en.strip()) < 5:
        failures.append("description_en missing or too short")

    # Gate 2: selected_pos must be valid
    sel_pos = result.get("selected_pos", "")
    valid_pos = {"noun", "verb", "adj", "adv", "prep", "conj", "intj", "pron", "num"}
    if sel_pos not in valid_pos:
        failures.append(f"selected_pos invalid: {sel_pos!r}")

    # Gate 3: variants — check type names are in ALL_VARIANT_TYPES
    # No longer restricted by POS (maximize morphological family)
    variants = result.get("variants_keep") or []
    for v in variants:
        vtype = v.get("type", "")
        if vtype and vtype not in ALL_VARIANT_TYPES:
            failures.append(f"unknown variant type: {vtype!r}")
            break

    # Gate 4: from quality check
    from_val = result.get("from")
    if from_val:
        from_lower = str(from_val).lower().strip()
        if from_lower in FROM_BANNED:
            failures.append(f"from banned word: {from_val!r}")
        if len(from_lower) <= 3:
            failures.append(f"from too short: {from_val!r}")
        if from_lower == word_id:
            failures.append(f"from self-reference: {from_val!r}")
        if from_lower == word_id + "s" or from_lower == word_id + "es":
            failures.append(f"from plural self-reference: {from_val!r}")

    # Gate 5: NEVER "more X" / "most X" periphrastic forms
    for v in variants:
        val = v.get("value", "")
        if val.startswith("more ") or val.startswith("most "):
            failures.append(f"periphrastic variant not allowed: {val!r}")
            break

    return HardGateResult(
        passed=len(failures) == 0,
        failures=failures,
    )


# ===========================================================================
# SECTION 5: Unified Pipeline (spec §3)
# ===========================================================================

def _rule_plural(word_id: str) -> str:
    # Simple rule-based plural as last-resort fallback
    if word_id.endswith(("s", "x", "z", "ch", "sh")):
        return word_id + "es"
    if word_id.endswith("y") and len(word_id) > 1 and word_id[-2] not in "aeiou":
        return word_id[:-1] + "ies"
    return word_id + "s"


def process_word_pipeline(
    word_entry: Dict[str, Any],
    soup,
    ai_env: Optional[Dict] = None,
) -> PipelineResult:
    # ── Step 1: Parse Wiktionary HTML ──
    wikt_data = parse_wiktionary_full(soup)

    result = PipelineResult()

    if not wikt_data.pos_blocks:
        result.status = "error"
        result.rejection_reason = "no POS blocks found in Wiktionary"
        return result

    # ── Step 2: Calculate dictionary score ──
    dict_score = calculate_dict_score(word_entry, wikt_data)
    result.dict_score = dict_score

    # ── Step 3: Determine if AI is needed ──
    # spec §5.4: score >= 8 → optional, 5~7 → recommended, < 5 → mandatory
    # v1.1 policy: ALWAYS call AI (AI-centric architecture)
    # Only skip if ai_env is unavailable AND score >= 8
    need_ai = True
    if ai_env is None:
        ai_env = _load_ai_env()
    if ai_env is None and dict_score.score >= 8:
        need_ai = False

    # ── Step 4: AI Judgment ──
    ai_response = None
    if need_ai and ai_env:
        ai_response = _call_ai(word_entry, wikt_data, dict_score, ai_env)
        if ai_response:
            result.ai_used = True

    # ── Step 5: Build result from AI or fallback ──
    word_id = word_entry.get("id", "")
    canonical_pos = word_entry.get("canonical_pos", "noun")

    if ai_response:
        # AI-driven path (primary)
        result.selected_pos = ai_response.get("selected_pos") or canonical_pos
        result.description_en = ai_response.get("description_en")
        result.confidence = ai_response.get("confidence", "medium")

        # from
        from_val = ai_response.get("from")
        if from_val and isinstance(from_val, str) and from_val.lower() != "null":
            result.from_word = from_val.lower().strip()
        else:
            result.from_word = None

        # variants from AI — normalize type names, deduplicate
        _VTYPE_NORM = {
            "third_person_singular": "verb_form",
            "3rd_person_singular":   "verb_form",
            "third-person singular": "verb_form",
            "simple_past":           "past",
            "past_tense":            "past",
            "adverb":                "adv_form",
            "noun_derived":          "noun_form",
            "verb_form_derived":     "verb_derived",
            "adverb_form":           "adv_form",
            "adjective_form":        "adj_form",
        }
        raw_variants = ai_response.get("variants_keep") or []
        result.variants = []
        seen_keys: Set[Tuple[str, str]] = set()
        for v in raw_variants:
            if isinstance(v, dict):
                vtype = v.get("type", "").strip()
                vtype = _VTYPE_NORM.get(vtype, vtype)
                vval  = v.get("value", "").strip()
                # Skip periphrastic forms
                if vval.startswith("more ") or vval.startswith("most "):
                    continue
                if vtype and vval:
                    key = (vtype, vval.lower())
                    if key not in seen_keys:
                        seen_keys.add(key)
                        result.variants.append({"type": vtype, "value": vval})
    else:
        # Fallback path (no AI available): use parser data directly
        result.selected_pos = canonical_pos
        result.confidence = "low"
        result.description_en = None

        # Use the first definition as description
        for pb in wikt_data.pos_blocks:
            if pb.pos == canonical_pos and pb.definitions:
                result.description_en = pb.definitions[0]
                break
        if not result.description_en:
            for pb in wikt_data.pos_blocks:
                if pb.definitions:
                    result.description_en = pb.definitions[0]
                    break

        # Variants from parser, filtered by POS
        inflections: List[Dict[str, str]] = []
        for pb in wikt_data.pos_blocks:
            if pb.pos == canonical_pos:
                inflections.extend(pb.inflections)
        if not inflections:
            for pb in wikt_data.pos_blocks:
                inflections.extend(pb.inflections)

        allowed = VARIANTS_KEEP_BY_POS.get(canonical_pos)
        if allowed is not None:
            inflections = [v for v in inflections if v.get("type") in allowed]
        # Deduplicate
        seen_keys = set()
        for v in inflections:
            key = (v.get("type", ""), v.get("value", "").lower())
            if key not in seen_keys:
                seen_keys.add(key)
                result.variants.append(v)

    # Noun plural fallback (rule-based) — only if AI returned no plural
    sel_pos = result.selected_pos or canonical_pos
    if sel_pos == "noun":
        has_plural = any(v.get("type") == "plural" for v in result.variants)
        if not has_plural:
            rule_pl = _rule_plural(word_id)
            if rule_pl != word_id:
                result.variants.append({"type": "plural", "value": rule_pl})

    # ── Step 6: Hard Gate validation ──
    gate_input = {
        "selected_pos": result.selected_pos,
        "from": result.from_word,
        "variants_keep": result.variants,
        "description_en": result.description_en,
        "confidence": result.confidence,
    }
    gate = validate_hard_gate(word_id, gate_input, word_entry)
    result.gate_result = gate

    if gate.passed:
        result.status = "ok"
    else:
        result.status = "rejected"
        result.rejection_reason = "; ".join(gate.failures)

    return result


# ---------------------------------------------------------------------------
# Convenience: fetch + process in one call
# ---------------------------------------------------------------------------

def fetch_and_process(
    term: str,
    word_entry: Dict[str, Any],
    ai_env: Optional[Dict] = None,
    timeout: int = 20,
) -> Tuple[str, Optional[PipelineResult]]:
    try:
        import requests
        headers = {"User-Agent": "Mozilla/5.0 (compatible; BOMTS-Glossary/3.2)"}
        url = f"https://en.wiktionary.org/wiki/{requests.utils.quote(term)}"
        resp = requests.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()
    except Exception:
        return "", None

    soup = BeautifulSoup(resp.text, "lxml")
    return url, process_word_pipeline(word_entry, soup, ai_env=ai_env)


# ---------------------------------------------------------------------------
# Backward compat: filter_variants_by_pos (used by external callers)
# ---------------------------------------------------------------------------

def filter_variants_by_pos(
    variants: List[Dict[str, str]],
    canonical_pos: str,
) -> List[Dict[str, str]]:
    allowed = VARIANTS_KEEP_BY_POS.get(canonical_pos)
    if allowed is None:
        return variants
    return [v for v in variants if v.get("type") in allowed]
