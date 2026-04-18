#!/usr/bin/env python3
"""
migrate_words_relations.py  — v2 (mw-heading compatible)

Glossary migration helper for BOM_TS.
Plan: Glossary Migration & Canonical Consolidation Plan v1.0

Goals
- Enrich words.json with:
  - from      (Etymology 기반)
  - synonyms
  - antonyms
  - derived_terms
  - inflections → variants (past / present_participle / plural / noun_form)
  - source_urls (Wiktionary)
- Create missing base-words from `from` into pending_words.json
- Produce reports for duplicate / merge candidates
- Optionally promote `from` links into base-word variants
- Step 10: re-run generate_glossary.py generate

Notes
- Script is conservative by default (--dry-run).
- Use --apply to write changes.
- Use --promote-from-variants to also cross-link base words.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import quote

try:
    import requests
    from bs4 import BeautifulSoup, Tag
except ImportError:
    print(
        "Missing dependency. Install with:\n"
        "  pip install requests beautifulsoup4 lxml",
        file=sys.stderr,
    )
    raise

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WIKT_BASE = "https://en.wiktionary.org/wiki/"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BOMTS-Glossary-Migrator/2.0)"
}

# canonical_pos → preferred variant type when cross-linking base words
VARIANT_TYPE_BY_POS: Dict[str, str] = {
    "noun": "noun_form",
    "verb": "verb",
    "adj": "adjective",
    "adv": "adverb",
    "proper": "alias",
    "mixed": "alias",
    "prefix": "alias",
    "suffix": "alias",
}

# Wiktionary inflection template name → variants.type
INFL_MAP: Dict[str, str] = {
    "simple past": "past",
    "past tense": "past",
    "past": "past",
    "past participle": "past_participle",
    "present participle": "present_participle",
    "third-person singular simple present": "verb_form",
    "third person singular": "verb_form",
    "plural": "plural",
}


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@dataclass
class Stats:
    inspected: int = 0
    enriched_from: int = 0
    enriched_synonyms: int = 0
    enriched_antonyms: int = 0
    enriched_derived_terms: int = 0
    enriched_variants: int = 0
    source_urls_added: int = 0
    missing_from_candidates: int = 0
    promoted: int = 0
    fetch_errors: int = 0


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def norm_token(value: str) -> str:
    value = (value or "").strip()
    value = value.replace("\u2019", "'").replace("\u2010", "-").replace("\u2013", "-").replace("\u2014", "-")
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


def has_variant(word: Dict[str, Any], variant_type: str,
                value: Optional[str] = None,
                short: Optional[str] = None,
                long: Optional[str] = None) -> bool:
    for v in (word.get("variants") or []):
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
    if has_variant(word,
                   variant_type=variant.get("type", ""),
                   value=variant.get("value"),
                   short=variant.get("short"),
                   long=variant.get("long")):
        return False
    variants.append(variant)
    return True


def merge_id_list(existing: List[str], new_values: List[str]) -> List[str]:
    merged = list(existing or [])
    seen = {norm_id(v) for v in merged}
    for raw in new_values:
        vid = norm_id(raw)
        if not vid or vid in seen:
            continue
        merged.append(vid)
        seen.add(vid)
    return merged


# ---------------------------------------------------------------------------
# Wiktionary HTML parser  — mw-heading compatible (2024+ structure)
# ---------------------------------------------------------------------------

def fetch_wiktionary(term: str, timeout: int = 20) -> Tuple[str, BeautifulSoup]:
    url = f"{WIKT_BASE}{quote(term)}"
    resp = requests.get(url, timeout=timeout, headers=REQUEST_HEADERS)
    resp.raise_for_status()
    return url, BeautifulSoup(resp.text, "lxml")


def _mw_heading_level(div: Tag) -> Optional[int]:
    """Return heading level (2,3,4…) if div is a mw-heading, else None."""
    classes = div.get("class") or []
    for cls in classes:
        m = re.match(r"mw-heading(\d)", cls)
        if m:
            return int(m.group(1))
    return None


def _get_sections(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Walk the page top-level and collect sections as:
      { 'level': int, 'title': str, 'nodes': [sibling tags until next heading] }
    Uses the new mw-heading div structure.
    """
    sections: List[Dict[str, Any]] = []
    for div in soup.find_all("div", class_=re.compile(r"mw-heading")):
        lvl = _mw_heading_level(div)
        if lvl is None:
            continue
        # The heading text is inside the div (h2/h3/h4…)
        title_tag = div.find(re.compile(r"^h\d$"))
        title = title_tag.get_text(" ", strip=True) if title_tag else div.get_text(" ", strip=True)
        # Remove "[edit]" suffix Wiktionary inserts
        title = re.sub(r"\s*\[\s*edit\s*\]\s*$", "", title).strip()

        # Collect sibling content nodes until the next same-or-higher heading div
        content: List[Any] = []
        node = div.find_next_sibling()
        while node:
            if isinstance(node, Tag):
                node_lvl = _mw_heading_level(node) if node.name == "div" else None
                if node_lvl is not None and node_lvl <= lvl:
                    break
            content.append(node)
            node = node.find_next_sibling()

        sections.append({"level": lvl, "title": title, "nodes": content})
    return sections


