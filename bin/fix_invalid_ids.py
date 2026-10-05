"""규칙 위반 id 정리 (1회성, 2026-10-05): id -> from(약어 원형) 또는 기본형. 판단 불가 항목은 diagnose 가 INVALID_ID 로 표시.
실행: 사전 상위 디렉터리에서 python glossary/bin/fix_invalid_ids.py"""
import json, re, sys
sys.path.insert(0, ".")
from glossary.core.writer import GlossaryWriter

OVERRIDE = {"accumulation (또는 accumulated)": "accumulation", "cap (또는 capacity)": "cap",
            "physical and medical rehabilitation": None, "temporary file": None}


def plan(words, compounds):
    ids = {x["id"] for x in words} | {x["id"] for x in compounds}
    refs = {wid for c in compounds for wid in (c.get("words") or [])}
    out = []
    for x in words:
        i = x["id"]
        if re.fullmatch(r"[a-z][a-z0-9]*", i) or i.startswith("[n]") or "[n]" in i:
            continue
        cands = []
        f = (x.get("from") or "").strip().lower()
        if f: cands.append(f)
        base = re.split(r"[\s(,]", re.sub(r"\s*\(.*\)", "", i).split(",")[0].strip())[0].lower()
        cands.append(base)
        new = next((c for c in cands if re.fullmatch(r"[a-z][a-z0-9]*", c) and c not in ids), None)
        if i in refs:
            new = None
        new = OVERRIDE.get(i, new)
        out.append((i, new, x.get("lang", {}).get("ko"), f))
    for c in compounds:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", c["id"]) and "[n]" not in c["id"]:
            out.append((c["id"], None, c.get("lang", {}).get("ko"), "compound"))
    return out

def apply(gw, p):
    done, flagged = [], []
    for old, new, ko, f in p:
        if new is None:
            flagged.append(old); continue          # diagnose --write 가 INVALID_ID 로 표시
        e = dict(gw.get_word(old))
        e["id"] = new
        e.setdefault("lang", {})["en"] = e.get("lang", {}).get("en") or old
        e["note"] = (e.get("note", "") + f" id 정리: '{old}' -> '{new}'").strip()
        e["variants"] = [v for v in (e.get("variants") or []) if str(v.get("short", "")).lower() != new]
        e.pop("need_modify", None)
        gw.remove_word(old)
        gw.add_word(e)
        done.append((old, new))
    return done, flagged

if __name__ == "__main__":
    with GlossaryWriter() as gw:
        p = plan(gw.words, gw.compounds)
        done, flagged = apply(gw, p)
        f = gw.validate()
        print("validate:", f[:6])
        if f: gw.rollback(); sys.exit(1)
        gw.save()
    for o, n in done: print(f"  정리 {o!r} -> {n}")
    for o in flagged: print(f"  표시 {o!r} (INVALID_ID)")
