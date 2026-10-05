"""용어 영역(areas) -- doc/glossary_area_rule.md

영역을 선언하지 않은 사용처의 결과를 바꾸지 않는다. 이 모듈은 읽기·계산만 하고 파일을 쓰지 않는다
(쓰기는 core.writer.GlossaryWriter).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

_GLOSSARY = Path(__file__).resolve().parent.parent
AREAS_PATH = _GLOSSARY / "dictionary" / "areas.json"
GENERAL = "general"


def load_areas(path: Path = AREAS_PATH) -> List[Dict[str, Any]]:
    if not path.exists():
        return [{"id": GENERAL, "name_ko": "일반", "tags": ["root"]}]
    return json.loads(path.read_text(encoding="utf-8")).get("areas", [])


def area_ids(areas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    return [a["id"] for a in (areas if areas is not None else load_areas())]


def _domains(entry: Dict[str, Any]) -> List[str]:
    d = entry.get("domain")
    if isinstance(d, str):
        return [d]
    return [x for x in (d or []) if isinstance(x, str)]


def effective_senses(entry: Dict[str, Any]) -> Dict[str, List[str]]:
    """영역 -> 한글명 목록. senses 가 없으면 기존 lang.ko 를 첫 domain 영역의 뜻으로 읽는다 (파일은 그대로)."""
    s = entry.get("senses")
    if isinstance(s, dict) and s:
        return {k: [n for n in (v if isinstance(v, list) else [v]) if n] for k, v in s.items()}
    ko = (entry.get("lang") or {}).get("ko") or entry.get("ko") or ""
    doms = _domains(entry)
    return {(doms[0] if doms else GENERAL): [ko]} if ko else {}


def display_meaning(entry: Dict[str, Any], order: Optional[List[str]] = None) -> str:
    """'금지, 번호' -- 영역 사이 ', ', 한 영역 안의 여러 이름 '/'. general 먼저, 이후 영역 목록 순서."""
    senses = effective_senses(entry)
    order = order if order is not None else area_ids()
    keys = sorted(senses, key=lambda k: (k != GENERAL, order.index(k) if k in order else len(order), k))
    return ", ".join("/".join(senses[k]) for k in keys if senses[k])


def meaning(entry: Dict[str, Any], chain: Optional[List[str]]) -> Optional[Dict[str, Any]]:
    """선언된 영역 순서(앞=일반, 뒤=구체)의 뒤에서부터 찾은 뜻. chain 이 없으면 general -> 대표 뜻."""
    senses = effective_senses(entry)
    for area in reversed(list(chain or [])):
        if senses.get(area):
            return {"area": area, "names": senses[area]}
    if senses.get(GENERAL):
        return {"area": GENERAL, "names": senses[GENERAL]}
    if senses:
        k = next(iter(senses))
        return {"area": k, "names": senses[k]}
    return None


def area_abbreviation_map(entries: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    """영역 -> {약어: 단어 id}"""
    out: Dict[str, Dict[str, str]] = {}
    for e in entries:
        for area, short in (e.get("area_abbreviations") or {}).items():
            if short:
                out.setdefault(area, {})[str(short).lower()] = e["id"]
    return out


def ko_index(entries: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
    """한글명 -> [{id, area}] (R2 확인용 전체 색인)"""
    idx: Dict[str, List[Dict[str, str]]] = {}
    for e in entries:
        for area, names in effective_senses(e).items():
            for n in names:
                n = n.strip()
                if n:
                    idx.setdefault(n, []).append({"id": e["id"], "area": area})
    return idx


def diagnose(words: List[Dict[str, Any]], compounds: List[Dict[str, Any]],
             areas: Optional[List[Dict[str, Any]]] = None, only_explicit: bool = False) -> Dict[str, List[Dict[str, str]]]:
    """원칙 위반 진단: id -> [{code, detail}].
    only_explicit=True 면 senses 를 가진(새 규칙으로 등록된) 항목만 본다 -- validate 경고용."""
    known = set(area_ids(areas))
    entries = list(words) + list(compounds)
    issues: Dict[str, List[Dict[str, str]]] = {}

    def add(eid: str, code: str, detail: str) -> None:
        lst = issues.setdefault(eid, [])
        if not any(i["code"] == code and i["detail"] == detail for i in lst):
            lst.append({"code": code, "detail": detail})

    explicit = {e["id"] for e in entries if isinstance(e.get("senses"), dict) and e.get("senses")}
    for e in entries:
        if only_explicit and e["id"] not in explicit:
            continue
        senses = effective_senses(e)
        if senses and GENERAL not in senses:
            add(e["id"], "NO_GENERAL_SENSE", f"general 뜻 없음 (현재: {display_meaning(e)} @ {', '.join(senses)})")
        for a in set(_domains(e)) | set(senses) | set((e.get("area_abbreviations") or {})):
            if a not in known:
                add(e["id"], "UNKNOWN_AREA", f"영역 목록에 없는 영역 '{a}'")
    for name, refs in ko_index(entries).items():
        ids = sorted({r["id"] for r in refs})
        if len(ids) > 1:
            for eid in ids:
                if only_explicit and eid not in explicit:
                    continue
                add(eid, "R2_DUP_KO", f"'{name}' = {', '.join(ids)}")
    return issues