def _find_english_subsections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return subsections (level 3/4) that belong under English (level 2)."""
    in_english = False
    result: List[Dict[str, Any]] = []
    for sec in sections:
        if sec["level"] == 2:
            if sec["title"].lower() == "english":
                in_english = True
            elif in_english:
                break  # next language section
        elif in_english:
            result.append(sec)
    return result


def _text_from_nodes(nodes: List[Any]) -> str:
    parts = []
    for n in nodes:
        if isinstance(n, Tag):
            parts.append(n.get_text(" ", strip=True))
    return " ".join(parts)


def _extract_links_from_nodes(nodes: List[Any]) -> List[str]:
    out: List[str] = []
    for n in nodes:
        if not isinstance(n, Tag):
            continue
        for a in n.find_all("a"):
            text = norm_token(a.get_text(" ", strip=True))
            if not text:
                continue
            if ":" in text or text.lower() in {"edit", "appendix"}:
                continue
            if not re.match(r"^[A-Za-z][A-Za-z0-9' _-]*$", text):
                continue
            out.append(norm_id(text))
    return unique_keep_order(out)


# Etymology: "From X + suffix" patterns
FROM_PATTERNS = [
    re.compile(r"^\s*From\s+([A-Za-z][A-Za-z'\-\s]*?)(?:\s*\+\s*[-A-Za-z]+|\s*[.,;(])", re.I),
    re.compile(r"^\s*From\s+the\s+plural\s+of\s+([A-Za-z][A-Za-z'\-\s]*?)(?:\s*[.,;(])", re.I),
    re.compile(r"^\s*From\s+the\s+past\s+participle\s+of\s+([A-Za-z][A-Za-z'\-\s]*?)(?:\s*[.,;(])", re.I),
    re.compile(r"^\s*From\s+([A-Za-z][A-Za-z'\-\s]*?)\s+with\s+", re.I),
]


def _extract_from_text(text: str) -> Optional[str]:
    text = norm_token(text)
    for pat in FROM_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        candidate = norm_token(m.group(1))
        candidate = re.sub(r"^(the|a|an)\s+", "", candidate, flags=re.I)
        if " " in candidate:
            candidate = candidate.split()[0]
        candidate = candidate.strip(" .,;:()[]{}\"'")
        if candidate:
            return norm_id(candidate)
    return None


def _extract_from_etymology(nodes: List[Any]) -> Optional[str]:
    for n in nodes:
        if not isinstance(n, Tag) or n.name != "p":
            continue
        text = n.get_text(" ", strip=True)
        candidate = _extract_from_text(text)
        if candidate:
            return candidate
        # fallback: first linked term after "From "
        if text.lower().startswith("from "):
            for a in n.find_all("a"):
                raw = norm_token(a.get_text(" ", strip=True))
                if re.match(r"^[A-Za-z][A-Za-z'\- ]*$", raw):
                    return norm_id(raw)
    return None


def _extract_inflections(nodes: List[Any]) -> List[Dict[str, str]]:
    """
    Extract inflection table values (past, present_participle, plural…).
    Wiktionary uses <b> / <strong> inside inflection-table spans.
    """
    variants: List[Dict[str, str]] = []
    for n in nodes:
        if not isinstance(n, Tag):
            continue
        # Look for inflection table
        table = n.find(class_=re.compile(r"inflection-table|wikitable"))
        if not table:
            # Also check direct <span class="..."> patterns in headword line
            # e.g. <b>activated</b> inside a conjugation span
            pass

        # Simple approach: find <span> with data labels in inflection tables
        for row in n.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                label = cells[0].get_text(" ", strip=True).lower()
                value_cell = cells[1]
                val = value_cell.get_text(" ", strip=True)
                val = re.sub(r"\s*\[.*?\]", "", val).strip()
                if not val or val.lower() == "—":
                    continue
                for infl_label, vtype in INFL_MAP.items():
                    if infl_label in label:
                        norm_val = norm_id(val)
                        if norm_val:
                            variants.append({"type": vtype, "value": val})
                        break
    return variants


def parse_wiktionary_entry(term: str) -> Dict[str, Any]:
    url, soup = fetch_wiktionary(term)
    sections = _get_sections(soup)
    eng_subs = _find_english_subsections(sections)

    result: Dict[str, Any] = {
        "source_url": url,
        "from": None,
        "synonyms": [],
        "antonyms": [],
        "derived_terms": [],
        "inflections": [],
    }

    for sec in eng_subs:
        title_lower = sec["title"].lower()
        nodes = sec["nodes"]

        if title_lower.startswith("etymology"):
            candidate = _extract_from_etymology(nodes)
            if candidate and not result["from"]:
                result["from"] = candidate

        elif title_lower == "synonyms":
            result["synonyms"] = _extract_links_from_nodes(nodes)

        elif title_lower == "antonyms":
            result["antonyms"] = _extract_links_from_nodes(nodes)

        elif title_lower == "derived terms":
            result["derived_terms"] = _extract_links_from_nodes(nodes)

        elif title_lower in ("verb", "noun", "adjective", "adverb"):
            inflections = _extract_inflections(nodes)
            result["inflections"].extend(inflections)

    return result


# ---------------------------------------------------------------------------
# Migration logic
# ---------------------------------------------------------------------------

def build_word_index(words_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {w["id"]: w for w in words_data.get("words", [])}


def create_pending_stub(word_id: str, domain: str = "general") -> Dict[str, Any]:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "id": word_id,
        "domain": domain,
        "status": "active",
        "canonical_pos": "mixed",
        "lang": {"en": word_id},
        "description_i18n": {
            "ko": "from 관계 보강을 위해 생성된 pending canonical 후보"
        },
        "reason": "auto-created: missing 'from' base during glossary migration v1.0",
        "created_at": now,
        "updated_at": now,
    }


def promote_from_variants(
    words_data: Dict[str, Any],
    promote_report: List[Dict[str, Any]],
    stats: Stats,
) -> None:
    """
    For each word that has `from` pointing to another registered word,
    add this word's id as a variant on the base word.
    """
    idx = build_word_index(words_data)
    for w in words_data.get("words", []):
        from_id = norm_id(w.get("from", ""))
        if not from_id or from_id == w["id"]:
            continue
        if from_id not in idx:
            continue
        base = idx[from_id]
        vtype = VARIANT_TYPE_BY_POS.get(w.get("canonical_pos", "mixed"), "alias")
        added = add_variant(base, {"type": vtype, "value": w["id"]})
        if added:
            stats.promoted += 1
        promote_report.append({
            "word_id": w["id"],
            "from": from_id,
            "base_word_id": base["id"],
            "proposed_variant_type": vtype,
            "domain_match": (w.get("domain") == base.get("domain")),
            "status": "promoted_to_variant" if added else "already_present",
        })


def find_duplicate_candidates(words_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    buckets: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for w in words_data.get("words", []):
        from_id = norm_id(w.get("from", ""))
        domain = w.get("domain", "")
        if from_id:
            buckets[(from_id, domain)].append(w["id"])
    out: List[Dict[str, Any]] = []
    for (from_id, domain), ids in sorted(buckets.items()):
        uniq = unique_keep_order(ids)
        if len(uniq) < 2:
            continue
        out.append({"from": from_id, "domain": domain, "word_ids": uniq,
                    "reason": "same from + same domain"})
    return out


def migrate(
    words_path: Path,
    pending_words_path: Path,
    report_dir: Path,
    apply_changes: bool,
    promote_from: bool,
    run_generate: bool,
    glossary_root: Path,
    sleep_sec: float = 0.5,
) -> int:
    words_data = read_json(words_path)
    copy.deepcopy(words_data)  # keep original reference for diff reporting

    words = words_data.get("words", [])
    if not isinstance(words, list):
        raise ValueError(f"Invalid words file: {words_path}")

    stats = Stats()
    index = build_word_index(words_data)
    existing_ids: Set[str] = set(index.keys())

    # Load or create pending_words.json
    if pending_words_path.exists():
        pending_data = read_json(pending_words_path)
        if not isinstance(pending_data.get("words"), list):
            pending_data = {"words": []}
    else:
        pending_data = {"words": []}
    pending_index: Dict[str, Any] = {w["id"]: w for w in pending_data["words"]}

    enrich_report: List[Dict[str, Any]] = []
    missing_from_report: List[Dict[str, Any]] = []
    promote_report: List[Dict[str, Any]] = []

    total = len(words)
    for i, word in enumerate(words):
        stats.inspected += 1
        term = ((word.get("lang") or {}).get("en") or word["id"]).strip()
        print(f"[{i+1}/{total}] {word['id']} ({term}) ...", flush=True)

        try:
            parsed = parse_wiktionary_entry(term)
        except Exception as exc:
            stats.fetch_errors += 1
            print(f"  ERROR: {exc}", flush=True)
            enrich_report.append({
                "word_id": word["id"], "term": term,
                "status": "fetch_error", "error": str(exc),
            })
            time.sleep(sleep_sec)
            continue

        changed = False

        # 1. source_url
        if parsed.get("source_url"):
            if ensure_source_url(word, parsed["source_url"]):
                stats.source_urls_added += 1
                changed = True

        # 2. from (etymology)
        from_id = norm_id(parsed.get("from") or "")
        if from_id and from_id != word["id"]:
            if not word.get("from"):
                word["from"] = from_id
                stats.enriched_from += 1
                changed = True
                print(f"  from → {from_id}", flush=True)
            # Ensure base word exists (registered or pending)
            if from_id not in existing_ids and from_id not in pending_index:
                stub = create_pending_stub(from_id, domain=word.get("domain", "general"))
                pending_data["words"].append(stub)
                pending_index[from_id] = stub
                stats.missing_from_candidates += 1
                missing_from_report.append({
                    "word_id": word["id"], "from": from_id,
                    "action": "added_to_pending_words",
                })

        # 3. synonyms / antonyms / derived_terms
        for rel_key, stat_attr in (
            ("synonyms",     "enriched_synonyms"),
            ("antonyms",     "enriched_antonyms"),
            ("derived_terms","enriched_derived_terms"),
        ):
            before = set(norm_id(v) for v in (word.get(rel_key) or []))
            merged = merge_id_list(word.get(rel_key) or [], parsed.get(rel_key) or [])
            after = set(norm_id(v) for v in merged)
            if after != before:
                word[rel_key] = merged
                setattr(stats, stat_attr, getattr(stats, stat_attr) + 1)
                changed = True
                print(f"  {rel_key}: {len(merged)} items", flush=True)

        # 4. inflections → variants
        for infl in (parsed.get("inflections") or []):
            added = add_variant(word, infl)
            if added:
                stats.enriched_variants += 1
                changed = True
                print(f"  variant {infl['type']} = {infl.get('value')}", flush=True)

        enrich_report.append({
            "word_id": word["id"],
            "term": term,
            "status": "changed" if changed else "no_change",
            "from": word.get("from"),
            "synonyms_count": len(word.get("synonyms") or []),
            "antonyms_count": len(word.get("antonyms") or []),
            "derived_terms_count": len(word.get("derived_terms") or []),
            "variants_count": len(word.get("variants") or []),
        })

        time.sleep(sleep_sec)

    # Step 5: promote from → base word variants
    if promote_from:
        promote_from_variants(words_data, promote_report, stats)

    # Step 8: duplicate detection
    duplicate_candidates = find_duplicate_candidates(words_data)

    summary = {
        "stats": stats.__dict__,
        "duplicate_candidate_count": len(duplicate_candidates),
        "pending_word_count": len(pending_data.get("words", [])),
        "apply_changes": apply_changes,
        "promote_from_variants": promote_from,
    }

    # Always write reports
    report_dir.mkdir(parents=True, exist_ok=True)
    write_json(report_dir / "migration_enrich_report.json", enrich_report)
    write_json(report_dir / "migration_missing_from_report.json", missing_from_report)
    write_json(report_dir / "migration_promote_report.json", promote_report)
    write_json(report_dir / "migration_duplicate_candidates.json", duplicate_candidates)
    write_json(report_dir / "migration_summary.json", summary)

    if apply_changes:
        write_json(words_path, words_data)
        write_json(pending_words_path, pending_data)
        print("\n[APPLY] words.json / pending_words.json updated.")
    else:
        print("\n[DRY-RUN] No files modified.")

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # Step 10: re-generate projections
    if apply_changes and run_generate:
        gen_py = glossary_root / "generate_glossary.py"
        if gen_py.exists():
            print("\n[Step 10] Running generate_glossary.py generate ...")
            subprocess.run(
                [sys.executable, str(gen_py), "generate"],
                cwd=str(glossary_root),
                check=False,
            )

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Enrich glossary words.json with Wiktionary data "
                    "(from/synonyms/antonyms/derived_terms/variants)."
    )
    p.add_argument("--words",         default="dictionary/words.json")
    p.add_argument("--pending-words", default="dictionary/pending_words.json")
    p.add_argument("--report-dir",    default="build/report")
    p.add_argument("--glossary-root", default=".",
                   help="Root of glossary/ directory (for generate_glossary.py)")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply",   action="store_true")
    p.add_argument("--promote-from-variants", action="store_true")
    p.add_argument("--run-generate", action="store_true",
                   help="After --apply, run generate_glossary.py generate (Step 10)")
    p.add_argument("--sleep", type=float, default=0.5,
                   help="Seconds between requests (default: 0.5)")
    return p


def main() -> int:
    args = build_parser().parse_args()
    return migrate(
        words_path        = Path(args.words),
        pending_words_path= Path(args.pending_words),
        report_dir        = Path(args.report_dir),
        apply_changes     = args.apply,
        promote_from      = args.promote_from_variants,
        run_generate      = args.run_generate,
        glossary_root     = Path(args.glossary_root),
        sleep_sec         = args.sleep,
    )


if __name__ == "__main__":
    raise SystemExit(main())
