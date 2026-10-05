"""용어 영역(areas) -- doc/glossary_area_rule.md"""
import json

import pytest

from glossary.core import areas as ar
from glossary.core import auditor as au
from glossary.core import writer

AREAS = [{"id": "general", "name_ko": "일반", "tags": ["root"]},
         {"id": "trading", "name_ko": "매매", "tags": ["domain", "legacy"]},
         {"id": "data", "name_ko": "데이터 명명", "tags": ["naming"]}]


def test_effective_senses_legacy_reads_lang_ko_as_first_domain():
    assert ar.effective_senses({"id": "value", "domain": ["market"], "lang": {"ko": "거래대금"}}) == {"market": ["거래대금"]}
    assert ar.effective_senses({"id": "x", "domain": "general", "lang": {"ko": "엑스"}}) == {"general": ["엑스"]}
    assert ar.effective_senses({"id": "no", "senses": {"general": ["금지"], "data": ["번호"]}}) == {"general": ["금지"], "data": ["번호"]}


def test_display_meaning_format():
    e = {"id": "subject", "senses": {"data": ["번호"], "general": ["주제", "과목", "주체"]}}
    assert ar.display_meaning(e, ["general", "trading", "data"]) == "주제/과목/주체, 번호"


def test_meaning_walks_declared_areas_from_most_specific():
    e = {"id": "no", "senses": {"general": ["금지"], "data": ["번호"]}}
    assert ar.meaning(e, ["general", "data"]) == {"area": "data", "names": ["번호"]}
    assert ar.meaning(e, ["general", "trading"]) == {"area": "general", "names": ["금지"]}
    assert ar.meaning(e, None) == {"area": "general", "names": ["금지"]}


def test_diagnose_r2_general_unknown():
    words = [{"id": "abort", "domain": ["system"], "lang": {"ko": "중단"}},
             {"id": "stop", "domain": ["general"], "lang": {"ko": "중단"}},
             {"id": "value", "domain": ["market"], "lang": {"ko": "거래대금"}},
             {"id": "zz", "domain": ["nowhere"], "lang": {"ko": "지지"}}]
    d = ar.diagnose(words, [], AREAS)
    assert {i["code"] for i in d["abort"]} >= {"R2_DUP_KO", "NO_GENERAL_SENSE", "UNKNOWN_AREA"} - {"UNKNOWN_AREA"}
    assert any(i["code"] == "R2_DUP_KO" for i in d["stop"])
    assert any(i["code"] == "NO_GENERAL_SENSE" for i in d["value"])
    assert any(i["code"] == "UNKNOWN_AREA" for i in d["zz"])
    assert ar.diagnose(words, [], AREAS, only_explicit=True) == {}          # 기존 항목은 validate 경고 대상이 아님


@pytest.fixture()
def gw(tmp_path, monkeypatch):
    (tmp_path / "words.json").write_text(json.dumps({"words": [
        {"id": "value", "domain": ["market"], "lang": {"en": "value", "ko": "거래대금"}},
        {"id": "no", "domain": ["system"], "lang": {"en": "no", "ko": "금지"}}]}, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "compounds.json").write_text('{"compounds": []}', encoding="utf-8")
    (tmp_path / "areas.json").write_text(json.dumps({"areas": AREAS}, ensure_ascii=False), encoding="utf-8")
    for name in ("WORDS_PATH", "COMPOUNDS_PATH", "AREAS_PATH"):
        monkeypatch.setattr(writer, name, tmp_path / f"{name.split('_')[0].lower()}.json")
    monkeypatch.setattr(writer, "_BACKUP_DIR", tmp_path / "backup")
    return writer.GlossaryWriter(), tmp_path


def test_add_sense_keeps_legacy_meaning_and_lang_ko(gw):
    w, d = gw
    w.add_sense("value", "general", ["값"])
    e = w.get_word("value")
    assert e["senses"] == {"market": ["거래대금"], "general": ["값"]}           # 기존 뜻을 잃지 않는다
    assert e["lang"]["ko"] == "거래대금" and e["domain"] == ["market", "general"]  # 대표 뜻은 그대로
    with pytest.raises(ValueError):
        w.add_sense("value", "nowhere", ["x"])                                    # 목록에 없는 영역 거부


def test_area_abbreviation_need_modify_and_area_list_saved(gw):
    w, d = gw
    assert w.add_area("school", "학교", ["domain"]) and not w.add_area("school", "학교")
    w.add_sense("no", "data", ["번호"]); w.set_area_abbreviation("no", "data", "NO")
    w.set_need_modify("value", [{"code": "NO_GENERAL_SENSE", "detail": "x"}])
    w.save()
    words = {x["id"]: x for x in json.loads((d / "words.json").read_text(encoding="utf-8"))["words"]}
    assert words["no"]["area_abbreviations"] == {"data": "no"} and words["value"]["need_modify"]["status"] == "open"
    assert "school" in {a["id"] for a in json.loads((d / "areas.json").read_text(encoding="utf-8"))["areas"]}
    w.set_need_modify("value", []); assert "need_modify" not in w.get_word("value")


def test_auditor_area_abbreviation_overrides_only_when_declared(tmp_path, monkeypatch):
    idx = tmp_path / "build" / "index"; idx.mkdir(parents=True)
    (idx / "word_min.json").write_text(json.dumps([{"id": "timestamp"}, {"id": "student"}]), encoding="utf-8")
    (idx / "compound_min.json").write_text(json.dumps([{"id": "active_trade"}]), encoding="utf-8")
    (idx / "variant_map.json").write_text(json.dumps({"at": {"root": "active_trade", "type": "abbreviation"}}), encoding="utf-8")
    (idx / "area_map.json").write_text(json.dumps({"data": {"at": "timestamp", "stud": "student"}}), encoding="utf-8")
    (idx / "senses.json").write_text(json.dumps({"timestamp": {"general": ["타임스탬프"], "data": ["시각"]}}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(au, "GLOSSARY_ROOT", tmp_path)
    plain = au.GlossaryAuditor()
    assert plain.resolve("at")["id"] == "active_trade" if hasattr(plain, "resolve") else True
    assert [i.code for i in plain.audit_identifier("stud_count", "module_var", "x") if i.severity == "FATAL"]   # 선언 없으면 영역 약어 없음
    data = au.GlossaryAuditor(areas=["general", "data"])
    r = data.resolve("at")
    assert r["id"] == "timestamp" and r["area"] == "data" and r["names"] == ["시각"]
    assert data.meaning("timestamp") == {"area": "data", "names": ["시각"]}
    assert "stud" not in str([i.detail for i in data.audit_identifier("stud_at", "module_var", "x") if i.severity == "FATAL"])
