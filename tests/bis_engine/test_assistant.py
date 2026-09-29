"""Tests for the plain-language assistant (template mode + LLM fallback)."""

from __future__ import annotations

import pytest

from bis_engine.engine.assistant import StandardsAssistant


@pytest.fixture(scope="module")
def assistant(retriever):
    return StandardsAssistant(retriever)


# ----------------------------------------------------------------- explain
def test_explain_code_english(assistant):
    out = assistant.answer("What is IS 456?")
    assert out["mode"] == "template"
    assert out["intent"] == "explain"
    assert "IS 456" in out["reply"]
    assert out["sources"] == ["IS 456"]


def test_explain_in_hindi(assistant):
    out = assistant.answer("IS 456 क्या है?", lang="hi")
    assert out["lang"] == "hi"
    assert "IS 456" in out["reply"]
    assert "आसान भाषा" in out["reply"]


def test_explain_in_telugu(assistant):
    out = assistant.answer("IS 4984 అంటే ఏమిటి?", lang="te")
    assert out["lang"] == "te"
    assert "IS 4984" in out["reply"]
    assert "సులభ" in out["reply"]


def test_explain_falls_back_to_summary_for_unmapped_codes(assistant):
    out = assistant.answer("What is IS 822?")
    assert out["intent"] == "explain"
    assert "IS 822" in out["reply"]


# --------------------------------------------------------------- recommend
def test_recommend_standard_for_product(assistant):
    out = assistant.answer("Which standard for drinking water pipes?")
    assert out["intent"] == "recommend"
    assert "IS 4984" in out["reply"]
    assert "IS 4984" in out["sources"]


def test_recommend_in_hindi(assistant):
    out = assistant.answer("पीने के पानी के पाइप के लिए कौन सा मानक?")
    assert out["lang"] == "hi"
    assert "IS 4984" in out["reply"]


def test_recommend_includes_allied_hint(assistant):
    out = assistant.answer("Which standard for TMT bars?")
    assert "IS 1786" in out["reply"]


# ------------------------------------------------------------ certification
def test_certification_intent(assistant):
    out = assistant.answer("Does a pressure cooker need ISI mark?")
    assert out["intent"] == "certification"
    assert "IS 2347" in out["reply"]
    assert "ISI" in out["reply"]


def test_certification_for_named_code(assistant):
    out = assistant.answer("certification requirements for IS 13252 (Part 1)")
    assert "CRS" in out["reply"]


# ------------------------------------------------------------------ version
def test_version_intent(assistant):
    out = assistant.answer("What is the latest version of IS 1786?")
    assert out["intent"] == "version"
    assert "2008" in out["reply"]


def test_version_intent_flags_known_pitfall(assistant):
    out = assistant.answer("Latest version of IS 456?")
    assert "1978" in out["reply"]  # the bad example is surfaced


# --------------------------------------------------------------------- help
def test_help_on_gibberish(assistant):
    out = assistant.answer("hello there")
    assert out["intent"] == "help"
    assert out["sources"] == []
    assert "BIS catalogue" in out["reply"]


def test_unknown_code_never_invents(assistant):
    out = assistant.answer("What is IS 99999?")
    assert "IS 99999" not in out["reply"]


# --------------------------------------------------------------- LLM fallback
def test_llm_mode_absent_by_default(assistant):
    out = assistant.answer("What is IS 456?")
    assert out["mode"] == "template"


def test_llm_failure_falls_back_to_template(assistant, monkeypatch):
    monkeypatch.setattr(assistant, "llm_enabled", True)
    monkeypatch.setattr(assistant, "_llm_reply", lambda *a, **k: None)
    out = assistant.answer("What is IS 456?")
    assert out["mode"] == "template"


def test_llm_success_upgrades_reply(assistant, monkeypatch):
    monkeypatch.setattr(assistant, "llm_enabled", True)
    monkeypatch.setattr(
        assistant, "_llm_reply",
        lambda message, lang, sources, history: "LLM explanation of the standard.")
    out = assistant.answer("What is IS 456?")
    assert out["mode"] == "llm"
    assert "LLM explanation" in out["reply"]
    assert "BIS catalogue" in out["reply"]  # disclaimer always appended


# ---------------------------------------------------------------- API layer
def test_assistant_endpoint(client):
    res = client.post("/api/assistant", json={"message": "What is IS 456?"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["intent"] == "explain"
    assert data["mode"] == "template"


def test_assistant_endpoint_respects_lang(client):
    res = client.post("/api/assistant", json={"message": "What is IS 456?", "lang": "te"})
    assert res.json()["lang"] == "te"


def test_assistant_endpoint_validates_input(client):
    assert client.post("/api/assistant", json={"message": "h"}).status_code == 422
    assert client.post("/api/assistant",
                       json={"message": "What is IS 456?", "lang": "fr"}).status_code == 422
