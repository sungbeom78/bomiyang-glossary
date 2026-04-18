"""
patch_domain_words.py
fetch_fail 도메인 전용 단어(KIS, KOSDAQ 등)에 수동으로 description_en과
기본 plural variant를 추가한다.
Wiktionary에 등재되지 않은 도메인 약어/고유명사들.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
WORDS_PATH = ROOT / "dictionary" / "words.json"

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Manual patches: (word_id, description_en, canonical_pos, variants_to_add)
# variants_to_add = [(type, value), ...]
PATCHES = {
    "cls": {
        "description_en": "Class object or classifier; in Python, the first argument of a class method referring to the class itself.",
        "canonical_pos": "noun",
        "variants": [],  # abbreviation, no plural
    },
    "db": {
        "description_en": "Database; a structured data store used to persist and query application or trading data.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "dsn": {
        "description_en": "Data Source Name; a connection string or identifier used to specify database connection parameters.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "eod": {
        "description_en": "End of Day; refers to the market close time, used as a boundary for daily trading session resets.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "goldenkey": {
        "description_en": "A system-level authentication key or access token used to authorize privileged operations in the trading system.",
        "canonical_pos": "noun",
        "variants": [("plural", "goldenkeys")],
    },
    "kis": {
        "description_en": "Korea Investment Securities; a Korean brokerage whose API is used for domestic stock trading.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "kosdaq": {
        "description_en": "Korea Securities Dealers Automated Quotations; the Korean tech-focused stock exchange for small and mid-cap companies.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "kospi": {
        "description_en": "Korea Composite Stock Price Index; the main benchmark index of the Korea Exchange (KRX).",
        "canonical_pos": "noun",
        "variants": [],
    },
    "kr": {
        "description_en": "Korea market prefix; used to namespace Korean domestic stock symbols, accounts, and session identifiers.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "main": {
        "description_en": "The primary entry point of a program or the main execution module.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "meta": {
        "description_en": "Metadata or configuration that describes other data structures; used commonly in system configuration contexts.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "mt5": {
        "description_en": "MetaTrader 5; a multi-asset trading platform used for FX futures and CFD trading via broker API integration.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "orderbook": {
        "description_en": "A real-time list of pending buy and sell orders for a financial instrument, organized by price level.",
        "canonical_pos": "noun",
        "variants": [("plural", "orderbooks")],
    },
    "pnl": {
        "description_en": "Profit and Loss; the net financial result of a set of trades or positions over a given period.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "postgresql": {
        "description_en": "An open-source relational database management system used for persistent storage of trading data.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "redis": {
        "description_en": "An in-memory data structure store used as a cache, message broker, and session state backend.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "upbit": {
        "description_en": "Upbit; a major Korean cryptocurrency exchange platform used for crypto asset trading.",
        "canonical_pos": "noun",
        "variants": [],
    },
    "url": {
        "description_en": "Uniform Resource Locator; a web address that identifies the location of a resource on the internet.",
        "canonical_pos": "noun",
        "variants": [("plural", "urls")],
    },
    "vwap": {
        "description_en": "Volume Weighted Average Price; a trading benchmark calculated as the ratio of traded value to total volume over a time period.",
        "canonical_pos": "noun",
        "variants": [],
    },
}


def main() -> None:
    data = json.loads(WORDS_PATH.read_text(encoding='utf-8'))
    ws = data['words']
    wmap = {w['id']: w for w in ws}

    patched = 0
    for wid, patch in PATCHES.items():
        w = wmap.get(wid)
        if not w:
            print(f"  [MISS] {wid}")
            continue

        changed = False

        # description_en
        if patch.get("description_en"):
            di = w.setdefault("description_i18n", {})
            if not di.get("en"):
                di["en"] = patch["description_en"]
                changed = True
                print(f"  [DESC] {wid}")

        # canonical_pos
        if patch.get("canonical_pos") and w.get("canonical_pos") != patch["canonical_pos"]:
            w["canonical_pos"] = patch["canonical_pos"]
            changed = True

        # variants
        existing_vals = {v.get('value', '').lower() for v in (w.get('variants') or [])}
        for vtype, vval in (patch.get("variants") or []):
            if vval.lower() not in existing_vals:
                if "variants" not in w or w["variants"] is None:
                    w["variants"] = []
                w["variants"].append({"type": vtype, "value": vval})
                existing_vals.add(vval.lower())
                changed = True
                print(f"  [VAR]  {wid}: +{vtype}:{vval}")

        if changed:
            w["updated_at"] = NOW
            patched += 1
        else:
            print(f"  [SKIP] {wid}: already OK")

    WORDS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8'
    )
    print(f"\n[DONE] Patched {patched} words -> words.json saved.")


if __name__ == "__main__":
    main()
