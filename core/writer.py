#!/usr/bin/env python3
"""
glossary/core/writer.py — GlossaryWriter: 단일 진입점 glossary 저장 관리자.

이 클래스를 통하지 않고 words.json / compounds.json을 직접 write하는 것은 금지.
(change-code-procedure.md §GLOSSARY 참조)

사용 예시:
    from glossary.core.writer import GlossaryWriter

    with GlossaryWriter() as gw:
        gw.add_word({"id": "example", ...})
        gw.add_compound({"id": "example_case", ...})
        # with 블록 종료 시 save() 자동 호출

또는 명시적으로:
    gw = GlossaryWriter()
    gw.add_word(...)
    errors = gw.validate()
    if not errors:
        gw.save()
    else:
        gw.rollback()
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── 경로 설정 ──────────────────────────────────────────────────────────
_CORE_DIR = Path(__file__).resolve().parent
_GLOSSARY = _CORE_DIR.parent
_DICT_DIR = _GLOSSARY / "dictionary"
_GENERATE_PY = _GLOSSARY / "generate_glossary.py"
_BACKUP_DIR = _GLOSSARY / "build" / "backup"

WORDS_PATH = _DICT_DIR / "words.json"
COMPOUNDS_PATH = _DICT_DIR / "compounds.json"
PENDING_PATH = _DICT_DIR / "pending_words.json"
AREAS_PATH = _DICT_DIR / "areas.json"      # 용어 영역 목록 (doc/glossary_area_rule.md)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path, key: str) -> list:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get(key, [])


def _save(path: Path, key: str, items: list) -> None:
    """지정 key의 배열을 지정 경로에 저장 (utf-8, no-BOM, indent=2)."""
    existing: dict = {}
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
    existing[key] = items
    path.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# ── GlossaryWriter ──────────────────────────────────────────────────────
class GlossaryWriter:
    """
    words.json / compounds.json의 단일 진입점 저장 관리자.

    모든 추가·수정·삭제 작업은 이 클래스를 경유.
    직접 파일 write는 금지 (change-code-procedure.md §GLOSSARY).
    """

    def __init__(self) -> None:
        self._words: List[Dict[str, Any]] = list(_load(WORDS_PATH, "words"))
        self._compounds: List[Dict[str, Any]] = list(_load(COMPOUNDS_PATH, "compounds"))
        self._areas: List[Dict[str, Any]] = list(_load(AREAS_PATH, "areas"))
        self._areas_dirty = False
        self._word_snap: Optional[List[Dict]] = None
        self._compound_snap: Optional[List[Dict]] = None
        self._area_snap: Optional[List[Dict]] = None
        self._dirty = False
        self._take_snapshot()

    # ── Context Manager ──────────────────────────────────────────────────
    def __enter__(self) -> "GlossaryWriter":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None and self._dirty:
            self.save()
        elif exc_type is not None:
            self.rollback()

    # ── Snapshot / Rollback ──────────────────────────────────────────────
    def _take_snapshot(self) -> None:
        import copy

        self._word_snap = copy.deepcopy(self._words)
        self._compound_snap = copy.deepcopy(self._compounds)
        self._area_snap = copy.deepcopy(self._areas)

    def rollback(self) -> None:
        """스냅샷으로 메모리 상태 복원 (파일은 건드리지 않음)."""
        if self._word_snap is not None:
            self._words = list(self._word_snap)
        if self._compound_snap is not None:
            self._compounds = list(self._compound_snap)
        if self._area_snap is not None:
            self._areas = list(self._area_snap)
        self._areas_dirty = False
        self._dirty = False

    # ── Words ─────────────────────────────────────────────────────────────
    def word_ids(self) -> set:
        return {w["id"] for w in self._words}

    def get_word(self, word_id: str) -> Optional[Dict]:
        return next((w for w in self._words if w["id"] == word_id), None)

    def add_word(self, word: Dict[str, Any], *, skip_duplicate: bool = False) -> bool:
        """
        words.json에 단어 추가.
        skip_duplicate=False(기본): 중복이면 ValueError.
        skip_duplicate=True: 중복이면 조용히 skip (True 반환).
        Returns: 실제로 추가되었으면 True, skip되었으면 False.
        """
        _normalize_entry(word)
        wid = word.get("id", "").strip()
        if not wid:
            raise ValueError("word.id 필드가 비어 있음")
        if wid in self.word_ids():
            if skip_duplicate:
                return False
            raise ValueError(f"이미 존재하는 word id: {wid!r}")
        _inject_timestamps(word)
        insert_index = next(
            (
                index
                for index, existing_entry in enumerate(self._words)
                if existing_entry.get("id", "") > wid
            ),
            len(self._words),
        )
        self._words.insert(insert_index, word)
        self._dirty = True
        return True

    def update_word(self, word_id: str, patch: Dict[str, Any]) -> bool:
        """
        기존 단어에 patch를 병합(overwrites matching keys).
        Returns: 업데이트 성공이면 True, 단어 미존재 시 False.
        """
        _normalize_entry(patch)
        for i, w in enumerate(self._words):
            if w["id"] == word_id:
                w.update(patch)
                _inject_timestamps(w, update_only=True)
                self._words[i] = w
                self._dirty = True
                return True
        return False

    def remove_word(self, word_id: str) -> bool:
        """단어 삭제. 반환: 삭제되었으면 True."""
        before = len(self._words)
        self._words = [w for w in self._words if w["id"] != word_id]
        changed = len(self._words) < before
        if changed:
            self._dirty = True
        return changed

    def add_word_variant(self, word_id: str, vtype: str, vvalue: str) -> bool:
        """특정 단어에 variant를 추가. 이미 있으면 skip."""
        w = self.get_word(word_id)
        if w is None:
            return False
        variants = w.get("variants", [])
        if not isinstance(variants, list):
            variants = []
        for v in variants:
            if v.get("type") == vtype and v.get("value") == vvalue:
                return False  # already exists
        variants.append({"type": vtype, "value": vvalue})
        w["variants"] = variants
        _inject_timestamps(w, update_only=True)
        self._dirty = True
        return True

    def add_word_abbreviation(
        self,
        word_id: str,
        short: str,
        long: Optional[str] = None,
        *,
        case_sensitive: bool = False,
        confidence: str = "high",
        ambiguity: str = "low",
    ) -> bool:
        """
        단어에 top-level abbreviation 필드를 설정 (단어 단위 약어 전용).

        복합어 기반 약어는 add_compound_variant()를 사용.

        Args:
            word_id:        대상 단어 id (풀네임 단어, 예: "automatic")
            short:          약어 표기 (예: "auto")
            long:           풀네임 word id (명시적으로 지정, 기본=word_id)
            case_sensitive: 대소문자 구분 여부 (기본 False)
            confidence:     신뢰도 ("high" | "medium" | "low")
            ambiguity:      모호성 ("low" | "medium" | "high")

        Returns: True=설정 완료, False=단어 미존재
        """
        w = self.get_word(word_id)
        if w is None:
            return False
        abbr: Dict[str, Any] = {
            "short": short.strip(),
            "long": (long or word_id).strip(),
            "case_sensitive": case_sensitive,
            "confidence": confidence,
            "ambiguity": ambiguity,
        }
        w["abbreviation"] = abbr
        _inject_timestamps(w, update_only=True)
        self._dirty = True
        return True

    # ── Compounds ─────────────────────────────────────────────────────────
    def compound_ids(self) -> set:
        return {c["id"] for c in self._compounds}

    def get_compound(self, cid: str) -> Optional[Dict]:
        return next((c for c in self._compounds if c["id"] == cid), None)

    def add_compound(
        self, compound: Dict[str, Any], *, skip_duplicate: bool = False
    ) -> bool:
        """compounds.json에 복합어 추가."""
        _normalize_entry(compound)
        cid = compound.get("id", "").strip()
        if not cid:
            raise ValueError("compound.id 필드가 비어 있음")
        if cid in self.compound_ids():
            if skip_duplicate:
                return False
            raise ValueError(f"이미 존재하는 compound id: {cid!r}")
        _inject_timestamps(compound)
        insert_index = next(
            (
                index
                for index, existing_entry in enumerate(self._compounds)
                if existing_entry.get("id", "") > cid
            ),
            len(self._compounds),
        )
        self._compounds.insert(insert_index, compound)
        self._dirty = True
        return True

    def update_compound(self, cid: str, patch: Dict[str, Any]) -> bool:
        """복합어 업데이트."""
        _normalize_entry(patch)
        for i, c in enumerate(self._compounds):
            if c["id"] == cid:
                c.update(patch)
                _inject_timestamps(c, update_only=True)
                self._compounds[i] = c
                self._dirty = True
                return True
        return False

    def remove_compound(self, cid: str) -> bool:
        """복합어 삭제."""
        before = len(self._compounds)
        self._compounds = [c for c in self._compounds if c["id"] != cid]
        changed = len(self._compounds) < before
        if changed:
            self._dirty = True
        return changed

    # ── Validation ────────────────────────────────────────────────────────
    def validate(self) -> List[str]:
        """
        generate_glossary.py validate 실행 결과를 파싱하여 FATAL 목록 반환.
        저장 전 호출 권장.
        """
        # 임시 저장 후 validate 실행
        self._write_to_disk()
        try:
            r = subprocess.run(
                [sys.executable, str(_GENERATE_PY), "validate"],
                cwd=str(_GLOSSARY.parent),
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            output = r.stdout + r.stderr
            fatals = [
                line.strip()
                for line in output.splitlines()
                if "[FATAL]" in line or line.strip().startswith("[V-")
            ]
            return fatals
        except Exception as exc:
            return [f"validate 실행 오류: {exc}"]

    # ── Areas (doc/glossary_area_rule.md) ────────────────────────────────
    def area_ids(self) -> set:
        return {a["id"] for a in self._areas}

    def add_area(self, area_id: str, name_ko: str, tags: Optional[List[str]] = None,
                 description: str = "") -> bool:
        """영역 목록에 추가. 이미 있으면 False. id 는 소문자 영숫자·밑줄."""
        import re as _re
        aid = area_id.strip().lower()
        if not _re.fullmatch(r"[a-z][a-z0-9_]*", aid):
            raise ValueError(f"영역 id 형식 오류: {area_id!r}")
        if aid in self.area_ids():
            return False
        entry: Dict[str, Any] = {"id": aid, "name_ko": name_ko, "tags": list(tags or ["area"])}
        if description:
            entry["description"] = description
        self._areas.append(entry)
        self._areas_dirty = True
        self._dirty = True
        return True

    def _entry(self, entry_id: str) -> Dict[str, Any]:
        e = self.get_word(entry_id) or self.get_compound(entry_id)
        if e is None:
            raise ValueError(f"단어/복합어 없음: {entry_id!r}")
        return e

    def _require_area(self, area: str) -> None:
        if self._areas and area not in self.area_ids():
            raise ValueError(f"영역 목록에 없는 영역: {area!r} (먼저 add_area)")

    def add_sense(self, entry_id: str, area: str, names: List[str]) -> None:
        """영역별 한글명 추가 (R1). senses 가 없던 기존 항목은 현재 뜻(lang.ko @ 첫 domain)을 먼저 옮겨 담아 잃지 않는다.
        소속 영역 목록(domain)에도 area 를 추가한다. lang.ko(대표 뜻)는 바꾸지 않는다."""
        from .areas import effective_senses
        self._require_area(area)
        e = self._entry(entry_id)
        if not isinstance(e.get("senses"), dict) or not e.get("senses"):
            e["senses"] = effective_senses(e)
        cur = e["senses"].setdefault(area, [])
        for n in names:
            n = (n or "").strip()
            if n and n not in cur:
                cur.append(n)
        dom = e.get("domain")
        doms = [dom] if isinstance(dom, str) else list(dom or [])
        if area not in doms:
            doms.append(area)
            e["domain"] = doms
        if not (e.get("lang") or {}).get("ko"):
            e.setdefault("lang", {})["ko"] = cur[0] if cur else ""
        self._dirty = True

    def set_area_abbreviation(self, entry_id: str, area: str, short: str) -> None:
        """영역 안에서만 유효한 약어 (전역 약어와 철자가 겹쳐도 된다)."""
        self._require_area(area)
        e = self._entry(entry_id)
        e.setdefault("area_abbreviations", {})[area] = short.strip().lower()
        self._dirty = True

    def set_need_modify(self, entry_id: str, issues: List[Dict[str, str]]) -> None:
        """원칙 위반 표시 (값은 고치지 않는다). issues 가 비면 표시를 지운다."""
        e = self._entry(entry_id)
        if issues:
            e["need_modify"] = {"status": "open", "issues": issues, "noted_at": _now()}
        else:
            e.pop("need_modify", None)
        self._dirty = True

    # ── Save / Backup ─────────────────────────────────────────────────────
    def save(self) -> None:
        """
        words.json, compounds.json 파일에 저장.
        저장 전 자동 backup 생성.
        """
        _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(WORDS_PATH, _BACKUP_DIR / f"words_{ts}.json")
        shutil.copy2(COMPOUNDS_PATH, _BACKUP_DIR / f"compounds_{ts}.json")
        if AREAS_PATH.exists():
            shutil.copy2(AREAS_PATH, _BACKUP_DIR / f"areas_{ts}.json")
        self._write_to_disk()
        self._dirty = False
        self._take_snapshot()

    def _write_to_disk(self) -> None:
        """words, compounds를 실제 파일에 저장."""
        _save(WORDS_PATH, "words", self._words)
        _save(COMPOUNDS_PATH, "compounds", self._compounds)
        if self._areas_dirty:
            _save(AREAS_PATH, "areas", self._areas)
            self._areas_dirty = False

    # ── Properties ───────────────────────────────────────────────────────
    @property
    def words(self) -> List[Dict]:
        return list(self._words)

    @property
    def compounds(self) -> List[Dict]:
        return list(self._compounds)


# ── 헬퍼 ─────────────────────────────────────────────────────────────────
def _inject_timestamps(entry: Dict, *, update_only: bool = False) -> None:
    """created_at / updated_at 필드를 주입."""
    now = _now()
    entry["updated_at"] = now
    if not update_only:
        entry.setdefault("created_at", now)
        entry.setdefault("status", "active")


def _normalize_entry(entry: Dict) -> None:
    """id, lang, variants 등의 값을 소문자로 정규화."""
    if "id" in entry and isinstance(entry["id"], str):
        entry["id"] = entry["id"].strip().lower()

    if "lang" in entry and isinstance(entry["lang"], dict):
        for k, v in entry["lang"].items():
            if isinstance(v, str):
                entry["lang"][k] = v.strip().lower()

    if "variants" in entry and isinstance(entry["variants"], list):
        for v in entry["variants"]:
            if isinstance(v, dict) and "value" in v and isinstance(v["value"], str):
                v["value"] = v["value"].strip().lower()

    if "abbreviation" in entry and isinstance(entry["abbreviation"], dict):
        if "short" in entry["abbreviation"] and isinstance(
            entry["abbreviation"]["short"], str
        ):
            entry["abbreviation"]["short"] = (
                entry["abbreviation"]["short"].strip().lower()
            )
        if "long" in entry["abbreviation"] and isinstance(
            entry["abbreviation"]["long"], str
        ):
            entry["abbreviation"]["long"] = (
                entry["abbreviation"]["long"].strip().lower()
            )
