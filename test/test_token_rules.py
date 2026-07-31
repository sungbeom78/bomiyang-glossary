from unittest.mock import MagicMock

import httpx

from glossary.core.auditor import GlossaryAuditor
from glossary.core.token_rules import check_dictionary_api


def _noun_response() -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = [
        {
            "meanings": [
                {
                    "partOfSpeech": "noun",
                    "definitions": [{"definition": "test definition"}],
                }
            ]
        }
    ]
    return response


def test_dictionary_api_retry_after_error(monkeypatch) -> None:
    cache_clear = getattr(check_dictionary_api, "cache_clear", None)
    if callable(cache_clear):
        cache_clear()
    get = MagicMock(
        side_effect=[
            httpx.ReadTimeout("timeout"),
            _noun_response(),
        ]
    )
    monkeypatch.setattr("glossary.core.token_rules.httpx.get", get)

    valid, meaning = check_dictionary_api("year")

    assert valid is True
    assert meaning == "test definition"
    assert get.call_count == 2


def test_dictionary_api_failure_is_not_cached(monkeypatch) -> None:
    cache_clear = getattr(check_dictionary_api, "cache_clear", None)
    if callable(cache_clear):
        cache_clear()
    get = MagicMock(side_effect=httpx.ReadTimeout("timeout"))
    monkeypatch.setattr("glossary.core.token_rules.httpx.get", get)

    assert check_dictionary_api("activity") == (False, "")

    get.side_effect = None
    get.return_value = _noun_response()

    assert check_dictionary_api("activity") == (True, "test definition")


def test_glossary_auditor_uses_local_source_of_truth(monkeypatch) -> None:
    get = MagicMock(side_effect=AssertionError("external lookup must not run"))
    monkeypatch.setattr("glossary.core.token_rules.httpx.get", get)

    issues = GlossaryAuditor().audit_identifier(
        "definitelyunregisteredtoken",
        "function",
        "test",
    )

    assert any(issue.code == "UNREGISTERED_WORD" for issue in issues)
    get.assert_not_called()
