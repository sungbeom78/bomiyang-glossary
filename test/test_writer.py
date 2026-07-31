import json

from glossary.core import writer


def test_save_end_line(tmp_path) -> None:
    target = tmp_path / "words.json"

    writer._save(target, "words", [{"id": "alpha"}])

    assert target.read_bytes().endswith(b"\n")


def test_save_preserve_order(tmp_path, monkeypatch) -> None:
    words_path = tmp_path / "words.json"
    compounds_path = tmp_path / "compounds.json"
    words_path.write_text(
        json.dumps({"words": [{"id": "alpha"}, {"id": "zulu"}, {"id": "legacy"}]}),
        encoding="utf-8",
    )
    compounds_path.write_text('{"compounds": []}', encoding="utf-8")
    monkeypatch.setattr(writer, "WORDS_PATH", words_path)
    monkeypatch.setattr(writer, "COMPOUNDS_PATH", compounds_path)

    glossary_writer = writer.GlossaryWriter()
    glossary_writer.add_word({"id": "beta"})

    assert [word["id"] for word in glossary_writer._words] == [
        "alpha",
        "beta",
        "zulu",
        "legacy",
    ]
