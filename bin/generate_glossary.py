#!/usr/bin/env python3
"""
generate_glossary.py
terms.json → GLOSSARY.md 자동 생성 스크립트

사용법:
    python3 generate_glossary.py
    python3 generate_glossary.py --input terms.json --output GLOSSARY.md
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import date

CATEGORY_LABELS = {
    "market":   "🌐 시장 / 마켓 (Markets)",
    "tool":     "🔧 툴 / 플랫폼 (Tools & Platforms)",
    "infra":    "🏗️  인프라 (Infrastructure)",
    "domain":   "📐 도메인 개념 (Domain Concepts)",
    "order":    "📋 거래 / 주문 (Trading & Orders)",
    "risk":     "🛡️  리스크 관리 (Risk Management)",
    "data":     "📊 시장 데이터 (Market Data)",
    "account":  "💰 계좌 / 잔고 (Account & Balance)",
    "system":   "⚙️  시스템 운영 (System Operation)",
    "config":   "🔑 설정 / 환경변수 (Config & Env)",
    "report":   "📈 리포트 / 알림 (Report & Notification)",
    "module":   "📁 모듈 / 디렉토리 (Modules & Directories)",
    "class":    "🧩 클래스 / 열거형 (Classes & Enums)",
    "session":  "🕐 세션 / 시간 (Sessions & Time)",
    "selector": "🔍 종목 선정 / 스코어링 (Selector & Scoring)",
    "status":   "🚦 상태값 (Status Values)",
}

CATEGORY_ORDER = [
    "market", "tool", "infra", "domain", "order", "risk",
    "data", "account", "system", "config", "report",
    "module", "class", "session", "selector", "status",
]


def load_terms(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_conflict_map(terms: list) -> dict:
    """abbr_short 기준 중복 맵 생성"""
    m = defaultdict(list)
    for t in terms:
        m[t["abbr_short"]].append(t["id"])
    return {k: v for k, v in m.items() if len(v) > 1}


def generate_md(data: dict) -> str:
    meta = data["meta"]
    terms = data["terms"]
    today = date.today().isoformat()

    # category → terms 매핑 (primary category = categories[0])
    cat_map: dict[str, list] = defaultdict(list)
    for t in terms:
        primary = t.get("categories", ["domain"])[0]
        cat_map[primary].append(t)

    conflict_map = build_conflict_map(terms)

    lines = []

    # ── 헤더 ──────────────────────────────────────────────────────────
    lines.append(f"# {meta['project']} – 용어 사전 (Glossary)")
    lines.append("")
    lines.append(f"> {meta['description']}")
    lines.append(f">")
    lines.append(f"> **버전:** {meta['version']}  |  **최종 수정:** {today}")
    lines.append(f">")
    lines.append(f"> ⚠️  이 파일은 `terms.json`으로부터 자동 생성됩니다. 직접 편집하지 마세요.")
    lines.append("")

    # ── 사용 규칙 ──────────────────────────────────────────────────────
    lines.append("## 📌 약어 사용 규칙")
    lines.append("")
    lines.append("| 약어 종류 | 사용 위치 |")
    lines.append("|-----------|-----------|")
    for k, v in meta["usage_rules"].items():
        lines.append(f"| `{k}` | {', '.join(v)} |")
    lines.append("")

    # ── 중요 수정 사항 ──────────────────────────────────────────────────
    lines.append("## 🔄 기존 용어에서 수정된 사항")
    lines.append("")
    lines.append("| 기존 (잘못된 용어) | 수정 후 | 이유 |")
    lines.append("|-------------------|---------|------|")
    lines.append("| `mt5Futures` / `MT5_FUT` | `fxFutures` / `FX_FUT` | MT5는 툴(플랫폼)이며 마켓이 아님 |")
    lines.append("")

    # ── abbr_short 충돌 주의 ───────────────────────────────────────────
    same_concept_conflicts = {k: v for k, v in conflict_map.items()}
    if same_concept_conflicts:
        lines.append("## ⚠️  abbr_short 중복 주의 (동일 개념 다계층)")
        lines.append("")
        lines.append("아래 약어는 동일 개념의 다른 계층(도메인↔DB↔클래스↔모듈)에서 공유됩니다. 컨텍스트로 구분하세요.")
        lines.append("")
        lines.append("| abbr_short | 공유 용어들 |")
        lines.append("|------------|-------------|")
        for short, ids in sorted(same_concept_conflicts.items()):
            lines.append(f"| `{short}` | {', '.join(f'`{i}`' for i in ids)} |")
        lines.append("")

    # ── 목차 ──────────────────────────────────────────────────────────
    lines.append("## 목차")
    lines.append("")
    for i, cat in enumerate(CATEGORY_ORDER, 1):
        label = CATEGORY_LABELS.get(cat, cat)
        anchor = label.lower().replace(" ", "-").replace("/", "").replace("(", "").replace(")", "").replace("&", "").replace("🌐", "").replace("🔧", "").replace("🏗️", "").replace("📐", "").replace("📋", "").replace("🛡️", "").replace("📊", "").replace("💰", "").replace("⚙️", "").replace("🔑", "").replace("📈", "").replace("📁", "").replace("🧩", "").replace("🕐", "").replace("🔍", "").replace("🚦", "").strip("-").strip()
        lines.append(f"{i}. [{label}](#{anchor})")
    lines.append("")

    # ── 카테고리별 테이블 ──────────────────────────────────────────────
    for cat in CATEGORY_ORDER:
        if cat not in cat_map:
            continue
        label = CATEGORY_LABELS.get(cat, cat)
        lines.append(f"---")
        lines.append("")
        lines.append(f"## {label}")
        lines.append("")

        cat_terms = sorted(cat_map[cat], key=lambda t: t.get("ko", ""))

        # 클래스 카테고리는 module 컬럼 추가
        if cat == "class":
            lines.append("| 한글명 | 클래스명 | abbr_long | abbr_short | 유형 | 모듈 | 설명 |")
            lines.append("|--------|---------|-----------|------------|------|------|------|")
            for t in cat_terms:
                module = t.get("module", "-")
                ctype = t.get("class_type", "-")
                desc = t.get("description", "")
                not_str = ""
                if t.get("NOT"):
                    not_str = f" ❌ NOT: {', '.join(f'`{n}`' for n in t['NOT'])}"
                note_str = f" *(⚠️ {t['note']})*" if t.get("note") else ""
                lines.append(f"| {t['ko']} | `{t['en']}` | `{t['abbr_long']}` | `{t['abbr_short']}` | {ctype} | `{module}` | {desc}{not_str}{note_str} |")
        else:
            lines.append("| 한글명 | 영문명 | abbr_long | abbr_short | 카테고리 | 설명 |")
            lines.append("|--------|--------|-----------|------------|----------|------|")
            for t in cat_terms:
                cats = ", ".join(f"`{c}`" for c in t.get("categories", []))
                desc = t.get("description", "")
                not_str = ""
                if t.get("NOT"):
                    not_str = f" ❌ NOT: {', '.join(f'`{n}`' for n in t['NOT'])}"
                note_str = f" *(⚠️ {t['note']})*" if t.get("note") else ""
                lines.append(f"| {t['ko']} | `{t['en']}` | `{t['abbr_long']}` | `{t['abbr_short']}` | {cats} | {desc}{not_str}{note_str} |")
        lines.append("")

    # ── 전체 색인 ─────────────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("## 🔤 전체 색인 (abbr_short 알파벳순)")
    lines.append("")
    lines.append("| abbr_short | abbr_long | 한글명 | 영문명 |")
    lines.append("|------------|-----------|--------|--------|")
    sorted_terms = sorted(terms, key=lambda t: t["abbr_short"])
    for t in sorted_terms:
        lines.append(f"| `{t['abbr_short']}` | `{t['abbr_long']}` | {t['ko']} | `{t['en']}` |")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="terms.json → GLOSSARY.md 생성")
    parser.add_argument("--input", default="../terms.json")
    parser.add_argument("--output", default="../GLOSSARY.md")
    args = parser.parse_args()

    data = load_terms(args.input)
    md = generate_md(data)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"✅ {args.output} 생성 완료 ({len(data['terms'])}개 용어)")


if __name__ == "__main__":
    main()
