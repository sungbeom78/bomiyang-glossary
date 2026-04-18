from pathlib import Path

script = r'''#!/usr/bin/env python3
"""
migrate_words_relations.py

Glossary migration helper for BOM_TS.

Goals
- Enrich words with:
  - from
  - synonyms
  - antonyms
  - derived_terms
  - source_urls
- Keep current typed `variants` structure
- Create missing base words from `from` into pending_words.json
- Produce reports for duplicate / merge candidates
- Optionally promote safe `from` links into base-word variants

Notes
- This script is intentionally conservative by default.
- It does NOT auto-delete words unless `--promote-from-variants` is explicitly used.
- It expects the current words file shape shown in the project's schema.
- Schema must be updated separately if `from`, `synonyms`, `antonyms`, `derived_terms`
  are to be validated as first-class properties.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import quote

try:
    import requests
    from bs4 import BeautifulSoup, Tag
except ImportError as e:
    print(
        "Missing dependency. Install with:\n"
        "  pip install requests beautifulsoup4 lxml",
        file=sys.stderr,
    )
    raise

# -----------------------------
# Config / constants
# -----------------------------

VARIANT_TYPE_BY_POS = {
    "noun": "noun_form",
    "verb": "verb",
    "adj": "adjective",
    "adv": "adverb",
    "proper": "alias",
    "mixed": "alias",
    "prefix": "alias",
    "suffix": "alias",
}

DEFAULT_SOURCE_BASE = "https://en.wiktionary.org/wiki/"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BOMTS-Glossary-Migrator/1.0)"
}


@dataclass
class Stats:
    inspected: int = 0
    enriched_from: int = 0
    enriched_synonyms: int = 0
    enriched_antonyms: int = 0
    enriched_derived_terms: int = 0
    source_urls_added: int = 0
    missing_from_candidates: int = 0
    promote_candidates: int = 0
    promoted: int = 0


# -----------------------------
# File helpers
# -----------------------------

def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


# -----------------------------
# Basic normalization helpers
# -----------------------------

def norm_token(value: str) -> str:
    value = (value or "").strip()
    value = value.replace("’", "'").replace("‐", "-").replace("–", "-").replace("—", "-")
    value = re.sub(r"\s+", " ", value)
    return value


def norm_id(value: str) -> str:
    value = norm_token(value).lower()
    value = value.replace(" ", "_")
    value = re.sub(r"[^a-z0-9_]+", "", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def unique_keep_order(values: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for raw in values:
        value = norm_token(raw)
        if not value:
            continue
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def ensure_list(obj: Dict[str, Any], key: str) -> List[Any]:
    if key not in obj or obj[key] is None:
        obj[key] = []
    if not isinstance(obj[key], list):
        obj[key] = [obj[key]]
    return obj[key]


def ensure_source_url(word: Dict[str, Any], url: str) -> bool:
    urls = ensure_list(word, "source_urls")
    if url not in urls:
        urls.append(url)
        return True
    return False


def has_variant(word: Dict[str, Any], variant_type: str, value: Optional[str] = None,
                short: Optional[str] = None, long: Optional[str] = None) -> bool:
    variants = word.get("variants") or []
    for v in variants:
        if v.get("type") != variant_type:
            continue
        if value is not None and norm_token(v.get("value", "")) != norm_token(value):
            continue
        if short is not None and norm_token(v.get("short", "")) != norm_token(short):
            continue
        if long is not None and norm_token(v.get("long", "")) != norm_token(long):
            continue
        return True
    return False


def add_variant(word: Dict[str, Any], variant: Dict[str, Any]) -> bool:
    variants = ensure_list(word, "variants")
    if has_variant(
        word,
        variant_type=variant.get("type", ""),
        value=variant.get("value"),
        short=variant.get("short"),
        long=variant.get("long"),
    ):
        return False
    variants.append(variant)
    return True


# -----------------------------
# Wiktionary parsing
# -----------------------------

def fetch_wiktionary_html(term: str, timeout: int = 15) -> Tuple[str, str]:
    url = f"{DEFAULT_SOURCE_BASE}{quote(term)}"
    resp = requests.get(url, timeout=timeout, headers=REQUEST_HEADERS)
    resp.raise_for_status()
    return url, resp.text


def _next_section_nodes(start_node: Tag, stop_names: Set[str]) -> List[Tag]:
    out: List[Tag] = []
    node = start_node.find_next_sibling()
    while node:
        if getattr(node, "name", None) in stop_names:
            break
        out.append(node)
        node = node.find_next_sibling()
    return out


def _find_english_section(soup: BeautifulSoup) -> List[Tag]:
    english_anchor = soup.find(id="English")
    if not english_anchor:
        return []
    h2 = english_anchor.find_parent(["h2", "h3"])
    if not h2:
        return []
    return _next_section_nodes(h2, {"h2"})


def _find_subsection_nodes(section_nodes: List[Tag], title_pattern: str) -> List[Tag]:
    regex = re.compile(title_pattern, re.I)
    for node in section_nodes:
        if node.name not in {"h3", "h4"}:
            continue
        text = " ".join(node.stripped_strings)
        if regex.search(text):
            return _next_section_nodes(node, {"h2", "h3"})
    return []


FROM_PATTERNS = [
    re.compile(r"^\s*From\s+([A-Za-z][A-Za-z' -]*?)(?:\s+\+\s+[-A-Za-z]+|\s*[.,;(])", re.I),
    re.compile(r"^\s*From\s+the\s+plural\s+of\s+([A-Za-z][A-Za-z' -]*?)(?:\s*[.,;(])", re.I),
    re.compile(r"^\s*From\s+the\s+past\s+participle\s+of\s+([A-Za-z][A-Za-z' -]*?)(?:\s*[.,;(])", re.I),
    re.compile(r"^\s*From\s+([A-Za-z][A-Za-z' -]*?)\s+with\s+", re.I),
]


def extract_from_term_from_text(text: str) -> Optional[str]:
    text = norm_token(text)
    for pat in FROM_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        candidate = norm_token(m.group(1))
        # Keep first lexical token if phrase is too long.
        candidate = re.sub(r"\s+", " ", candidate)
        # Remove leading determiners or labels.
        candidate = re.sub(r"^(the|a|an)\s+", "", candidate, flags=re.I)
        # Keep first token if there are multiple words and the rest are likely descriptors.
        if " " in candidate:
            candidate = candidate.split()[0]
        candidate = candidate.strip(" .,;:()[]{}")
        if candidate:
            return norm_id(candidate)
    return None


def extract_from_term_from_etymology_nodes(nodes: List[Tag]) -> Optional[str]:
    if not nodes:
        return None
    # Prefer the first paragraph after Etymology.
    for node in nodes:
        if node.name == "p":
            text = " ".join(node.stripped_strings)
            candidate = extract_from_term_from_text(text)
            if candidate:
                return candidate
            # Fallback: first linked term in paragraph after "From"
            text_lower = text.lower()
            if text_lower.startswith("from "):
                for a in node.find_all("a"):
                    raw = norm_token(a.get_text(" ", strip=True))
                    if re.match(r"^[A-Za-z][A-Za-z' -]*$", raw):
                        return norm_id(raw)
    return None


def extract_relation_list(nodes: List[Tag]) -> List[str]:
    out: List[str] = []
    for node in nodes:
        if node.name not in {"ul", "ol", "dl"}:
            continue
        for a in node.find_all("a"):
            text = norm_token(a.get_text(" ", strip=True))
            if not text:
                continue
            # Skip obvious meta links.
            if ":" in text or text.lower() in {"edit", "appendix"}:
                continue
            if not re.match(r"^[A-Za-z][A-Za-z0-9' _-]*$", text):
                continue
            out.append(norm_id(text))
    return unique_keep_order(out)


def parse_wiktionary_entry(term: str) -> Dict[str, Any]:
    url, html = fetch_wiktionary_html(term)
    soup = BeautifulSoup(html, "lxml")
    english_nodes = _find_english_section(soup)

    ety_nodes = _find_subsection_nodes(english_nodes, r"^Etymology")
    syn_nodes = _find_subsection_nodes(english_nodes, r"^Synonyms$")
    ant_nodes = _find_subsection_nodes(english_nodes, r"^Antonyms$")
    der_nodes = _find_subsection_nodes(english_nodes, r"^Derived terms$")

    result = {
        "source_url": url,
        "from": extract_from_term_from_etymology_nodes(ety_nodes),
        "synonyms": extract_relation_list(syn_nodes),
        "antonyms": extract_relation_list(ant_nodes),
        "derived_terms": extract_relation_list(der_nodes),
    }
    return result


# -----------------------------
# Migration logic
# -----------------------------

def build_word_index(words_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {w["id"]: w for w in words_data.get("words", [])}


def build_lookup_index(words_data: Dict[str, Any]) -> Dict[str, Set[str]]:
    """
    Search index for canonical reuse.
    key -> set(word ids)
    """
    idx: Dict[str, Set[str]] = defaultdict(set)
    for w in words_data.get("words", []):
        wid = w["id"]
        idx[norm_id(wid)].add(wid)

        en = ((w.get("lang") or {}).get("en") or "").strip()
        if en:
            idx[norm_id(en)].add(wid)

        for rel_key in ("synonyms", "antonyms", "derived_terms"):
            for v in w.get(rel_key, []) or []:
                idx[norm_id(v)].add(wid)

        for v in w.get("variants", []) or []:
            if "value" in v:
                idx[norm_id(v["value"])].add(wid)
            if "short" in v:
                idx[norm_id(v["short"])].add(wid)
            if "long" in v:
                idx[norm_id(v["long"])].add(wid)
    return idx


def merge_relation_ids(existing: List[str], new_values: List[str], existing_word_ids: Set[str]) -> List[str]:
    merged = list(existing or [])
    seen = {norm_id(v) for v in merged}
    for raw in new_values:
        vid = norm_id(raw)
        if not vid or vid in seen:
            continue
        # Keep only id-like values; they may be registered later via pending_words.
        merged.append(vid)
        seen.add(vid)
    return merged


def infer_variant_type_from_pos(pos: str) -> str:
    return VARIANT_TYPE_BY_POS.get(pos, "alias")


def create_pending_word_stub(word_id: str, source_word: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    domain = "general"
    if source_word:
        domain = source_word.get("domain", "general")
    return {
        "id": word_id,
        "domain": domain,
        "status": "active",
        "canonical_pos": "mixed",
        "lang": {"en": word_id},
        "description_i18n": {
            "ko": "from 관계 보강을 위해 생성된 pending canonical 후보"
        },
        "reason": "auto-created from missing 'from' relation during glossary migration",
        "created_at": now,
        "updated_at": now,
    }


def promote_from_variants(
    words_data: Dict[str, Any],
    promote_report: List[Dict[str, Any]],
    stats: Stats,
) -> None:
    """
    Conservative promotion:
    if word.from exists as another word id,
    add current word id under base word variants by current canonical_pos.
    Does NOT delete current word automatically.
    """
    idx = build_word_index(words_data)
    for w in words_data.get("words", []):
        from_id = norm_id(w.get("from", ""))
        if not from_id or from_id == w["id"]:
            continue
        if from_id not in idx:
            continue

        base = idx[from_id]
        variant_type = infer_variant_type_from_pos(w.get("canonical_pos", "mixed"))
        added = add_variant(base, {"type": variant_type, "value": w["id"]})
        if added:
            stats.promoted += 1

        candidate = {
            "word_id": w["id"],
            "from": from_id,
            "base_word_id": base["id"],
            "proposed_variant_type": variant_type,
            "domain_match": (w.get("domain") == base.get("domain")),
            "status": "promoted_to_variant" if added else "already_present",
        }
        promote_report.append(candidate)


def find_duplicate_candidates(words_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Final duplicate check after from enrichment.
    Conservative rule:
    same from + same domain -> candidate cluster
    """
    buckets: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for w in words_data.get("words", []):
        from_id = norm_id(w.get("from", ""))
        domain = w.get("domain", "")
        if from_id:
            buckets[(from_id, domain)].append(w["id"])

    out: List[Dict[str, Any]] = []
    for (from_id, domain), ids in sorted(buckets.items()):
        uniq_ids = unique_keep_order(ids)
        if len(uniq_ids) < 2:
            continue
        out.append(
            {
                "from": from_id,
                "domain": domain,
                "word_ids": uniq_ids,
                "reason": "same from + same domain",
            }
        )
    return out


def migrate(
    words_path: Path,
    pending_words_path: Path,
    report_dir: Path,
    apply_changes: bool,
    promote_from: bool,
    sleep_sec: float = 0.3,
) -> int:
    words_data = read_json(words_path)
    original = copy.deepcopy(words_data)

    words = words_data.get("words", [])
    if not isinstance(words, list):
        raise ValueError(f"Invalid words file format: {words_path}")

    stats = Stats()
    index = build_word_index(words_data)
    existing_ids: Set[str] = set(index.keys())

    pending_words_data: Dict[str, Any]
    if pending_words_path.exists():
        pending_words_data = read_json(pending_words_path)
        if "words" not in pending_words_data or not isinstance(pending_words_data["words"], list):
            pending_words_data = {"words": []}
    else:
        pending_words_data = {"words": []}
    pending_index = {w["id"]: w for w in pending_words_data.get("words", [])}

    enrich_report: List[Dict[str, Any]] = []
    missing_from_report: List[Dict[str, Any]] = []
    promote_report: List[Dict[str, Any]] = []

    for word in words:
        stats.inspected += 1
        term = ((word.get("lang") or {}).get("en") or word["id"]).strip()
        try:
            parsed = parse_wiktionary_entry(term)
        except Exception as e:
            enrich_report.append(
                {
                    "word_id": word["id"],
                    "term": term,
                    "status": "fetch_error",
                    "error": str(e),
                }
            )
            continue

        changed = False

        if parsed.get("source_url"):
            if ensure_source_url(word, parsed["source_url"]):
                stats.source_urls_added += 1
                changed = True

        from_id = norm_id(parsed.get("from", ""))
        if from_id and from_id != word["id"]:
            if not word.get("from"):
                word["from"] = from_id
                stats.enriched_from += 1
                changed = True
            else:
                word["from"] = norm_id(word["from"])

            if from_id not in existing_ids and from_id not in pending_index:
                stub = create_pending_word_stub(from_id, source_word=word)
                pending_words_data["words"].append(stub)
                pending_index[from_id] = stub
                stats.missing_from_candidates += 1
                missing_from_report.append(
                    {
                        "word_id": word["id"],
                        "from": from_id,
                        "action": "added_to_pending_words",
                    }
                )

        for rel_key, stat_attr in (
            ("synonyms", "enriched_synonyms"),
            ("antonyms", "enriched_antonyms"),
            ("derived_terms", "enriched_derived_terms"),
        ):
            before = set(norm_id(v) for v in (word.get(rel_key) or []))
            merged = merge_relation_ids(word.get(rel_key) or [], parsed.get(rel_key) or [], existing_ids)
            after = set(norm_id(v) for v in merged)
            if after != before:
                word[rel_key] = merged
                setattr(stats, stat_attr, getattr(stats, stat_attr) + 1)
                changed = True

        enrich_report.append(
            {
                "word_id": word["id"],
                "term": term,
                "status": "changed" if changed else "no_change",
                "from": word.get("from"),
                "synonyms_count": len(word.get("synonyms") or []),
                "antonyms_count": len(word.get("antonyms") or []),
                "derived_terms_count": len(word.get("derived_terms") or []),
            }
        )

        time.sleep(sleep_sec)

    if promote_from:
        promote_from_variants(words_data, promote_report, stats)

    duplicate_candidates = find_duplicate_candidates(words_data)

    summary = {
        "stats": stats.__dict__,
        "duplicate_candidate_count": len(duplicate_candidates),
        "pending_word_count": len(pending_words_data.get("words", [])),
        "apply_changes": apply_changes,
        "promote_from_variants": promote_from,
    }

    # Always write reports
    write_json(report_dir / "migration_enrich_report.json", enrich_report)
    write_json(report_dir / "migration_missing_from_report.json", missing_from_report)
    write_json(report_dir / "migration_promote_report.json", promote_report)
    write_json(report_dir / "migration_duplicate_candidates.json", duplicate_candidates)
    write_json(report_dir / "migration_summary.json", summary)

    if apply_changes:
        write_json(words_path, words_data)
        write_json(pending_words_path, pending_words_data)

    # Console summary
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not apply_changes:
        print("\n[DRY-RUN] No files were modified.")
    else:
        print("\n[APPLY] words.json / pending_words.json updated.")

    return 0


# -----------------------------
# CLI
# -----------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Enrich glossary words with from/synonyms/antonyms/derived_terms and create pending base words."
    )
    p.add_argument(
        "--words",
        default="dictionary/words.json",
        help="Path to words.json",
    )
    p.add_argument(
        "--pending-words",
        default="dictionary/pending_words.json",
        help="Path to pending_words.json",
    )
    p.add_argument(
        "--report-dir",
        default="build/report",
        help="Directory for migration reports",
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Run without modifying files")
    mode.add_argument("--apply", action="store_true", help="Apply changes to files")
    p.add_argument(
        "--promote-from-variants",
        action="store_true",
        help="Also add current word id as a variant under its `from` base word when safe",
    )
    p.add_argument(
        "--sleep",
        type=float,
        default=0.3,
        help="Sleep seconds between requests (default: 0.3)",
    )
    return p


def main() -> int:
    args = build_parser().parse_args()
    return migrate(
        words_path=Path(args.words),
        pending_words_path=Path(args.pending_words),
        report_dir=Path(args.report_dir),
        apply_changes=args.apply,
        promote_from=args.promote_from_variants,
        sleep_sec=args.sleep,
    )


if __name__ == "__main__":
    raise SystemExit(main())
'''

path = Path("/mnt/data/migrate_words_relations.py")
path.write_text(script, encoding="utf-8")
print(f"Wrote {path}")
