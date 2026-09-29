"""Static site route tests (v0.2) — every page must render with its assets."""

import pytest


@pytest.mark.parametrize("path", ["/", "/analyzer", "/standards", "/alerts",
                                  "/assistant", "/docs-page"])
def test_pages_render(client, path):
    res = client.get(path)
    assert res.status_code == 200
    assert "styles.css" in res.text


@pytest.mark.parametrize("path", ["/", "/assistant", "/analyzer"])
def test_i18n_and_chat_assets_present(client, path):
    res = client.get(path)
    assert "/static/js/i18n.js" in res.text
    assert 'data-i18n="nav.assistant"' in res.text


def test_assistant_page_has_chat_shell(client):
    res = client.get("/assistant")
    assert 'id="chat-page"' in res.text
    assert 'id="chat-log"' in res.text
    assert "/static/js/chat.js" in res.text


def test_analyzer_page_has_upload_zone(client):
    res = client.get("/analyzer")
    assert 'id="file-input"' in res.text
    assert 'accept=".pdf,.docx"' in res.text


def test_standard_detail_route(client):
    res = client.get("/standards/IS%20456")
    assert res.status_code == 200
    assert 'id="detail"' in res.text
